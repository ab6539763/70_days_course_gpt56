"""构建并验证 NexusAI 0.0.7 联系人目录发布包。"""

from argparse import ArgumentParser
from hashlib import sha256
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile


ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "course/day07/solution/contact_directory.py"
NAME = "nexus-contact-directory-0.0.7"

parser = ArgumentParser(description="构建 Day 7 联系人目录")
parser.add_argument("--output", type=Path, default=ROOT / "artifacts/day07")
args = parser.parse_args()
output = args.output.resolve()
stage = output / NAME
archive_path = output / f"{NAME}.zip"

if stage.exists():
    shutil.rmtree(stage)
stage.mkdir(parents=True, exist_ok=True)
script = stage / "contact_directory.py"
shutil.copy2(SOURCE, script)
(stage / "README.txt").write_text(
    "智枢 NexusAI 企业联系人目录 0.0.7\n"
    "要求：Python 3.10+\n"
    "运行：python3 contact_directory.py\n"
    "仅允许模拟联系人和 .test 邮箱；发布包不包含运行数据。\n",
    encoding="utf-8",
)
script_hash = sha256(script.read_bytes()).hexdigest()
(stage / "SHA256SUMS").write_text(
    f"{script_hash}  contact_directory.py\n",
    encoding="utf-8",
)

first = subprocess.run(
    [sys.executable, str(script)],
    cwd=stage,
    input="\n".join(
        [
            "E70007", "技术部",
            "1", "C1", "演示联系人", "产品部", "产品经理",
            "demo@example.test", "product, agent",
            "0",
        ]
    )
    + "\n",
    text=True,
    capture_output=True,
    check=False,
)
second = subprocess.run(
    [sys.executable, str(script)],
    cwd=stage,
    input="3\nagent\n6\n0\n",
    text=True,
    capture_output=True,
    check=False,
)
if first.returncode != 0 or second.returncode != 0:
    raise SystemExit("联系人目录双进程冒烟失败")
if "恢复成功：revision=2，联系人 1 名" not in second.stdout:
    raise SystemExit("联系人恢复冒烟失败")
if "搜索结果：1 名" not in second.stdout:
    raise SystemExit("联系人搜索冒烟失败")

(stage / "nexus_contacts.json").unlink()
expected = {"contact_directory.py", "README.txt", "SHA256SUMS"}
if {path.name for path in stage.iterdir()} != expected:
    raise SystemExit("发布文件白名单失败")

output.mkdir(parents=True, exist_ok=True)
if archive_path.exists():
    archive_path.unlink()
with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as archive:
    for path in sorted(stage.iterdir()):
        archive.write(path, arcname=f"{NAME}/{path.name}")

archive_hash = sha256(archive_path.read_bytes()).hexdigest()
print("Day 7 发布构建通过")
print(f"发布压缩包：{archive_path}")
print(f"脚本 SHA-256：{script_hash}")
print(f"压缩包 SHA-256：{archive_hash}")
print("联系人双进程搜索冒烟：通过")
print("运行数据未进入制品：通过")
