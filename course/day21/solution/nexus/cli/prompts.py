"""CLI 交互输入与规范化。"""

from nexus.constants import VALID_DEPARTMENTS
from nexus.domain.contact import Contact
from nexus.exceptions import ModelConfigError
from nexus.models.factory import create_model


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
        return state.update_model_config(
            provider,
            model_id,
            temperature,
            max_tokens,
        )
    except ModelConfigError as error:
        return False, error.message
