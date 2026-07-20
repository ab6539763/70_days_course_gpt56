"""Day 10 模块化包与异常单测。"""

import json
import sys
import tempfile
from pathlib import Path


SOLUTION = Path(__file__).parents[1] / "solution"
sys.path.insert(0, str(SOLUTION))

from nexus.domain.contact import Contact
from nexus.domain.message import ChatMessage
from nexus.exceptions import (
    InvalidMessageError,
    ModelConfigError,
    PersistenceError,
    SchemaValidationError,
)
from nexus.models.base import BaseModel
from nexus.models.factory import create_model
from nexus.models.openai_model import OpenAIModel
from nexus.models.qwen_model import QwenModel
from nexus.persistence.storage import load_state, persist_change
from nexus.platform.state import PlatformState


openai_model = OpenAIModel("gpt-4o-mini", 0.2, 512)
qwen_model = QwenModel("qwen-plus", 0.5, 256)
assert isinstance(openai_model, BaseModel)
assert isinstance(create_model({"provider": "openai", "model_id": "gpt-4o-mini"}), OpenAIModel)
assert openai_model.format_request([{"role": "user", "content": "hi"}])["messages"]
assert qwen_model.format_request([{"role": "user", "content": "hi"}])["input"]

try:
    openai_model.temperature = 3
    raise AssertionError("temperature 应拒绝超范围")
except ModelConfigError as error:
    assert error.code == "MODEL_CONFIG"

try:
    openai_model.max_tokens = 0
    raise AssertionError("max_tokens 应拒绝非正数")
except ModelConfigError:
    pass

contact = Contact("c10", "周航", "技术部", "架构师", "zhou@example.test", ["pkg"])
state = PlatformState.empty()
assert state.add_contact(contact)[0]
state.add_message("user", "包结构测试")
changed, message, reply = state.simulate_chat("异常体系")
assert changed and reply.startswith("[qwen]")

try:
    state.add_message("tool", "bad")
    raise AssertionError("非法角色应抛 InvalidMessageError")
except InvalidMessageError as error:
    assert error.code == "INVALID_MESSAGE"

try:
    PlatformState.from_dict({"schema_version": 99, "revision": 1, "owner": {}, "contacts": []})
    raise AssertionError("非法 schema 应抛 SchemaValidationError")
except SchemaValidationError as error:
    assert error.code == "SCHEMA_VALIDATION"

v2 = {
    "schema_version": 2,
    "revision": 6,
    "owner": {"employee_id": "E10", "department": "技术部"},
    "contacts": [contact.to_dict()],
    "messages": [{"role": "user", "content": "旧消息"}],
}
migrated, needs_migration = PlatformState.from_dict(v2)
assert needs_migration is True
assert migrated.to_dict()["schema_version"] == 3

with tempfile.TemporaryDirectory(prefix="nexus-day10-model-") as temporary:
    path = Path(temporary) / "state.json"
    path.write_text(json.dumps(v2, ensure_ascii=False), encoding="utf-8")
    restored, status, error = load_state(str(path))
    assert status == "migrated" and error == ""
    assert persist_change(restored, str(path)) == 7
    loaded, status, _ = load_state(str(path))
    assert status == "loaded"

    broken = Path(temporary) / "broken.json"
    broken.write_text("{bad json", encoding="utf-8")
    try:
        load_state(str(broken))
        raise AssertionError("坏 JSON 应抛 PersistenceError")
    except PersistenceError as error:
        assert error.code == "PERSISTENCE"

    rejected_path = Path(temporary) / "reject.json"
    rejected_path.write_text(
        json.dumps({"schema_version": 99, "revision": 1, "owner": {}, "contacts": []}),
        encoding="utf-8",
    )
    rejected, status, error = load_state(str(rejected_path))
    assert rejected is None and status == "rejected"

try:
    create_model({"provider": "unknown", "model_id": "x"})
    raise AssertionError("未知供应商应抛 ModelConfigError")
except ModelConfigError:
    pass

print("Day 10 模块单测通过：包导入、自定义异常、持久化与迁移均正确。")
