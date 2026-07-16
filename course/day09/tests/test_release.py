"""Day 9 发布链测试。"""

from hashlib import sha256
from pathlib import Path
import subprocess
import sys
import tempfile
import zipfile


DAY = Path(__file__).parents[1]
BUILDER = DAY / "deploy" / "build_release.py"
NAME = "nexus-model-platform-0.0.9"
EXPECTED = {
    f"{NAME}/model_platform.py",
    f"{NAME}/README.txt",
    f"{NAME}/SHA256SUMS",
}

with tempfile.TemporaryDirectory(prefix="nexus-day09-release-") as temporary:
    output = Path(temporary) / "build"
    build = subprocess.run(
        [sys.executable, str(BUILDER), "--output", str(output)],
        text=True, capture_output=True, check=False,
    )
    assert build.returncode == 0, build.stderr
    archive_path = output / f"{NAME}.zip"
    deployed_root = Path(temporary) / "deployed"
    with zipfile.ZipFile(archive_path) as archive:
        assert set(archive.namelist()) == EXPECTED
        archive.extractall(deployed_root)
    deployed = deployed_root / NAME
    script = deployed / "model_platform.py"
    digest = (deployed / "SHA256SUMS").read_text(encoding="utf-8").split()[0]
    assert sha256(script.read_bytes()).hexdigest() == digest
    first = subprocess.run(
        [sys.executable, str(script)], cwd=deployed,
        input="E99\n产品部\n4\nuser\n部署测试\n9\n发布后还能推理吗\n0\n",
        text=True, capture_output=True, check=False,
    )
    second = subprocess.run(
        [sys.executable, str(script)], cwd=deployed,
        input="5\n7\n0\n", text=True, capture_output=True, check=False,
    )
    assert first.returncode == 0 and second.returncode == 0
    assert "恢复成功" in second.stdout
    assert "消息总数：2" in second.stdout
    assert "schema=3" in second.stdout
    assert "[qwen]" in second.stdout

print("Day 9 发布链验收通过：制品隔离、哈希与模型恢复均正确。")
