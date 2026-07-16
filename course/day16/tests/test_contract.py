"""Day 16 OpenAPI 契约、错误码与请求校验单测。"""

import sys
from pathlib import Path


SOLUTION = Path(__file__).parents[1] / "solution"
sys.path.insert(0, str(SOLUTION))

from nexus.constants import APP_VERSION
from nexus.web.errors import (
    ERROR_EMPTY_PROMPT,
    ERROR_HTTP_STATUS,
    build_error_body,
)
from nexus.web.openapi import build_openapi_spec
from nexus.web.validation import (
    RequestValidationError,
    validate_chat_request,
    validate_clear_request,
)


spec = build_openapi_spec("http://test.local")
assert spec["openapi"] == "3.0.3"
assert spec["info"]["version"] == APP_VERSION
assert "/api/chat" in spec["paths"]
assert "/api/openapi.json" in spec["paths"]
assert "ApiError" in spec["components"]["schemas"]
assert "ChatRequest" in spec["components"]["schemas"]

chat = validate_chat_request({"prompt": "  你好  "})
assert chat["prompt"] == "你好"

try:
    validate_chat_request({"prompt": ""})
except RequestValidationError as error:
    assert error.code == ERROR_EMPTY_PROMPT
else:
    raise AssertionError("应拒绝空 prompt")

try:
    validate_chat_request({"prompt": "x", "extra": 1})
except RequestValidationError as error:
    assert error.code == "VALIDATION_FAILED"
else:
    raise AssertionError("应拒绝未知字段")

clear = validate_clear_request(None)
assert clear["keep_system"] is True

clear2 = validate_clear_request({"keep_system": False})
assert clear2["keep_system"] is False

body = build_error_body(ERROR_EMPTY_PROMPT, "prompt 不能为空")
assert body["ok"] is False
assert body["error"]["code"] == ERROR_EMPTY_PROMPT
assert body["trace_id"]
assert ERROR_EMPTY_PROMPT in ERROR_HTTP_STATUS

print("Day 16 契约单测通过：OpenAPI、校验与标准错误码均正确。")
