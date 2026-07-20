"""Day 21 乐观锁、expected_revision 与 REVISION_CONFLICT 单测。"""

import json
import os
import sys
import tempfile
from pathlib import Path


SOLUTION = Path(__file__).parents[1] / "solution"
sys.path.insert(0, str(SOLUTION))

from nexus.exceptions import RevisionConflictError
from nexus.persistence.revision_guard import (
    assert_revision_on_disk,
    parse_expected_revision,
    resolve_expected_revision,
)
from nexus.persistence.storage import load_state, persist_change
from nexus.platform.state import PlatformState
from nexus.web.app import create_app
from nexus.web.errors import ERROR_REVISION_CONFLICT
from nexus.web.state_manager import WebStateManager


os.environ["NEXUS_USE_MOCK"] = "1"

assert parse_expected_revision(0) == 0
assert parse_expected_revision("3") == 3
assert resolve_expected_revision("2", None) == 2
assert resolve_expected_revision(None, 5) == 5

with tempfile.TemporaryDirectory(prefix="nexus-day21-rev-") as temporary:
    data_file = Path(temporary) / "state.json"
    state = PlatformState.empty()
    state.owner = "LOCK_TEST"
    persist_change(state, str(data_file))

    try:
        assert_revision_on_disk(str(data_file), 0)
    except RevisionConflictError:
        pass
    else:
        raise AssertionError("过期 expected_revision 应冲突")

    manager_a = WebStateManager(str(data_file))
    manager_b = WebStateManager(str(data_file))
    base = manager_a.revision_info()["revision"]
    manager_a.chat("第一次写入", expected_revision=base)
    after = manager_a.revision_info()["revision"]
    assert after == base + 1

    try:
        manager_b.chat("过期写入", expected_revision=base)
    except RevisionConflictError as error:
        assert error.expected == base
        assert error.actual == after
    else:
        raise AssertionError("应抛出 RevisionConflictError")

    manager_b.chat("重试写入", expected_revision=after)
    assert manager_b.revision_info()["revision"] == after + 1

    app = create_app(session_dir=str(Path(temporary) / "sessions"))
    client = app.test_client()
    created = client.post("/api/session", json={"owner": "web-lock"})
    session = created.get_json()["session_id"]
    headers = {"X-Session-Id": session}

    revision = client.get("/api/revision", headers=headers)
    assert revision.status_code == 200
    rev_payload = revision.get_json()
    assert rev_payload["revision"] == 1

    chat = client.post(
        "/api/chat",
        json={"prompt": "带锁对话", "expected_revision": 1},
        headers={**headers, "X-Expected-Revision": "1"},
    )
    assert chat.status_code == 200
    assert chat.get_json()["revision"] == 2

    conflict = client.post(
        "/api/chat",
        json={"prompt": "冲突", "expected_revision": 1},
        headers=headers,
    )
    assert conflict.status_code == 409
    conflict_body = conflict.get_json()
    assert conflict_body["error"]["code"] == ERROR_REVISION_CONFLICT
    assert conflict_body["actual_revision"] == 2

    stream = client.post(
        "/api/chat/stream",
        json={"prompt": "流式锁", "expected_revision": 2},
        headers=headers,
    )
    stream_text = stream.get_data(as_text=True)
    assert "event: done" in stream_text

    stale_stream = client.post(
        "/api/chat/stream",
        json={"prompt": "流式冲突", "expected_revision": 2},
        headers=headers,
    )
    stale_text = stale_stream.get_data(as_text=True)
    assert "REVISION_CONFLICT" in stale_text

    cleared = client.post(
        "/api/clear",
        json={"keep_system": True, "expected_revision": 3},
        headers=headers,
    )
    assert cleared.status_code == 200

    openapi = client.get("/api/openapi.json").get_json()
    assert "/api/revision" in openapi["paths"]
    assert "ExpectedRevisionHeader" in openapi["components"]["parameters"]
    assert "RevisionConflictResponse" in openapi["components"]["schemas"]

print("Day 21 乐观锁单测通过：expected_revision、409 冲突与 GET /api/revision 均正确。")
