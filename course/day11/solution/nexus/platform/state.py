"""平台聚合根：联系人、消息、模型配置与语料索引。"""

from pathlib import Path

from nexus.constants import CORPUS_DIR, DEFAULT_MODEL_CONFIG, SCHEMA_VERSION
from nexus.documents.corpus import CorpusService, empty_document_index
from nexus.documents.loader import load_document
from nexus.domain.contact import Contact
from nexus.domain.message import ChatMessage
from nexus.exceptions import DocumentLoadError, InvalidMessageError, ModelConfigError, SchemaValidationError
from nexus.models.factory import create_model


class PlatformState:
    """聚合联系人、消息、模型配置、语料索引，并维护 revision。"""

    def __init__(
        self,
        owner=None,
        contacts=None,
        messages=None,
        model_config=None,
        document_index=None,
        revision=0,
    ):
        self.owner = owner
        self.contacts = list(contacts or [])
        self.messages = list(messages or [])
        self.model_config = dict(model_config or DEFAULT_MODEL_CONFIG)
        self.document_index = dict(document_index or empty_document_index(CORPUS_DIR))
        self.revision = revision

    def active_model(self):
        return create_model(self.model_config)

    def corpus_service(self):
        service = CorpusService(self.document_index)
        corpus_dir = Path(self.document_index.get("corpus_dir", CORPUS_DIR))
        for record in service.documents:
            path = corpus_dir / record.filename
            if path.exists():
                service._text_cache[record.filename] = load_document(path)
        return service

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

    def ingest_corpus(self, corpus_dir, keywords):
        service = CorpusService(self.document_index)
        count, totals = service.ingest_directory(corpus_dir, keywords)
        self.document_index = service.document_index
        return True, f"已导入 {count} 份语料｜关键词统计 {totals}"

    def search_corpus(self, keyword):
        service = self.corpus_service()
        return service.search_keyword(keyword)

    def to_dict(self):
        return {
            "schema_version": SCHEMA_VERSION,
            "revision": self.revision,
            "owner": self.owner,
            "contacts": [contact.to_dict() for contact in self.contacts],
            "messages": [message.to_dict() for message in self.messages],
            "model_config": self.model_config,
            "document_index": self.document_index,
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
        docs = self.document_index.get("documents", [])
        return {
            "contacts": len(self.contacts),
            "messages": len(self.messages),
            "documents": len(docs),
            "roles": {
                role: len([item for item in self.messages if item.role == role])
                for role in ChatMessage.ALLOWED_ROLES
            },
            "model": str(self.active_model()),
            "keyword_totals": self.document_index.get("keyword_totals", {}),
        }

    @classmethod
    def empty(cls):
        return cls()

    @classmethod
    def from_dict(cls, data):
        version = data.get("schema_version")
        if version not in (1, 2, 3, 4):
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
        migrated = version in (1, 2, 3)
        model_config = data.get("model_config", DEFAULT_MODEL_CONFIG)
        document_index = data.get("document_index", empty_document_index(CORPUS_DIR))
        try:
            create_model(model_config)
        except ModelConfigError as error:
            raise SchemaValidationError(f"model_config 非法：{error.message}") from error
        if not isinstance(document_index.get("documents"), list):
            raise SchemaValidationError("document_index.documents 必须是列表")
        return cls(
            owner=data["owner"],
            contacts=contacts,
            messages=messages,
            model_config=model_config,
            document_index=document_index,
            revision=data["revision"],
        ), migrated
