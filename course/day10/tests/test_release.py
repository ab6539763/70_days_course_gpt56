"""Day 10 发布链测试。"""

import os
import subprocess
import sys
import tempfile
import zipfile
from hashlib import sha256
from pathlib import Path


DAY = Path(__file__).parents[1]
BUILDER = DAY / "deploy" / "build_release.py"
NAME = "nexus-modular-platform-0.0.10"
PACKAGE_ROOT = f"{NAME}/nexus"
EXPECTED = {
    f"{NAME}/main.py",
    f"{NAME}/requirements.txt",
    f"{NAME}/README.txt",
    f"{NAME}/SHA256SUMS",
    f"{PACKAGE_ROOT}/__init__.py",
    f"{PACKAGE_ROOT}/__main__.py",
    f"{PACKAGE_ROOT}/constants.py",
    f"{PACKAGE_ROOT}/exceptions.py",
    f"{PACKAGE_ROOT}/cli/__init__.py",
    f"{PACKAGE_ROOT}/cli/app.py",
    f"{PACKAGE_ROOT}/cli/prompts.py",
    f"{PACKAGE_ROOT}/domain/__init__.py",
    f"{PACKAGE_ROOT}/domain/contact.py",
    f"{PACKAGE_ROOT}/domain/message.py",
    f"{PACKAGE_ROOT}/models/__init__.py",
    f"{PACKAGE_ROOT}/models/base.py",
    f"{PACKAGE_ROOT}/models/factory.py",
    f"{PACKAGE_ROOT}/models/openai_model.py",
    f"{PACKAGE_ROOT}/models/qwen_model.py",
    f"{PACKAGE_ROOT}/persistence/__init__.py",
    f"{PACKAGE_ROOT}/persistence/storage.py",
    f"{PACKAGE_ROOT}/platform/__init__.py",
    f"{PACKAGE_ROOT}/platform/state.py",
}

with tempfile.TemporaryDirectory(prefix="nexus-day10-release-") as temporary:
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
        assert set(archive.namelist()) == EXPECTED
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
        input="E10\n产品部\n4\nuser\n部署测试\n9\n发布后模块化推理\n0\n",
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
    assert first.returncode == 0 and second.returncode == 0
    assert "恢复成功" in second.stdout
    assert "消息总数：2" in second.stdout
    assert "schema=3" in second.stdout
    assert "[qwen]" in second.stdout

print("Day 10 发布链验收通过：包结构制品、哈希与部署恢复均正确。")
