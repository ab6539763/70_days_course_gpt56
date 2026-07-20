"""Web 路由：页面与 JSON API。"""

from __future__ import annotations

from flask import Flask, jsonify, render_template, request

from nexus.constants import APP_VERSION
from nexus.exceptions import ApiCallError, InvalidMessageError, PersistenceError, SchemaValidationError
from nexus.http.config import resolve_api_key, use_mock_mode
from nexus.observability.logging import bind_trace_id, current_trace_id, get_logger, log_event


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

    @app.get("/api/health")
    def health():
        try:
            summary = manager.summary()
        except (PersistenceError, SchemaValidationError) as error:
            return jsonify({"ok": False, "error": getattr(error, "message", str(error))}), 503
        return jsonify(
            {
                "ok": True,
                "app_version": APP_VERSION,
                "trace_id": current_trace_id(),
                "mock_mode": use_mock_mode(),
                "api_key_configured": resolve_api_key() != "" or use_mock_mode(),
                **summary,
            }
        )

    @app.get("/api/messages")
    def messages():
        try:
            payload = manager.snapshot()
        except PersistenceError as error:
            return jsonify({"ok": False, "error": error.message}), 500
        except SchemaValidationError as error:
            return jsonify({"ok": False, "error": error.message}), 400
        return jsonify({"ok": True, "trace_id": current_trace_id(), **payload})

    @app.post("/api/chat")
    def chat():
        body = request.get_json(silent=True) or {}
        prompt = str(body.get("prompt", "")).strip()
        if prompt == "":
            return jsonify({"ok": False, "error": "prompt 不能为空"}), 400
        if not use_mock_mode() and resolve_api_key() == "":
            return jsonify({"ok": False, "error": "未配置 NEXUS_API_KEY，请设置 NEXUS_USE_MOCK=1"}), 400
        try:
            payload = manager.chat(prompt)
        except InvalidMessageError as error:
            return jsonify({"ok": False, "error": error.message}), 400
        except ApiCallError as error:
            log_event(_web_logger, 40, "web_api_error", error=error.message)
            return jsonify({"ok": False, "error": error.message, "trace_id": current_trace_id()}), 502
        except PersistenceError as error:
            return jsonify({"ok": False, "error": error.message}), 500
        except SchemaValidationError as error:
            return jsonify({"ok": False, "error": error.message}), 400
        return jsonify({"ok": True, "trace_id": current_trace_id(), **payload})

    @app.post("/api/clear")
    def clear():
        body = request.get_json(silent=True) or {}
        keep_system = bool(body.get("keep_system", True))
        try:
            payload = manager.clear(keep_system=keep_system)
        except PersistenceError as error:
            return jsonify({"ok": False, "error": error.message}), 500
        except SchemaValidationError as error:
            return jsonify({"ok": False, "error": error.message}), 400
        return jsonify({"ok": True, "trace_id": current_trace_id(), **payload})
