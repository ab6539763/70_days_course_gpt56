"""Day 9 继承、多态与魔术方法单测。"""

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import json
import tempfile


SOLUTION = Path(__file__).parents[1] / "solution" / "model_platform.py"
spec = spec_from_file_location("day09_model", SOLUTION)
platform = module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(platform)

openai_model = platform.OpenAIModel("gpt-4o-mini", 0.2, 512)
qwen_model = platform.QwenModel("qwen-plus", 0.5, 256)

assert isinstance(openai_model, platform.BaseModel)
assert isinstance(qwen_model, platform.BaseModel)
assert openai_model.PROVIDER == "openai"
assert qwen_model.PROVIDER == "qwen"
assert "openai/gpt-4o-mini" in str(openai_model)
assert "QwenModel" in repr(qwen_model)

messages = [{"role": "user", "content": "查询制度"}]
openai_payload = openai_model.format_request(messages)
qwen_payload = qwen_model.format_request(messages)
assert "messages" in openai_payload
assert "input" in qwen_payload and "parameters" in qwen_payload
assert openai_payload["temperature"] == 0.2
assert qwen_payload["parameters"]["temperature"] == 0.5

openai_reply = openai_model(messages)
qwen_reply = qwen_model(messages)
assert openai_reply.startswith("[openai]")
assert qwen_reply.startswith("[qwen]")

restored_openai = platform.create_model(openai_model.to_dict())
assert type(restored_openai) is platform.OpenAIModel
assert restored_openai.model_id == "gpt-4o-mini"

try:
    openai_model.temperature = 3
    raise AssertionError("temperature 应拒绝超范围值")
except ValueError as error:
    assert "0 到 2" in str(error)

openai_model.temperature = 1.5
assert openai_model.temperature == 1.5

parsed = qwen_model.parse_response("  你好  ")
assert parsed["provider"] == "qwen"
assert parsed["finish_reason"] == "stop"

contact = platform.Contact(
    "c2", "王强", "产品部", "产品经理", "wang@example.test", ["prompt"]
)
state = platform.PlatformState.empty()
assert state.add_contact(contact)[0]
assert state.add_message("user", "制度在哪里")[0]
changed, message, assistant_text = state.simulate_chat("报销流程是什么")
assert changed and "assistant" in message
assert assistant_text.startswith("[qwen]")
assert state.statistics()["model"].startswith("qwen/qwen-plus")

switched, switch_message = state.update_model_config(
    "openai", "gpt-4o-mini", 0.1, 800
)
assert switched and "openai/gpt-4o-mini" in switch_message
assert state.active_model().PROVIDER == "openai"

v2 = {
    "schema_version": 2,
    "revision": 6,
    "owner": {"employee_id": "E9", "department": "技术部"},
    "contacts": [contact.to_dict()],
    "messages": [{"role": "user", "content": "旧消息"}],
}
migrated, needs_migration, error = platform.PlatformState.from_dict(v2)
assert error == "" and needs_migration is True
assert migrated.to_dict()["schema_version"] == 3
assert migrated.model_config["provider"] == "qwen"

with tempfile.TemporaryDirectory(prefix="nexus-day09-model-") as temporary:
    path = Path(temporary) / "state.json"
    path.write_text(json.dumps(v2, ensure_ascii=False), encoding="utf-8")
    restored, status, error = platform.load_state(str(path))
    assert status == "migrated" and error == ""
    assert platform.persist_change(restored, str(path)) == 7
    loaded, status, _ = platform.load_state(str(path))
    assert status == "loaded"
    saved = json.loads(path.read_text(encoding="utf-8"))
    assert saved["schema_version"] == 3
    assert "model_config" in saved

rejected, migrated, error = platform.PlatformState.from_dict({"schema_version": 99})
assert rejected is None and migrated is False
assert "schema_version" in error

try:
    platform.create_model({"provider": "unknown", "model_id": "x"})
    raise AssertionError("未知供应商应拒绝")
except ValueError as error:
    assert "不支持" in str(error)

print("Day 9 模型单测通过：继承、多态、property、__call__ 与 v2→v3 迁移均正确。")
