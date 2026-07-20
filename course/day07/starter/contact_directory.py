"""Day 7 阶段项目起步版：企业联系人目录。"""

import json


def create_contact(contact_id, name, department, role, email):
    """返回一条具名字典联系人。"""

    return {
        "contact_id": contact_id.strip().upper(),
        "name": " ".join(name.split()),
        "department": " ".join(department.split()),
        "role": " ".join(role.split()),
        "email": email.strip().lower(),
        "skills": [],
    }


data = {
    "schema_version": 1,
    "revision": 1,
    "owner": {"employee_id": "E70007", "department": "客户服务部"},
    "contacts": [],
}
data["contacts"].append(
    create_contact(
        "c1",
        "李梅",
        "技术部",
        "AI 应用工程师",
        "limei@example.test",
    )
)

with open("nexus_contacts.json", "w", encoding="utf-8") as file:
    json.dump(data, file, ensure_ascii=False, indent=2, sort_keys=True)
    file.write("\n")

print("Day 7 起步版已保存一名模拟联系人。")
