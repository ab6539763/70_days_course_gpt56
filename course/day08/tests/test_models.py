"""Day 8 面向对象模型单测。"""

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import json
import tempfile


SOLUTION = Path(__file__).parents[1] / "solution" / "oop_platform.py"
spec = spec_from_file_location("day08_oop", SOLUTION)
platform = module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(platform)

assert platform.ChatMessage.is_valid_role(" USER ")
assert not platform.ChatMessage.is_valid_role("tool")
message = platform.ChatMessage(" USER ", "  查询   制度 ")
assert message.role == "user"
assert message.content == "查询 制度"
assert message.preview(2) == "查询"
assert platform.ChatMessage.from_dict(message.to_dict()).to_dict() == message.to_dict()
assert platform.ChatMessage.system("  安全   回答 ").role == "system"

contact = platform.Contact(
    " c 1 ", " 李梅 ", "技术部", " AI   工程师 ",
    "LI@example.test", ["RAG", "rag", "python"]
)
assert contact.contact_id == "C1"
assert contact.name == "李梅"
assert contact.email == "li@example.test"
assert contact.skills == ["python", "rag"]
assert contact.matches("PYTHON")
assert contact.update_role("高级 AI 工程师")
assert not contact.update_role("高级 AI 工程师")
assert platform.Contact.from_dict(contact.to_dict()).to_dict() == contact.to_dict()
assert platform.Contact.is_valid_email("a@example.test")
assert not platform.Contact.is_valid_email("bad")

state = platform.PlatformState.empty()
assert state.add_contact(contact)[0]
assert not state.add_contact(contact)[0]
assert state.add_message("user", " 你好 ")[0]
assert not state.add_message("tool", "错误")[0]
assert not state.add_message("assistant", "   ")[0]
assert state.statistics() == {
    "contacts": 1,
    "messages": 1,
    "roles": {"system": 0, "user": 1, "assistant": 0},
}
assert state.search_contacts("高级")[0] is contact

v1 = {
    "schema_version": 1,
    "revision": 4,
    "owner": {"employee_id": "E7", "department": "技术部"},
    "contacts": [contact.to_dict()],
}
migrated, needs_migration, error = platform.PlatformState.from_dict(v1)
assert error == "" and needs_migration is True
assert migrated.to_dict()["schema_version"] == 2
assert migrated.messages == []

with tempfile.TemporaryDirectory(prefix="nexus-day08-model-") as temporary:
    path = Path(temporary) / "state.json"
    path.write_text(json.dumps(v1, ensure_ascii=False), encoding="utf-8")
    restored, status, error = platform.load_state(str(path))
    assert status == "migrated" and error == ""
    assert platform.persist_change(restored, str(path)) == 5
    loaded, status, _ = platform.load_state(str(path))
    assert status == "loaded"
    assert loaded.to_dict() == restored.to_dict()

rejected, migrated, error = platform.PlatformState.from_dict(
    {"schema_version": 99}
)
assert rejected is None and migrated is False
assert "schema_version" in error

print("Day 8 模型单测通过：实例、类方法、静态方法和 Schema 迁移均正确。")
