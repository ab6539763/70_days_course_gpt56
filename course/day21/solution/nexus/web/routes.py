"""Web 路由：页面、JSON API、会话隔离与 OpenAPI 文档。"""

from __future__ import annotations

from flask import Flask, jsonify, render_template, request

from nexus.config.session_config import session_file_path, validate_session_id
from nexus.constants import (
    APP_VERSION,
    DEFAULT_HISTORY_WINDOW,
    MAX_HISTORY_WINDOW,
    REVISION_HEADER,
    SESSION_HEADER,
)
from nexus.exceptions import ApiCallError, InvalidMessageError, PersistenceError, RevisionConflictError, SchemaValidationError
from nexus.persistence.revision_guard import resolve_expected_revision
from nexus.http.config import resolve_api_key, use_mock_mode
from nexus.observability.logging import bind_trace_id, current_trace_id, get_logger, log_event
from nexus.web.errors import (
    ERROR_API_KEY_MISSING,
    ERROR_HTTP_STATUS,
    ERROR_INVALID_RESUME,
    ERROR_INVALID_SESSION,
    ERROR_INVALID_WINDOW,
    ERROR_REVISION_CONFLICT,
    ERROR_REVISION_REQUIRED,
    ERROR_RESUME_EXPIRED,
    ERROR_SERVICE_UNAVAILABLE,
    ERROR_SESSION_REQUIRED,
    ERROR_UPSTREAM_API,
    ERROR_VALIDATION,
    revision_conflict_body,
    api_error,
    api_ok,
    from_nexus_exception,
)
from nexus.web.openapi import build_openapi_spec
from nexus.web.sse import format_sse_event, stream_from_generator
from nexus.web.validation import (
    RequestValidationError,
    ensure_expected_revision,
    validate_chat_request,
    validate_clear_request,
    validate_session_create_request,
    validate_stream_chat_request,
)


_web_logger = get_logger("web")


def register_routes(app: Flask) -> None:
    registry = app.config["SESSION_REGISTRY"]
    resume_store = app.config["STREAM_RESUME_STORE"]

    def resolve_manager():
        session_id = request.headers.get(SESSION_HEADER, "").strip()
        if not session_id:
            return None, api_error(
                ERROR_SESSION_REQUIRED,
                f"缺少 {SESSION_HEADER} 请求头，请先 POST /api/session 创建会话",
            )
        try:
            validate_session_id(session_id)
        except ValueError as error:
            return None, api_error(ERROR_INVALID_SESSION, str(error))
        if not session_file_path(session_id, registry.session_dir).exists():
            return None, api_error(ERROR_INVALID_SESSION, f"会话不存在：{session_id}")
        return registry.manager_for(session_id), None

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

    @app.post("/api/session")
    def create_session():
        body = request.get_json(silent=True)
        try:
            validated = validate_session_create_request(body)
        except RequestValidationError as error:
            return api_error(error.code, error.message)
        payload = registry.create_session(owner=validated.get("owner"))
        log_event(_web_logger, 20, "web_session_create", session_id=payload["session_id"])
        return api_ok(**payload)

    @app.get("/api/session")
    def get_session():
        session_id = request.headers.get(SESSION_HEADER, "").strip()
        if not session_id:
            return api_error(ERROR_SESSION_REQUIRED, f"缺少 {SESSION_HEADER} 请求头")
        try:
            info = registry.session_info(session_id)
        except ValueError as error:
            return api_error(ERROR_INVALID_SESSION, str(error))
        except FileNotFoundError as error:
            return api_error(ERROR_INVALID_SESSION, str(error))
        except (PersistenceError, SchemaValidationError) as error:
            body, status = from_nexus_exception(error)
            return jsonify(body), status
        return api_ok(**info)

    @app.get("/api/sessions")
    def list_sessions():
        sessions = registry.list_sessions()
        return api_ok(sessions=sessions, count=len(sessions), session_dir=str(registry.session_dir))

    @app.get("/api/health")
    def health():
        sessions = registry.list_sessions()
        return api_ok(
            app_version=APP_VERSION,
            mock_mode=use_mock_mode(),
            api_key_configured=resolve_api_key() != "" or use_mock_mode(),
            default_history_window=DEFAULT_HISTORY_WINDOW,
            max_history_window=MAX_HISTORY_WINDOW,
            session_count=len(sessions),
            session_dir=str(registry.session_dir),
            pending_resume_count=resume_store.count(),
        )

    @app.get("/api/window")
    def window():
        manager, error_response = resolve_manager()
        if error_response is not None:
            return error_response
        query_window = request.args.get("max_history")
        override = int(query_window) if query_window is not None else None
        try:
            payload = manager.window_info(history_window=override)
        except ValueError as error:
            return api_error(ERROR_INVALID_WINDOW, str(error))
        except PersistenceError as error:
            body, status = from_nexus_exception(error)
            return jsonify(body), status
        except SchemaValidationError as error:
            body, status = from_nexus_exception(error)
            return jsonify(body), status
        payload["session_id"] = manager.session_id
        return api_ok(**payload)

    def _resolve_write_revision(validated: dict):
        try:
            merged = resolve_expected_revision(
                request.headers.get(REVISION_HEADER),
                validated.get("expected_revision"),
            )
            return ensure_expected_revision(merged, mutate=True)
        except RequestValidationError as error:
            raise error
        except ValueError as error:
            raise RequestValidationError(ERROR_VALIDATION, str(error)) from error

    @app.get("/api/revision")
    def revision():
        manager, error_response = resolve_manager()
        if error_response is not None:
            return error_response
        try:
            payload = manager.revision_info()
        except PersistenceError as error:
            body, status = from_nexus_exception(error)
            return jsonify(body), status
        except SchemaValidationError as error:
            body, status = from_nexus_exception(error)
            return jsonify(body), status
        payload["session_id"] = manager.session_id
        return api_ok(**payload)

    @app.get("/api/messages")
    def messages():
        manager, error_response = resolve_manager()
        if error_response is not None:
            return error_response
        try:
            payload = manager.snapshot()
        except PersistenceError as error:
            body, status = from_nexus_exception(error)
            return jsonify(body), status
        except SchemaValidationError as error:
            body, status = from_nexus_exception(error)
            return jsonify(body), status
        payload["session_id"] = manager.session_id
        return api_ok(**payload)

    @app.post("/api/chat")
    def chat():
        manager, error_response = resolve_manager()
        if error_response is not None:
            return error_response
        body = request.get_json(silent=True)
        try:
            validated = validate_chat_request(body)
            expected_revision = _resolve_write_revision(validated)
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
                history_window=validated.get("max_history"),
                expected_revision=expected_revision,
            )
        except RevisionConflictError as error:
            body = revision_conflict_body(error)
            return jsonify(body), ERROR_HTTP_STATUS[ERROR_REVISION_CONFLICT]
        except ValueError as error:
            return api_error(ERROR_INVALID_WINDOW, str(error))
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
        payload["session_id"] = manager.session_id
        return api_ok(**payload)

    @app.get("/api/stream/resume/<resume_token>")
    def stream_resume_info(resume_token):
        manager, error_response = resolve_manager()
        if error_response is not None:
            return error_response
        try:
            payload = manager.get_resume_info(resume_store, resume_token)
        except ValueError as error:
            message = str(error)
            if "过期" in message or "不存在" in message:
                return api_error(ERROR_RESUME_EXPIRED, message)
            return api_error(ERROR_INVALID_RESUME, message)
        payload["session_id"] = manager.session_id
        return api_ok(**payload)

    @app.post("/api/chat/stream")
    def chat_stream():
        manager, error_response = resolve_manager()
        if error_response is not None:
            return error_response
        body = request.get_json(silent=True)
        try:
            validated = validate_stream_chat_request(body)
            expected_revision = _resolve_write_revision(validated)
        except RequestValidationError as error:
            return api_error(error.code, error.message)
        if not use_mock_mode() and resolve_api_key() == "":
            return api_error(
                ERROR_API_KEY_MISSING,
                "未配置 NEXUS_API_KEY，请设置 NEXUS_USE_MOCK=1",
            )

        interrupt_header = request.headers.get("X-Stream-Simulate-Interrupt", "").strip()
        interrupt_after = None
        if interrupt_header:
            try:
                interrupt_after = int(interrupt_header)
            except ValueError:
                return api_error(
                    ERROR_VALIDATION,
                    "X-Stream-Simulate-Interrupt 必须是整数",
                )

        def event_stream():
            try:
                for item in manager.chat_stream(
                    prompt=validated.get("prompt"),
                    system_prompt=validated.get("system_prompt", "你是企业助手"),
                    history_window=validated.get("max_history"),
                    resume_token=validated.get("resume_token"),
                    resume_store=resume_store,
                    interrupt_after=interrupt_after,
                    expected_revision=expected_revision,
                ):
                    payload = dict(item["payload"])
                    if item["event"] == "done":
                        payload["ok"] = True
                    if item["event"] in ("done", "interrupted", "resume"):
                        payload["trace_id"] = current_trace_id()
                        payload["session_id"] = manager.session_id
                    yield format_sse_event(item["event"], payload)
            except ValueError as error:
                message = str(error)
                if "过期" in message or "不存在" in message:
                    code = ERROR_RESUME_EXPIRED
                elif "resume_token" in message:
                    code = ERROR_INVALID_RESUME
                else:
                    code = ERROR_INVALID_WINDOW
                yield format_sse_event(
                    "error",
                    {
                        "ok": False,
                        "error": {"code": code, "message": message},
                        "trace_id": current_trace_id(),
                    },
                )
            except InvalidMessageError as error:
                body_payload, _status = from_nexus_exception(error)
                yield format_sse_event("error", body_payload)
            except ApiCallError as error:
                log_event(_web_logger, 40, "web_stream_api_error", error=error.message)
                yield format_sse_event(
                    "error",
                    {
                        "ok": False,
                        "error": {"code": ERROR_UPSTREAM_API, "message": error.message},
                        "trace_id": current_trace_id(),
                    },
                )
            except RevisionConflictError as error:
                yield format_sse_event("error", revision_conflict_body(error))
            except (PersistenceError, SchemaValidationError) as error:
                body_payload, _status = from_nexus_exception(error)
                yield format_sse_event("error", body_payload)

        return stream_from_generator(event_stream())

    @app.post("/api/clear")
    def clear():
        manager, error_response = resolve_manager()
        if error_response is not None:
            return error_response
        body = request.get_json(silent=True)
        try:
            validated = validate_clear_request(body)
            expected_revision = _resolve_write_revision(validated)
        except RequestValidationError as error:
            return api_error(error.code, error.message)
        try:
            payload = manager.clear(
                keep_system=validated["keep_system"],
                expected_revision=expected_revision,
            )
        except RevisionConflictError as error:
            return jsonify(revision_conflict_body(error)), ERROR_HTTP_STATUS[ERROR_REVISION_CONFLICT]
        except PersistenceError as error:
            body, status = from_nexus_exception(error)
            return jsonify(body), status
        except SchemaValidationError as error:
            body, status = from_nexus_exception(error)
            return jsonify(body), status
        payload["session_id"] = manager.session_id
        return api_ok(**payload)
