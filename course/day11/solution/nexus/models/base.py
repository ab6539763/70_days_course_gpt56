"""多供应商大模型公共接口。"""

from nexus.exceptions import ModelConfigError


class BaseModel:
    """多供应商大模型公共接口：子类通过重写实现多态。"""

    PROVIDER = "base"

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

    def format_request(self, messages):
        raise NotImplementedError(
            f"{self.__class__.__name__} 必须实现 format_request"
        )

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

    def __call__(self, messages):
        payload = self.format_request(messages)
        request_messages = payload.get("messages") or payload["input"]["messages"]
        return self.simulate_response(request_messages)

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
