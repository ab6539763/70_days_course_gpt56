"""Day 16 Web API 与 OpenAPI 路由单测。"""

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
from nexus.web.errors import ERROR_EMPTY_PROMPT


server, base_url = mock_api.start_mock_api_server()
os.environ["NEXUS_API_KEY"] = "web-test-key"
os.environ["NEXUS_API_BASE_URL"] = base_url
os.environ["NEXUS_USE_MOCK"] = "0"
reset_bootstrap()

with tempfile.TemporaryDirectory(prefix="nexus-day16-web-") as temporary:
    data_file = Path(temporary) / "nexus_platform.json"
    app = create_app(data_file=str(data_file))
    client = app.test_client()

    health = client.get("/api/health")
    assert health.status_code == 200
    health_payload = health.get_json()
    assert health_payload["ok"] is True
    assert health_payload["app_version"] == APP_VERSION
    assert health_payload["trace_id"]

    openapi = client.get("/api/openapi.json")
    assert openapi.status_code == 200
    openapi_payload = openapi.get_json()
    assert openapi_payload["openapi"] == "3.0.3"
    assert openapi_payload["info"]["version"] == APP_VERSION

    docs = client.get("/docs")
    assert docs.status_code == 200
    assert b"swagger-ui" in docs.data.lower()

    page = client.get("/")
    assert page.status_code == 200

    empty = client.post("/api/chat", json={"prompt": "  "})
    assert empty.status_code == 400
    empty_payload = empty.get_json()
    assert empty_payload["error"]["code"] == ERROR_EMPTY_PROMPT

    bad_field = client.post("/api/chat", json={"prompt": "x", "unknown": 1})
    assert bad_field.status_code == 400
    assert bad_field.get_json()["error"]["code"] == "VALIDATION_FAILED"

    first = client.post("/api/chat", json={"prompt": "Web 第一轮"})
    assert first.status_code == 200, first.get_json()
    first_payload = first.get_json()
    assert first_payload["ok"] is True
    assert "HTTP mock 回复" in first_payload["assistant"]
    assert len(first_payload["messages"]) == 2

    second = client.post("/api/chat", json={"prompt": "Web 第二轮"})
    assert second.status_code == 200
    assert len(second.get_json()["messages"]) == 4

    cleared = client.post("/api/clear", json={"keep_system": True})
    assert cleared.status_code == 200
    assert cleared.get_json()["messages"] == []

    saved = json.loads(data_file.read_text(encoding="utf-8"))
    assert saved["schema_version"] == 4
    assert saved["owner"] == "WEB_USER"

server.shutdown()
print("Day 16 Web 单测通过：OpenAPI、标准错误与多轮 API 均正确。")
