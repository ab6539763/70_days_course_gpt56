"""Day 12 CLI API 对话、语料与 Mock HTTP 测试。"""

import importlib.util
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
MOCK = Path(__file__).parent / "mock_api.py"
spec = importlib.util.spec_from_file_location("mock_api", MOCK)
mock_api = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(mock_api)

server, base_url = mock_api.start_mock_api_server()


def run_main(directory, script_input, extra_env=None):
    env = {
        **os.environ,
        "PYTHONPATH": str(SOLUTION),
        "NEXUS_API_KEY": "cli-test-key",
        "NEXUS_API_BASE_URL": base_url,
    }
    if extra_env:
        env.update(extra_env)
    env.pop("NEXUS_USE_MOCK", None)
    return subprocess.run(
        [sys.executable, str(MAIN)],
        cwd=directory,
        env=env,
        input=script_input,
        text=True,
        capture_output=True,
        check=False,
    )


with tempfile.TemporaryDirectory(prefix="nexus-day12-cli-") as temporary:
    working = Path(temporary)
    corpus = working / "corpus"
    shutil.copytree(FIXTURES, corpus)
    first = run_main(
        working,
        "\n".join(
            [
                "E120012", "研发部",
                f"10\n{corpus}\n报销,制度",
                "12\nAPI 对话测试",
                "9\n模拟对话测试",
                "7", "0",
            ]
        )
        + "\n",
    )
    assert first.returncode == 0, first.stderr + first.stdout
    assert "HTTP mock 回复" in first.stdout
    assert "[qwen] 模拟回复" in first.stdout
    assert "schema=4" in first.stdout

    second = run_main(working, "12\n第二次 API\n5\n0\n")
    assert second.returncode == 0, second.stderr
    assert "恢复成功" in second.stdout
    assert "HTTP mock 回复" in second.stdout
    data = json.loads((working / "nexus_platform.json").read_text(encoding="utf-8"))
    assert data["schema_version"] == 4
    assert len(data["messages"]) >= 2

with tempfile.TemporaryDirectory(prefix="nexus-day12-nokey-") as temporary:
    working = Path(temporary)
    env = {**os.environ, "PYTHONPATH": str(SOLUTION)}
    env.pop("NEXUS_API_KEY", None)
    env.pop("NEXUS_USE_MOCK", None)
    no_key = subprocess.run(
        [sys.executable, str(MAIN)],
        cwd=working,
        env=env,
        input="E12\n技术部\n12\n应被拒绝\n0\n",
        text=True,
        capture_output=True,
        check=False,
    )
    assert "未设置 NEXUS_API_KEY" in no_key.stdout

server.shutdown()
print("Day 12 CLI 验收通过：API 对话、模拟回退与双进程恢复均正确。")
