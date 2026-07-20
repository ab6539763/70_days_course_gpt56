"""构建并冒烟验证 NexusAI 0.0.3 可校验治理 CLI 发布包。"""

from argparse import ArgumentParser
from hashlib import sha256
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile


ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "course/day03/solution/validated_cleaner.py"
RELEASE_NAME = "nexus-validated-cleaner-0.0.3"

parser = ArgumentParser(description="构建 Day 3 发布包")
parser.add_argument(
    "--output",
    type=Path,
    default=ROOT / "artifacts/day03",
)
args = parser.parse_args()

output = args.output.resolve()
stage = output / RELEASE_NAME
archive_path = output / f"{RELEASE_NAME}.zip"

if stage.exists():
    shutil.rmtree(stage)
stage.mkdir(parents=True, exist_ok=True)

deployed_script = stage / "validated_cleaner.py"
shutil.copy2(SOURCE, deployed_script)
(stage / "README.txt").write_text(
    "智枢 NexusAI 可校验文本治理工作台 0.0.3\n"
    "要求：Python 3.10+\n"
    "运行：python3 validated_cleaner.py\n"
    "限制：仅用于模拟数据教学，不处理生产个人信息。\n",
    encoding="utf-8",
)

script_hash = sha256(deployed_script.read_bytes()).hexdigest()
(stage / "SHA256SUMS").write_text(
    f"{script_hash}  validated_cleaner.py\n",
    encoding="utf-8",
)

smoke_secret = "SMOKE-DEMO-3"
smoke_input = "\n".join(
    [
        "e30003",
        "销售部",
        "sales specialist",
        f"查询 LEAD-3 并隐藏 {smoke_secret}",
        "80",
        "25",
        smoke_secret,
        "lead",
        "2",
        "0",
    ]
) + "\n"
smoke = subprocess.run(
    [sys.executable, str(deployed_script)],
    cwd=stage,
    input=smoke_input,
    text=True,
    capture_output=True,
    check=False,
)
if smoke.returncode != 0:
    raise SystemExit(f"部署冒烟失败：\n{smoke.stderr}")
if "E30003" not in smoke.stdout or "销售部 / Sales Specialist" not in smoke.stdout:
    raise SystemExit("部署冒烟失败：身份标准化错误")
if smoke_secret in smoke.stdout or "[已脱敏]" not in smoke.stdout:
    raise SystemExit("部署冒烟失败：模拟敏感片段治理错误")
if "已安全退出" not in smoke.stdout:
    raise SystemExit("部署冒烟失败：菜单退出链路未完成")

output.mkdir(parents=True, exist_ok=True)
if archive_path.exists():
    archive_path.unlink()
with zipfile.ZipFile(
    archive_path,
    mode="w",
    compression=zipfile.ZIP_DEFLATED,
) as archive:
    for path in sorted(stage.iterdir()):
        archive.write(path, arcname=f"{RELEASE_NAME}/{path.name}")

archive_hash = sha256(archive_path.read_bytes()).hexdigest()
print("Day 3 发布构建通过")
print(f"发布目录：{stage}")
print(f"发布压缩包：{archive_path}")
print(f"脚本 SHA-256：{script_hash}")
print(f"压缩包 SHA-256：{archive_hash}")
print("部署冒烟测试：通过")
