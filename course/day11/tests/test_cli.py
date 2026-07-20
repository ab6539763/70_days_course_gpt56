"""Day 11 CLI 语料导入、检索双进程与迁移测试。"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


SOLUTION = Path(__file__).parents[1] / "solution"
FIXTURES = Path(__file__).parents[1] / "fixtures" / "corpus"
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


with tempfile.TemporaryDirectory(prefix="nexus-day11-cli-") as temporary:
    working = Path(temporary)
    corpus = working / "corpus"
    shutil.copytree(FIXTURES, corpus)
    first = run_main(
        working,
        "\n".join(
            [
                "E110011", "研发部",
                f"10\n{corpus}\n报销,制度,Agent",
                "11\n报销",
                "6", "7", "0",
            ]
        )
        + "\n",
    )
    assert first.returncode == 0, first.stderr + first.stdout
    assert "已导入 4 份语料" in first.stdout
    assert "语料命中" in first.stdout
    assert "schema=4" in first.stdout
    assert "'documents': 4" in first.stdout or "documents=4" in first.stdout

    second = run_main(working, "11\n制度\n7\n0\n")
    assert second.returncode == 0, second.stderr
    assert "恢复成功" in second.stdout
    assert "语料=4" in second.stdout
    assert "语料命中" in second.stdout

    data = json.loads((working / "nexus_platform.json").read_text(encoding="utf-8"))
    assert data["schema_version"] == 4
    assert len(data["document_index"]["documents"]) == 4

with tempfile.TemporaryDirectory(prefix="nexus-day11-migrate-") as temporary:
    working = Path(temporary)
    old = {
        "schema_version": 3,
        "revision": 6,
        "owner": {"employee_id": "E7", "department": "技术部"},
        "contacts": [],
        "messages": [],
        "model_config": {
            "provider": "qwen",
            "model_id": "qwen-plus",
            "temperature": 0.7,
            "max_tokens": 1024,
        },
    }
    (working / "nexus_platform.json").write_text(
        json.dumps(old, ensure_ascii=False), encoding="utf-8"
    )
    migrated = run_main(working, "7\n0\n")
    assert migrated.returncode == 0
    assert "Schema 已迁移至 v4" in migrated.stdout
    saved = json.loads((working / "nexus_platform.json").read_text(encoding="utf-8"))
    assert saved["schema_version"] == 4
    assert saved["revision"] == 7
    assert "document_index" in saved

with tempfile.TemporaryDirectory(prefix="nexus-day11-badcorpus-") as temporary:
    working = Path(temporary)
    bad = run_main(working, "E11\n技术部\n10\nmissing_dir\n报销\n0\n")
    assert bad.returncode == 0
    assert "语料目录不存在" in bad.stdout

print("Day 11 CLI 验收通过：语料导入、检索持久化与 Schema 迁移均正确。")
