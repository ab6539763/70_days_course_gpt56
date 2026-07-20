"""Day 17 Token 窗口、take_last 与 token 粗估单测。"""

import os
import sys
from pathlib import Path


SOLUTION = Path(__file__).parents[1] / "solution"
sys.path.insert(0, str(SOLUTION))

from nexus.config.window_config import resolve_history_window
from nexus.constants import DEFAULT_HISTORY_WINDOW, MAX_HISTORY_WINDOW
from nexus.platform.state import PlatformState
from nexus.utils.token_estimate import estimate_messages_tokens, estimate_tokens


assert estimate_tokens("abcd") == 1
assert estimate_tokens("") == 0

os.environ["NEXUS_USE_MOCK"] = "1"
os.environ["NEXUS_HISTORY_WINDOW"] = "4"
assert resolve_history_window() == 4
assert resolve_history_window(2) == 2

state = PlatformState.empty()
for index in range(6):
    state.add_message("user", f"问题{index}")
    state.add_message("assistant", f"回答{index}")

messages, meta = state.build_conversation_request(history_window=4)
assert meta["non_system_total"] == 12
assert meta["non_system_sent"] == 4
assert meta["window_applied"] is True
assert len([item for item in messages if item["role"] != "system"]) == 4

full_tokens = meta["tokens_estimated_full"]
sent_tokens = meta["tokens_estimated_sent"]
assert sent_tokens <= full_tokens
assert estimate_messages_tokens(messages) == sent_tokens

changed, _, reply, turn_meta = state.conversation_turn(
    "窗口测试", history_window=2, force_mock=True,
)
assert changed and turn_meta["history_window"] == 2
assert len(state.messages) == 14

snapshot = state.window_snapshot(history_window=2)
assert snapshot["history_window"] == 2

try:
    resolve_history_window(MAX_HISTORY_WINDOW + 1)
except ValueError:
    pass
else:
    raise AssertionError("应拒绝超大窗口")

print("Day 17 Token 窗口单测通过：take_last、粗估与 conversation_turn 均正确。")
