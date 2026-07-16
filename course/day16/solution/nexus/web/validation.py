"""请求体验证：与 OpenAPI schema 对齐。"""

from __future__ import annotations

from typing import Any, Dict

from nexus.web.errors import ERROR_EMPTY_PROMPT, ERROR_INVALID_JSON, ERROR_VALIDATION


CHAT_REQUEST_SCHEMA = {
    "type": "object",
    "required": ["prompt"],
    "properties": {
        "prompt": {"type": "string", "minLength": 1},
        "system_prompt": {"type": "string"},
    },
    "additionalProperties": False,
}

CLEAR_REQUEST_SCHEMA = {
    "type": "object",
    "properties": {
        "keep_system": {"type": "boolean"},
    },
    "additionalProperties": False,
}


class RequestValidationError(Exception):
    """Web 请求体校验失败。"""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


def _require_object(body: Any) -> Dict[str, Any]:
    if body is None:
        raise RequestValidationError(ERROR_INVALID_JSON, "请求体必须是 JSON 对象")
    if not isinstance(body, dict):
        raise RequestValidationError(ERROR_INVALID_JSON, "请求体必须是 JSON 对象")
    return body


def validate_chat_request(body: Any) -> Dict[str, Any]:
    """校验 POST /api/chat 请求体。"""
    data = _require_object(body)
    if set(data.keys()) - set(CHAT_REQUEST_SCHEMA["properties"].keys()):
        raise RequestValidationError(ERROR_VALIDATION, "包含未定义的字段")
    prompt = str(data.get("prompt", "")).strip()
    if prompt == "":
        raise RequestValidationError(ERROR_EMPTY_PROMPT, "prompt 不能为空")
    result = {"prompt": prompt}
    if "system_prompt" in data:
        result["system_prompt"] = str(data["system_prompt"])
    return result


def validate_clear_request(body: Any) -> Dict[str, Any]:
    """校验 POST /api/clear 请求体；空 body 合法。"""
    if body is None:
        return {"keep_system": True}
    data = _require_object(body)
    if set(data.keys()) - set(CLEAR_REQUEST_SCHEMA["properties"].keys()):
        raise RequestValidationError(ERROR_VALIDATION, "包含未定义的字段")
    keep_system = data.get("keep_system", True)
    if not isinstance(keep_system, bool):
        raise RequestValidationError(ERROR_VALIDATION, "keep_system 必须是布尔值")
    return {"keep_system": keep_system}
