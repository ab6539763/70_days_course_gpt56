"""Web 层平台状态加载与持久化封装。"""

from __future__ import annotations

from nexus.constants import DATA_FILE
from nexus.exceptions import ApiCallError, InvalidMessageError, PersistenceError, SchemaValidationError
from nexus.observability.logging import bind_trace_id, get_logger, log_event
from nexus.persistence.storage import load_state, persist_change
from nexus.platform.state import PlatformState
from nexus.config.window_config import resolve_history_window


_web_logger = get_logger("web")


class WebStateManager:
    """每次 API 调用从 JSON 加载状态，变更后落盘。"""

    def __init__(self, data_file=DATA_FILE):
        self.data_file = data_file

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
            persist_change(state, self.data_file)
        if state.owner is None:
            state.owner = "WEB_USER"
            persist_change(state, self.data_file)
            log_event(_web_logger, 20, "web_owner_init", owner=state.owner)
        return state

    def chat(self, prompt, system_prompt="你是企业助手", history_window=None):
        state = self.load_or_create()
        if prompt.strip() == "":
            raise InvalidMessageError("消息内容不能为空")
        changed, message, assistant_text, window_meta = state.conversation_turn(
            prompt.strip(),
            system_prompt=system_prompt,
            history_window=history_window,
        )
        revision = persist_change(state, self.data_file)
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

    def window_info(self, history_window=None):
        state = self.load_or_create()
        snapshot = state.window_snapshot(history_window=history_window)
        return {
            "default_history_window": resolve_history_window(),
            "messages_stored": len(state.messages),
            **snapshot,
        }

    def clear(self, keep_system=True):
        state = self.load_or_create()
        changed, message = state.clear_messages(keep_system=keep_system)
        revision = persist_change(state, self.data_file)
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
