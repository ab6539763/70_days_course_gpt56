"""Web API 标准错误码与响应构造。"""

from __future__ import annotations

from typing import Any, Dict, Tuple

from flask import jsonify

from nexus.observability.logging import current_trace_id


# 机器可读错误码（写入 OpenAPI components/schemas/ApiError）
ERROR_EMPTY_PROMPT = "EMPTY_PROMPT"
ERROR_API_KEY_MISSING = "API_KEY_MISSING"
ERROR_INVALID_JSON = "INVALID_JSON"
ERROR_INVALID_MESSAGE = "INVALID_MESSAGE"
ERROR_UPSTREAM_API = "UPSTREAM_API"
ERROR_PERSISTENCE = "PERSISTENCE"
ERROR_SCHEMA_REJECTED = "SCHEMA_REJECTED"
ERROR_VALIDATION = "VALIDATION_FAILED"
ERROR_INVALID_WINDOW = "INVALID_WINDOW"
ERROR_SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
ERROR_SESSION_REQUIRED = "SESSION_REQUIRED"
ERROR_INVALID_SESSION = "INVALID_SESSION"

ERROR_HTTP_STATUS = {
    ERROR_EMPTY_PROMPT: 400,
    ERROR_API_KEY_MISSING: 400,
    ERROR_INVALID_JSON: 400,
    ERROR_INVALID_MESSAGE: 400,
    ERROR_VALIDATION: 400,
    ERROR_INVALID_WINDOW: 400,
    ERROR_SCHEMA_REJECTED: 400,
    ERROR_SESSION_REQUIRED: 400,
    ERROR_INVALID_SESSION: 400,
    ERROR_UPSTREAM_API: 502,
    ERROR_PERSISTENCE: 500,
    ERROR_SERVICE_UNAVAILABLE: 503,
}


def build_error_body(code: str, message: str, **extra: Any) -> Dict[str, Any]:
    """构造标准错误 JSON 体。"""
    payload: Dict[str, Any] = {
        "ok": False,
        "error": {"code": code, "message": message},
        "trace_id": current_trace_id(),
    }
    payload.update(extra)
    return payload


def api_error(code: str, message: str, status: int | None = None, **extra: Any):
    """返回 Flask jsonify 响应与 HTTP 状态码。"""
    http_status = status if status is not None else ERROR_HTTP_STATUS.get(code, 400)
    return jsonify(build_error_body(code, message, **extra)), http_status


def api_ok(**fields: Any):
    """构造成功 JSON 响应（HTTP 200）。"""
    payload: Dict[str, Any] = {"ok": True, "trace_id": current_trace_id()}
    payload.update(fields)
    return jsonify(payload), 200


def from_nexus_exception(error) -> Tuple[Dict[str, Any], int]:
    """把 Nexus 异常映射为标准 API 错误。"""
    mapping = {
        "INVALID_MESSAGE": ERROR_INVALID_MESSAGE,
        "API_CALL": ERROR_UPSTREAM_API,
        "PERSISTENCE": ERROR_PERSISTENCE,
        "SCHEMA_VALIDATION": ERROR_SCHEMA_REJECTED,
    }
    code = mapping.get(getattr(error, "code", ""), ERROR_VALIDATION)
    status = ERROR_HTTP_STATUS.get(code, 400)
    return build_error_body(code, error.message), status
