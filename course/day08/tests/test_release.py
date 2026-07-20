"""Day 8 发布链测试。"""

from hashlib import sha256
from pathlib import Path
import subprocess
import sys
import tempfile
import zipfile


DAY = Path(__file__).parents[1]
BUILDER = DAY / "deploy" / "build_release.py"
NAME = "nexus-oop-platform-0.0.8"
EXPECTED = {
    f"{NAME}/oop_platform.py",
    f"{NAME}/README.txt",
    f"{NAME}/SHA256SUMS",
}

with tempfile.TemporaryDirectory(prefix="nexus-day08-release-") as temporary:
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
    script = deployed / "oop_platform.py"
    digest = (deployed / "SHA256SUMS").read_text(encoding="utf-8").split()[0]
    assert sha256(script.read_bytes()).hexdigest() == digest
    first = subprocess.run(
        [sys.executable, str(script)], cwd=deployed,
        input="E88\n产品部\n4\nsystem\n你是测试助手\n4\nuser\n你好\n0\n",
        text=True, capture_output=True, check=False,
    )
    second = subprocess.run(
        [sys.executable, str(script)], cwd=deployed,
        input="5\n6\n0\n", text=True, capture_output=True, check=False,
    )
    assert first.returncode == 0 and second.returncode == 0
    assert "恢复成功：revision=3｜联系人=0｜消息=2" in second.stdout
    assert "消息总数：2" in second.stdout
    assert "'system': 1" in second.stdout and "'user': 1" in second.stdout

print("Day 8 发布链验收通过：制品隔离、哈希与对象恢复均正确。")
