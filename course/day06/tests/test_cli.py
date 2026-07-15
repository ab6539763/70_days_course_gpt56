"""Day 6 CLI 端到端：函数编排、双进程恢复与退出码。"""

from pathlib import Path
import json
import subprocess
import sys
import tempfile


SOLUTION = Path(__file__).parents[1] / "solution" / "functional_task_board.py"


def run_cli(directory: Path, lines: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SOLUTION)],
        cwd=directory,
        input="\n".join(lines) + "\n",
        text=True,
        capture_output=True,
        check=False,
    )


with tempfile.TemporaryDirectory(prefix="nexus-day06-cli-") as temporary:
    working = Path(temporary)
    first = run_cli(
        working,
        [
            "E60006", "客服部",
            "1", "T2", "重构 JSON 仓储", "2", "json, refactor",
            "1", "T1", "设计函数接口", "1", "function, api",
            "2",
            "3", "T2",
            "5",
            "7",
            "0",
        ],
    )
    assert first.returncode == 0, first.stderr
    assert "身份已保存：E60006｜客户服务部｜revision=1" in first.stdout
    assert "已新增 T2并保存｜revision=2" in first.stdout
    assert "已新增 T1并保存｜revision=3" in first.stdout
    assert first.stdout.index("P1 T1") < first.stdout.index("P2 T2")
    assert "首页预览：['T1', 'T2']" in first.stdout
    assert "已完成 T2并保存｜revision=4" in first.stdout
    assert "总数=2｜进行中=1｜已完成=1｜高优先级=1" in first.stdout
    assert "递归校验总数：2" in first.stdout
    assert "摘要：schema=1｜revision=4｜tasks=2" in first.stdout

    second = run_cli(
        working,
        [
            "4", "T1",
            "6",
            "1", "T2", "重建函数测试", "3", "test",
            "5",
            "0",
        ],
    )
    assert second.returncode == 0, second.stderr
    assert "恢复成功：revision=4，任务 2 条" in second.stdout
    assert "身份已恢复：E60006｜客户服务部" in second.stdout
    assert "员工编号（" not in second.stdout
    assert "已删除 T1｜设计函数接口并保存｜revision=5" in second.stdout
    assert "清理：移除 1 条｜revision=6" in second.stdout
    assert "已新增 T2并保存｜revision=7" in second.stdout
    assert "总数=1｜进行中=1｜已完成=0｜高优先级=0" in second.stdout
    final_data = json.loads(
        (working / "nexus_tasks.json").read_text(encoding="utf-8")
    )
    assert final_data["revision"] == 7
    assert final_data["tasks"][0]["title"] == "重建函数测试"

with tempfile.TemporaryDirectory(prefix="nexus-day06-lock-") as temporary:
    locked = run_cli(Path(temporary), ["", "A1", "E"])
    assert locked.returncode == 2
    assert "连续三次无效" in locked.stdout
    assert not (Path(temporary) / "nexus_tasks.json").exists()

with tempfile.TemporaryDirectory(prefix="nexus-day06-schema-") as temporary:
    working = Path(temporary)
    path = working / "nexus_tasks.json"
    original = '{"schema_version": 8, "revision": 0, "employee": null, "tasks": []}\n'
    path.write_text(original, encoding="utf-8")
    rejected = run_cli(working, [])
    assert rejected.returncode == 3
    assert "不支持的 schema_version" in rejected.stdout
    assert path.read_text(encoding="utf-8") == original

print("Day 6 CLI 验收通过：函数编排、双进程、锁定和版本拒绝均正确。")
