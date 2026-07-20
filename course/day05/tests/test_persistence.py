"""Day 5 端到端测试：首次保存、跨进程恢复、变更落盘与版本拒绝。"""

from pathlib import Path
import json
import subprocess
import sys
import tempfile


SOLUTION = Path(__file__).parents[1] / "solution" / "persistent_task_board.py"


def run_board(
    working_directory: Path,
    lines: list[str],
) -> subprocess.CompletedProcess[str]:
    """在指定数据目录启动真实 CLI。"""

    return subprocess.run(
        [sys.executable, str(SOLUTION)],
        cwd=working_directory,
        input="\n".join(lines) + "\n",
        text=True,
        capture_output=True,
        check=False,
    )


with tempfile.TemporaryDirectory(prefix="nexus-day05-data-") as temporary:
    working = Path(temporary)
    data_file = working / "nexus_tasks.json"

    first = run_board(
        working,
        [
            "E50005",
            "客服部",
            "1", "T2", "评审 RAG 数据集", "2", "rag, urgent, RAG",
            "1", "T1", "设计 Agent 状态模型", "1", "agent, graph",
            "2",
            "3", "T2",
            "7",
            "0",
        ],
    )
    assert first.returncode == 0, first.stderr
    assert "身份已保存：E50005｜客户服务部" in first.stdout
    assert "新增并保存：T2" in first.stdout
    assert "新增并保存：T1" in first.stdout
    assert first.stdout.index("P1 T1") < first.stdout.index("P2 T2")
    assert "首页预览：['T1', 'T2']" in first.stdout
    assert "完成并保存：T2｜revision=4" in first.stdout
    assert "schema_version：1" in first.stdout
    assert "revision：4" in first.stdout
    assert "已持久化 2 条任务｜revision=4" in first.stdout
    assert data_file.is_file()

    raw = data_file.read_text(encoding="utf-8")
    assert "客户服务部" in raw, "JSON 应直接保存可读中文"
    assert "\\u5ba2" not in raw, "JSON 不应把中文转成 ASCII 转义"
    assert raw.endswith("\n")

    saved = json.loads(raw)
    assert saved["schema_version"] == 1
    assert saved["revision"] == 4
    assert saved["employee"] == {
        "employee_id": "E50005",
        "department": "客户服务部",
    }
    assert len(saved["tasks"]) == 2
    task_by_id = {task["task_id"]: task for task in saved["tasks"]}
    assert task_by_id["T2"]["is_done"] is True
    assert task_by_id["T2"]["tags"] == ["rag", "urgent"]
    assert task_by_id["T1"]["priority"] == 1

    # 第二个进程不再询问身份，直接恢复并继续 CRUD。
    second = run_board(
        working,
        [
            "5",
            "2",
            "4", "T1",
            "6",
            "7",
            "1", "T2", "重新评审 RAG 数据集", "3", "rag",
            "0",
        ],
    )
    assert second.returncode == 0, second.stderr
    assert "恢复成功：revision=4，任务 2 条" in second.stdout
    assert "身份已恢复：E50005｜客户服务部" in second.stdout
    assert "员工编号（" not in second.stdout
    assert "总数：2" in second.stdout
    assert "删除并保存：T1｜设计 Agent 状态模型｜revision=5" in second.stdout
    assert "清理完成：移除 1 条，revision=6" in second.stdout
    assert "task_count：0" in second.stdout
    assert "新增并保存：T2｜P3｜重新评审 RAG 数据集｜revision=7" in second.stdout
    assert "已持久化 1 条任务｜revision=7" in second.stdout

    final_data = json.loads(data_file.read_text(encoding="utf-8"))
    assert final_data["revision"] == 7
    assert final_data["tasks"] == [
        {
            "is_done": False,
            "priority": 3,
            "tags": ["rag"],
            "task_id": "T2",
            "title": "重新评审 RAG 数据集",
        }
    ]

# 未知 schema 必须拒绝且不能覆盖原文件。
with tempfile.TemporaryDirectory(prefix="nexus-day05-version-") as temporary:
    working = Path(temporary)
    data_file = working / "nexus_tasks.json"
    original = '{"schema_version": 99, "revision": 1, "employee": null, "tasks": []}\n'
    data_file.write_text(original, encoding="utf-8")
    rejected = run_board(working, [])
    assert rejected.returncode == 3
    assert "不支持的 schema_version" in rejected.stdout
    assert data_file.read_text(encoding="utf-8") == original

# 空文件视为首次初始化，覆盖部署预创建空卷的场景。
with tempfile.TemporaryDirectory(prefix="nexus-day05-empty-") as temporary:
    working = Path(temporary)
    (working / "nexus_tasks.json").touch()
    initialized = run_board(working, ["E1", "销售部", "0"])
    assert initialized.returncode == 0, initialized.stderr
    assert "身份已保存：E1｜销售部" in initialized.stdout
    initialized_data = json.loads(
        (working / "nexus_tasks.json").read_text(encoding="utf-8")
    )
    assert initialized_data["revision"] == 1

print("Day 5 持久化验收通过：首次、恢复、CRUD、版本拒绝和空文件均正确。")
