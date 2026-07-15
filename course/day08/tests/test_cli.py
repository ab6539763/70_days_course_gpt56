"""Day 8 CLI 双进程与 v1→v2 迁移测试。"""

from pathlib import Path
import json
import subprocess
import sys
import tempfile


SOLUTION = Path(__file__).parents[1] / "solution" / "oop_platform.py"


def run_cli(directory, lines):
    return subprocess.run(
        [sys.executable, str(SOLUTION)],
        cwd=directory,
        input="\n".join(lines) + "\n",
        text=True,
        capture_output=True,
        check=False,
    )


with tempfile.TemporaryDirectory(prefix="nexus-day08-cli-") as temporary:
    working = Path(temporary)
    first = run_cli(
        working,
        [
            "E80008", "研发部",
            "1", "C1", "李梅", "技术部", "AI 工程师",
            "li@example.test", "python,rag",
            "4", "tool", "无效",
            "4", "system", "  你是   企业助手 ",
            "4", "user", " 查询   制度 ",
            "4", "assistant", " 请查看知识库 ",
            "5", "6", "7", "0",
        ],
    )
    assert first.returncode == 0, first.stderr
    assert "维护人已保存｜revision=1" in first.stdout
    assert "已新增 C1｜李梅｜revision=2" in first.stdout
    assert "消息角色必须是" in first.stdout
    assert "已新增 system 消息｜revision=3" in first.stdout
    assert "已新增 user 消息｜revision=4" in first.stdout
    assert "已新增 assistant 消息｜revision=5" in first.stdout
    assert "消息总数：3" in first.stdout
    assert "摘要：schema=2｜revision=5｜contacts=1｜messages=3" in first.stdout

    second = run_cli(working, ["3", "python", "5", "0"])
    assert second.returncode == 0, second.stderr
    assert "恢复成功：revision=5｜联系人=1｜消息=3" in second.stdout
    assert "搜索结果：1 名" in second.stdout
    assert "C1｜李梅｜AI 工程师" in second.stdout

    data = json.loads((working / "nexus_platform.json").read_text(encoding="utf-8"))
    assert data["schema_version"] == 2
    assert [item["role"] for item in data["messages"]] == [
        "system", "user", "assistant"
    ]

with tempfile.TemporaryDirectory(prefix="nexus-day08-migrate-") as temporary:
    working = Path(temporary)
    old = {
        "schema_version": 1,
        "revision": 4,
        "owner": {"employee_id": "E7", "department": "技术部"},
        "contacts": [],
    }
    (working / "nexus_platform.json").write_text(
        json.dumps(old, ensure_ascii=False), encoding="utf-8"
    )
    migrated = run_cli(working, ["7", "0"])
    assert migrated.returncode == 0
    assert "Schema v1 已迁移至 v2｜revision=5" in migrated.stdout
    saved = json.loads((working / "nexus_platform.json").read_text(encoding="utf-8"))
    assert saved["schema_version"] == 2
    assert saved["messages"] == []

print("Day 8 CLI 验收通过：对象持久化、对话恢复和 Schema 迁移均正确。")
