"""Day 11 语料加载、pathlib 与正则单测。"""

import json
import sys
import tempfile
from pathlib import Path


SOLUTION = Path(__file__).parents[1] / "solution"
FIXTURES = Path(__file__).parents[1] / "fixtures" / "corpus"
sys.path.insert(0, str(SOLUTION))

from nexus.documents.keywords import count_keyword, count_keywords, normalize_keywords
from nexus.documents.loader import discover_documents, load_document, load_json_as_text
from nexus.documents.corpus import CorpusService, empty_document_index
from nexus.exceptions import DocumentLoadError, PersistenceError, SchemaValidationError
from nexus.persistence.storage import load_state, persist_change
from nexus.platform.state import PlatformState


assert normalize_keywords("报销, 制度 ,报销") == ["报销", "制度"]
text = load_document(FIXTURES / "policy.txt")
assert "报销" in text
assert count_keyword(text, "报销") >= 2
assert load_json_as_text(FIXTURES / "meta.json").count("制度") >= 1
assert len(discover_documents(FIXTURES)) == 4

state = PlatformState.empty()
changed, message = state.ingest_corpus(str(FIXTURES), "报销,制度,Agent")
assert changed and "已导入 4 份语料" in message
assert len(state.document_index["documents"]) == 4
assert state.document_index["keyword_totals"]["报销"] >= 3
matched = state.search_corpus("制度")
assert matched and matched[0][1] > 0

v3 = {
    "schema_version": 3,
    "revision": 8,
    "owner": {"employee_id": "E11", "department": "技术部"},
    "contacts": [],
    "messages": [],
    "model_config": {
        "provider": "qwen",
        "model_id": "qwen-plus",
        "temperature": 0.7,
        "max_tokens": 1024,
    },
}
migrated, needs_migration = PlatformState.from_dict(v3)
assert needs_migration is True
assert migrated.to_dict()["schema_version"] == 4
assert "document_index" in migrated.to_dict()

with tempfile.TemporaryDirectory(prefix="nexus-day11-model-") as temporary:
    path = Path(temporary) / "state.json"
    path.write_text(json.dumps(v3, ensure_ascii=False), encoding="utf-8")
    restored, status, error = load_state(str(path))
    assert status == "migrated" and error == ""
    assert persist_change(restored, str(path)) == 9
    loaded, status, _ = load_state(str(path))
    assert status == "loaded"
    saved = json.loads(path.read_text(encoding="utf-8"))
    assert saved["schema_version"] == 4

    bad_encoding = Path(temporary) / "bad.txt"
    bad_encoding.write_bytes(b"\xff\xfe")
    try:
        load_document(bad_encoding)
        raise AssertionError("应拒绝非 UTF-8 文件")
    except DocumentLoadError as error:
        assert error.code == "DOCUMENT_LOAD"

try:
    PlatformState.from_dict({"schema_version": 99, "revision": 1, "owner": {}, "contacts": []})
    raise AssertionError("非法 schema 应拒绝")
except SchemaValidationError:
    pass

try:
    CorpusService(empty_document_index()).ingest_directory(FIXTURES, "")
    raise AssertionError("空关键词应拒绝")
except DocumentLoadError:
    pass

print("Day 11 模块单测通过：pathlib、UTF-8、re 统计与 v3→v4 迁移均正确。")
