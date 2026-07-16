"""Day 16 CLI、Web 入口与 API 契约菜单测试。"""

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


with tempfile.TemporaryDirectory(prefix="nexus-day16-cli-") as temporary:
    working = Path(temporary)
    (working / ".env").write_text(
        "NEXUS_API_KEY=cli-dotenv-key\nNEXUS_USE_MOCK=1\nNEXUS_WEB_PORT=18081\n",
        encoding="utf-8",
    )
    corpus = working / "corpus"
    shutil.copytree(FIXTURES, corpus)
    first = run_main(
        working,
        "\n".join(
            [
                "E160016", "研发部",
                "16",
                "13",
                "7", "0",
            ]
        )
        + "\n",
    )
    assert first.returncode == 0, first.stderr + first.stdout
    assert "OpenAPI" in first.stdout
    assert "error.code" in first.stdout or "API 契约" in first.stdout

    web_proc = subprocess.Popen(
        [
            sys.executable,
            str(MAIN),
            "--web",
            "--host",
            "127.0.0.1",
            "--port",
            "18081",
        ],
        cwd=working,
        env={
            **os.environ,
            "PYTHONPATH": str(SOLUTION),
            "NEXUS_USE_MOCK": "1",
            "NEXUS_WEB_PORT": "18081",
        },
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        for _ in range(30):
            try:
                with urlopen("http://127.0.0.1:18081/api/openapi.json", timeout=1) as response:
                    payload = response.read().decode("utf-8")
                assert "0.0.16" in payload
                assert "openapi" in payload
                break
            except Exception:
                time.sleep(0.2)
        else:
            raise AssertionError("OpenAPI 端点未在预期时间内可用")
    finally:
        web_proc.terminate()
        web_proc.wait(timeout=5)

server.shutdown()
print("Day 16 CLI/Web 验收通过：菜单16、OpenAPI 端点与 --web 均正确。")
