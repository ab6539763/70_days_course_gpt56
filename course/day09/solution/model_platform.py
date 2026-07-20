"""Day 9 参考实现：多供应商模型继承体系与平台 Schema v3。"""

import json
import os


DATA_FILE = "nexus_platform.json"
SCHEMA_VERSION = 3
VALID_DEPARTMENTS = ("客户服务部", "销售部", "财务部", "技术部", "产品部")
DEFAULT_MODEL_CONFIG = {
    "provider": "qwen",
    "model_id": "qwen-plus",
    "temperature": 0.7,
    "max_tokens": 1024,
}


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


class Contact:
    """企业协作者领域对象。"""

    def __init__(self, contact_id, name, department, role, email, skills=None):
        self.contact_id = contact_id.strip().upper().replace(" ", "")
        self.name = " ".join(name.split())
        self.department = department
        self.role = " ".join(role.split())
        self.email = email.strip().lower()
        self.skills = self.normalize_skills(skills or [])

    def to_dict(self):
        return {
            "contact_id": self.contact_id,
            "name": self.name,
            "department": self.department,
            "role": self.role,
            "email": self.email,
            "skills": self.skills,
        }

    def matches(self, keyword):
        query = keyword.strip().lower()
        if query == "":
            return False
        searchable = " ".join(
            [
                self.name,
                self.department,
                self.role,
                self.email,
                " ".join(self.skills),
            ]
        ).lower()
        return query in searchable

    def update_role(self, new_role):
        normalized = " ".join(new_role.split())
        if normalized == "" or normalized == self.role:
            return False
        self.role = normalized
        return True

    @classmethod
    def from_dict(cls, data):
        return cls(
            data["contact_id"],
            data["name"],
            data["department"],
            data["role"],
            data["email"],
            data.get("skills", []),
        )

    @staticmethod
    def normalize_skills(skills):
        return sorted(
            {skill.strip().lower() for skill in skills if skill.strip()}
        )

    @staticmethod
    def is_valid_email(email):
        value = email.strip().lower()
        if value.count("@") != 1:
            return False
        local_part, domain = value.split("@")
        return (
            local_part != ""
            and domain != ""
            and "." in domain
            and domain[0:1] != "."
            and domain[-1:] != "."
        )


class BaseModel:
    """多供应商大模型公共接口：子类通过重写实现多态。"""

    PROVIDER = "base"

    def __init__(self, model_id, temperature=0.7, max_tokens=1024):
        self.model_id = model_id.strip()
        self.max_tokens = int(max_tokens)
        self.temperature = temperature

    @property
    def temperature(self):
        return self._temperature

    @temperature.setter
    def temperature(self, value):
        numeric = float(value)
        if numeric < 0 or numeric > 2:
            raise ValueError("temperature 必须在 0 到 2 之间")
        self._temperature = numeric

    @property
    def display_name(self):
        return f"{self.PROVIDER}/{self.model_id}"

    def build_messages(self, system_prompt, user_prompt, history=None):
        """把平台消息列表转换为模型请求消息。"""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": user_prompt})
        return messages

    def format_request(self, messages):
        """子类必须实现供应商特定的请求体结构。"""
        raise NotImplementedError(
            f"{self.__class__.__name__} 必须实现 format_request"
        )

    def parse_response(self, raw_text):
        """子类可重写响应解析逻辑。"""
        return {"provider": self.PROVIDER, "content": raw_text.strip()}

    def simulate_response(self, messages):
        """教学版模拟推理：Day 12 才会替换为真实 HTTP 调用。"""
        last_user = ""
        for item in reversed(messages):
            if item["role"] == "user":
                last_user = item["content"]
                break
        preview = last_user[:40] if last_user else "空输入"
        return f"[{self.PROVIDER}] 模拟回复：{preview}"

    def __call__(self, messages):
        """让模型实例可调用，统一推理入口。"""
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


class OpenAIModel(BaseModel):
    """OpenAI Chat Completions 兼容格式。"""

    PROVIDER = "openai"

    def __init__(self, model_id="gpt-4o-mini", temperature=0.7, max_tokens=1024):
        super().__init__(model_id, temperature, max_tokens)

    def format_request(self, messages):
        return {
            "model": self.model_id,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }

    def parse_response(self, raw_text):
        parsed = super().parse_response(raw_text)
        parsed["api_style"] = "chat.completions"
        return parsed


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


MODEL_REGISTRY = {
    "openai": OpenAIModel,
    "qwen": QwenModel,
}


def create_model(config):
    """多态工厂：根据 provider 创建对应子类实例。"""
    provider = config.get("provider", "").strip().lower()
    model_cls = MODEL_REGISTRY.get(provider)
    if model_cls is None:
        raise ValueError(f"不支持的模型供应商：{provider}")
    return model_cls(
        config.get("model_id", ""),
        config.get("temperature", 0.7),
        config.get("max_tokens", 1024),
    )


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
        """根据持久化配置恢复多态模型实例。"""
        return create_model(self.model_config)

    def update_model_config(self, provider, model_id, temperature, max_tokens):
        """切换供应商前先用临时实例校验参数。"""
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
            return False, "消息角色必须是 system/user/assistant"
        message = ChatMessage(role, content)
        if message.content == "":
            return False, "消息内容不能为空"
        self.messages.append(message)
        return True, f"已新增 {message.role} 消息"

    def simulate_chat(self, user_prompt, system_prompt="你是企业助手"):
        """使用当前 active_model 多态执行一次模拟推理。"""
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
            return None, False, "不支持的 schema_version"
        required = {"revision", "owner", "contacts"}
        if not required.issubset(data.keys()):
            return None, False, "缺少 revision/owner/contacts"
        contacts = [Contact.from_dict(item) for item in data["contacts"]]
        messages = [
            ChatMessage.from_dict(item) for item in data.get("messages", [])
        ]
        migrated = version in (1, 2)
        model_config = data.get("model_config", DEFAULT_MODEL_CONFIG)
        return cls(
            owner=data["owner"],
            contacts=contacts,
            messages=messages,
            model_config=model_config,
            revision=data["revision"],
        ), migrated, ""


def load_state(data_file=DATA_FILE):
    if not os.path.exists(data_file):
        return PlatformState.empty(), "new", ""
    with open(data_file, "r", encoding="utf-8") as file:
        raw = file.read().strip()
    if raw == "":
        return PlatformState.empty(), "empty", ""
    state, migrated, error = PlatformState.from_dict(json.loads(raw))
    if state is None:
        return None, "rejected", error
    return state, "migrated" if migrated else "loaded", ""


def save_state(state, data_file=DATA_FILE):
    with open(data_file, "w", encoding="utf-8") as file:
        json.dump(
            state.to_dict(),
            file,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        file.write("\n")


def persist_change(state, data_file=DATA_FILE):
    state.revision += 1
    save_state(state, data_file)
    return state.revision


def normalize_department(raw):
    value = " ".join(raw.split())
    value = {"客服部": "客户服务部", "研发部": "技术部"}.get(value, value)
    return value if value in VALID_DEPARTMENTS else ""


def prompt_owner():
    employee_id = input("维护人员工编号：").strip().upper().replace(" ", "")
    department = ""
    while department == "":
        department = normalize_department(input("维护人部门："))
        if department == "":
            print("部门不在白名单。")
    return {"employee_id": employee_id, "department": department}


def prompt_contact():
    contact_id = input("联系人编号：")
    name = input("姓名：")
    department = ""
    while department == "":
        department = normalize_department(input("部门："))
        if department == "":
            print("部门不在白名单。")
    role = input("岗位：")
    while True:
        email = input("模拟邮箱：")
        if Contact.is_valid_email(email):
            break
        print("邮箱格式无效。")
    skills = input("技能（逗号分隔）：").split(",")
    return Contact(contact_id, name, department, role, email, skills)


def prompt_model_switch(state):
    print("可选供应商：openai / qwen")
    provider = input("供应商：").strip().lower()
    model_id = input("模型 ID：").strip()
    temperature_raw = input("temperature(0-2)：").strip()
    max_tokens_raw = input("max_tokens：").strip()
    try:
        temperature = float(temperature_raw)
        max_tokens = int(max_tokens_raw)
    except ValueError:
        return False, "temperature 或 max_tokens 格式无效"
    try:
        changed, message = state.update_model_config(
            provider,
            model_id,
            temperature,
            max_tokens,
        )
    except ValueError as error:
        return False, str(error)
    return changed, message


def run_cli(data_file=DATA_FILE):
    print("=" * 76)
    print("智枢 NexusAI 0.0.9｜多供应商模型继承平台")
    print("=" * 76)
    state, status, error = load_state(data_file)
    if status == "rejected":
        print(f"数据拒绝：{error}。")
        return 3
    if status == "migrated":
        revision = persist_change(state, data_file)
        saved = json.loads(open(data_file, encoding="utf-8").read())
        version = saved.get("schema_version")
        print(
            f"Schema 已迁移至 v{version}｜revision={revision}｜"
            f"model={state.active_model()}。"
        )
    elif status == "loaded":
        print(
            f"恢复成功：revision={state.revision}｜"
            f"联系人={len(state.contacts)}｜消息={len(state.messages)}｜"
            f"模型={state.active_model()}。"
        )

    if state.owner is None:
        state.owner = prompt_owner()
        revision = persist_change(state, data_file)
        print(f"维护人已保存｜revision={revision}。")

    while True:
        print(
            "\n1新增联系人 2查看联系人 3搜索 4新增消息 5消息历史 "
            "6统计 7摘要 8模型信息 9模拟对话 0退出"
        )
        choice = input("请选择：").strip()
        if choice == "1":
            changed, message = state.add_contact(prompt_contact())
            if changed:
                revision = persist_change(state, data_file)
                print(f"{message}｜revision={revision}。")
            else:
                print(message)
        elif choice == "2":
            for contact in state.search_contacts("@"):
                print(
                    f"{contact.contact_id}｜{contact.name}｜"
                    f"{contact.department}｜{contact.role}｜{contact.email}"
                )
        elif choice == "3":
            matched = state.search_contacts(input("关键词："))
            print(f"搜索结果：{len(matched)} 名。")
            for contact in matched:
                print(f"{contact.contact_id}｜{contact.name}｜{contact.role}")
        elif choice == "4":
            changed, message = state.add_message(
                input("角色："),
                input("内容："),
            )
            if changed:
                revision = persist_change(state, data_file)
                print(f"{message}｜revision={revision}。")
            else:
                print(message)
        elif choice == "5":
            print(f"消息总数：{len(state.messages)}。")
            for index, message in enumerate(state.messages, start=1):
                print(f"{index}. {message.role}｜{message.preview()}")
        elif choice == "6":
            print(f"统计：{state.statistics()}")
        elif choice == "7":
            print(
                f"摘要：schema=3｜revision={state.revision}｜"
                f"contacts={len(state.contacts)}｜messages={len(state.messages)}｜"
                f"model={state.active_model()}"
            )
        elif choice == "8":
            model = state.active_model()
            print(f"当前模型：{model}")
            print(f"repr：{model!r}")
            print(f"请求样例：{model.format_request([{'role': 'user', 'content': 'ping'}])}")
            switch = input("是否切换模型？(y/N)：").strip().lower()
            if switch == "y":
                changed, message = prompt_model_switch(state)
                if changed:
                    revision = persist_change(state, data_file)
                    print(f"{message}｜revision={revision}。")
                else:
                    print(message)
        elif choice == "9":
            user_prompt = input("用户问题：").strip()
            if user_prompt == "":
                print("用户问题不能为空。")
                continue
            changed, message, assistant_text = state.simulate_chat(user_prompt)
            if changed:
                revision = persist_change(state, data_file)
                print(f"{message}｜revision={revision}。")
                print(f"assistant：{assistant_text}")
            else:
                print(message)
        elif choice == "0":
            print(f"安全退出｜revision={state.revision}。")
            return 0
        else:
            print("菜单错误：仅支持0-9。")


if __name__ == "__main__":
    raise SystemExit(run_cli())
