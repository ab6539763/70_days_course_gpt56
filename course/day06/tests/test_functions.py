"""Day 6 函数级测试：参数、返回值、作用域与业务函数。"""

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import json
import tempfile


SOLUTION = Path(__file__).parents[1] / "solution" / "functional_task_board.py"
spec = spec_from_file_location("day06_board", SOLUTION)
board = module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(board)

# 工厂每次返回独立可变对象。
first_default = board.create_default_data()
second_default = board.create_default_data()
first_default["tasks"].append({"task_id": "T-X"})
assert second_default["tasks"] == []

assert board.normalize_identifier(" e 60006 ", "E") == (
    True,
    "E60006",
    "",
)
assert board.normalize_identifier("", "T")[0] is False
assert "T 开头" in board.normalize_identifier("A1", "T")[2]
assert board.normalize_department("客服部") == (True, "客户服务部")
assert board.normalize_department("未知部")[0] is False

# *args 合并任意标签组。
assert board.merge_tags(
    [" RAG", "agent"],
    ["rag", "", " TEST "],
) == ["agent", "rag", "test"]

task = board.create_task("T1", "  设计   Agent  ", tags=["Agent", "agent"])
assert task == {
    "task_id": "T1",
    "title": "设计 Agent",
    "priority": 3,
    "is_done": False,
    "tags": ["agent"],
}

# **kwargs 只更新允许字段，未知字段不进入任务。
assert board.update_task(task, priority=1, owner="E1") is True
assert task["priority"] == 1
assert "owner" not in task
assert board.update_task(task, priority=1) is False

valid, error = board.validate_data(board.create_default_data())
assert valid is True and error == ""
invalid = board.create_default_data()
invalid["schema_version"] = 99
assert board.validate_data(invalid) == (False, "不支持的 schema_version")

with tempfile.TemporaryDirectory(prefix="nexus-day06-functions-") as temporary:
    data_file = Path(temporary) / "state.json"
    data, status, error = board.load_data(str(data_file))
    assert status == "new" and error == ""
    data["employee"] = {"employee_id": "E1", "department": "销售部"}
    assert board.persist_change(data, str(data_file)) == 1
    assert data_file.is_file()

    restored, status, error = board.load_data(str(data_file))
    assert status == "loaded" and error == ""
    assert restored == data

    data_file.write_text("", encoding="utf-8")
    empty, status, _ = board.load_data(str(data_file))
    assert status == "empty" and empty["revision"] == 0

    rejected_document = board.create_default_data()
    rejected_document["schema_version"] = 2
    data_file.write_text(json.dumps(rejected_document), encoding="utf-8")
    _, status, error = board.load_data(str(data_file))
    assert status == "rejected"
    assert "schema_version" in error

data = board.create_default_data()
t2 = board.create_task("T2", "第二任务", priority=2, tags=["rag"])
t1 = board.create_task("T1", "第一任务", priority=1, tags=["agent"])
assert board.add_task(data, t2)[0] is True
assert board.add_task(data, t1)[0] is True
assert board.add_task(data, t1)[0] is False

ordered = board.ordered_tasks(data["tasks"])
assert [item["task_id"] for item in ordered] == ["T1", "T2"]
assert [item["task_id"] for item in board.ordered_tasks(data["tasks"], limit=1)] == ["T1"]
assert [item["task_id"] for item in data["tasks"]] == ["T2", "T1"], "查询不得修改主列表"

assert board.complete_task(data, "T2") == (True, "已完成 T2")
assert board.complete_task(data, "T2")[0] is False
assert board.complete_task(data, "T9")[0] is False

stats = board.task_statistics(data["tasks"])
assert stats == {
    "total": 2,
    "active": 1,
    "done": 1,
    "high_priority_active": 1,
    "tags": ["agent", "rag"],
}
assert board.count_tasks_recursive(data["tasks"]) == 2
assert board.count_tasks_recursive([]) == 0

assert board.delete_task(data, "T9")[0] is False
assert board.delete_task(data, "T1")[0] is True
assert board.cleanup_completed(data) == 1
assert data["tasks"] == []

assert board.format_line("E1", "销售部") == "E1｜销售部"
assert board.format_line("A", "B", "C", separator="/") == "A/B/C"

print("Day 6 函数单测通过：参数、返回值、CRUD、持久化和递归均正确。")
