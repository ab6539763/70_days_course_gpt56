"""Day 10 课堂起步：拆分第一个模块与自定义异常。"""

# TODO: 把 ChatMessage 移到 nexus/domain/message.py
# TODO: 定义 NexusError 与 SchemaValidationError
# TODO: 在 load_state 中捕获 json.JSONDecodeError


class ChatMessage:
    ALLOWED_ROLES = ("system", "user", "assistant")

    def __init__(self, role, content):
        self.role = role.strip().lower()
        self.content = " ".join(content.split())


if __name__ == "__main__":
    print(ChatMessage("user", "  模块化起步  ").role)
