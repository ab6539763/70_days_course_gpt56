"""Day 12 文档与语料回归单测（Day 11 能力保留）。"""

import json
import sys
import tempfile
from pathlib import Path


SOLUTION = Path(__file__).parents[1] / "solution"
FIXTURES = Path(__file__).parents[1] / "fixtures" / "corpus"
sys.path.insert(0, str(SOLUTION))

from nexus.platform.state import PlatformState
from nexus.persistence.storage import load_state, persist_change


state = PlatformState.empty()
changed, message = state.ingest_corpus(str(FIXTURES), "报销,制度")
assert changed and "已导入 4 份语料" in message

v3 = {
    "schema_version": 3,
    "revision": 3,
    "owner": {"employee_id": "E12", "department": "技术部"},
    "contacts": [],
    "messages": [],
    "model_config": {
        "provider": "qwen",
        "model_id": "qwen-plus",
        "temperature": 0.7,
        "max_tokens": 1024,
    },
}
with tempfile.TemporaryDirectory(prefix="nexus-day12-doc-") as temporary:
    path = Path(temporary) / "state.json"
    path.write_text(json.dumps(v3, ensure_ascii=False), encoding="utf-8")
    restored, status, error = load_state(str(path))
    assert status == "migrated" and error == ""
    assert persist_change(restored, str(path)) == 4
    saved = json.loads(path.read_text(encoding="utf-8"))
    assert saved["schema_version"] == 4

print("Day 12 语料回归通过：Day 11 导入与 v3→v4 迁移仍正确。")
