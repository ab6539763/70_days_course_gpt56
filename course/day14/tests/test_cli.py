"""Day 14 CLI 多轮助手、dotenv 与配置菜单测试。"""

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


def run_main(directory, script_input, extra_env=None, chat=False):
    env = {
        **os.environ,
        "PYTHONPATH": str(SOLUTION),
        "NEXUS_API_BASE_URL": base_url,
        "NEXUS_USE_MOCK": "1",
    }
    if extra_env:
        env.update(extra_env)
    command = [sys.executable, str(MAIN)]
    if chat:
        command.append("--chat")
    return subprocess.run(
        command,
        cwd=directory,
        env=env,
        input=script_input,
        text=True,
        capture_output=True,
        check=False,
    )


with tempfile.TemporaryDirectory(prefix="nexus-day14-cli-") as temporary:
    working = Path(temporary)
    (working / ".env").write_text(
        "NEXUS_API_KEY=cli-dotenv-key\nNEXUS_USE_MOCK=1\n",
        encoding="utf-8",
    )
    corpus = working / "corpus"
    shutil.copytree(FIXTURES, corpus)
    first = run_main(
        working,
        "\n".join(
            [
                "E140014", "研发部",
                "14",
                "你好，第一轮",
                "第二轮追问",
                "/history",
                "/save",
                "/clear",
                "/exit",
                "13",
                "7", "0",
            ]
        )
        + "\n",
    )
    assert first.returncode == 0, first.stderr + first.stdout
    assert "trace_id=" in first.stdout
    assert "多轮对话助手" in first.stdout
    assert "assistant>" in first.stdout
    assert "[qwen]" in first.stdout
    assert "最近" in first.stdout
    assert "已清空对话" in first.stdout

    second = run_main(working, "13\n7\n0\n")
    assert second.returncode == 0
    assert "恢复成功" in second.stdout

    chat_only = run_main(
        working,
        "\n".join(["/help", "直接对话", "/exit"]) + "\n",
        chat=True,
    )
    assert chat_only.returncode == 0, chat_only.stderr + chat_only.stdout
    assert "/help" in chat_only.stdout or "多轮对话助手命令" in chat_only.stdout

server.shutdown()
print("Day 14 CLI 验收通过：菜单14、--chat、slash 命令与 trace 均正确。")
