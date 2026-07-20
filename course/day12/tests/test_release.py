"""Day 12 发布链测试。"""

import importlib.util
import os
import subprocess
import sys
import tempfile
import zipfile
from hashlib import sha256
from pathlib import Path


DAY = Path(__file__).parents[1]
BUILDER = DAY / "deploy" / "build_release.py"
MOCK = DAY / "tests" / "mock_api.py"
NAME = "nexus-api-platform-0.0.12"

spec = importlib.util.spec_from_file_location("mock_api", MOCK)
mock_api = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(mock_api)
server, base_url = mock_api.start_mock_api_server()

with tempfile.TemporaryDirectory(prefix="nexus-day12-release-") as temporary:
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
        assert f"{NAME}/main.py" in names
        assert f"{NAME}/requirements.txt" in names
        assert f"{NAME}/nexus/http/client.py" in names
        archive.extractall(deployed_root)
    deployed = deployed_root / NAME
    env = {
        **os.environ,
        "PYTHONPATH": str(deployed),
        "NEXUS_API_KEY": "release-key",
        "NEXUS_API_BASE_URL": base_url,
    }
    first = subprocess.run(
        [sys.executable, str(deployed / "main.py")],
        cwd=deployed,
        env=env,
        input="E12\n产品部\n4\nuser\n部署前消息\n12\n发布后 API 问题\n0\n",
        text=True,
        capture_output=True,
        check=False,
    )
    second = subprocess.run(
        [sys.executable, str(deployed / "main.py")],
        cwd=deployed,
        env=env,
        input="5\n7\n0\n",
        text=True,
        capture_output=True,
        check=False,
    )
    assert first.returncode == 0 and second.returncode == 0, first.stderr
    assert "HTTP mock 回复" in first.stdout
    assert "恢复成功" in second.stdout
    assert "schema=4" in second.stdout

server.shutdown()
print("Day 12 发布链验收通过：requests 依赖、Mock API 与部署恢复均正确。")
