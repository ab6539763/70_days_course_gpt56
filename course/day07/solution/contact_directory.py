"""Day 7 阶段项目：可持久化企业联系人目录。

综合 Day 1-6：字符串治理、条件循环、集合去重、字典/JSON 与函数契约。
所有数据均为模拟资料；真实企业通讯录必须接入认证、权限和权威身份源。
"""

import json
import os


PRODUCT_NAME = "智枢 NexusAI"
VERSION = "0.0.7"
SCHEMA_VERSION = 1
DATA_FILE = "nexus_contacts.json"
VALID_DEPARTMENTS = (
    "客户服务部",
    "销售部",
    "财务部",
    "技术部",
    "产品部",
)


def create_default_data():
    """创建独立的联系人目录文档。"""

    return {
        "schema_version": SCHEMA_VERSION,
        "revision": 0,
        "owner": None,
        "contacts": [],
    }


def normalize_identifier(raw_value, prefix):
    """标准化 E/C 标识符，返回 valid/value/reason。"""

    value = raw_value.strip().upper().replace(" ", "")
    if value == "":
        return False, value, "不能为空"
    if value[0:1] != prefix or len(value) < 2:
        return False, value, f"必须以 {prefix} 开头并包含后续编号"
    return True, value, ""


def normalize_department(raw_value):
    """统一部门别名并检查白名单。"""

    value = " ".join(raw_value.split())
    aliases = {
        "客服部": "客户服务部",
        "客户服务中心": "客户服务部",
        "研发部": "技术部",
    }
    value = aliases.get(value, value)
    return value in VALID_DEPARTMENTS, value


def normalize_email(raw_value):
    """执行教学版邮箱格式校验，不发起真实邮件验证。"""

    value = raw_value.strip().lower()
    if value.count("@") != 1:
        return False, value, "必须包含且仅包含一个 @"
    local_part, domain = value.split("@")
    if local_part == "" or domain == "":
        return False, value, "@ 两侧不能为空"
    if "." not in domain or domain[0:1] == "." or domain[-1:] == ".":
        return False, value, "域名必须包含有效的点分隔"
    return True, value, ""


def normalize_skills(*skill_groups):
    """合并任意技能组，清理、去重并排序。"""

    result = set()
    for group in skill_groups:
        for skill in group:
            value = skill.strip().lower()
            if value:
                result.add(value)
    return sorted(result)


def create_contact(
    contact_id,
    name,
    department,
    role,
    email,
    skills=None,
):
    """构造联系人字典。"""

    if skills is None:
        skills = []
    return {
        "contact_id": contact_id,
        "name": " ".join(name.split()),
        "department": department,
        "role": " ".join(role.split()),
        "email": email,
        "skills": normalize_skills(skills),
    }


def validate_data(data):
    """验证顶层 Schema v1。"""

    if not isinstance(data, dict):
        return False, "顶层必须是对象"
    if data.get("schema_version") != SCHEMA_VERSION:
        return False, "不支持的 schema_version"
    required = {"revision", "owner", "contacts"}
    if not required.issubset(data.keys()):
        return False, "缺少 revision/owner/contacts"
    if not isinstance(data["contacts"], list):
        return False, "contacts 必须是列表"
    return True, ""


def load_data(data_file=DATA_FILE):
    """加载目录并返回 data/status/error。"""

    if not os.path.exists(data_file):
        return create_default_data(), "new", ""
    with open(data_file, "r", encoding="utf-8") as file:
        raw = file.read().strip()
    if raw == "":
        return create_default_data(), "empty", ""
    data = json.loads(raw)
    valid, error = validate_data(data)
    if not valid:
        return data, "rejected", error
    return data, "loaded", ""


def save_data(data, data_file=DATA_FILE):
    """保存稳定 UTF-8 JSON。"""

    with open(data_file, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2, sort_keys=True)
        file.write("\n")
    return data_file


def persist_change(data, data_file=DATA_FILE):
    """增加 revision 后保存。"""

    data["revision"] += 1
    save_data(data, data_file)
    return data["revision"]


def add_contact(data, contact):
    """检查编号和邮箱唯一性后新增。"""

    ids = {item["contact_id"] for item in data["contacts"]}
    emails = {item["email"] for item in data["contacts"]}
    if contact["contact_id"] in ids:
        return False, f"联系人编号 {contact['contact_id']} 已存在"
    if contact["email"] in emails:
        return False, f"邮箱 {contact['email']} 已存在"
    data["contacts"].append(contact)
    return True, f"已新增 {contact['contact_id']}｜{contact['name']}"


def update_contact(data, contact_id, **changes):
    """更新允许字段，并守住邮箱唯一性。"""

    allowed = {"name", "department", "role", "email", "skills"}
    for contact in data["contacts"]:
        if contact["contact_id"] != contact_id:
            continue
        if "email" in changes:
            duplicate = any(
                item["contact_id"] != contact_id
                and item["email"] == changes["email"]
                for item in data["contacts"]
            )
            if duplicate:
                return False, f"邮箱 {changes['email']} 已存在"
        changed = False
        for key, value in changes.items():
            if key in allowed and contact.get(key) != value:
                contact[key] = value
                changed = True
        if changed:
            return True, f"已更新 {contact_id}"
        return False, f"联系人 {contact_id} 无字段变化"
    return False, f"未找到联系人 {contact_id}"


def delete_contact(data, contact_id):
    """按编号删除联系人。"""

    for index, contact in enumerate(data["contacts"]):
        if contact["contact_id"] == contact_id:
            removed = data["contacts"].pop(index)
            return True, f"已删除 {removed['contact_id']}｜{removed['name']}"
    return False, f"未找到联系人 {contact_id}"


def ordered_contacts(contacts):
    """返回按部门、姓名、编号排序的新列表。"""

    decorated = [
        [item["department"], item["name"], item["contact_id"], item]
        for item in contacts
    ]
    decorated.sort()
    return [item[3] for item in decorated]


def search_contacts(contacts, keyword):
    """跨姓名、部门、岗位、邮箱和技能执行大小写无关搜索。"""

    query = keyword.strip().lower()
    if query == "":
        return []
    matched = []
    for contact in contacts:
        searchable = " ".join(
            [
                contact["name"],
                contact["department"],
                contact["role"],
                contact["email"],
                " ".join(contact["skills"]),
            ]
        ).lower()
        if query in searchable:
            matched.append(contact)
    return ordered_contacts(matched)


def directory_statistics(contacts):
    """返回联系人总数、部门计数和唯一技能。"""

    department_counts = {}
    skills = set()
    for contact in contacts:
        department = contact["department"]
        department_counts[department] = department_counts.get(department, 0) + 1
        skills.update(contact["skills"])
    return {
        "total": len(contacts),
        "departments": {
            key: department_counts[key]
            for key in sorted(department_counts)
        },
        "skills": sorted(skills),
    }


def prompt_owner():
    """采集目录维护人，三次编号失败返回 None。"""

    employee_id = None
    for attempt in range(1, 4):
        valid, value, reason = normalize_identifier(
            input(f"维护人员工编号（第 {attempt}/3 次）："),
            "E",
        )
        if valid:
            employee_id = value
            break
        print(f"校验失败：员工编号{reason}。")
    if employee_id is None:
        return None
    while True:
        valid, department = normalize_department(input("维护人部门："))
        if valid:
            return {"employee_id": employee_id, "department": department}
        print(f"校验失败：部门必须是 {' / '.join(VALID_DEPARTMENTS)}。")


def prompt_contact(existing_ids):
    """交互采集联系人。"""

    while True:
        valid, contact_id, reason = normalize_identifier(
            input("联系人编号（C 开头）："),
            "C",
        )
        if not valid:
            print(f"校验失败：联系人编号{reason}。")
            continue
        if contact_id in existing_ids:
            print("校验失败：联系人编号已存在。")
            continue
        break
    while True:
        name = " ".join(input("姓名：").split())
        if name:
            break
        print("校验失败：姓名不能为空。")
    while True:
        valid, department = normalize_department(input("部门："))
        if valid:
            break
        print("校验失败：部门不在白名单。")
    while True:
        role = " ".join(input("岗位：").split())
        if role:
            break
        print("校验失败：岗位不能为空。")
    while True:
        valid, email, reason = normalize_email(input("模拟邮箱："))
        if valid:
            break
        print(f"校验失败：邮箱{reason}。")
    skills = input("技能（逗号分隔）：").split(",")
    return create_contact(
        contact_id,
        name,
        department,
        role,
        email,
        skills=skills,
    )


def run_cli(data_file=DATA_FILE):
    """运行联系人目录，返回进程状态码。"""

    print("=" * 76)
    print(f"{PRODUCT_NAME} {VERSION}｜企业联系人目录")
    print("=" * 76)
    print("仅使用模拟联系人和 .test 邮箱，不得录入真实个人信息。")
    data, status, error = load_data(data_file)
    if status == "rejected":
        print(f"数据拒绝：{error}。")
        return 3
    if status == "loaded":
        print(
            f"恢复成功：revision={data['revision']}，"
            f"联系人 {len(data['contacts'])} 名。"
        )
    if data["owner"] is None:
        owner = prompt_owner()
        if owner is None:
            print("安全退出：维护人员工编号连续三次无效。")
            return 2
        data["owner"] = owner
        revision = persist_change(data, data_file)
        print(
            f"维护人已保存：{owner['employee_id']}｜"
            f"{owner['department']}｜revision={revision}。"
        )
    else:
        owner = data["owner"]
        print(
            f"维护人已恢复：{owner['employee_id']}｜"
            f"{owner['department']}。"
        )

    while True:
        print("\n1=新增 2=查看 3=搜索 4=更新岗位 5=删除 6=统计 7=摘要 0=退出")
        choice = input("请选择：").strip()
        if choice == "1":
            contact = prompt_contact(
                {item["contact_id"] for item in data["contacts"]}
            )
            changed, message = add_contact(data, contact)
            if changed:
                revision = persist_change(data, data_file)
                print(f"{message}并保存｜revision={revision}。")
            else:
                print(message)
        elif choice == "2":
            contacts = ordered_contacts(data["contacts"])
            if not contacts:
                print("当前没有联系人。")
                continue
            for position, contact in enumerate(contacts, start=1):
                print(
                    f"{position}. {contact['contact_id']}｜{contact['name']}｜"
                    f"{contact['department']}｜{contact['role']}｜"
                    f"{contact['email']}｜技能：{', '.join(contact['skills']) or '无'}"
                )
        elif choice == "3":
            keyword = input("搜索关键词：")
            matched = search_contacts(data["contacts"], keyword)
            print(f"搜索结果：{len(matched)} 名。")
            for contact in matched:
                print(
                    f"{contact['contact_id']}｜{contact['name']}｜"
                    f"{contact['department']}｜{contact['role']}"
                )
        elif choice == "4":
            _, contact_id, _ = normalize_identifier(
                input("要更新的联系人编号："),
                "C",
            )
            role = " ".join(input("新岗位：").split())
            changed, message = update_contact(
                data,
                contact_id,
                role=role,
            )
            if changed:
                revision = persist_change(data, data_file)
                print(f"{message}并保存｜revision={revision}。")
            else:
                print(message)
        elif choice == "5":
            _, contact_id, _ = normalize_identifier(
                input("要删除的联系人编号："),
                "C",
            )
            changed, message = delete_contact(data, contact_id)
            if changed:
                revision = persist_change(data, data_file)
                print(f"{message}并保存｜revision={revision}。")
            else:
                print(message)
        elif choice == "6":
            stats = directory_statistics(data["contacts"])
            print(
                f"统计：总数={stats['total']}｜"
                f"部门={stats['departments']}｜技能={stats['skills']}"
            )
        elif choice == "7":
            print(
                f"摘要：schema={data['schema_version']}｜"
                f"revision={data['revision']}｜"
                f"contacts={len(data['contacts'])}｜file={data_file}"
            )
        elif choice == "0":
            print(
                f"安全退出：已持久化 {len(data['contacts'])} 名联系人｜"
                f"revision={data['revision']}。"
            )
            return 0
        else:
            print("菜单错误：仅支持 0-7。")


if __name__ == "__main__":
    raise SystemExit(run_cli())
