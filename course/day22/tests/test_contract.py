"""Day 22 OpenAPI 契约与审计日志端点单测。"""

import sys
from pathlib import Path


SOLUTION = Path(__file__).parents[1] / "solution"
sys.path.insert(0, str(SOLUTION))

from nexus.constants import APP_VERSION, REVISION_HEADER
from nexus.web.errors import ERROR_REVISION_CONFLICT, build_error_body
from nexus.web.openapi import build_openapi_spec
from nexus.web.validation import validate_chat_request, validate_clear_request


spec = build_openapi_spec("http://test.local")
assert spec["info"]["version"] == APP_VERSION
assert "/api/revision" in spec["paths"]
assert "/api/audit" in spec["paths"]
assert "AuditLogResponse" in spec["components"]["schemas"]
assert "ExpectedRevisionHeader" in spec["components"]["parameters"]
assert "RevisionConflictResponse" in spec["components"]["schemas"]
assert "expected_revision" in spec["components"]["schemas"]["ChatRequest"]["properties"]

chat_path = spec["paths"]["/api/chat"]["post"]
assert any(
    item.get("$ref") == "#/components/parameters/ExpectedRevisionHeader"
    for item in chat_path["parameters"]
)
assert "409" in chat_path["responses"]

body = validate_chat_request({"prompt": "hi", "expected_revision": 3})
assert body["expected_revision"] == 3
clear_body = validate_clear_request({"keep_system": True, "expected_revision": 2})
assert clear_body["expected_revision"] == 2

conflict = build_error_body(ERROR_REVISION_CONFLICT, "冲突", expected_revision=1, actual_revision=2)
assert conflict["error"]["code"] == ERROR_REVISION_CONFLICT
assert REVISION_HEADER == "X-Expected-Revision"

print("Day 22 契约单测通过：OpenAPI 审计日志端点与 expected_revision 均正确。")
