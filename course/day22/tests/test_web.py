"""Day 22 Web API、审计日志、乐观锁、断流恢复与会话隔离路由单测。"""

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

from nexus.constants import APP_VERSION, REVISION_HEADER, SESSION_HEADER
from nexus.http.config import reset_bootstrap
from nexus.web.app import create_app
from nexus.web.errors import ERROR_EMPTY_PROMPT, ERROR_INVALID_SESSION, ERROR_REVISION_CONFLICT, ERROR_SESSION_REQUIRED


server, base_url = mock_api.start_mock_api_server()
os.environ["NEXUS_API_KEY"] = "web-test-key"
os.environ["NEXUS_API_BASE_URL"] = base_url
os.environ["NEXUS_USE_MOCK"] = "1"
os.environ["NEXUS_HISTORY_WINDOW"] = "20"
reset_bootstrap()

with tempfile.TemporaryDirectory(prefix="nexus-day22-web-") as temporary:
    session_dir = Path(temporary) / "sessions"
    audit_dir = Path(temporary) / "audit"
    os.environ["NEXUS_AUDIT_DIR"] = str(audit_dir)
    app = create_app(session_dir=str(session_dir))
    client = app.test_client()

    health = client.get("/api/health")
    assert health.status_code == 200
    health_payload = health.get_json()
    assert health_payload["app_version"] == APP_VERSION
    assert "audit_dir" in health_payload
    assert "audit_count" in health_payload

    created = client.post("/api/session", json={"owner": "测试用户"})
    session_id = created.get_json()["session_id"]
    headers = {SESSION_HEADER: session_id}

    revision = client.get("/api/revision", headers=headers)
    assert revision.get_json()["revision"] == 1

    openapi = client.get("/api/openapi.json")
    spec = openapi.get_json()
    assert "/api/revision" in spec["paths"]
    assert "/api/audit" in spec["paths"]
    assert "/api/stream/resume/{resume_token}" in spec["paths"]

    stream = client.post(
        "/api/chat/stream",
        json={"prompt": "流式测试", "expected_revision": 1},
        headers=headers,
    )
    assert stream.status_code == 200
    stream_text = stream.get_data(as_text=True)
    assert "event: done" in stream_text

    interrupt_headers = {**headers, "X-Stream-Simulate-Interrupt": "1"}
    interrupted = client.post(
        "/api/chat/stream",
        json={"prompt": "断流测试", "expected_revision": 2},
        headers=interrupt_headers,
    )
    interrupted_text = interrupted.get_data(as_text=True)
    assert "event: interrupted" in interrupted_text
    data_lines = [line for line in interrupted_text.split("\n") if line.startswith("data:")]
    interrupted_payload = json.loads(data_lines[-1].replace("data:", "", 1).strip())
    resume_token = interrupted_payload["resume_token"]
    resume_revision = interrupted_payload["revision"]

    resumed = client.post(
        "/api/chat/stream",
        json={"resume_token": resume_token, "expected_revision": resume_revision},
        headers=headers,
    )
    assert "event: done" in resumed.get_data(as_text=True)

    conflict = client.post(
        "/api/chat",
        json={"prompt": "冲突", "expected_revision": 1},
        headers=headers,
    )
    assert conflict.get_json()["error"]["code"] == ERROR_REVISION_CONFLICT

    ok = client.post(
        "/api/chat",
        json={"prompt": "正常", "expected_revision": client.get("/api/revision", headers=headers).get_json()["revision"]},
        headers={**headers, REVISION_HEADER: str(client.get("/api/revision", headers=headers).get_json()["revision"])},
    )
    assert ok.status_code == 200

    audit = client.get("/api/audit", headers=headers)
    assert audit.status_code == 200
    audit_payload = audit.get_json()
    assert audit_payload["count"] >= 2
    assert audit_payload["session_id"] == session_id
    assert any(item["action"] == "web_chat" for item in audit_payload["records"])

    missing = client.post("/api/chat", json={"prompt": "无会话"})
    assert missing.get_json()["error"]["code"] == ERROR_SESSION_REQUIRED

    empty = client.post(
        "/api/chat/stream",
        json={"prompt": "  ", "expected_revision": 1},
        headers=headers,
    )
    assert empty.get_json()["error"]["code"] == ERROR_EMPTY_PROMPT

server.shutdown()
print("Day 22 Web 单测通过：审计日志、乐观锁、断流恢复与会话隔离均正确。")
