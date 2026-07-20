"""Web 层平台状态加载与持久化封装。"""

from __future__ import annotations

import time

from nexus.constants import DATA_FILE
from nexus.exceptions import ApiCallError, InvalidMessageError, PersistenceError, SchemaValidationError
from nexus.observability.audit_log import AuditLogStore
from nexus.observability.logging import bind_trace_id, get_logger, log_event
from nexus.persistence.storage import load_state, persist_change
from nexus.platform.state import PlatformState
from nexus.config.window_config import resolve_history_window
from nexus.web.stream_resume import StreamResumeStore, validate_resume_token


_web_logger = get_logger("web")


class WebStateManager:
    """每次 API 调用从 JSON 加载状态，变更后落盘。"""

    def __init__(self, data_file=DATA_FILE, session_id=None, audit_store: AuditLogStore | None = None):
        self.data_file = data_file
        self.session_id = session_id
        self.audit_store = audit_store

    def _audit_event(self, state, action: str, detail: str = ""):
        if self.audit_store is None:
            return None
        return {
            "action": action,
            "operator": state.owner or "UNKNOWN",
            "session_id": self.session_id or "",
            "detail": detail,
        }

    def audit_log(self, limit: int = 50):
        if self.audit_store is None:
            return []
        records = self.audit_store.list_for(self.data_file, limit=limit)
        return [item.to_dict() for item in records]

    def load_or_create(self):
        """加载平台状态；schema 拒绝时向上抛出 SchemaValidationError。"""
        bind_trace_id()
        try:
            state, status, error = load_state(self.data_file)
        except PersistenceError as error:
            log_event(_web_logger, 40, "web_load_failed", error=error.message)
            raise
        if status == "rejected":
            raise SchemaValidationError(error)
        if status == "migrated":
            persist_change(
                state,
                self.data_file,
                audit_event=self._audit_event(state, "schema_migrate"),
                audit_store=self.audit_store,
            )
        if state.owner is None:
            if self.session_id:
                state.owner = f"SESSION_{self.session_id[-8:]}"
            else:
                state.owner = "WEB_USER"
            persist_change(
                state,
                self.data_file,
                audit_event=self._audit_event(state, "owner_init"),
                audit_store=self.audit_store,
            )
            log_event(
                _web_logger,
                20,
                "web_owner_init",
                owner=state.owner,
                session_id=self.session_id,
            )
        return state

    def revision_info(self):
        state = self.load_or_create()
        return {"revision": state.revision}

    def chat(
        self,
        prompt,
        system_prompt="你是企业助手",
        history_window=None,
        expected_revision=None,
    ):
        state = self.load_or_create()
        if prompt.strip() == "":
            raise InvalidMessageError("消息内容不能为空")
        changed, message, assistant_text, window_meta = state.conversation_turn(
            prompt.strip(),
            system_prompt=system_prompt,
            history_window=history_window,
        )
        revision = persist_change(
            state,
            self.data_file,
            expected_revision=expected_revision,
            audit_event=self._audit_event(state, "web_chat", detail=prompt.strip()[:80]),
            audit_store=self.audit_store,
        )
        log_event(
            _web_logger,
            20,
            "web_chat_turn",
            revision=revision,
            user_len=len(prompt.strip()),
            window_applied=window_meta.get("window_applied"),
        )
        return {
            "changed": changed,
            "message": message,
            "assistant": assistant_text,
            "revision": revision,
            "messages": [item.to_dict() for item in state.messages],
            "window": window_meta,
        }

    def chat_stream(
        self,
        prompt=None,
        system_prompt="你是企业助手",
        history_window=None,
        resume_token=None,
        resume_store: StreamResumeStore | None = None,
        interrupt_after=None,
        expected_revision=None,
    ):
        """流式对话：支持 resume_token 断流恢复与 expected_revision 乐观锁。"""
        state = self.load_or_create()
        store = resume_store or StreamResumeStore()
        if resume_token:
            yield from self._resume_stream(
                state,
                store,
                resume_token,
                system_prompt=system_prompt,
                history_window=history_window,
                interrupt_after=interrupt_after,
                expected_revision=expected_revision,
            )
            return
        if prompt is None or prompt.strip() == "":
            raise InvalidMessageError("消息内容不能为空")
        yield from self._start_stream(
            state,
            store,
            prompt.strip(),
            system_prompt=system_prompt,
            history_window=history_window,
            interrupt_after=interrupt_after,
            expected_revision=expected_revision,
        )

    def _start_stream(
        self,
        state,
        store: StreamResumeStore,
        prompt,
        system_prompt="你是企业助手",
        history_window=None,
        interrupt_after=None,
        expected_revision=None,
    ):
        partial_parts = []
        generator = state.conversation_turn_stream(
            prompt,
            system_prompt=system_prompt,
            history_window=history_window,
            interrupt_after=interrupt_after,
        )
        try:
            for item in generator:
                if item["event"] == "chunk":
                    partial_parts.append(item["payload"]["delta"])
                if item["event"] == "done":
                    revision = persist_change(
                        state,
                        self.data_file,
                        expected_revision=expected_revision,
                        audit_event=self._audit_event(state, "web_chat_stream_done"),
                        audit_store=self.audit_store,
                    )
                    log_event(
                        _web_logger,
                        20,
                        "web_chat_stream_done",
                        revision=revision,
                        window_applied=item["payload"]["window"].get("window_applied"),
                    )
                    item["payload"]["revision"] = revision
                    item["payload"]["messages"] = [
                        message.to_dict() for message in state.messages
                    ]
                yield item
        except ApiCallError as error:
            partial = "".join(partial_parts)
            if partial:
                revision = persist_change(
                    state,
                    self.data_file,
                    expected_revision=expected_revision,
                    audit_event=self._audit_event(state, "web_stream_interrupted"),
                    audit_store=self.audit_store,
                )
                record = store.create(
                    session_id=self.session_id or "",
                    data_file=self.data_file,
                    user_prompt=prompt,
                    partial_assistant=partial,
                    system_prompt=system_prompt,
                    history_window=history_window,
                )
                log_event(
                    _web_logger,
                    30,
                    "web_stream_interrupted",
                    resume_token=record.resume_token,
                    partial_len=len(partial),
                    revision=revision,
                )
                yield {
                    "event": "interrupted",
                    "payload": {
                        "resume_token": record.resume_token,
                        "partial": partial,
                        "expires_at": record.expires_at,
                        "error": error.message,
                        "revision": revision,
                    },
                }
                return
            raise

    def _resume_stream(
        self,
        state,
        store: StreamResumeStore,
        resume_token,
        system_prompt="你是企业助手",
        history_window=None,
        interrupt_after=None,
        expected_revision=None,
    ):
        token = validate_resume_token(resume_token)
        record = store.get(token)
        if record is None:
            raise ValueError("resume_token 不存在或已过期")
        if self.session_id and record.session_id != self.session_id:
            raise ValueError("resume_token 与会话不匹配")
        if record.data_file != self.data_file:
            raise ValueError("resume_token 与数据文件不匹配")
        partial_parts = [record.partial_assistant]
        generator = state.resume_stream_turn(
            record.partial_assistant,
            system_prompt=record.system_prompt or system_prompt,
            history_window=record.history_window if record.history_window is not None else history_window,
            interrupt_after=interrupt_after,
        )
        try:
            for item in generator:
                if item["event"] == "chunk":
                    partial_parts.append(item["payload"]["delta"])
                if item["event"] == "done":
                    store.consume(token)
                    revision = persist_change(
                        state,
                        self.data_file,
                        expected_revision=expected_revision,
                        audit_event=self._audit_event(state, "web_stream_resume_done"),
                        audit_store=self.audit_store,
                    )
                    log_event(
                        _web_logger,
                        20,
                        "web_stream_resume_done",
                        resume_token=token,
                        revision=revision,
                    )
                    item["payload"]["revision"] = revision
                    item["payload"]["messages"] = [
                        message.to_dict() for message in state.messages
                    ]
                    item["payload"]["resume_token"] = token
                yield item
        except ApiCallError as error:
            partial = "".join(partial_parts)
            revision = persist_change(
                state,
                self.data_file,
                expected_revision=expected_revision,
                audit_event=self._audit_event(state, "web_stream_interrupted_resume"),
                audit_store=self.audit_store,
            )
            refreshed = store.create(
                session_id=record.session_id,
                data_file=record.data_file,
                user_prompt=record.user_prompt,
                partial_assistant=partial,
                system_prompt=record.system_prompt,
                history_window=record.history_window,
            )
            store.consume(token)
            yield {
                "event": "interrupted",
                "payload": {
                    "resume_token": refreshed.resume_token,
                    "partial": partial,
                    "expires_at": refreshed.expires_at,
                    "error": error.message,
                    "revision": revision,
                },
            }
            return

    def get_resume_info(self, resume_store: StreamResumeStore, resume_token: str) -> dict:
        token = validate_resume_token(resume_token)
        record = resume_store.get(token)
        if record is None:
            raise ValueError("resume_token 不存在或已过期")
        if self.session_id and record.session_id != self.session_id:
            raise ValueError("resume_token 与会话不匹配")
        return {
            "resume_token": record.resume_token,
            "session_id": record.session_id,
            "partial": record.partial_assistant,
            "user_prompt": record.user_prompt,
            "expires_at": record.expires_at,
            "ttl_remaining": max(0, int(record.expires_at - time.time())),
        }

    def window_info(self, history_window=None):
        state = self.load_or_create()
        snapshot = state.window_snapshot(history_window=history_window)
        return {
            "default_history_window": resolve_history_window(),
            "messages_stored": len(state.messages),
            "revision": state.revision,
            **snapshot,
        }

    def clear(self, keep_system=True, expected_revision=None):
        state = self.load_or_create()
        changed, message = state.clear_messages(keep_system=keep_system)
        revision = persist_change(
            state,
            self.data_file,
            expected_revision=expected_revision,
            audit_event=self._audit_event(state, "web_clear", detail=f"keep_system={keep_system}"),
            audit_store=self.audit_store,
        )
        log_event(_web_logger, 20, "web_clear", revision=revision)
        return {
            "changed": changed,
            "message": message,
            "revision": revision,
            "messages": [item.to_dict() for item in state.messages],
        }

    def snapshot(self):
        state = self.load_or_create()
        return {
            "revision": state.revision,
            "owner": state.owner,
            "messages": [
                {
                    "role": item.role,
                    "content": item.content,
                    "preview": item.preview(),
                }
                for item in state.messages
            ],
            "model": str(state.active_model()),
        }

    def summary(self):
        state = self.load_or_create()
        stats = state.statistics()
        return {
            "schema_version": 4,
            "revision": state.revision,
            "owner": state.owner,
            "messages": stats["messages"],
            "contacts": stats["contacts"],
            "documents": stats["documents"],
            "model": stats["model"],
        }
