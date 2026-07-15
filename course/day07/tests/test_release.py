"""Day 7 发布链：联系人制品隔离、哈希、解压与 CRUD 恢复。"""

from hashlib import sha256
from pathlib import Path
import json
import subprocess
import sys
import tempfile
import zipfile


DAY = Path(__file__).parents[1]
BUILDER = DAY / "deploy" / "build_release.py"
NAME = "nexus-contact-directory-0.0.7"
EXPECTED = {
    f"{NAME}/contact_directory.py",
    f"{NAME}/README.txt",
    f"{NAME}/SHA256SUMS",
}

with tempfile.TemporaryDirectory(prefix="nexus-day07-release-") as temporary:
    output = Path(temporary) / "build"
    build = subprocess.run(
        [sys.executable, str(BUILDER), "--output", str(output)],
        text=True,
        capture_output=True,
        check=False,
    )
    assert build.returncode == 0, build.stderr
    assert "联系人双进程搜索冒烟：通过" in build.stdout
    archive_path = output / f"{NAME}.zip"
    deployed_root = Path(temporary) / "deployed"
    with zipfile.ZipFile(archive_path) as archive:
        assert set(archive.namelist()) == EXPECTED
        assert all("nexus_contacts.json" not in name for name in archive.namelist())
        archive.extractall(deployed_root)

    deployed = deployed_root / NAME
    script = deployed / "contact_directory.py"
    digest = (deployed / "SHA256SUMS").read_text(encoding="utf-8").split()[0]
    assert sha256(script.read_bytes()).hexdigest() == digest

    first = subprocess.run(
        [sys.executable, str(script)],
        cwd=deployed,
        input="\n".join(
            [
                "E97007", "财务部",
                "1", "C9", "审计联系人", "财务部", "审计专员",
                "audit@example.test", "audit, json",
                "0",
            ]
        )
        + "\n",
        text=True,
        capture_output=True,
        check=False,
    )
    assert first.returncode == 0, first.stderr
    second = subprocess.run(
        [sys.executable, str(script)],
        cwd=deployed,
        input="4\nC9\n高级审计专员\n3\n高级\n6\n0\n",
        text=True,
        capture_output=True,
        check=False,
    )
    assert second.returncode == 0, second.stderr
    assert "恢复成功：revision=2，联系人 1 名" in second.stdout
    assert "已更新 C9并保存｜revision=3" in second.stdout
    assert "搜索结果：1 名" in second.stdout
    data = json.loads(
        (deployed / "nexus_contacts.json").read_text(encoding="utf-8")
    )
    assert data["revision"] == 3
    assert data["contacts"][0]["role"] == "高级审计专员"

print("Day 7 发布链验收通过：制品隔离、哈希与联系人恢复均正确。")
