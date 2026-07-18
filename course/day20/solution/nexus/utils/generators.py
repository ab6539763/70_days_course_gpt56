"""消息历史生成器：yield 迭代为流式输出做铺垫。"""

from __future__ import annotations

from typing import Any, Dict, Generator, Iterable, List


MessageDict = Dict[str, str]


def iter_message_dicts(messages: Iterable[Any]) -> Generator[MessageDict, None, None]:
    """逐个 yield 消息 dict，避免一次性复制大列表。"""
    for item in messages:
        if hasattr(item, "to_dict"):
            yield item.to_dict()
        elif isinstance(item, dict):
            yield {"role": item["role"], "content": item["content"]}
        else:
            raise TypeError("消息必须是 dict 或带 to_dict 的对象")


def take_last(messages: List[MessageDict], limit: int) -> List[MessageDict]:
    """取最近 limit 条消息，用于窗口记忆。"""
    if limit <= 0:
        return []
    collected: List[MessageDict] = []
    for message in iter_message_dicts(messages):
        collected.append(message)
    return collected[-limit:]
