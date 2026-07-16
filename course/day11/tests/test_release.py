"""Day 11 发布链测试。"""

import os
import subprocess
import sys
import tempfile
import zipfile
from hashlib import sha256
from pathlib import Path


DAY = Path(__file__).parents[1]
BUILDER = DAY / "deploy" / "build_release.py"
NAME = "nexus-corpus-platform-0.0.11"
PACKAGE_ROOT = f"{NAME}/nexus"

with tempfile.TemporaryDirectory(prefix="nexus-day11-release-") as temporary:
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
        assert f"{NAME}/corpus/policy.txt" in names
        assert f"{PACKAGE_ROOT}/documents/loader.py" in names
        archive.extractall(deployed_root)
    deployed = deployed_root / NAME
    digest_lines = (deployed / "SHA256SUMS").read_text(encoding="utf-8").strip().splitlines()
    for line in digest_lines:
        digest, filename = line.split(maxsplit=1)
        target = deployed / filename.strip()
        assert sha256(target.read_bytes()).hexdigest() == digest
    env = {**os.environ, "PYTHONPATH": str(deployed)}
    first = subprocess.run(
        [sys.executable, str(deployed / "main.py")],
        cwd=deployed,
        env=env,
        input="E11\n产品部\n10\ncorpus\n报销,制度,Agent\n11\nAgent\n0\n",
        text=True,
        capture_output=True,
        check=False,
    )
    second = subprocess.run(
        [sys.executable, str(deployed / "main.py")],
        cwd=deployed,
        env=env,
        input="6\n7\n0\n",
        text=True,
        capture_output=True,
        check=False,
    )
    assert first.returncode == 0 and second.returncode == 0, first.stderr
    assert "恢复成功" in second.stdout
    assert "schema=4" in second.stdout
    assert "'documents': 4" in second.stdout
    assert "语料命中" in first.stdout

print("Day 11 发布链验收通过：语料制品、哈希与部署恢复均正确。")
