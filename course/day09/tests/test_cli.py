"""Day 9 CLI 双进程、模型切换与 Schema 迁移测试。"""

from pathlib import Path
import json
import subprocess
import sys
import tempfile


SOLUTION = Path(__file__).parents[1] / "solution" / "model_platform.py"


def run_cli(directory, lines):
    return subprocess.run(
        [sys.executable, str(SOLUTION)],
        cwd=directory,
        input="\n".join(lines) + "\n",
        text=True,
        capture_output=True,
        check=False,
    )


with tempfile.TemporaryDirectory(prefix="nexus-day09-cli-") as temporary:
    working = Path(temporary)
    first = run_cli(
        working,
        [
            "E90009", "研发部",
            "1", "C9", "赵敏", "技术部", "平台工程师",
            "zhao@example.test", "python,agent",
            "4", "system", "  你是企业助手 ",
            "4", "user", " 查询制度 ",
            "8", "N",
            "9", "报销流程是什么",
            "5", "6", "7", "0",
        ],
    )
    assert first.returncode == 0, first.stderr
    assert "维护人已保存｜revision=1" in first.stdout
    assert "已新增 C9｜赵敏｜revision=2" in first.stdout
    assert "已新增 system 消息｜revision=3" in first.stdout
    assert "已新增 user 消息｜revision=4" in first.stdout
    assert "当前模型：qwen/qwen-plus" in first.stdout
    assert "assistant：[qwen]" in first.stdout
    assert "消息总数：3" in first.stdout
    assert "schema=3" in first.stdout

    second = run_cli(
        working,
        [
            "8", "y", "openai", "gpt-4o-mini", "0.2", "512",
            "9", "切换后还能回答吗",
            "7", "0",
        ],
    )
    assert second.returncode == 0, second.stderr
    assert "恢复成功" in second.stdout
    assert "模型已切换为 openai/gpt-4o-mini" in second.stdout
    assert "assistant：[openai]" in second.stdout
    assert "model=openai/gpt-4o-mini" in second.stdout

    data = json.loads((working / "nexus_platform.json").read_text(encoding="utf-8"))
    assert data["schema_version"] == 3
    assert data["model_config"]["provider"] == "openai"
    assert [item["role"] for item in data["messages"]][-1] == "assistant"

with tempfile.TemporaryDirectory(prefix="nexus-day09-migrate-") as temporary:
    working = Path(temporary)
    old = {
        "schema_version": 2,
        "revision": 4,
        "owner": {"employee_id": "E7", "department": "技术部"},
        "contacts": [],
        "messages": [{"role": "user", "content": "历史问题"}],
    }
    (working / "nexus_platform.json").write_text(
        json.dumps(old, ensure_ascii=False), encoding="utf-8"
    )
    migrated = run_cli(working, ["7", "0"])
    assert migrated.returncode == 0
    assert "Schema 已迁移至 v3" in migrated.stdout
    saved = json.loads((working / "nexus_platform.json").read_text(encoding="utf-8"))
    assert saved["schema_version"] == 3
    assert saved["model_config"]["provider"] == "qwen"
    assert saved["revision"] == 5

print("Day 9 CLI 验收通过：模型多态、切换持久化与 Schema 迁移均正确。")
