"""Day 2 发布链路测试：构建、校验、解压和部署后启动。"""

from hashlib import sha256
from pathlib import Path
import subprocess
import sys
import tempfile
import zipfile


DAY_DIRECTORY = Path(__file__).parents[1]
BUILD_SCRIPT = DAY_DIRECTORY / "deploy" / "build_release.py"
EXPECTED_FILES = {
    "nexus-text-cleaner-0.0.2/text_cleaner.py",
    "nexus-text-cleaner-0.0.2/README.txt",
    "nexus-text-cleaner-0.0.2/SHA256SUMS",
}

with tempfile.TemporaryDirectory(prefix="nexus-day02-release-") as temporary:
    output_directory = Path(temporary) / "build"
    build_result = subprocess.run(
        [
            sys.executable,
            str(BUILD_SCRIPT),
            "--output",
            str(output_directory),
        ],
        text=True,
        capture_output=True,
        check=False,
    )

    assert build_result.returncode == 0, build_result.stderr
    assert "部署冒烟测试：通过" in build_result.stdout

    archive_file = output_directory / "nexus-text-cleaner-0.0.2.zip"
    assert archive_file.is_file(), "构建流程没有生成 zip 发布包"

    with zipfile.ZipFile(archive_file) as archive:
        assert set(archive.namelist()) == EXPECTED_FILES, "发布包文件集合不正确"
        extract_directory = Path(temporary) / "deployed"
        archive.extractall(extract_directory)

    deployed_directory = extract_directory / "nexus-text-cleaner-0.0.2"
    deployed_script = deployed_directory / "text_cleaner.py"
    checksum_line = (deployed_directory / "SHA256SUMS").read_text(
        encoding="utf-8"
    ).strip()
    expected_digest = checksum_line.split()[0]
    actual_digest = sha256(deployed_script.read_bytes()).hexdigest()
    assert actual_digest == expected_digest, "部署脚本 SHA-256 校验失败"

    # 在解压后的部署目录再次启动，确认发布包不依赖仓库相对路径。
    deployed_result = subprocess.run(
        [sys.executable, str(deployed_script)],
        cwd=deployed_directory,
        input="\n".join(
            [
                "e70001",
                "客户服务中心",
                "quality analyst",
                "复核 CASE-7，模拟凭据 DEMO-SECRET",
                "DEMO-SECRET",
                "case",
            ]
        )
        + "\n",
        text=True,
        capture_output=True,
        check=False,
    )

    assert deployed_result.returncode == 0, deployed_result.stderr
    assert "员工编号        ：E70001" in deployed_result.stdout
    assert "客户服务部 / Quality Analyst" in deployed_result.stdout
    assert "DEMO-SECRET" not in deployed_result.stdout
    assert "[已脱敏]" in deployed_result.stdout

print("Day 2 发布链路验收通过：构建、校验、解压和部署后启动均正确。")
