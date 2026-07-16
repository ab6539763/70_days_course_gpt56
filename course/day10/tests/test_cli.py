"""Day 10 CLI 双进程、异常路径与 Schema 迁移测试。"""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


SOLUTION = Path(__file__).parents[1] / "solution"
MAIN = SOLUTION / "main.py"
ENV = {**os.environ, "PYTHONPATH": str(SOLUTION)}


def run_main(directory, script_input):
    return subprocess.run(
        [sys.executable, str(MAIN)],
        cwd=directory,
        env=ENV,
        input=script_input,
        text=True,
        capture_output=True,
        check=False,
    )


with tempfile.TemporaryDirectory(prefix="nexus-day10-cli-") as temporary:
    working = Path(temporary)
    first = run_main(
        working,
        "\n".join(
            [
                "E100010", "研发部",
                "1", "C10", "周航", "技术部", "架构师",
                "zhou@example.test", "python,package",
                "4", "tool", "无效",
                "4", "system", "  你是企业助手 ",
                "4", "user", " 模块化测试 ",
                "9", "包结构有什么好处",
                "5", "7", "0",
            ]
        )
        + "\n",
    )
    assert first.returncode == 0, first.stderr
    assert "维护人已保存｜revision=1" in first.stdout
    assert "消息角色必须是" in first.stdout
    assert "assistant：[qwen]" in first.stdout
    assert "schema=3" in first.stdout

    second = run_main(working, "8\ny\nopenai\ngpt-4o-mini\n0.2\n512\n7\n0\n")
    assert second.returncode == 0, second.stderr
    assert "恢复成功" in second.stdout
    assert "openai/gpt-4o-mini" in second.stdout

    data = json.loads((working / "nexus_platform.json").read_text(encoding="utf-8"))
    assert data["schema_version"] == 3
    assert data["model_config"]["provider"] == "openai"

with tempfile.TemporaryDirectory(prefix="nexus-day10-migrate-") as temporary:
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
    migrated = run_main(working, "7\n0\n")
    assert migrated.returncode == 0
    assert "Schema 已迁移至 v3" in migrated.stdout
    saved = json.loads((working / "nexus_platform.json").read_text(encoding="utf-8"))
    assert saved["schema_version"] == 3
    assert saved["revision"] == 5

with tempfile.TemporaryDirectory(prefix="nexus-day10-badjson-") as temporary:
    working = Path(temporary)
    (working / "nexus_platform.json").write_text("{bad", encoding="utf-8")
    bad = run_main(working, "0\n")
    assert bad.returncode == 2
    assert "持久化错误" in bad.stdout

print("Day 10 CLI 验收通过：模块化启动、异常路径与迁移均正确。")
