"""Day 7 联系人目录函数单测。"""

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import tempfile


SOLUTION = Path(__file__).parents[1] / "solution" / "contact_directory.py"
spec = spec_from_file_location("day07_directory", SOLUTION)
directory = module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(directory)

one = directory.create_default_data()
two = directory.create_default_data()
one["contacts"].append({"contact_id": "C-X"})
assert two["contacts"] == []

assert directory.normalize_identifier(" c 1 ", "C") == (True, "C1", "")
assert directory.normalize_identifier("", "C")[0] is False
assert directory.normalize_department("研发部") == (True, "技术部")
assert directory.normalize_department("未知部")[0] is False
assert directory.normalize_email(" Demo@Example.Test ") == (
    True,
    "demo@example.test",
    "",
)
assert directory.normalize_email("bad-email")[0] is False
assert directory.normalize_email("@example.test")[0] is False
assert directory.normalize_skills(
    [" RAG", "python"],
    ["rag", "Agent"],
) == ["agent", "python", "rag"]

c2 = directory.create_contact(
    "C2", " 李梅 ", "技术部", " AI   工程师 ",
    "limei@example.test", ["python", "RAG"]
)
c1 = directory.create_contact(
    "C1", "王芳", "销售部", "销售经理",
    "wangfang@example.test", ["sales"]
)
assert c2["name"] == "李梅"
assert c2["role"] == "AI 工程师"
assert c2["skills"] == ["python", "rag"]

data = directory.create_default_data()
assert directory.add_contact(data, c2)[0] is True
assert directory.add_contact(data, c1)[0] is True
assert directory.add_contact(data, c1)[0] is False
duplicate_email = directory.create_contact(
    "C3", "重复邮箱", "产品部", "产品经理",
    "limei@example.test"
)
assert directory.add_contact(data, duplicate_email)[0] is False

assert directory.update_contact(data, "C2", role="高级 AI 工程师")[0] is True
assert directory.update_contact(data, "C2", role="高级 AI 工程师")[0] is False
assert directory.update_contact(
    data, "C2", email="wangfang@example.test"
)[0] is False
assert directory.update_contact(data, "C9", role="未知")[0] is False

ordered = directory.ordered_contacts(data["contacts"])
assert [item["contact_id"] for item in ordered] == ["C1", "C2"]
assert [item["contact_id"] for item in data["contacts"]] == ["C2", "C1"]

assert [item["contact_id"] for item in directory.search_contacts(
    data["contacts"], "PYTHON"
)] == ["C2"]
assert [item["contact_id"] for item in directory.search_contacts(
    data["contacts"], "销售"
)] == ["C1"]
assert directory.search_contacts(data["contacts"], "") == []

stats = directory.directory_statistics(data["contacts"])
assert stats == {
    "total": 2,
    "departments": {"技术部": 1, "销售部": 1},
    "skills": ["python", "rag", "sales"],
}

with tempfile.TemporaryDirectory(prefix="nexus-day07-functions-") as temporary:
    path = Path(temporary) / "contacts.json"
    data["owner"] = {"employee_id": "E7", "department": "技术部"}
    assert directory.persist_change(data, str(path)) == 1
    restored, status, error = directory.load_data(str(path))
    assert status == "loaded" and error == ""
    assert restored == data

assert directory.delete_contact(data, "C9")[0] is False
assert directory.delete_contact(data, "C1")[0] is True
assert len(data["contacts"]) == 1

print("Day 7 函数单测通过：唯一性、搜索、统计、更新和持久化均正确。")
