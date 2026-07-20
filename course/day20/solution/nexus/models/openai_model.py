"""OpenAI Chat Completions 兼容模型。"""

from nexus.models.base import BaseModel


class OpenAIModel(BaseModel):
    """OpenAI Chat Completions 兼容格式。"""

    PROVIDER = "openai"

    def __init__(self, model_id="gpt-4o-mini", temperature=0.7, max_tokens=1024):
        super().__init__(model_id, temperature, max_tokens)

    def format_request(self, messages, stream=False):
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
        parsed["api_style"] = "chat.completions"
        return parsed
