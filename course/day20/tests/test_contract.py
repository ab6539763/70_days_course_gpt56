"""Day 20 OpenAPI 契约与断流恢复端点单测。"""

import sys
from pathlib import Path


SOLUTION = Path(__file__).parents[1] / "solution"
sys.path.insert(0, str(SOLUTION))

from nexus.constants import APP_VERSION, MAX_HISTORY_WINDOW
from nexus.web.errors import (
    ERROR_INVALID_RESUME,
    ERROR_INVALID_SESSION,
    ERROR_RESUME_EXPIRED,
    ERROR_SESSION_REQUIRED,
    build_error_body,
)
from nexus.web.openapi import build_openapi_spec
from nexus.web.validation import (
    RequestValidationError,
    validate_session_create_request,
    validate_stream_chat_request,
)


spec = build_openapi_spec("http://test.local")
assert spec["openapi"] == "3.0.3"
assert spec["info"]["version"] == APP_VERSION
assert "/api/session" in spec["paths"]
assert "/api/stream/resume/{resume_token}" in spec["paths"]
assert "/api/chat/stream" in spec["paths"]
assert "SessionHeader" in spec["components"]["parameters"]
assert "StreamChatRequest" in spec["components"]["schemas"]
assert "StreamInterruptedEvent" in spec["components"]["schemas"]
assert "ResumeInfoResponse" in spec["components"]["schemas"]
chat_path = spec["paths"]["/api/chat"]["post"]
assert any(item.get("$ref") == "#/components/parameters/SessionHeader" for item in chat_path["parameters"])
stream_path = spec["paths"]["/api/chat/stream"]["post"]
assert "X-Stream-Simulate-Interrupt" in str(stream_path["parameters"])

session = validate_session_create_request({"owner": "团队A"})
assert session["owner"] == "团队A"
assert validate_session_create_request(None) == {}

body = build_error_body(ERROR_SESSION_REQUIRED, "缺少会话")
assert body["error"]["code"] == ERROR_SESSION_REQUIRED
body2 = build_error_body(ERROR_INVALID_SESSION, "非法")
assert body2["error"]["code"] == ERROR_INVALID_SESSION
body3 = build_error_body(ERROR_INVALID_RESUME, "非法 token")
assert body3["error"]["code"] == ERROR_INVALID_RESUME
body4 = build_error_body(ERROR_RESUME_EXPIRED, "过期")
assert body4["error"]["code"] == ERROR_RESUME_EXPIRED

try:
    validate_stream_chat_request({"prompt": ""})
except RequestValidationError:
    pass
else:
    raise AssertionError("空 prompt 应失败")

resume_body = validate_stream_chat_request(
    {"resume_token": "rst_" + "a" * 32}
)
assert resume_body["resume_token"].startswith("rst_")
assert MAX_HISTORY_WINDOW >= 20

print("Day 20 契约单测通过：OpenAPI 断流恢复端点与 resume_token 均正确。")
