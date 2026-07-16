"""Day 13 CLI dotenv、API 与配置菜单测试。"""

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
        "NEXUS_API_BASE_URL": base_url,
    }
    if extra_env:
        env.update(extra_env)
    return subprocess.run(
        [sys.executable, str(MAIN)],
        cwd=directory,
        env=env,
        input=script_input,
        text=True,
        capture_output=True,
        check=False,
    )


with tempfile.TemporaryDirectory(prefix="nexus-day13-cli-") as temporary:
    working = Path(temporary)
    (working / ".env").write_text(
        "NEXUS_API_KEY=cli-dotenv-key\nNEXUS_USE_MOCK=0\n",
        encoding="utf-8",
    )
    corpus = working / "corpus"
    shutil.copytree(FIXTURES, corpus)
    first = run_main(
        working,
        "\n".join(
            [
                "E130013", "研发部",
                "13",
                f"12\nCLI API 测试",
                "9\n模拟测试",
                "7", "0",
            ]
        )
        + "\n",
    )
    assert first.returncode == 0, first.stderr + first.stdout
    assert "API Key：" in first.stdout
    assert "cli-dotenv-key" not in first.stdout
    assert "HTTP mock 回复" in first.stdout
    assert "[qwen] 模拟回复" in first.stdout

    second = run_main(working, "13\n12\n第二次\n0\n")
    assert second.returncode == 0
    assert "恢复成功" in second.stdout

server.shutdown()
print("Day 13 CLI 验收通过：dotenv、API 重试与配置菜单均正确。")
