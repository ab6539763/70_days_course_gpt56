"""通义千问 DashScope 兼容模型（OpenAI 兼容模式）。"""

from nexus.models.base import BaseModel


class QwenModel(BaseModel):
    """通义千问 DashScope OpenAI 兼容模式。"""

    PROVIDER = "qwen"

    def __init__(self, model_id="qwen-plus", temperature=0.7, max_tokens=1024):
        super().__init__(model_id, temperature, max_tokens)

    def format_request(self, messages, stream=False):
        # HTTP 层统一使用 Chat Completions 顶层 messages 结构。
        body = {
            "model": self.model_id,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
        if stream:
            body["stream"] = True
        return body

    def parse_response(self, raw_text):
        parsed = super().parse_response(raw_text)
        parsed["finish_reason"] = "stop"
        return parsed
