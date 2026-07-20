"""构建并验证 NexusAI 0.0.6 函数化任务服务发布包。"""

from argparse import ArgumentParser
from hashlib import sha256
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile


ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "course/day06/solution/functional_task_board.py"
NAME = "nexus-functional-task-board-0.0.6"

parser = ArgumentParser(description="构建 Day 6 函数化任务服务")
parser.add_argument("--output", type=Path, default=ROOT / "artifacts/day06")
args = parser.parse_args()
output = args.output.resolve()
stage = output / NAME
archive_path = output / f"{NAME}.zip"

if stage.exists():
    shutil.rmtree(stage)
stage.mkdir(parents=True, exist_ok=True)
script = stage / "functional_task_board.py"
shutil.copy2(SOURCE, script)
(stage / "README.txt").write_text(
    "智枢 NexusAI 函数化任务服务 0.0.6\n"
    "要求：Python 3.10+\n"
    "运行：python3 functional_task_board.py\n"
    "数据：当前目录 nexus_tasks.json，发布包不携带运行数据。\n",
    encoding="utf-8",
)
script_hash = sha256(script.read_bytes()).hexdigest()
(stage / "SHA256SUMS").write_text(
    f"{script_hash}  functional_task_board.py\n",
    encoding="utf-8",
)

first = subprocess.run(
    [sys.executable, str(script)],
    cwd=stage,
    input="\n".join(
        [
            "E60006", "销售部",
            "1", "T1", "验证函数发布", "1", "function, deploy",
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
    input="5\n0\n",
    text=True,
    capture_output=True,
    check=False,
)
if first.returncode != 0 or second.returncode != 0:
    raise SystemExit("发布双进程冒烟失败")
if "恢复成功：revision=2，任务 1 条" not in second.stdout:
    raise SystemExit("发布恢复冒烟失败")

runtime_data = stage / "nexus_tasks.json"
runtime_data.unlink()
expected = {"functional_task_board.py", "README.txt", "SHA256SUMS"}
if {path.name for path in stage.iterdir()} != expected:
    raise SystemExit("发布文件白名单失败")

output.mkdir(parents=True, exist_ok=True)
if archive_path.exists():
    archive_path.unlink()
with zipfile.ZipFile(
    archive_path,
    "w",
    compression=zipfile.ZIP_DEFLATED,
) as archive:
    for path in sorted(stage.iterdir()):
        archive.write(path, arcname=f"{NAME}/{path.name}")

archive_hash = sha256(archive_path.read_bytes()).hexdigest()
print("Day 6 发布构建通过")
print(f"发布压缩包：{archive_path}")
print(f"脚本 SHA-256：{script_hash}")
print(f"压缩包 SHA-256：{archive_hash}")
print("函数化 CLI 双进程冒烟：通过")
print("运行数据未进入制品：通过")
