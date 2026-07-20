"""Day 15 HTTP API、重试与 Mock 服务器单测。"""

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

from nexus.exceptions import ApiCallError
from nexus.http.client import build_bearer_headers, post_json
from nexus.http.config import reset_bootstrap
from nexus.models.openai_model import OpenAIModel
from nexus.platform.state import PlatformState


server, base_url = mock_api.start_mock_api_server()
os.environ["NEXUS_API_KEY"] = "test-key-day15"
os.environ["NEXUS_API_BASE_URL"] = base_url
os.environ["NEXUS_API_RETRY"] = "3"
os.environ.pop("NEXUS_USE_MOCK", None)
reset_bootstrap()

headers = build_bearer_headers("test-key")
payload = {"model": "demo", "messages": [{"role": "user", "content": "ping"}]}
response = post_json(f"{base_url}/chat/completions", headers, payload)
assert "choices" in response

mock_api.set_fail_count(2)
openai = OpenAIModel("gpt-4o-mini", 0.2, 128)
text = openai.invoke_api([{"role": "user", "content": "重试测试"}])
assert "HTTP mock 回复" in text

state = PlatformState.empty()
changed, message, assistant = state.api_chat("API 单测")
assert changed and "HTTP mock 回复" in assistant
assert len(state.messages) == 2

os.environ["NEXUS_USE_MOCK"] = "1"
mock_reply = state.simulate_chat("模拟")
assert "[qwen]" in mock_reply[2]
assert len(state.messages) == 4

server.shutdown()
print("Day 15 API 单测通过：重试装饰器、日志与 invoke_api 均正确。")
