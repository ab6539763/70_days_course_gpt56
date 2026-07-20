"""Day 17 多轮对话单测（含窗口 metadata）。"""

import importlib.util
import os
import sys
from pathlib import Path


SOLUTION = Path(__file__).parents[1] / "solution"
sys.path.insert(0, str(SOLUTION))

MOCK = Path(__file__).parent / "mock_api.py"
spec = importlib.util.spec_from_file_location("mock_api", MOCK)
mock_api = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(mock_api)

from nexus.http.config import reset_bootstrap
from nexus.platform.state import PlatformState


server, base_url = mock_api.start_mock_api_server()
os.environ["NEXUS_API_KEY"] = "chat-test-key"
os.environ["NEXUS_API_BASE_URL"] = base_url
os.environ.pop("NEXUS_USE_MOCK", None)
reset_bootstrap()

state = PlatformState.empty()
changed1, _, reply1, meta1 = state.conversation_turn("第一轮问题")
assert changed1 and "HTTP mock 回复" in reply1
assert len(state.messages) == 2
assert meta1["history_window"] == 20

changed2, _, reply2, meta2 = state.conversation_turn("第二轮追问")
assert changed2 and len(state.messages) == 4
request, req_meta = state.build_conversation_request(history_window=2)
assert req_meta["non_system_sent"] == 2
assert request[-2]["role"] == "user"
assert request[-1]["role"] == "assistant"

cleared, message = state.clear_messages(keep_system=True)
assert cleared and len(state.messages) == 0

os.environ["NEXUS_USE_MOCK"] = "1"
mock_state = PlatformState.empty()
_, _, mock_reply = mock_state.simulate_chat("mock 单轮")
assert "[qwen]" in mock_reply
assert len(mock_state.messages) == 2

server.shutdown()
print("Day 17 多轮对话单测通过：history 持久化、窗口 metadata 与 clear 均正确。")
