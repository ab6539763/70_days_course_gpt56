"""Day 15 CLI、Web 入口与配置菜单测试。"""

import importlib.util
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from urllib.request import urlopen


SOLUTION = Path(__file__).parents[1] / "solution"
FIXTURES = Path(__file__).parents[1] / "fixtures" / "corpus"
MAIN = SOLUTION / "main.py"
MOCK = Path(__file__).parent / "mock_api.py"
spec = importlib.util.spec_from_file_location("mock_api", MOCK)
mock_api = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(mock_api)

server, base_url = mock_api.start_mock_api_server()


def run_main(directory, script_input, extra_env=None, extra_args=None):
    env = {
        **os.environ,
        "PYTHONPATH": str(SOLUTION),
        "NEXUS_API_BASE_URL": base_url,
        "NEXUS_USE_MOCK": "1",
    }
    if extra_env:
        env.update(extra_env)
    command = [sys.executable, str(MAIN)]
    if extra_args:
        command.extend(extra_args)
    return subprocess.run(
        command,
        cwd=directory,
        env=env,
        input=script_input,
        text=True,
        capture_output=True,
        check=False,
    )


with tempfile.TemporaryDirectory(prefix="nexus-day15-cli-") as temporary:
    working = Path(temporary)
    (working / ".env").write_text(
        "NEXUS_API_KEY=cli-dotenv-key\nNEXUS_USE_MOCK=1\nNEXUS_WEB_PORT=18080\n",
        encoding="utf-8",
    )
    corpus = working / "corpus"
    shutil.copytree(FIXTURES, corpus)
    first = run_main(
        working,
        "\n".join(
            [
                "E150015", "研发部",
                "14",
                "CLI 多轮测试",
                "/exit",
                "13",
                "7", "0",
            ]
        )
        + "\n",
    )
    assert first.returncode == 0, first.stderr + first.stdout
    assert "trace_id=" in first.stdout
    assert "配置摘要" in first.stdout

    web_proc = subprocess.Popen(
        [
            sys.executable,
            str(MAIN),
            "--web",
            "--host",
            "127.0.0.1",
            "--port",
            "18080",
        ],
        cwd=working,
        env={
            **os.environ,
            "PYTHONPATH": str(SOLUTION),
            "NEXUS_USE_MOCK": "1",
            "NEXUS_WEB_PORT": "18080",
        },
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        for _ in range(30):
            try:
                with urlopen("http://127.0.0.1:18080/api/health", timeout=1) as response:
                    payload = response.read().decode("utf-8")
                assert "0.0.15" in payload
                break
            except Exception:
                time.sleep(0.2)
        else:
            raise AssertionError("Web 服务未在预期时间内启动")
    finally:
        web_proc.terminate()
        web_proc.wait(timeout=5)

server.shutdown()
print("Day 15 CLI/Web 验收通过：CLI 回归、--web 健康检查均正确。")
