"""审计日志：记录每次 revision 变更的操作者、动作与 trace_id。"""

from __future__ import annotations

import json
import os
import time
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List, Optional

from nexus.constants import DEFAULT_AUDIT_DIR, DEFAULT_AUDIT_MAX_ENTRIES
from nexus.observability.logging import current_trace_id, get_logger, log_event


_audit_logger = get_logger("audit")


@dataclass
class AuditRecord:
    """一条 revision 变更审计记录。"""

    audit_id: str
    revision: int
    action: str
    operator: str
    session_id: str
    trace_id: str
    data_file: str
    created_at: float
    detail: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


class AuditLogStore:
    """按 data_file 分组的审计日志（内存 + JSONL 落盘）。"""

    def __init__(self, audit_dir=None, max_entries=None):
        self.audit_dir = Path(audit_dir or resolve_audit_dir())
        self.max_entries = int(max_entries or resolve_audit_max_entries())
        self.audit_dir.mkdir(parents=True, exist_ok=True)
        self._records: Dict[str, List[AuditRecord]] = {}

    def _key(self, data_file: str) -> str:
        return str(Path(data_file).resolve())

    def _file_path(self, data_file: str) -> Path:
        name = Path(data_file).stem or "default"
        safe = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in name)
        return self.audit_dir / f"{safe}.jsonl"

    def append(
        self,
        data_file: str,
        revision: int,
        action: str,
        operator: str = "",
        session_id: str = "",
        trace_id: str = "",
        detail: str = "",
    ) -> AuditRecord:
        """追加审计记录并可选写入 JSONL。"""
        record = AuditRecord(
            audit_id=f"aud_{uuid.uuid4().hex[:16]}",
            revision=int(revision),
            action=str(action or "persist"),
            operator=str(operator or "UNKNOWN"),
            session_id=str(session_id or ""),
            trace_id=str(trace_id or current_trace_id()),
            data_file=str(data_file),
            created_at=time.time(),
            detail=str(detail or ""),
        )
        key = self._key(data_file)
        bucket = self._records.setdefault(key, [])
        bucket.append(record)
        if len(bucket) > self.max_entries:
            del bucket[: len(bucket) - self.max_entries]
        self._append_file(record)
        log_event(
            _audit_logger,
            20,
            "audit_recorded",
            audit_id=record.audit_id,
            revision=record.revision,
            action=record.action,
            session_id=record.session_id,
        )
        return record

    def _append_file(self, record: AuditRecord) -> None:
        path = self._file_path(record.data_file)
        try:
            with open(path, "a", encoding="utf-8") as file:
                file.write(json.dumps(record.to_dict(), ensure_ascii=False) + "\n")
        except OSError as error:
            log_event(_audit_logger, 40, "audit_write_failed", error=str(error))

    def list_for(self, data_file: str, limit: int = 50) -> List[AuditRecord]:
        """读取指定 data_file 的审计记录（新到旧）。"""
        key = self._key(data_file)
        records = list(self._records.get(key, []))
        if not records:
            records = self._load_file(data_file)
            self._records[key] = records
        records = sorted(records, key=lambda item: item.created_at, reverse=True)
        return records[: max(1, int(limit))]

    def _load_file(self, data_file: str) -> List[AuditRecord]:
        path = self._file_path(data_file)
        if not path.exists():
            return []
        records: List[AuditRecord] = []
        try:
            for line in path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                payload = json.loads(line)
                records.append(AuditRecord(**payload))
        except (OSError, json.JSONDecodeError, TypeError) as error:
            log_event(_audit_logger, 30, "audit_load_failed", error=str(error))
            return []
        if len(records) > self.max_entries:
            records = records[-self.max_entries :]
        return records

    def count_for(self, data_file: str) -> int:
        return len(self.list_for(data_file, limit=self.max_entries))

    def total_count(self) -> int:
        return sum(len(items) for items in self._records.values())


def resolve_audit_dir() -> str:
    raw = os.environ.get("NEXUS_AUDIT_DIR", DEFAULT_AUDIT_DIR).strip()
    if raw == "":
        raise ValueError("NEXUS_AUDIT_DIR 不能为空")
    return raw


def resolve_audit_max_entries() -> int:
    raw = os.environ.get("NEXUS_AUDIT_MAX_ENTRIES", str(DEFAULT_AUDIT_MAX_ENTRIES)).strip()
    try:
        value = int(raw)
    except ValueError as error:
        raise ValueError(f"NEXUS_AUDIT_MAX_ENTRIES 必须是整数：{raw}") from error
    if value <= 0:
        raise ValueError(f"NEXUS_AUDIT_MAX_ENTRIES 必须大于 0：{value}")
    return value


def record_audit_event(
    data_file: str,
    revision: int,
    action: str,
    operator: str = "",
    session_id: str = "",
    trace_id: str = "",
    detail: str = "",
    audit_store: Optional[AuditLogStore] = None,
) -> Optional[AuditRecord]:
    """便捷封装：在 persist_change 后写入审计记录。"""
    if audit_store is None:
        return None
    return audit_store.append(
        data_file=data_file,
        revision=revision,
        action=action,
        operator=operator,
        session_id=session_id,
        trace_id=trace_id or current_trace_id(),
        detail=detail,
    )
