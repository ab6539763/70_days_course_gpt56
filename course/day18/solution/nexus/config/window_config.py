"""Token 窗口与 history 配置。"""

from __future__ import annotations

import os

from nexus.constants import DEFAULT_HISTORY_WINDOW, MAX_HISTORY_WINDOW


def resolve_history_window(override=None) -> int:
    """解析 history 窗口大小：参数优先，其次 NEXUS_HISTORY_WINDOW 环境变量。"""
    if override is not None:
        return _normalize_window(override)
    raw = os.environ.get("NEXUS_HISTORY_WINDOW", str(DEFAULT_HISTORY_WINDOW)).strip()
    try:
        return _normalize_window(int(raw))
    except ValueError as error:
        raise ValueError(f"NEXUS_HISTORY_WINDOW 必须是整数：{raw}") from error


def _normalize_window(value: int) -> int:
    numeric = int(value)
    if numeric < 0:
        raise ValueError(f"history 窗口不能为负数：{numeric}")
    if numeric > MAX_HISTORY_WINDOW:
        raise ValueError(f"history 窗口不能超过 {MAX_HISTORY_WINDOW}：{numeric}")
    return numeric
