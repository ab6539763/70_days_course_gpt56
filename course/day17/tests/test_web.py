"""Day 17 Web API、Token 窗口与 OpenAPI 路由单测。"""

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

with tempfile.TemporaryDirectory(prefix="nexus-day17-web-") as temporary:
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
    assert "/api/window" in openapi.get_json()["paths"]

    for index in range(5):
        client.post("/api/chat", json={"prompt": f"第{index}轮"})

    limited = client.post("/api/chat", json={"prompt": "窗口限制", "max_history": 2})
    assert limited.status_code == 200
    limited_payload = limited.get_json()
    assert limited_payload["window"]["history_window"] == 2
    assert limited_payload["window"]["window_applied"] is True
    assert len(limited_payload["messages"]) == 12

    empty = client.post("/api/chat", json={"prompt": "  "})
    assert empty.get_json()["error"]["code"] == ERROR_EMPTY_PROMPT

server.shutdown()
print("Day 17 Web 单测通过：/api/window、max_history 与 OpenAPI 均正确。")
