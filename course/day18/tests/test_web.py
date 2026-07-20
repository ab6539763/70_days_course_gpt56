"""Day 18 Web API、SSE 流式与 OpenAPI 路由单测。"""

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

from nexus.constants import APP_VERSION
from nexus.http.config import reset_bootstrap
from nexus.web.app import create_app
from nexus.web.errors import ERROR_EMPTY_PROMPT, ERROR_INVALID_WINDOW


server, base_url = mock_api.start_mock_api_server()
os.environ["NEXUS_API_KEY"] = "web-test-key"
os.environ["NEXUS_API_BASE_URL"] = base_url
os.environ["NEXUS_USE_MOCK"] = "0"
os.environ["NEXUS_HISTORY_WINDOW"] = "20"
reset_bootstrap()

with tempfile.TemporaryDirectory(prefix="nexus-day18-web-") as temporary:
    data_file = Path(temporary) / "nexus_platform.json"
    app = create_app(data_file=str(data_file))
    client = app.test_client()

    health = client.get("/api/health")
    assert health.status_code == 200
    health_payload = health.get_json()
    assert health_payload["app_version"] == APP_VERSION
    assert "default_history_window" in health_payload

    window = client.get("/api/window")
    assert window.status_code == 200
    window_payload = window.get_json()
    assert window_payload["ok"] is True
    assert window_payload["default_history_window"] == 20

    bad_window = client.get("/api/window?max_history=9999")
    assert bad_window.status_code == 400
    assert bad_window.get_json()["error"]["code"] == ERROR_INVALID_WINDOW

    openapi = client.get("/api/openapi.json")
    spec = openapi.get_json()
    assert "/api/window" in spec["paths"]
    assert "/api/chat/stream" in spec["paths"]

    stream = client.post("/api/chat/stream", json={"prompt": "流式测试"})
    assert stream.status_code == 200
    assert "text/event-stream" in (stream.content_type or "")
    stream_text = stream.get_data(as_text=True)
    assert "event: chunk" in stream_text
    assert "event: done" in stream_text
    assert '"delta"' in stream_text
    assert '"revision"' in stream_text

    for index in range(5):
        client.post("/api/chat", json={"prompt": f"第{index}轮"})

    limited = client.post(
        "/api/chat/stream",
        json={"prompt": "窗口流式", "max_history": 2},
    )
    assert limited.status_code == 200
    limited_text = limited.get_data(as_text=True)
    assert "event: done" in limited_text
    done_line = [line for line in limited_text.split("\n") if line.startswith("data:")][-1]
    done_payload = json.loads(done_line.replace("data:", "", 1).strip())
    assert done_payload["window"]["history_window"] == 2
    assert done_payload["window"]["window_applied"] is True
    assert len(done_payload["messages"]) == 14

    empty = client.post("/api/chat/stream", json={"prompt": "  "})
    assert empty.get_json()["error"]["code"] == ERROR_EMPTY_PROMPT

server.shutdown()
print("Day 18 Web 单测通过：/api/chat/stream、max_history 与 OpenAPI 均正确。")
