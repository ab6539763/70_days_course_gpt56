"""Token 粗估：教学用字符启发式。"""

from __future__ import annotations

from typing import Iterable


def estimate_tokens(text: str) -> int:
    """粗估 token 数：约 4 字符 1 token（中英混合教学近似）。"""
    if not text:
        return 0
    return max(1, (len(text) + 3) // 4)


def estimate_messages_tokens(messages: Iterable[dict]) -> int:
    """估算 messages 数组总 token。"""
    total = 0
    for item in messages:
        total += estimate_tokens(str(item.get("content", "")))
    return total
