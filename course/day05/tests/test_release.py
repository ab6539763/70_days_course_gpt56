"""Day 5 发布链：构建、数据隔离、哈希、解压和跨进程恢复。"""

from hashlib import sha256
from pathlib import Path
import json
import subprocess
import sys
import tempfile
import zipfile


DAY = Path(__file__).parents[1]
BUILDER = DAY / "deploy" / "build_release.py"
NAME = "nexus-persistent-task-board-0.0.5"
EXPECTED = {
    f"{NAME}/persistent_task_board.py",
    f"{NAME}/README.txt",
    f"{NAME}/SHA256SUMS",
}

with tempfile.TemporaryDirectory(prefix="nexus-day05-release-") as temporary:
    output = Path(temporary) / "build"
    build = subprocess.run(
        [sys.executable, str(BUILDER), "--output", str(output)],
        text=True,
        capture_output=True,
        check=False,
    )
    assert build.returncode == 0, build.stderr
    assert "跨进程恢复冒烟：通过" in build.stdout
    assert "运行时 JSON 未进入发布包：通过" in build.stdout

    archive_path = output / f"{NAME}.zip"
    deployed_root = Path(temporary) / "deployed"
    with zipfile.ZipFile(archive_path) as archive:
        assert set(archive.namelist()) == EXPECTED
        assert all("nexus_tasks.json" not in name for name in archive.namelist())
        archive.extractall(deployed_root)

    deployed = deployed_root / NAME
    script = deployed / "persistent_task_board.py"
    expected_hash = (deployed / "SHA256SUMS").read_text(
        encoding="utf-8"
    ).split()[0]
    assert sha256(script.read_bytes()).hexdigest() == expected_hash
    assert not (deployed / "nexus_tasks.json").exists()

    first = subprocess.run(
        [sys.executable, str(script)],
        cwd=deployed,
        input="\n".join(
            [
                "E95005",
                "财务部",
                "1", "T9", "复核 JSON 账单", "1", "json, audit",
                "0",
            ]
        )
        + "\n",
        text=True,
        capture_output=True,
        check=False,
    )
    assert first.returncode == 0, first.stderr
    data_file = deployed / "nexus_tasks.json"
    assert data_file.is_file()
    first_data = json.loads(data_file.read_text(encoding="utf-8"))
    assert first_data["revision"] == 2
    assert first_data["tasks"][0]["task_id"] == "T9"

    second = subprocess.run(
        [sys.executable, str(script)],
        cwd=deployed,
        input="3\nT9\n7\n0\n",
        text=True,
        capture_output=True,
        check=False,
    )
    assert second.returncode == 0, second.stderr
    assert "恢复成功：revision=2，任务 1 条" in second.stdout
    assert "完成并保存：T9｜revision=3" in second.stdout
    assert "task_count：1" in second.stdout
    second_data = json.loads(data_file.read_text(encoding="utf-8"))
    assert second_data["revision"] == 3
    assert second_data["tasks"][0]["is_done"] is True

print("Day 5 发布链验收通过：制品无数据、哈希正确、部署后可跨进程恢复。")
