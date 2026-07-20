"""多供应商大模型公共接口。"""

from nexus.exceptions import ApiCallError, ModelConfigError
from nexus.http.client import build_bearer_headers, post_json
from nexus.http.config import resolve_api_credentials, use_mock_mode
from nexus.http.stream_client import extract_stream_delta, post_stream_json
from nexus.constants import DEFAULT_STREAM_CHUNK_SIZE


class BaseModel:
    """多供应商大模型公共接口：子类通过重写实现多态。"""

    PROVIDER = "base"
    CHAT_PATH = "/chat/completions"

    def __init__(self, model_id, temperature=0.7, max_tokens=1024):
        self.model_id = model_id.strip()
        self.temperature = temperature
        self.max_tokens = max_tokens

    @property
    def temperature(self):
        return self._temperature

    @temperature.setter
    def temperature(self, value):
        numeric = float(value)
        if numeric < 0 or numeric > 2:
            raise ModelConfigError("temperature 必须在 0 到 2 之间")
        self._temperature = numeric

    @property
    def max_tokens(self):
        return self._max_tokens

    @max_tokens.setter
    def max_tokens(self, value):
        numeric = int(value)
        if numeric <= 0:
            raise ModelConfigError("max_tokens 必须大于 0")
        self._max_tokens = numeric

    @property
    def display_name(self):
        return f"{self.PROVIDER}/{self.model_id}"

    def build_messages(self, system_prompt, user_prompt, history=None):
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": user_prompt})
        return messages

    def format_request(self, messages, stream=False):
        raise NotImplementedError(
            f"{self.__class__.__name__} 必须实现 format_request"
        )

    def chat_url(self, base_url):
        root = base_url.rstrip("/")
        if root.endswith("/v1"):
            return f"{root}{self.CHAT_PATH}"
        return f"{root}/v1{self.CHAT_PATH}"

    def extract_assistant_content(self, payload):
        """解析 Chat Completions 兼容响应。"""
        try:
            return payload["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError, TypeError) as error:
            raise ApiCallError(f"无法解析 API 响应结构：{payload}") from error

    def parse_response(self, raw_text):
        return {"provider": self.PROVIDER, "content": raw_text.strip()}

    def simulate_response(self, messages):
        last_user = ""
        for item in reversed(messages):
            if item["role"] == "user":
                last_user = item["content"]
                break
        preview = last_user[:40] if last_user else "空输入"
        return f"[{self.PROVIDER}] 模拟回复：{preview}"

    def invoke_api(self, messages, api_key=None, base_url=None):
        """通过 HTTP POST 调用 Chat Completions 兼容接口。"""
        key, base = resolve_api_credentials(self.PROVIDER, api_key, base_url)
        if key == "":
            raise ApiCallError("缺少 API Key：请设置环境变量 NEXUS_API_KEY")
        body = self.format_request(messages, stream=False)
        response_payload = post_json(
            self.chat_url(base),
            build_bearer_headers(key),
            body,
        )
        content = self.extract_assistant_content(response_payload)
        return self.parse_response(content)["content"]

    def iter_stream_deltas(
        self,
        messages,
        api_key=None,
        base_url=None,
        force_mock=False,
        chunk_size=DEFAULT_STREAM_CHUNK_SIZE,
    ):
        """逐段 yield assistant 文本 delta；Mock 模式按 chunk_size 切分。"""
        if force_mock or use_mock_mode():
            yield from self.simulate_stream(messages, chunk_size=chunk_size)
            return
        key, base = resolve_api_credentials(self.PROVIDER, api_key, base_url)
        if key == "":
            raise ApiCallError("缺少 API Key：请设置环境变量 NEXUS_API_KEY")
        body = self.format_request(messages, stream=True)
        for chunk in post_stream_json(
            self.chat_url(base),
            build_bearer_headers(key),
            body,
        ):
            delta = extract_stream_delta(chunk)
            if delta:
                yield delta

    def simulate_stream(self, messages, chunk_size=DEFAULT_STREAM_CHUNK_SIZE):
        """Mock 流式：把 simulate_response 按固定长度切片。"""
        text = self.simulate_response(messages)
        if chunk_size <= 0:
            chunk_size = DEFAULT_STREAM_CHUNK_SIZE
        for index in range(0, len(text), chunk_size):
            yield text[index : index + chunk_size]

    def __call__(self, messages, api_key=None, base_url=None, force_mock=False):
        if force_mock or use_mock_mode():
            return self.simulate_response(messages)
        return self.invoke_api(messages, api_key=api_key, base_url=base_url)

    def __str__(self):
        return (
            f"{self.display_name} "
            f"(temperature={self.temperature}, max_tokens={self.max_tokens})"
        )

    def __repr__(self):
        return (
            f"{self.__class__.__name__}("
            f"model_id={self.model_id!r}, "
            f"temperature={self.temperature}, "
            f"max_tokens={self.max_tokens})"
        )

    def to_dict(self):
        return {
            "provider": self.PROVIDER,
            "model_id": self.model_id,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
