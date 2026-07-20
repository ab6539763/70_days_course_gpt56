"""Day 13 文档语料回归单测。"""

import json
import sys
import tempfile
from pathlib import Path


SOLUTION = Path(__file__).parents[1] / "solution"
FIXTURES = Path(__file__).parents[1] / "fixtures" / "corpus"
sys.path.insert(0, str(SOLUTION))

from nexus.persistence.storage import load_state, persist_change
from nexus.platform.state import PlatformState


state = PlatformState.empty()
assert state.ingest_corpus(str(FIXTURES), "报销,制度")[0]

v3 = {
    "schema_version": 3,
    "revision": 3,
    "owner": {"employee_id": "E13", "department": "技术部"},
    "contacts": [],
    "messages": [],
    "model_config": {
        "provider": "qwen",
        "model_id": "qwen-plus",
        "temperature": 0.7,
        "max_tokens": 1024,
    },
}
with tempfile.TemporaryDirectory(prefix="nexus-day13-doc-") as temporary:
    path = Path(temporary) / "state.json"
    path.write_text(json.dumps(v3, ensure_ascii=False), encoding="utf-8")
    restored, status, error = load_state(str(path))
    assert status == "migrated" and error == ""
    assert persist_change(restored, str(path)) == 4

print("Day 13 语料回归通过。")
