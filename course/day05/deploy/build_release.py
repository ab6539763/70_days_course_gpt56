"""构建并验证 NexusAI 0.0.5 JSON 持久化台账发布包。"""

from argparse import ArgumentParser
from hashlib import sha256
from pathlib import Path
import json
import shutil
import subprocess
import sys
import zipfile


ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "course/day05/solution/persistent_task_board.py"
RELEASE_NAME = "nexus-persistent-task-board-0.0.5"
RUNTIME_DATA = "nexus_tasks.json"

parser = ArgumentParser(description="构建 Day 5 持久化任务台账")
parser.add_argument(
    "--output",
    type=Path,
    default=ROOT / "artifacts/day05",
)
args = parser.parse_args()
output = args.output.resolve()
stage = output / RELEASE_NAME
archive_path = output / f"{RELEASE_NAME}.zip"

if stage.exists():
    shutil.rmtree(stage)
stage.mkdir(parents=True, exist_ok=True)

script = stage / "persistent_task_board.py"
shutil.copy2(SOURCE, script)
(stage / "README.txt").write_text(
    "智枢 NexusAI JSON 持久化任务台账 0.0.5\n"
    "要求：Python 3.10+\n"
    "运行：python3 persistent_task_board.py\n"
    "运行数据：当前目录 nexus_tasks.json（首次启动自动创建）\n"
    "发布包不包含任何员工或任务数据，只允许使用模拟资料。\n",
    encoding="utf-8",
)
script_hash = sha256(script.read_bytes()).hexdigest()
(stage / "SHA256SUMS").write_text(
    f"{script_hash}  persistent_task_board.py\n",
    encoding="utf-8",
)

# 首次启动创建身份与任务。
first = subprocess.run(
    [sys.executable, str(script)],
    cwd=stage,
    input="\n".join(
        [
            "E50005",
            "销售部",
            "1", "T1", "部署持久化冒烟", "1", "deploy, json",
            "0",
        ]
    )
    + "\n",
    text=True,
    capture_output=True,
    check=False,
)
if first.returncode != 0 or "已持久化 1 条任务" not in first.stdout:
    raise SystemExit(f"首次部署冒烟失败：\n{first.stdout}{first.stderr}")

# 第二个进程必须恢复同一身份和任务。
second = subprocess.run(
    [sys.executable, str(script)],
    cwd=stage,
    input="5\n7\n0\n",
    text=True,
    capture_output=True,
    check=False,
)
if second.returncode != 0:
    raise SystemExit(f"恢复部署冒烟失败：\n{second.stdout}{second.stderr}")
for expected in ["恢复成功：revision=2，任务 1 条", "总数：1", "task_count：1"]:
    if expected not in second.stdout:
        raise SystemExit(f"恢复部署冒烟失败：缺少 {expected}")

runtime_file = stage / RUNTIME_DATA
runtime_data = json.loads(runtime_file.read_text(encoding="utf-8"))
if runtime_data["tasks"][0]["task_id"] != "T1":
    raise SystemExit("恢复部署冒烟失败：JSON 任务内容错误")

# 冒烟产生的数据是运行时状态，必须在打包前删除，防止试点数据进入制品。
runtime_file.unlink()
expected_stage_files = {
    "persistent_task_board.py",
    "README.txt",
    "SHA256SUMS",
}
actual_stage_files = {path.name for path in stage.iterdir()}
if actual_stage_files != expected_stage_files:
    raise SystemExit(
        f"发布文件白名单失败：{sorted(actual_stage_files)}"
    )

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
print("Day 5 发布构建通过")
print(f"发布目录：{stage}")
print(f"发布压缩包：{archive_path}")
print(f"脚本 SHA-256：{script_hash}")
print(f"压缩包 SHA-256：{archive_hash}")
print("首次启动与跨进程恢复冒烟：通过")
print("运行时 JSON 未进入发布包：通过")
