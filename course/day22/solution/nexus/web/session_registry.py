"""Web 会话注册表：创建、列举与按 Session ID 绑定 state 文件。"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from nexus.config.session_config import (
    ensure_session_dir,
    generate_session_id,
    resolve_session_dir,
    session_file_path,
    validate_session_id,
)
from nexus.exceptions import PersistenceError, SchemaValidationError
from nexus.observability.audit_log import AuditLogStore
from nexus.observability.logging import get_logger, log_event
from nexus.persistence.storage import load_state, persist_change
from nexus.platform.state import PlatformState
from nexus.web.state_manager import WebStateManager


_registry_logger = get_logger("session")


class SessionRegistry:
    """管理 sessions/ 目录下按会话隔离的 JSON state 文件。"""

    def __init__(self, session_dir=None, audit_store: AuditLogStore | None = None):
        self.session_dir = ensure_session_dir(
            resolve_session_dir(session_dir) if session_dir is not None else None
        )
        self.audit_store = audit_store

    def create_session(self, owner=None) -> Dict[str, Any]:
        """创建新会话文件并返回 session_id 与元数据。"""
        session_id = generate_session_id()
        path = session_file_path(session_id, self.session_dir)
        state = PlatformState.empty()
        state.owner = owner or f"SESSION_{session_id[-8:]}"
        revision = persist_change(
            state,
            str(path),
            audit_event={
                "action": "session_create",
                "operator": state.owner,
                "session_id": session_id,
                "detail": "create_session",
            },
            audit_store=self.audit_store,
        )
        log_event(
            _registry_logger,
            20,
            "session_created",
            session_id=session_id,
            owner=state.owner,
            revision=revision,
        )
        return {
            "session_id": session_id,
            "owner": state.owner,
            "revision": revision,
            "messages": 0,
            "data_file": str(path),
        }

    def manager_for(self, session_id: str) -> WebStateManager:
        """返回绑定到指定会话文件的 WebStateManager。"""
        safe_id = validate_session_id(session_id)
        path = session_file_path(safe_id, self.session_dir)
        return WebStateManager(str(path), session_id=safe_id, audit_store=self.audit_store)

    def session_info(self, session_id: str) -> Dict[str, Any]:
        """读取会话元数据（不修改 state）。"""
        safe_id = validate_session_id(session_id)
        path = session_file_path(safe_id, self.session_dir)
        if not path.exists():
            raise FileNotFoundError(f"会话不存在：{safe_id}")
        try:
            state, status, error = load_state(str(path))
        except PersistenceError as error:
            raise PersistenceError(error.message) from error
        if status == "rejected":
            raise SchemaValidationError(error)
        if state is None:
            state = PlatformState.empty()
        stats = state.statistics()
        return {
            "session_id": safe_id,
            "owner": state.owner,
            "revision": state.revision,
            "messages": stats["messages"],
            "contacts": stats["contacts"],
            "documents": stats["documents"],
            "model": stats["model"],
            "data_file": str(path),
            "status": status,
        }

    def list_sessions(self) -> List[Dict[str, Any]]:
        """列举会话目录下全部会话摘要。"""
        items = []
        for path in sorted(self.session_dir.glob("*.json")):
            session_id = path.stem
            try:
                validate_session_id(session_id)
            except ValueError:
                continue
            try:
                items.append(self.session_info(session_id))
            except (PersistenceError, SchemaValidationError, FileNotFoundError):
                items.append(
                    {
                        "session_id": session_id,
                        "owner": None,
                        "revision": 0,
                        "messages": 0,
                        "data_file": str(path),
                        "status": "corrupt",
                    }
                )
        return items
