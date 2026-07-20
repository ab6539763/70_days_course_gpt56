"""流式断流恢复：resume_token 暂存与 TTL 治理。"""

from __future__ import annotations

import os
import time
import uuid
from dataclasses import dataclass
from typing import Dict, Optional

from nexus.constants import DEFAULT_STREAM_RESUME_TTL, RESUME_TOKEN_PREFIX


@dataclass
class StreamResumeRecord:
    """一次未完成流式对话的恢复上下文。"""

    resume_token: str
    session_id: str
    data_file: str
    user_prompt: str
    partial_assistant: str
    system_prompt: str
    history_window: Optional[int]
    created_at: float
    expires_at: float


class StreamResumeStore:
    """进程内 resume_token 存储（教学用；生产可换 Redis）。"""

    def __init__(self, ttl_seconds=None):
        self.ttl_seconds = int(ttl_seconds or resolve_resume_ttl())
        self._records: Dict[str, StreamResumeRecord] = {}

    def _purge_expired(self) -> None:
        now = time.time()
        expired = [token for token, item in self._records.items() if item.expires_at <= now]
        for token in expired:
            self._records.pop(token, None)

    def create(
        self,
        session_id: str,
        data_file: str,
        user_prompt: str,
        partial_assistant: str,
        system_prompt="你是企业助手",
        history_window=None,
    ) -> StreamResumeRecord:
        """登记断流上下文并返回 resume_token。"""
        self._purge_expired()
        token = f"{RESUME_TOKEN_PREFIX}{uuid.uuid4().hex}"
        now = time.time()
        record = StreamResumeRecord(
            resume_token=token,
            session_id=session_id,
            data_file=data_file,
            user_prompt=user_prompt,
            partial_assistant=partial_assistant,
            system_prompt=system_prompt,
            history_window=history_window,
            created_at=now,
            expires_at=now + self.ttl_seconds,
        )
        self._records[token] = record
        return record

    def get(self, resume_token: str) -> Optional[StreamResumeRecord]:
        """读取未过期的恢复记录。"""
        self._purge_expired()
        record = self._records.get(str(resume_token or "").strip())
        if record is None:
            return None
        if record.expires_at <= time.time():
            self._records.pop(record.resume_token, None)
            return None
        return record

    def consume(self, resume_token: str) -> Optional[StreamResumeRecord]:
        """读取并删除恢复记录（成功完成后调用）。"""
        record = self.get(resume_token)
        if record is not None:
            self._records.pop(record.resume_token, None)
        return record

    def count(self) -> int:
        self._purge_expired()
        return len(self._records)


def resolve_resume_ttl() -> int:
    """解析 NEXUS_STREAM_RESUME_TTL 环境变量。"""
    raw = os.environ.get("NEXUS_STREAM_RESUME_TTL", str(DEFAULT_STREAM_RESUME_TTL)).strip()
    try:
        ttl = int(raw)
    except ValueError as error:
        raise ValueError(f"NEXUS_STREAM_RESUME_TTL 必须是整数：{raw}") from error
    if ttl <= 0:
        raise ValueError(f"NEXUS_STREAM_RESUME_TTL 必须大于 0：{ttl}")
    return ttl


def validate_resume_token(resume_token: str) -> str:
    """校验 resume_token 基本格式。"""
    normalized = str(resume_token or "").strip()
    if not normalized.startswith(RESUME_TOKEN_PREFIX):
        raise ValueError(f"resume_token 格式非法：{normalized}")
    if len(normalized) < len(RESUME_TOKEN_PREFIX) + 8:
        raise ValueError(f"resume_token 格式非法：{normalized}")
    return normalized
