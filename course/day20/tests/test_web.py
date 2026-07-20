"""Day 20 Web API、会话隔离、SSE 与断流恢复路由单测。"""

import importlib.util
import json
import os
import sys
import tempfile
from pathlib import Path


SOLUTION = Path(__file__).parents[1] / "solution"
sys.path.insert(0, str(SOLUTION))

MOCK = Path(__file__).parent / "mock_api.py"
spec = importlib.util.spec_from_file_location("mock_api", MOCK)
mock_api = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(mock_api)

from nexus.constants import APP_VERSION, SESSION_HEADER
from nexus.http.config import reset_bootstrap
from nexus.web.app import create_app
from nexus.web.errors import ERROR_EMPTY_PROMPT, ERROR_INVALID_SESSION, ERROR_SESSION_REQUIRED


server, base_url = mock_api.start_mock_api_server()
os.environ["NEXUS_API_KEY"] = "web-test-key"
os.environ["NEXUS_API_BASE_URL"] = base_url
os.environ["NEXUS_USE_MOCK"] = "1"
os.environ["NEXUS_HISTORY_WINDOW"] = "20"
reset_bootstrap()

with tempfile.TemporaryDirectory(prefix="nexus-day20-web-") as temporary:
    session_dir = Path(temporary) / "sessions"
    app = create_app(session_dir=str(session_dir))
    client = app.test_client()

    health = client.get("/api/health")
    assert health.status_code == 200
    health_payload = health.get_json()
    assert health_payload["app_version"] == APP_VERSION
    assert health_payload["session_count"] == 0
    assert "pending_resume_count" in health_payload
    assert "session_dir" in health_payload

    missing = client.post("/api/chat", json={"prompt": "无会话"})
    assert missing.get_json()["error"]["code"] == ERROR_SESSION_REQUIRED

    created = client.post("/api/session", json={"owner": "测试用户"})
    assert created.status_code == 200
    session_id = created.get_json()["session_id"]
    headers = {SESSION_HEADER: session_id}

    openapi = client.get("/api/openapi.json")
    spec = openapi.get_json()
    assert "/api/session" in spec["paths"]
    assert "/api/stream/resume/{resume_token}" in spec["paths"]
    assert "StreamChatRequest" in spec["components"]["schemas"]

    stream = client.post("/api/chat/stream", json={"prompt": "流式测试"}, headers=headers)
    assert stream.status_code == 200
    stream_text = stream.get_data(as_text=True)
    assert "event: chunk" in stream_text
    assert "event: done" in stream_text

    interrupt_headers = {**headers, "X-Stream-Simulate-Interrupt": "1"}
    interrupted = client.post(
        "/api/chat/stream",
        json={"prompt": "断流测试"},
        headers=interrupt_headers,
    )
    interrupted_text = interrupted.get_data(as_text=True)
    assert "event: interrupted" in interrupted_text
    data_lines = [line for line in interrupted_text.split("\n") if line.startswith("data:")]
    interrupted_payload = json.loads(data_lines[-1].replace("data:", "", 1).strip())
    resume_token = interrupted_payload["resume_token"]

    resumed = client.post(
        "/api/chat/stream",
        json={"resume_token": resume_token},
        headers=headers,
    )
    resumed_text = resumed.get_data(as_text=True)
    assert "event: done" in resumed_text

    second = client.post("/api/session", json={})
    session_b = second.get_json()["session_id"]
    headers_b = {SESSION_HEADER: session_b}

    client.post("/api/chat", json={"prompt": "会话A"}, headers=headers)
    client.post("/api/chat", json={"prompt": "会话B"}, headers=headers_b)

    messages_a = client.get("/api/messages", headers=headers).get_json()
    messages_b = client.get("/api/messages", headers=headers_b).get_json()
    users_a = [item for item in messages_a["messages"] if item["role"] == "user"]
    users_b = [item for item in messages_b["messages"] if item["role"] == "user"]
    assert users_a[-1]["content"] == "会话A"
    assert users_b[-1]["content"] == "会话B"

    listing = client.get("/api/sessions")
    assert listing.get_json()["count"] == 2

    bad = client.get("/api/messages", headers={SESSION_HEADER: "nxs_invalid"})
    assert bad.get_json()["error"]["code"] == ERROR_INVALID_SESSION

    empty = client.post("/api/chat/stream", json={"prompt": "  "}, headers=headers)
    assert empty.get_json()["error"]["code"] == ERROR_EMPTY_PROMPT

    for index in range(5):
        client.post("/api/chat", json={"prompt": f"第{index}轮"}, headers=headers)

    limited = client.post(
        "/api/chat/stream",
        json={"prompt": "窗口流式", "max_history": 2},
        headers=headers,
    )
    limited_text = limited.get_data(as_text=True)
    done_line = [line for line in limited_text.split("\n") if line.startswith("data:")][-1]
    done_payload = json.loads(done_line.replace("data:", "", 1).strip())
    assert done_payload["window"]["history_window"] == 2
    assert done_payload["window"]["window_applied"] is True
    assert done_payload["session_id"] == session_id

server.shutdown()
print("Day 20 Web 单测通过：断流恢复、会话隔离与 SSE 均正确。")
