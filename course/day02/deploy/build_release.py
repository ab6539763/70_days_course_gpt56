"""构建 Day 2 可分发发布包并执行部署前完整性检查。

示例：
    python3 course/day02/deploy/build_release.py --output artifacts/day02

发布包只包含可独立运行的 Python 脚本、使用说明和 SHA-256 校验文件，
不包含源代码缓存、测试数据或任何本地环境配置。
"""

from argparse import ArgumentParser
from hashlib import sha256
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
SOURCE = REPOSITORY_ROOT / "course/day02/solution/text_cleaner.py"

SMOKE_INPUT = "\n".join(
    [
        "e90001",
        "客服部",
        "support agent",
        "查询 ORDER-1，模拟号码 DEMO-10086",
        "DEMO-10086",
        "order",
    ]
) + "\n"


parser = ArgumentParser(description="构建智枢 Day 2 文本治理工具发布包")
parser.add_argument(
    "--output",
    type=Path,
    default=REPOSITORY_ROOT / "artifacts/day02",
    help="发布产物目录，默认为 artifacts/day02",
)
arguments = parser.parse_args()
output_directory = arguments.output.resolve()
staging_directory = output_directory / "nexus-text-cleaner-0.0.2"
archive_file = output_directory / "nexus-text-cleaner-0.0.2.zip"

# 每次构建都从空暂存目录开始，避免旧版本文件混入新发布包。
if staging_directory.exists():
    shutil.rmtree(staging_directory)
staging_directory.mkdir(parents=True, exist_ok=True)

deployed_script = staging_directory / "text_cleaner.py"
shutil.copy2(SOURCE, deployed_script)

readme = staging_directory / "README.txt"
readme.write_text(
    "智枢 NexusAI 文本清洗工作台 0.0.2\n"
    "环境要求：Python 3.10+\n"
    "运行命令：python3 text_cleaner.py\n"
    "数据声明：只处理模拟数据，不保存任何输入。\n",
    encoding="utf-8",
)

# SHA-256 用于确认收到的脚本与构建时脚本字节完全一致。
script_digest = sha256(deployed_script.read_bytes()).hexdigest()
checksum_file = staging_directory / "SHA256SUMS"
checksum_file.write_text(
    f"{script_digest}  text_cleaner.py\n",
    encoding="utf-8",
)

# 从暂存目录直接启动发布版，而不是再次运行源文件。
smoke_result = subprocess.run(
    [sys.executable, str(deployed_script)],
    cwd=staging_directory,
    input=SMOKE_INPUT,
    text=True,
    capture_output=True,
    check=False,
)
if smoke_result.returncode != 0:
    raise SystemExit(f"发布版冒烟测试失败：\n{smoke_result.stderr}")
if "员工编号        ：E90001" not in smoke_result.stdout:
    raise SystemExit("发布版冒烟测试失败：员工编号未标准化")
if "客户服务部 / Support Agent" not in smoke_result.stdout:
    raise SystemExit("发布版冒烟测试失败：组织或岗位未标准化")
if "DEMO-10086" in smoke_result.stdout or "[已脱敏]" not in smoke_result.stdout:
    raise SystemExit("发布版冒烟测试失败：模拟敏感片段未正确脱敏")

# 使用 DEFLATED 生成跨平台 zip，归档内保留单一顶层目录。
output_directory.mkdir(parents=True, exist_ok=True)
if archive_file.exists():
    archive_file.unlink()
with zipfile.ZipFile(
    archive_file,
    mode="w",
    compression=zipfile.ZIP_DEFLATED,
) as archive:
    for file_path in sorted(staging_directory.iterdir()):
        archive.write(
            file_path,
            arcname=f"{staging_directory.name}/{file_path.name}",
        )

archive_digest = sha256(archive_file.read_bytes()).hexdigest()
print("Day 2 发布构建通过")
print(f"发布目录：{staging_directory}")
print(f"发布压缩包：{archive_file}")
print(f"脚本 SHA-256：{script_digest}")
print(f"压缩包 SHA-256：{archive_digest}")
print("部署冒烟测试：通过")
