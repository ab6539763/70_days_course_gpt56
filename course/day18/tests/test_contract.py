"""Day 18 OpenAPI 契约与 SSE 流式端点单测。"""

import sys
from pathlib import Path


SOLUTION = Path(__file__).parents[1] / "solution"
sys.path.insert(0, str(SOLUTION))

from nexus.constants import APP_VERSION, MAX_HISTORY_WINDOW
from nexus.web.errors import ERROR_EMPTY_PROMPT, ERROR_INVALID_WINDOW, build_error_body
from nexus.web.openapi import build_openapi_spec
from nexus.web.validation import RequestValidationError, validate_chat_request


spec = build_openapi_spec("http://test.local")
assert spec["openapi"] == "3.0.3"
assert spec["info"]["version"] == APP_VERSION
assert "/api/window" in spec["paths"]
assert "/api/chat/stream" in spec["paths"]
stream_path = spec["paths"]["/api/chat/stream"]["post"]["responses"]["200"]
assert "text/event-stream" in stream_path["content"]
chat_schema = spec["components"]["schemas"]["ChatRequest"]["properties"]
assert "max_history" in chat_schema
assert "StreamChunkEvent" in spec["components"]["schemas"]
assert "StreamDoneEvent" in spec["components"]["schemas"]

chat = validate_chat_request({"prompt": "你好", "max_history": 8})
assert chat["max_history"] == 8

try:
    validate_chat_request({"prompt": "x", "max_history": MAX_HISTORY_WINDOW + 1})
except RequestValidationError as error:
    assert error.code == ERROR_INVALID_WINDOW
else:
    raise AssertionError("应拒绝超大 max_history")

body = build_error_body(ERROR_INVALID_WINDOW, "窗口非法")
assert body["error"]["code"] == ERROR_INVALID_WINDOW

print("Day 18 契约单测通过：OpenAPI SSE 端点与 schema 均正确。")
