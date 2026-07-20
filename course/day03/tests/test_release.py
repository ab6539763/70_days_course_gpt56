"""Day 3 发布全链路：构建、文件集、哈希、解压与部署后重试。"""

from hashlib import sha256
from pathlib import Path
import subprocess
import sys
import tempfile
import zipfile


DAY = Path(__file__).parents[1]
BUILDER = DAY / "deploy" / "build_release.py"
RELEASE_NAME = "nexus-validated-cleaner-0.0.3"
EXPECTED = {
    f"{RELEASE_NAME}/validated_cleaner.py",
    f"{RELEASE_NAME}/README.txt",
    f"{RELEASE_NAME}/SHA256SUMS",
}

with tempfile.TemporaryDirectory(prefix="nexus-day03-") as temporary:
    output = Path(temporary) / "build"
    build = subprocess.run(
        [sys.executable, str(BUILDER), "--output", str(output)],
        text=True,
        capture_output=True,
        check=False,
    )
    assert build.returncode == 0, build.stderr
    assert "部署冒烟测试：通过" in build.stdout

    archive_path = output / f"{RELEASE_NAME}.zip"
    assert archive_path.is_file()
    deployed_root = Path(temporary) / "deployed"
    with zipfile.ZipFile(archive_path) as archive:
        assert set(archive.namelist()) == EXPECTED
        archive.extractall(deployed_root)

    deployed = deployed_root / RELEASE_NAME
    script = deployed / "validated_cleaner.py"
    expected_hash = (deployed / "SHA256SUMS").read_text(
        encoding="utf-8"
    ).split()[0]
    assert sha256(script.read_bytes()).hexdigest() == expected_hash

    # 部署后故意输入一次无效部门，证明发布版仍具备重试能力。
    secret = "DEPLOY-DEMO-3"
    deployed_run = subprocess.run(
        [sys.executable, str(script)],
        cwd=deployed,
        input="\n".join(
            [
                "E80008",
                "未知部",
                "财务部",
                "auditor",
                f"复核 BILL-8 和 {secret}",
                "300",
                "10",
                secret,
                "bill",
                "1",
                "0",
            ]
        )
        + "\n",
        text=True,
        capture_output=True,
        check=False,
    )
    assert deployed_run.returncode == 0, deployed_run.stderr
    assert "部门不在当前试点白名单" in deployed_run.stdout
    assert "E80008｜财务部｜Auditor" in deployed_run.stdout
    assert secret not in deployed_run.stdout
    assert "[已脱敏]" in deployed_run.stdout
    assert "已安全退出" in deployed_run.stdout

print("Day 3 发布链路验收通过：构建、完整性、解压、重试与部署冒烟均正确。")
