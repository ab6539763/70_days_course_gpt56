"""乐观锁：expected_revision 与磁盘 revision 比对。"""

from __future__ import annotations

import os
from typing import Optional

from nexus.exceptions import RevisionConflictError, SchemaValidationError


def require_revision() -> bool:
    """是否强制 Web 写操作携带 expected_revision。"""
    raw = os.environ.get("NEXUS_REQUIRE_REVISION", "0").strip().lower()
    return raw in ("1", "true", "yes", "on")


def parse_expected_revision(raw) -> int:
    """解析 expected_revision 为正整数。"""
    if raw is None:
        raise ValueError("expected_revision 不能为空")
    if isinstance(raw, bool):
        raise ValueError("expected_revision 必须是整数")
    try:
        value = int(raw)
    except (TypeError, ValueError) as error:
        raise ValueError(f"expected_revision 必须是整数：{raw}") from error
    if value < 0:
        raise ValueError(f"expected_revision 不能为负数：{value}")
    return value


def assert_revision_on_disk(data_file: str, expected_revision: int) -> None:
    """写前重读磁盘 revision，与客户端期望值比对。"""
    from nexus.persistence.storage import load_state

    state, status, error = load_state(data_file)
    if status == "rejected":
        raise SchemaValidationError(error)
    actual = state.revision
    expected = int(expected_revision)
    if actual != expected:
        raise RevisionConflictError(
            f"revision 冲突：客户端期望 {expected}，磁盘当前 {actual}",
            expected=expected,
            actual=actual,
        )


def resolve_expected_revision(header_value: Optional[str], body_value) -> Optional[int]:
    """合并 Header 与 Body 的 expected_revision；Header 优先。"""
    if header_value is not None and str(header_value).strip() != "":
        return parse_expected_revision(str(header_value).strip())
    if body_value is not None:
        return parse_expected_revision(body_value)
    return None
