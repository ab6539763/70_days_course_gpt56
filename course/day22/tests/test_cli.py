"""Day 22 CLI、Web 与审计日志菜单测试。"""

import importlib.util
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from urllib.request import Request, urlopen


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
        "NEXUS_HISTORY_WINDOW": "20",
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


with tempfile.TemporaryDirectory(prefix="nexus-day22-cli-") as temporary:
    working = Path(temporary)
    (working / ".env").write_text(
        "NEXUS_API_KEY=cli-dotenv-key\nNEXUS_USE_MOCK=1\nNEXUS_WEB_PORT=18086\n",
        encoding="utf-8",
    )
    corpus = working / "corpus"
    shutil.copytree(FIXTURES, corpus)
    first = run_main(
        working,
        "\n".join(
            [
                "E220022", "研发部",
                "22",
                "21",
                "20",
                "19",
                "13",
                "7", "0",
            ]
        )
        + "\n",
    )
    assert first.returncode == 0, first.stderr + first.stdout
    assert "审计日志" in first.stdout
    assert "乐观锁" in first.stdout
    assert "REVISION_CONFLICT" in first.stdout or "冲突" in first.stdout
    assert "断流恢复" in first.stdout

    web_proc = subprocess.Popen(
        [
            sys.executable,
            str(MAIN),
            "--web",
            "--host",
            "127.0.0.1",
            "--port",
            "18086",
        ],
        cwd=working,
        env={
            **os.environ,
            "PYTHONPATH": str(SOLUTION),
            "NEXUS_USE_MOCK": "1",
            "NEXUS_WEB_PORT": "18086",
            "NEXUS_SESSION_DIR": str(working / "sessions"),
            "NEXUS_AUDIT_DIR": str(working / "audit"),
        },
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        for _ in range(30):
            try:
                req = Request(
                    "http://127.0.0.1:18086/api/audit",
                    headers={"X-Session-Id": "probe"},
                )
                with urlopen(req, timeout=1):
                    pass
            except Exception as error:
                if "404" not in str(error) and "400" not in str(error):
                    time.sleep(0.2)
                    continue
                req = Request(
                    "http://127.0.0.1:18086/api/session",
                    data=b"{}",
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with urlopen(req, timeout=1) as response:
                    payload = response.read().decode("utf-8")
                assert "session_id" in payload
                break
            time.sleep(0.2)
        else:
            raise AssertionError("Web 服务未在预期时间内可用")
    finally:
        web_proc.terminate()
        web_proc.wait(timeout=5)

server.shutdown()
print("Day 22 CLI/Web 验收通过：菜单22、审计日志与 --web 均正确。")
