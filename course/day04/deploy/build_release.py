"""构建并验证 NexusAI 0.0.4 任务台账发布包。"""

from argparse import ArgumentParser
from hashlib import sha256
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile


ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "course/day04/solution/task_board.py"
RELEASE_NAME = "nexus-task-board-0.0.4"

parser = ArgumentParser(description="构建 Day 4 任务台账发布包")
parser.add_argument(
    "--output",
    type=Path,
    default=ROOT / "artifacts/day04",
)
args = parser.parse_args()
output = args.output.resolve()
stage = output / RELEASE_NAME
archive_path = output / f"{RELEASE_NAME}.zip"

if stage.exists():
    shutil.rmtree(stage)
stage.mkdir(parents=True, exist_ok=True)

script = stage / "task_board.py"
shutil.copy2(SOURCE, script)
(stage / "README.txt").write_text(
    "智枢 NexusAI Agent 试点任务台账 0.0.4\n"
    "要求：Python 3.10+\n"
    "运行：python3 task_board.py\n"
    "说明：只处理模拟任务，退出后内存数据不会保存。\n",
    encoding="utf-8",
)
script_hash = sha256(script.read_bytes()).hexdigest()
(stage / "SHA256SUMS").write_text(
    f"{script_hash}  task_board.py\n",
    encoding="utf-8",
)

smoke_input = "\n".join(
    [
        "E40004",
        "销售部",
        "1", "T2", "整理客户需求", "2", "sales, urgent",
        "1", "T1", "设计 Agent 流程", "1", "agent",
        "2",
        "3", "T2",
        "5",
        "6",
        "0",
    ]
) + "\n"
smoke = subprocess.run(
    [sys.executable, str(script)],
    cwd=stage,
    input=smoke_input,
    text=True,
    capture_output=True,
    check=False,
)
if smoke.returncode != 0:
    raise SystemExit(f"部署冒烟失败：\n{smoke.stderr}")
required_output = [
    "首页预览：['T1', 'T2']",
    "完成成功：T2",
    "唯一标签：['agent', 'sales', 'urgent']",
    "清理完成：移除 1 条已完成任务",
    "内存中剩余 1 条任务",
]
for expected in required_output:
    if expected not in smoke.stdout:
        raise SystemExit(f"部署冒烟失败：缺少输出 {expected}")

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
print("Day 4 发布构建通过")
print(f"发布目录：{stage}")
print(f"发布压缩包：{archive_path}")
print(f"脚本 SHA-256：{script_hash}")
print(f"压缩包 SHA-256：{archive_hash}")
print("部署冒烟测试：通过")
