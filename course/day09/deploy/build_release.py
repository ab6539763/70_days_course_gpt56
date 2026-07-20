"""构建并验证 NexusAI 0.0.9 多供应商模型平台发布包。"""

from argparse import ArgumentParser
from hashlib import sha256
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile


ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "course/day09/solution/model_platform.py"
NAME = "nexus-model-platform-0.0.9"
parser = ArgumentParser()
parser.add_argument("--output", type=Path, default=ROOT / "artifacts/day09")
args = parser.parse_args()
output = args.output.resolve()
stage = output / NAME
archive_path = output / f"{NAME}.zip"
if stage.exists():
    shutil.rmtree(stage)
stage.mkdir(parents=True)
script = stage / "model_platform.py"
shutil.copy2(SOURCE, script)
(stage / "README.txt").write_text(
    "智枢 NexusAI 多供应商模型平台 0.0.9\nPython 3.10+\n"
    "运行：python3 model_platform.py\n发布包不含运行数据。\n",
    encoding="utf-8",
)
digest = sha256(script.read_bytes()).hexdigest()
(stage / "SHA256SUMS").write_text(f"{digest}  model_platform.py\n", encoding="utf-8")
first = subprocess.run(
    [sys.executable, str(script)], cwd=stage,
    input="E9\n技术部\n9\n部署冒烟问题\n0\n",
    text=True, capture_output=True, check=False,
)
second = subprocess.run(
    [sys.executable, str(script)], cwd=stage,
    input="7\n0\n", text=True, capture_output=True, check=False,
)
if first.returncode != 0 or "schema=3" not in second.stdout:
    raise SystemExit("部署双进程冒烟失败")
(stage / "nexus_platform.json").unlink()
if {p.name for p in stage.iterdir()} != {"model_platform.py", "README.txt", "SHA256SUMS"}:
    raise SystemExit("发布白名单失败")
output.mkdir(parents=True, exist_ok=True)
with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as archive:
    for path in sorted(stage.iterdir()):
        archive.write(path, arcname=f"{NAME}/{path.name}")
archive_digest = sha256(archive_path.read_bytes()).hexdigest()
print("Day 9 发布构建通过")
print(f"发布压缩包：{archive_path}")
print(f"脚本 SHA-256：{digest}")
print(f"压缩包 SHA-256：{archive_digest}")
print("模型推理双进程冒烟：通过")
print("运行数据未进入制品：通过")
