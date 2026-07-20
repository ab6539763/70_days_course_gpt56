"""Day 18 SSE 流式、delta 与 conversation_turn_stream 单测。"""

import os
import sys
from pathlib import Path


SOLUTION = Path(__file__).parents[1] / "solution"
sys.path.insert(0, str(SOLUTION))

from nexus.http.stream_client import collect_stream_text, extract_stream_delta
from nexus.platform.state import PlatformState
from nexus.web.sse import format_sse_event


assert extract_stream_delta(
    {"choices": [{"delta": {"content": "你"}}]}
) == "你"
assert extract_stream_delta({"choices": []}) == ""

chunks = [
    {"choices": [{"delta": {"content": "Hel"}}]},
    {"choices": [{"delta": {"content": "lo"}}]},
]
assert collect_stream_text(chunks) == "Hello"

sse = format_sse_event("chunk", {"delta": "A"})
assert sse.startswith("event: chunk\n")
assert '"delta": "A"' in sse

os.environ["NEXUS_USE_MOCK"] = "1"
os.environ["NEXUS_HISTORY_WINDOW"] = "4"
state = PlatformState.empty()
deltas = []
for item in state.conversation_turn_stream("流式第一轮", history_window=2, force_mock=True):
    if item["event"] == "chunk":
        deltas.append(item["payload"]["delta"])
    if item["event"] == "done":
        done = item["payload"]
assert len(deltas) >= 1
assert done["assistant"] == "".join(deltas)
assert len(state.messages) == 2
assert done["window"]["history_window"] == 2

for index in range(4):
    list(state.conversation_turn_stream(f"追加{index}", force_mock=True))

_, meta = state.build_conversation_request(history_window=2)
assert meta["window_applied"] is True

print("Day 18 SSE 流式单测通过：delta、SSE 格式与 conversation_turn_stream 均正确。")
