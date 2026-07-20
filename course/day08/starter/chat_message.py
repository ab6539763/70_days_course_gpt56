"""Day 8 课堂起步代码：第一个 Agent 领域类。"""


class ChatMessage:
    """表示一条结构化对话消息。"""

    ALLOWED_ROLES = ("system", "user", "assistant")

    def __init__(self, role, content):
        self.role = role.strip().lower()
        self.content = " ".join(content.split())

    def to_dict(self):
        """转换为未来模型 API 使用的字典。"""

        return {"role": self.role, "content": self.content}

    @classmethod
    def from_dict(cls, data):
        """从 JSON 字典恢复对象。"""

        return cls(data["role"], data["content"])

    @staticmethod
    def is_valid_role(role):
        """角色校验不依赖具体实例。"""

        return role.strip().lower() in ChatMessage.ALLOWED_ROLES


message = ChatMessage(" user ", "  请查询   企业制度  ")
print(message.to_dict())
