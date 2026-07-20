"""Day 4 发布测试：构建、哈希、解压及部署后 CRUD 冒烟。"""

from hashlib import sha256
from pathlib import Path
import subprocess
import sys
import tempfile
import zipfile


DAY = Path(__file__).parents[1]
BUILDER = DAY / "deploy" / "build_release.py"
NAME = "nexus-task-board-0.0.4"
EXPECTED_FILES = {
    f"{NAME}/task_board.py",
    f"{NAME}/README.txt",
    f"{NAME}/SHA256SUMS",
}

with tempfile.TemporaryDirectory(prefix="nexus-day04-") as temporary:
    output = Path(temporary) / "build"
    build = subprocess.run(
        [sys.executable, str(BUILDER), "--output", str(output)],
        text=True,
        capture_output=True,
        check=False,
    )
    assert build.returncode == 0, build.stderr
    assert "部署冒烟测试：通过" in build.stdout

    archive_path = output / f"{NAME}.zip"
    assert archive_path.is_file()
    deployed_root = Path(temporary) / "deployed"
    with zipfile.ZipFile(archive_path) as archive:
        assert set(archive.namelist()) == EXPECTED_FILES
        archive.extractall(deployed_root)

    deployed = deployed_root / NAME
    script = deployed / "task_board.py"
    expected_hash = (deployed / "SHA256SUMS").read_text(
        encoding="utf-8"
    ).split()[0]
    assert sha256(script.read_bytes()).hexdigest() == expected_hash

    deployed_run = subprocess.run(
        [sys.executable, str(script)],
        cwd=deployed,
        input="\n".join(
            [
                "E90009",
                "财务部",
                "1", "T9", "复核模拟账单", "1", "audit, finance, audit",
                "2",
                "3", "T9",
                "5",
                "4", "T9",
                "5",
                "0",
            ]
        )
        + "\n",
        text=True,
        capture_output=True,
        check=False,
    )
    assert deployed_run.returncode == 0, deployed_run.stderr
    assert "标签 ('audit', 'finance')" in deployed_run.stdout
    assert "首页预览：['T9']" in deployed_run.stdout
    assert "完成成功：T9" in deployed_run.stdout
    assert "已完成：1" in deployed_run.stdout
    assert "删除成功：T9｜复核模拟账单" in deployed_run.stdout
    assert "总数：0" in deployed_run.stdout
    assert "内存中剩余 0 条任务" in deployed_run.stdout

print("Day 4 发布链路验收通过：构建、哈希、解压与部署后 CRUD 均正确。")
