"""Day 18 发布链测试。"""

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
NAME = "nexus-sse-stream-0.0.18"

spec = importlib.util.spec_from_file_location("mock_api", MOCK)
mock_api = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(mock_api)
server, base_url = mock_api.start_mock_api_server()

with tempfile.TemporaryDirectory(prefix="nexus-day18-release-") as temporary:
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
        assert f"{NAME}/nexus/http/stream_client.py" in names
        assert f"{NAME}/nexus/web/sse.py" in names
        archive.extractall(deployed_root)
    deployed = deployed_root / NAME
    (deployed / ".env").write_text(
        f"NEXUS_API_KEY=release-key\nNEXUS_API_BASE_URL={base_url}\nNEXUS_USE_MOCK=1\n",
        encoding="utf-8",
    )
    env = {**os.environ, "PYTHONPATH": str(deployed)}
    smoke = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "from nexus.web.app import create_app; "
                "app=create_app('nexus_platform.json'); "
                "c=app.test_client(); "
                "body=c.post('/api/chat/stream', json={'prompt':'发布','max_history':2}).get_data(as_text=True); "
                "assert 'event: chunk' in body and 'event: done' in body; "
                "print('stream smoke ok')"
            ),
        ],
        cwd=deployed,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    cli = subprocess.run(
        [sys.executable, str(deployed / "main.py")],
        cwd=deployed,
        env=env,
        input="18\n13\n7\n0\n",
        text=True,
        capture_output=True,
        check=False,
    )
    assert smoke.returncode == 0, smoke.stderr + smoke.stdout
    assert cli.returncode == 0, cli.stderr
    assert "SSE 流式" in cli.stdout
    assert "schema=4" in cli.stdout

server.shutdown()
print("Day 18 发布链验收通过：SSE 流式模块与部署恢复均正确。")
