"""平台聚合根：联系人、消息与模型配置。"""

from nexus.constants import DEFAULT_MODEL_CONFIG, SCHEMA_VERSION
from nexus.domain.contact import Contact
from nexus.domain.message import ChatMessage
from nexus.exceptions import InvalidMessageError, ModelConfigError, SchemaValidationError
from nexus.models.factory import create_model


class PlatformState:
    """聚合联系人、消息、模型配置，并维护 revision。"""

    def __init__(
        self,
        owner=None,
        contacts=None,
        messages=None,
        model_config=None,
        revision=0,
    ):
        self.owner = owner
        self.contacts = list(contacts or [])
        self.messages = list(messages or [])
        self.model_config = dict(model_config or DEFAULT_MODEL_CONFIG)
        self.revision = revision

    def active_model(self):
        return create_model(self.model_config)

    def update_model_config(self, provider, model_id, temperature, max_tokens):
        candidate = create_model(
            {
                "provider": provider,
                "model_id": model_id,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
        )
        self.model_config = candidate.to_dict()
        return True, f"模型已切换为 {candidate}"

    def to_dict(self):
        return {
            "schema_version": SCHEMA_VERSION,
            "revision": self.revision,
            "owner": self.owner,
            "contacts": [contact.to_dict() for contact in self.contacts],
            "messages": [message.to_dict() for message in self.messages],
            "model_config": self.model_config,
        }

    def add_contact(self, contact):
        if any(item.contact_id == contact.contact_id for item in self.contacts):
            return False, f"联系人编号 {contact.contact_id} 已存在"
        if any(item.email == contact.email for item in self.contacts):
            return False, f"邮箱 {contact.email} 已存在"
        self.contacts.append(contact)
        return True, f"已新增 {contact.contact_id}｜{contact.name}"

    def search_contacts(self, keyword):
        matched = [item for item in self.contacts if item.matches(keyword)]
        return sorted(
            matched,
            key=lambda item: (item.department, item.name, item.contact_id),
        )

    def add_message(self, role, content):
        if not ChatMessage.is_valid_role(role):
            raise InvalidMessageError("消息角色必须是 system/user/assistant")
        message = ChatMessage(role, content)
        if message.content == "":
            raise InvalidMessageError("消息内容不能为空")
        self.messages.append(message)
        return True, f"已新增 {message.role} 消息"

    def simulate_chat(self, user_prompt, system_prompt="你是企业助手"):
        history = [message.to_dict() for message in self.messages]
        model = self.active_model()
        request_messages = model.build_messages(
            system_prompt,
            user_prompt,
            history=history,
        )
        assistant_text = model(request_messages)
        changed, message = self.add_message("assistant", assistant_text)
        return changed, message, assistant_text

    def statistics(self):
        return {
            "contacts": len(self.contacts),
            "messages": len(self.messages),
            "roles": {
                role: len([item for item in self.messages if item.role == role])
                for role in ChatMessage.ALLOWED_ROLES
            },
            "model": str(self.active_model()),
        }

    @classmethod
    def empty(cls):
        return cls()

    @classmethod
    def from_dict(cls, data):
        version = data.get("schema_version")
        if version not in (1, 2, 3):
            raise SchemaValidationError("不支持的 schema_version")
        required = {"revision", "owner", "contacts"}
        if not required.issubset(data.keys()):
            raise SchemaValidationError("缺少 revision/owner/contacts")
        try:
            contacts = [Contact.from_dict(item) for item in data["contacts"]]
            messages = [
                ChatMessage.from_dict(item) for item in data.get("messages", [])
            ]
        except (KeyError, TypeError) as error:
            raise SchemaValidationError(f"联系人或消息字段损坏：{error}") from error
        migrated = version in (1, 2)
        model_config = data.get("model_config", DEFAULT_MODEL_CONFIG)
        try:
            create_model(model_config)
        except ModelConfigError as error:
            raise SchemaValidationError(f"model_config 非法：{error.message}") from error
        return cls(
            owner=data["owner"],
            contacts=contacts,
            messages=messages,
            model_config=model_config,
            revision=data["revision"],
        ), migrated
