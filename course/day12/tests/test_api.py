"""Day 12 HTTP 客户端与 API 调用单测。"""

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
from nexus.models.openai_model import OpenAIModel
from nexus.models.qwen_model import QwenModel
from nexus.platform.state import PlatformState


server, base_url = mock_api.start_mock_api_server()
os.environ["NEXUS_API_KEY"] = "test-key-day12"
os.environ["NEXUS_API_BASE_URL"] = base_url
os.environ.pop("NEXUS_USE_MOCK", None)

headers = build_bearer_headers("test-key")
payload = {"model": "demo", "messages": [{"role": "user", "content": "ping"}]}
response = post_json(f"{base_url}/chat/completions", headers, payload)
assert "choices" in response

openai = OpenAIModel("gpt-4o-mini", 0.2, 128)
text = openai.invoke_api([{"role": "user", "content": "制度在哪里"}])
assert "HTTP mock 回复" in text

qwen = QwenModel("qwen-plus")
qwen_text = qwen.invoke_api([{"role": "user", "content": "报销流程"}])
assert "报销流程" in qwen_text

state = PlatformState.empty()
changed, message, assistant = state.api_chat("API 单测问题")
assert changed and "HTTP mock 回复" in assistant

os.environ["NEXUS_USE_MOCK"] = "1"
mock_reply = state.simulate_chat("模拟路径")
assert "[qwen]" in mock_reply[2]

os.environ.pop("NEXUS_USE_MOCK", None)
os.environ.pop("NEXUS_API_KEY", None)
try:
    openai.invoke_api([{"role": "user", "content": "无 key"}])
    raise AssertionError("缺少 key 应失败")
except ApiCallError as error:
    assert error.code == "API_CALL"

server.shutdown()

print("Day 12 API 单测通过：requests、Mock 服务器与 invoke_api 均正确。")
