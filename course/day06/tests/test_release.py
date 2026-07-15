"""Day 6 发布链：无数据制品、哈希、解压与函数化 CLI 恢复。"""

from hashlib import sha256
from pathlib import Path
import json
import subprocess
import sys
import tempfile
import zipfile


DAY = Path(__file__).parents[1]
BUILDER = DAY / "deploy" / "build_release.py"
NAME = "nexus-functional-task-board-0.0.6"
EXPECTED = {
    f"{NAME}/functional_task_board.py",
    f"{NAME}/README.txt",
    f"{NAME}/SHA256SUMS",
}

with tempfile.TemporaryDirectory(prefix="nexus-day06-release-") as temporary:
    output = Path(temporary) / "build"
    build = subprocess.run(
        [sys.executable, str(BUILDER), "--output", str(output)],
        text=True,
        capture_output=True,
        check=False,
    )
    assert build.returncode == 0, build.stderr
    assert "函数化 CLI 双进程冒烟：通过" in build.stdout
    archive_path = output / f"{NAME}.zip"
    deployed_root = Path(temporary) / "deployed"
    with zipfile.ZipFile(archive_path) as archive:
        assert set(archive.namelist()) == EXPECTED
        assert all("nexus_tasks.json" not in name for name in archive.namelist())
        archive.extractall(deployed_root)

    deployed = deployed_root / NAME
    script = deployed / "functional_task_board.py"
    expected_hash = (deployed / "SHA256SUMS").read_text(
        encoding="utf-8"
    ).split()[0]
    assert sha256(script.read_bytes()).hexdigest() == expected_hash

    first = subprocess.run(
        [sys.executable, str(script)],
        cwd=deployed,
        input="\n".join(
            [
                "E96006", "财务部",
                "1", "T9", "部署函数服务", "2", "deploy, function",
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
        input="3\nT9\n5\n0\n",
        text=True,
        capture_output=True,
        check=False,
    )
    assert second.returncode == 0, second.stderr
    assert "恢复成功：revision=2，任务 1 条" in second.stdout
    assert "已完成 T9并保存｜revision=3" in second.stdout
    assert "总数=1｜进行中=0｜已完成=1" in second.stdout
    data = json.loads(
        (deployed / "nexus_tasks.json").read_text(encoding="utf-8")
    )
    assert data["revision"] == 3
    assert data["tasks"][0]["is_done"] is True

print("Day 6 发布链验收通过：制品隔离、哈希与部署恢复均正确。")
