"""请求体验证：与 OpenAPI schema 对齐。"""

from __future__ import annotations

from typing import Any, Dict, Optional

from nexus.constants import DEFAULT_HISTORY_WINDOW, MAX_HISTORY_WINDOW
from nexus.persistence.revision_guard import parse_expected_revision, require_revision
from nexus.web.errors import (
    ERROR_EMPTY_PROMPT,
    ERROR_INVALID_JSON,
    ERROR_INVALID_WINDOW,
    ERROR_REVISION_REQUIRED,
    ERROR_VALIDATION,
)
from nexus.web.stream_resume import validate_resume_token


CHAT_REQUEST_SCHEMA = {
    "type": "object",
    "required": ["prompt"],
    "properties": {
        "prompt": {"type": "string", "minLength": 1},
        "system_prompt": {"type": "string"},
        "max_history": {"type": "integer", "minimum": 0, "maximum": MAX_HISTORY_WINDOW},
        "expected_revision": {"type": "integer", "minimum": 0},
    },
    "additionalProperties": False,
}

STREAM_CHAT_REQUEST_SCHEMA = {
    "type": "object",
    "properties": {
        "prompt": {"type": "string"},
        "system_prompt": {"type": "string"},
        "max_history": {"type": "integer", "minimum": 0, "maximum": MAX_HISTORY_WINDOW},
        "resume_token": {"type": "string"},
        "expected_revision": {"type": "integer", "minimum": 0},
    },
    "additionalProperties": False,
}

CLEAR_REQUEST_SCHEMA = {
    "type": "object",
    "properties": {
        "keep_system": {"type": "boolean"},
        "expected_revision": {"type": "integer", "minimum": 0},
    },
    "additionalProperties": False,
}

SESSION_CREATE_SCHEMA = {
    "type": "object",
    "properties": {
        "owner": {"type": "string", "minLength": 1},
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


def _parse_expected_revision_field(data: Dict[str, Any], result: Dict[str, Any]) -> None:
    if "expected_revision" not in data:
        return
    raw = data["expected_revision"]
    if not isinstance(raw, int) or isinstance(raw, bool):
        raise RequestValidationError(ERROR_VALIDATION, "expected_revision 必须是整数")
    try:
        result["expected_revision"] = parse_expected_revision(raw)
    except ValueError as error:
        raise RequestValidationError(ERROR_VALIDATION, str(error)) from error


def ensure_expected_revision(
    expected_revision: Optional[int],
    *,
    mutate: bool = True,
) -> Optional[int]:
    """写操作校验 expected_revision 是否满足环境策略。"""
    if expected_revision is not None:
        return expected_revision
    if mutate and require_revision():
        raise RequestValidationError(
            ERROR_REVISION_REQUIRED,
            "写操作必须提供 expected_revision（Body 或 X-Expected-Revision 头）",
        )
    return None


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
    if "max_history" in data:
        raw = data["max_history"]
        if not isinstance(raw, int) or isinstance(raw, bool):
            raise RequestValidationError(ERROR_VALIDATION, "max_history 必须是整数")
        if raw < 0 or raw > MAX_HISTORY_WINDOW:
            raise RequestValidationError(
                ERROR_INVALID_WINDOW,
                f"max_history 必须在 0 到 {MAX_HISTORY_WINDOW} 之间",
            )
        result["max_history"] = raw
    _parse_expected_revision_field(data, result)
    return result


def validate_stream_chat_request(body: Any) -> Dict[str, Any]:
    """校验 POST /api/chat/stream 请求体（支持 resume_token 断流恢复）。"""
    data = _require_object(body)
    if set(data.keys()) - set(STREAM_CHAT_REQUEST_SCHEMA["properties"].keys()):
        raise RequestValidationError(ERROR_VALIDATION, "包含未定义的字段")
    result: Dict[str, Any] = {}
    if "resume_token" in data:
        try:
            result["resume_token"] = validate_resume_token(str(data["resume_token"]))
        except ValueError as error:
            raise RequestValidationError(ERROR_VALIDATION, str(error)) from error
    prompt = str(data.get("prompt", "")).strip()
    if result.get("resume_token"):
        if prompt:
            result["prompt"] = prompt
    elif prompt == "":
        raise RequestValidationError(ERROR_EMPTY_PROMPT, "prompt 不能为空")
    else:
        result["prompt"] = prompt
    if "system_prompt" in data:
        result["system_prompt"] = str(data["system_prompt"])
    if "max_history" in data:
        raw = data["max_history"]
        if not isinstance(raw, int) or isinstance(raw, bool):
            raise RequestValidationError(ERROR_VALIDATION, "max_history 必须是整数")
        if raw < 0 or raw > MAX_HISTORY_WINDOW:
            raise RequestValidationError(
                ERROR_INVALID_WINDOW,
                f"max_history 必须在 0 到 {MAX_HISTORY_WINDOW} 之间",
            )
        result["max_history"] = raw
    _parse_expected_revision_field(data, result)
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
    result = {"keep_system": keep_system}
    _parse_expected_revision_field(data, result)
    return result


def validate_session_create_request(body: Any) -> Dict[str, Any]:
    """校验 POST /api/session 请求体；空 body 合法。"""
    if body is None:
        return {}
    data = _require_object(body)
    if set(data.keys()) - set(SESSION_CREATE_SCHEMA["properties"].keys()):
        raise RequestValidationError(ERROR_VALIDATION, "包含未定义的字段")
    result = {}
    if "owner" in data:
        owner = str(data["owner"]).strip()
        if owner == "":
            raise RequestValidationError(ERROR_VALIDATION, "owner 不能为空")
        result["owner"] = owner
    return result
