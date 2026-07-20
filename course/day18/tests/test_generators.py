"""Day 13 生成器与消息窗口单测。"""

import sys
from pathlib import Path


SOLUTION = Path(__file__).parents[1] / "solution"
sys.path.insert(0, str(SOLUTION))

from nexus.domain.message import ChatMessage
from nexus.utils.generators import iter_message_dicts, take_last


messages = [
    ChatMessage("user", "第一条"),
    ChatMessage("assistant", "回复一"),
    ChatMessage("user", "第二条"),
]
stream = list(iter_message_dicts(messages))
assert stream[0]["content"] == "第一条"
assert len(stream) == 3
window = take_last(messages, 2)
assert len(window) == 2
assert window[-1]["content"] == "第二条"

print("Day 13 生成器单测通过：yield 迭代与窗口截取均正确。")
