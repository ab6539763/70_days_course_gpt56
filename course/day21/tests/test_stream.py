"""Day 20 SSE 流式、断流模拟与 resume_stream_turn 单测。"""

import os
import sys
from pathlib import Path


SOLUTION = Path(__file__).parents[1] / "solution"
sys.path.insert(0, str(SOLUTION))

from nexus.exceptions import ApiCallError
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

interrupt_state = PlatformState.empty()
partial_parts = []
interrupted = False
try:
    for item in interrupt_state.conversation_turn_stream(
        "断流测试",
        force_mock=True,
        interrupt_after=1,
    ):
        if item["event"] == "chunk":
            partial_parts.append(item["payload"]["delta"])
except ApiCallError:
    interrupted = True
assert interrupted is True
assert len(partial_parts) >= 1

partial = "".join(partial_parts)
resume_events = list(interrupt_state.resume_stream_turn(partial, force_mock=True))
assert any(item["event"] == "resume" for item in resume_events)
resume_done = next(item for item in resume_events if item["event"] == "done")
assert resume_done["payload"]["resumed"] is True
assert resume_done["payload"]["assistant"].startswith(partial)

print("Day 20 SSE 流式单测通过：delta、断流模拟与 resume_stream_turn 均正确。")
