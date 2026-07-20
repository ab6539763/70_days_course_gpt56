"""Day 8 参考实现：Contact、ChatMessage 与 PlatformState 领域对象。"""

import json
import os


DATA_FILE = "nexus_platform.json"
SCHEMA_VERSION = 2
VALID_DEPARTMENTS = ("客户服务部", "销售部", "财务部", "技术部", "产品部")


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


class PlatformState:
    """聚合联系人与对话消息，并维护 revision。"""

    def __init__(self, owner=None, contacts=None, messages=None, revision=0):
        self.owner = owner
        self.contacts = list(contacts or [])
        self.messages = list(messages or [])
        self.revision = revision

    def to_dict(self):
        return {
            "schema_version": SCHEMA_VERSION,
            "revision": self.revision,
            "owner": self.owner,
            "contacts": [contact.to_dict() for contact in self.contacts],
            "messages": [message.to_dict() for message in self.messages],
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

    def statistics(self):
        return {
            "contacts": len(self.contacts),
            "messages": len(self.messages),
            "roles": {
                role: len([item for item in self.messages if item.role == role])
                for role in ChatMessage.ALLOWED_ROLES
            },
        }

    @classmethod
    def empty(cls):
        return cls()

    @classmethod
    def from_dict(cls, data):
        version = data.get("schema_version")
        if version not in (1, 2):
            return None, False, "不支持的 schema_version"
        required = {"revision", "owner", "contacts"}
        if not required.issubset(data.keys()):
            return None, False, "缺少 revision/owner/contacts"
        contacts = [Contact.from_dict(item) for item in data["contacts"]]
        messages = [
            ChatMessage.from_dict(item) for item in data.get("messages", [])
        ]
        migrated = version == 1
        return cls(
            owner=data["owner"],
            contacts=contacts,
            messages=messages,
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


def run_cli(data_file=DATA_FILE):
    print("=" * 76)
    print("智枢 NexusAI 0.0.8｜面向对象平台")
    print("=" * 76)
    state, status, error = load_state(data_file)
    if status == "rejected":
        print(f"数据拒绝：{error}。")
        return 3
    if status == "migrated":
        revision = persist_change(state, data_file)
        print(f"Schema v1 已迁移至 v2｜revision={revision}。")
    elif status == "loaded":
        print(
            f"恢复成功：revision={state.revision}｜"
            f"联系人={len(state.contacts)}｜消息={len(state.messages)}。"
        )

    if state.owner is None:
        state.owner = prompt_owner()
        revision = persist_change(state, data_file)
        print(f"维护人已保存｜revision={revision}。")

    while True:
        print("\n1新增联系人 2查看联系人 3搜索 4新增消息 5消息历史 6统计 7摘要 0退出")
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
                f"摘要：schema=2｜revision={state.revision}｜"
                f"contacts={len(state.contacts)}｜messages={len(state.messages)}"
            )
        elif choice == "0":
            print(f"安全退出｜revision={state.revision}。")
            return 0
        else:
            print("菜单错误：仅支持0-7。")


if __name__ == "__main__":
    raise SystemExit(run_cli())
