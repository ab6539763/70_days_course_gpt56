"""Agent 对话消息领域对象。"""


class ChatMessage:
    """Agent 对话消息：角色与内容始终一起传递。"""

    ALLOWED_ROLES = ("system", "user", "assistant")

    def __init__(self, role, content):
        self.role = role.strip().lower()
        self.content = self.normalize_content(content)

    def to_dict(self):
        return {"role": self.role, "content": self.content}

    def preview(self, limit=30):
        return self.content[:limit]

    @classmethod
    def from_dict(cls, data):
        return cls(data["role"], data["content"])

    @classmethod
    def system(cls, content):
        return cls("system", content)

    @staticmethod
    def normalize_content(content):
        return " ".join(content.split())

    @staticmethod
    def is_valid_role(role):
        return role.strip().lower() in ChatMessage.ALLOWED_ROLES
