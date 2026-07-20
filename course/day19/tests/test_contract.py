"""Day 19 OpenAPI 契约与会话隔离端点单测。"""

import sys
from pathlib import Path


SOLUTION = Path(__file__).parents[1] / "solution"
sys.path.insert(0, str(SOLUTION))

from nexus.constants import APP_VERSION, MAX_HISTORY_WINDOW
from nexus.web.errors import ERROR_INVALID_SESSION, ERROR_SESSION_REQUIRED, build_error_body
from nexus.web.openapi import build_openapi_spec
from nexus.web.validation import RequestValidationError, validate_session_create_request


spec = build_openapi_spec("http://test.local")
assert spec["openapi"] == "3.0.3"
assert spec["info"]["version"] == APP_VERSION
assert "/api/session" in spec["paths"]
assert "/api/sessions" in spec["paths"]
assert "/api/chat/stream" in spec["paths"]
assert "SessionHeader" in spec["components"]["parameters"]
assert "SessionCreateResponse" in spec["components"]["schemas"]
chat_path = spec["paths"]["/api/chat"]["post"]
assert any(item.get("$ref") == "#/components/parameters/SessionHeader" for item in chat_path["parameters"])

session = validate_session_create_request({"owner": "团队A"})
assert session["owner"] == "团队A"
assert validate_session_create_request(None) == {}

body = build_error_body(ERROR_SESSION_REQUIRED, "缺少会话")
assert body["error"]["code"] == ERROR_SESSION_REQUIRED
body2 = build_error_body(ERROR_INVALID_SESSION, "非法")
assert body2["error"]["code"] == ERROR_INVALID_SESSION

print("Day 19 契约单测通过：OpenAPI 会话端点与 X-Session-Id 均正确。")
