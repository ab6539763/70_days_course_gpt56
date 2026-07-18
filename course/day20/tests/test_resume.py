"""Day 20 断流恢复、resume_token 与 StreamResumeStore 单测。"""

import json
import os
import sys
import tempfile
import time
from pathlib import Path


SOLUTION = Path(__file__).parents[1] / "solution"
sys.path.insert(0, str(SOLUTION))

from nexus.constants import RESUME_TOKEN_PREFIX
from nexus.platform.state import PlatformState
from nexus.web.app import create_app
from nexus.web.errors import ERROR_INVALID_RESUME, ERROR_RESUME_EXPIRED
from nexus.web.stream_resume import StreamResumeStore, validate_resume_token
from nexus.web.state_manager import WebStateManager
from nexus.web.validation import validate_stream_chat_request


os.environ["NEXUS_USE_MOCK"] = "1"
os.environ["NEXUS_HISTORY_WINDOW"] = "20"

store = StreamResumeStore(ttl_seconds=60)
record = store.create(
    session_id="nxs_" + "a" * 32,
    data_file="/tmp/demo.json",
    user_prompt="测试",
    partial_assistant="部分",
)
assert record.resume_token.startswith(RESUME_TOKEN_PREFIX)
assert store.get(record.resume_token) is not None
assert validate_stream_chat_request({"resume_token": record.resume_token})["resume_token"]
assert store.consume(record.resume_token) is not None
assert store.get(record.resume_token) is None

try:
    validate_resume_token("bad-token")
except ValueError as error:
    assert "格式非法" in str(error)
else:
    raise AssertionError("应拒绝非法 resume_token")

try:
    validate_stream_chat_request({})
except Exception:
    pass
else:
    raise AssertionError("无 prompt 且无 resume_token 应失败")

with tempfile.TemporaryDirectory(prefix="nexus-day20-resume-") as temporary:
    data_file = Path(temporary) / "state.json"
    session_id = "nxs_" + "b" * 32
    manager = WebStateManager(str(data_file), session_id=session_id)
    resume_store = StreamResumeStore(ttl_seconds=120)

    events = list(
        manager.chat_stream(
            "断流单测",
            resume_store=resume_store,
            interrupt_after=1,
        )
    )
    interrupted = next(item for item in events if item["event"] == "interrupted")
    token = interrupted["payload"]["resume_token"]
    partial = interrupted["payload"]["partial"]
    assert partial
    assert resume_store.get(token) is not None

    resumed = list(
        manager.chat_stream(
            resume_token=token,
            resume_store=resume_store,
        )
    )
    assert any(item["event"] == "resume" for item in resumed)
    done = next(item for item in resumed if item["event"] == "done")
    assert done["payload"]["assistant"].startswith(partial)
    assert done["payload"]["resumed"] is True
    assert resume_store.get(token) is None

    state = manager.load_or_create()
    assert len(state.messages) == 2
    assert state.messages[-1].role == "assistant"

    expired_store = StreamResumeStore(ttl_seconds=1)
    expired = expired_store.create(
        session_id=session_id,
        data_file=str(data_file),
        user_prompt="过期",
        partial_assistant="x",
    )
    time.sleep(1.1)
    assert expired_store.get(expired.resume_token) is None

    app = create_app(session_dir=str(Path(temporary) / "sessions"))
    client = app.test_client()
    created = client.post("/api/session", json={"owner": "resume-test"})
    session = created.get_json()["session_id"]
    headers = {"X-Session-Id": session, "X-Stream-Simulate-Interrupt": "1"}

    stream = client.post(
        "/api/chat/stream",
        json={"prompt": "Web 断流"},
        headers=headers,
    )
    assert stream.status_code == 200
    stream_text = stream.get_data(as_text=True)
    assert "event: interrupted" in stream_text
    interrupted_line = [
        line for line in stream_text.split("\n") if line.startswith("data:")
    ][-1]
    interrupted_payload = json.loads(interrupted_line.replace("data:", "", 1).strip())
    web_token = interrupted_payload["resume_token"]

    info = client.get(f"/api/stream/resume/{web_token}", headers={"X-Session-Id": session})
    assert info.status_code == 200
    assert info.get_json()["partial"]

    resume_stream = client.post(
        "/api/chat/stream",
        json={"resume_token": web_token},
        headers={"X-Session-Id": session},
    )
    resume_text = resume_stream.get_data(as_text=True)
    assert "event: done" in resume_text

    bad_info = client.get(
        f"/api/stream/resume/{web_token}",
        headers={"X-Session-Id": session},
    )
    assert bad_info.get_json()["error"]["code"] == ERROR_RESUME_EXPIRED

    invalid = client.get(
        f"/api/stream/resume/not-a-token",
        headers={"X-Session-Id": session},
    )
    assert invalid.get_json()["error"]["code"] == ERROR_INVALID_RESUME

state2 = PlatformState.empty()
partial_parts = []
interrupted = False
try:
    for item in state2.conversation_turn_stream(
        "续传底层",
        interrupt_after=1,
        force_mock=True,
    ):
        if item["event"] == "chunk":
            partial_parts.append(item["payload"]["delta"])
except Exception:
    interrupted = True
assert interrupted is True
partial_text = "".join(partial_parts)
resumed_events = list(state2.resume_stream_turn(partial_text, force_mock=True))
assert any(item["event"] == "resume" for item in resumed_events)
done2 = next(item for item in resumed_events if item["event"] == "done")
assert done2["payload"]["assistant"].startswith(partial_text)

print("Day 20 断流恢复单测通过：resume_token、interrupted 事件与续传均正确。")
