"""通义千问 DashScope 兼容模型（教学简化版）。"""

from nexus.models.base import BaseModel


class QwenModel(BaseModel):
    """通义千问 DashScope 兼容格式（教学简化版）。"""

    PROVIDER = "qwen"

    def __init__(self, model_id="qwen-plus", temperature=0.7, max_tokens=1024):
        super().__init__(model_id, temperature, max_tokens)

    def format_request(self, messages):
        return {
            "model": self.model_id,
            "input": {"messages": messages},
            "parameters": {
                "temperature": self.temperature,
                "max_tokens": self.max_tokens,
            },
        }

    def parse_response(self, raw_text):
        parsed = super().parse_response(raw_text)
        parsed["finish_reason"] = "stop"
        return parsed
