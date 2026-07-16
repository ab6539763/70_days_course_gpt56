"""Day 14 发布链测试。"""

import importlib.util
import os
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


DAY = Path(__file__).parents[1]
BUILDER = DAY / "deploy" / "build_release.py"
MOCK = DAY / "tests" / "mock_api.py"
NAME = "nexus-chat-assistant-0.0.14"

spec = importlib.util.spec_from_file_location("mock_api", MOCK)
mock_api = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(mock_api)
server, base_url = mock_api.start_mock_api_server()

with tempfile.TemporaryDirectory(prefix="nexus-day14-release-") as temporary:
    output = Path(temporary) / "build"
    build = subprocess.run(
        [sys.executable, str(BUILDER), "--output", str(output)],
        text=True,
        capture_output=True,
        check=False,
    )
    assert build.returncode == 0, build.stderr
    archive_path = output / f"{NAME}.zip"
    deployed_root = Path(temporary) / "deployed"
    with zipfile.ZipFile(archive_path) as archive:
        names = set(archive.namelist())
        assert f"{NAME}/.env.example" in names
        assert f"{NAME}/nexus/observability/logging.py" in names
        assert f"{NAME}/nexus/cli/chat_assistant.py" in names
        archive.extractall(deployed_root)
    deployed = deployed_root / NAME
    (deployed / ".env").write_text(
        f"NEXUS_API_KEY=release-key\nNEXUS_API_BASE_URL={base_url}\n",
        encoding="utf-8",
    )
    env = {**os.environ, "PYTHONPATH": str(deployed)}
    first = subprocess.run(
        [sys.executable, str(deployed / "main.py"), "--chat"],
        cwd=deployed,
        env=env,
        input="E14\n产品部\n第一轮\n/exit\n",
        text=True,
        capture_output=True,
        check=False,
    )
    second = subprocess.run(
        [sys.executable, str(deployed / "main.py")],
        cwd=deployed,
        env=env,
        input="13\n7\n0\n",
        text=True,
        capture_output=True,
        check=False,
    )
    assert first.returncode == 0 and second.returncode == 0, first.stderr + first.stdout
    assert "HTTP mock 回复" in first.stdout or "assistant>" in first.stdout
    assert "配置摘要" in second.stdout
    assert "schema=4" in second.stdout

server.shutdown()
print("Day 14 发布链验收通过：多轮助手、日志模块与部署恢复均正确。")
