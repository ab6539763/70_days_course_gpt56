"""会话目录、Session ID 与独立 state 文件路径。"""

from __future__ import annotations

import os
import re
import uuid
from pathlib import Path

from nexus.constants import DEFAULT_SESSION_DIR, SESSION_ID_PREFIX, SESSION_ID_PATTERN


def resolve_session_dir(override=None) -> Path:
    """解析会话存储目录：参数优先，其次 NEXUS_SESSION_DIR 环境变量。"""
    if override is not None:
        return Path(str(override)).expanduser()
    raw = os.environ.get("NEXUS_SESSION_DIR", DEFAULT_SESSION_DIR).strip()
    if raw == "":
        raise ValueError("NEXUS_SESSION_DIR 不能为空")
    return Path(raw).expanduser()


def ensure_session_dir(directory: Path | None = None) -> Path:
    """确保会话目录存在并返回绝对路径。"""
    target = (directory or resolve_session_dir()).resolve()
    target.mkdir(parents=True, exist_ok=True)
    return target


def generate_session_id() -> str:
    """生成新的会话 ID（nxs_ + uuid hex）。"""
    return f"{SESSION_ID_PREFIX}{uuid.uuid4().hex}"


def validate_session_id(session_id: str) -> str:
    """校验 Session ID 格式，非法时抛 ValueError。"""
    normalized = str(session_id or "").strip()
    if normalized == "":
        raise ValueError("Session ID 不能为空")
    if len(normalized) > 80:
        raise ValueError("Session ID 过长")
    if not re.fullmatch(SESSION_ID_PATTERN, normalized):
        raise ValueError(f"Session ID 格式非法：{normalized}")
    return normalized


def session_file_path(session_id: str, directory: Path | None = None) -> Path:
    """返回会话对应的 JSON 文件路径（每会话一文件）。"""
    safe_id = validate_session_id(session_id)
    root = ensure_session_dir(directory)
    return root / f"{safe_id}.json"
