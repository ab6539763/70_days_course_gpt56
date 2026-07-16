"""Web 路由：页面、JSON API 与 OpenAPI 文档。"""

from __future__ import annotations

from flask import Flask, jsonify, render_template, request

from nexus.constants import APP_VERSION
from nexus.exceptions import ApiCallError, InvalidMessageError, PersistenceError, SchemaValidationError
from nexus.http.config import resolve_api_key, use_mock_mode
from nexus.observability.logging import bind_trace_id, current_trace_id, get_logger, log_event
from nexus.web.errors import (
    ERROR_API_KEY_MISSING,
    ERROR_SERVICE_UNAVAILABLE,
    ERROR_UPSTREAM_API,
    api_error,
    api_ok,
    from_nexus_exception,
)
from nexus.web.openapi import build_openapi_spec
from nexus.web.validation import RequestValidationError, validate_chat_request, validate_clear_request


_web_logger = get_logger("web")


def register_routes(app: Flask) -> None:
    manager = app.config["STATE_MANAGER"]

    @app.before_request
    def _bind_request_trace():
        incoming = request.headers.get("X-Trace-Id")
        bind_trace_id(incoming)

    @app.get("/")
    def index():
        log_event(_web_logger, 20, "web_index")
        return render_template(
            "chat.html",
            app_version=APP_VERSION,
            mock_mode=use_mock_mode(),
        )

    @app.get("/docs")
    def docs():
        log_event(_web_logger, 20, "web_docs")
        return render_template("docs.html", app_version=APP_VERSION)

    @app.get("/api/openapi.json")
    def openapi_json():
        base = request.host_url.rstrip("/")
        log_event(_web_logger, 20, "web_openapi", base=base)
        return jsonify(build_openapi_spec(base))

    @app.get("/api/health")
    def health():
        try:
            summary = manager.summary()
        except (PersistenceError, SchemaValidationError) as error:
            body, status = from_nexus_exception(error)
            if status == 400:
                body["error"]["code"] = ERROR_SERVICE_UNAVAILABLE
                status = 503
            return jsonify(body), status
        return api_ok(
            app_version=APP_VERSION,
            mock_mode=use_mock_mode(),
            api_key_configured=resolve_api_key() != "" or use_mock_mode(),
            **summary,
        )

    @app.get("/api/messages")
    def messages():
        try:
            payload = manager.snapshot()
        except PersistenceError as error:
            body, status = from_nexus_exception(error)
            return jsonify(body), status
        except SchemaValidationError as error:
            body, status = from_nexus_exception(error)
            return jsonify(body), status
        return api_ok(**payload)

    @app.post("/api/chat")
    def chat():
        body = request.get_json(silent=True)
        try:
            validated = validate_chat_request(body)
        except RequestValidationError as error:
            return api_error(error.code, error.message)
        if not use_mock_mode() and resolve_api_key() == "":
            return api_error(
                ERROR_API_KEY_MISSING,
                "未配置 NEXUS_API_KEY，请设置 NEXUS_USE_MOCK=1",
            )
        try:
            payload = manager.chat(
                validated["prompt"],
                system_prompt=validated.get("system_prompt", "你是企业助手"),
            )
        except InvalidMessageError as error:
            body, status = from_nexus_exception(error)
            return jsonify(body), status
        except ApiCallError as error:
            log_event(_web_logger, 40, "web_api_error", error=error.message)
            return api_error(ERROR_UPSTREAM_API, error.message)
        except PersistenceError as error:
            body, status = from_nexus_exception(error)
            return jsonify(body), status
        except SchemaValidationError as error:
            body, status = from_nexus_exception(error)
            return jsonify(body), status
        return api_ok(**payload)

    @app.post("/api/clear")
    def clear():
        body = request.get_json(silent=True)
        try:
            validated = validate_clear_request(body)
        except RequestValidationError as error:
            return api_error(error.code, error.message)
        try:
            payload = manager.clear(keep_system=validated["keep_system"])
        except PersistenceError as error:
            body, status = from_nexus_exception(error)
            return jsonify(body), status
        except SchemaValidationError as error:
            body, status = from_nexus_exception(error)
            return jsonify(body), status
        return api_ok(**payload)
