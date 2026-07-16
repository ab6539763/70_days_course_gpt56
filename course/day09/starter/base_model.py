"""Day 9 课堂起步代码：模型基类与第一个子类。"""


class BaseModel:
    """所有供应商模型的公共接口。"""

    PROVIDER = "base"

    def __init__(self, model_id, temperature=0.7, max_tokens=1024):
        self.model_id = model_id.strip()
        self._temperature = 0.7
        self.max_tokens = max_tokens
        # TODO: 通过 property 设置 temperature，限制 0~2

    @property
    def temperature(self):
        return self._temperature

    @temperature.setter
    def temperature(self, value):
        # TODO: 校验范围并赋值
        self._temperature = float(value)

    def format_request(self, messages):
        raise NotImplementedError("子类必须实现 format_request")

    def __call__(self, messages):
        payload = self.format_request(messages)
        return f"模拟回复：{payload}"


class OpenAIModel(BaseModel):
    """OpenAI 兼容请求格式。"""

    PROVIDER = "openai"

    def __init__(self, model_id="gpt-4o-mini", temperature=0.7, max_tokens=1024):
        # TODO: 调用 super().__init__
        self.model_id = model_id

    def format_request(self, messages):
        return {
            "model": self.model_id,
            "messages": messages,
            "temperature": self.temperature,
        }


model = OpenAIModel()
print(model.format_request([{"role": "user", "content": "你好"}]))
