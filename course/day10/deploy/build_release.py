"""构建并验证 NexusAI 0.0.10 模块化平台发布包。"""

from argparse import ArgumentParser
from hashlib import sha256
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile


ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "course/day10/solution"
NAME = "nexus-modular-platform-0.0.10"
WHITELIST = {"main.py", "requirements.txt", "README.txt", "SHA256SUMS", "nexus"}
parser = ArgumentParser()
parser.add_argument("--output", type=Path, default=ROOT / "artifacts/day10")
args = parser.parse_args()
output = args.output.resolve()
stage = output / NAME
archive_path = output / f"{NAME}.zip"
if stage.exists():
    shutil.rmtree(stage)
stage.mkdir(parents=True)
shutil.copytree(
    SOURCE / "nexus",
    stage / "nexus",
    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
)
shutil.copy2(SOURCE / "main.py", stage / "main.py")
shutil.copy2(SOURCE / "requirements.txt", stage / "requirements.txt")
(stage / "README.txt").write_text(
    "智枢 NexusAI 模块化平台 0.0.10\nPython 3.10+\n"
    "运行：PYTHONPATH=. python3 main.py\n"
    "或：PYTHONPATH=. python3 -m nexus\n发布包不含运行数据。\n",
    encoding="utf-8",
)
checksum_targets = [stage / "main.py", stage / "requirements.txt"]
lines = []
for target in checksum_targets:
    digest = sha256(target.read_bytes()).hexdigest()
    lines.append(f"{digest}  {target.name}\n")
(stage / "SHA256SUMS").write_text("".join(lines), encoding="utf-8")
env = {**dict(**__import__("os").environ), "PYTHONPATH": str(stage)}
first = subprocess.run(
    [sys.executable, str(stage / "main.py")],
    cwd=stage,
    env=env,
    input="E10\n技术部\n4\nuser\n部署冒烟\n9\n部署冒烟问题\n0\n",
    text=True,
    capture_output=True,
    check=False,
)
second = subprocess.run(
    [sys.executable, str(stage / "main.py")],
    cwd=stage,
    env=env,
    input="7\n0\n",
    text=True,
    capture_output=True,
    check=False,
)
if first.returncode != 0 or "schema=3" not in second.stdout:
    raise SystemExit("部署双进程冒烟失败")
json_path = stage / "nexus_platform.json"
if json_path.exists():
    json_path.unlink()
for cache_dir in stage.rglob("__pycache__"):
    shutil.rmtree(cache_dir)
if {p.name for p in stage.iterdir()} != WHITELIST:
    raise SystemExit("发布白名单失败")
output.mkdir(parents=True, exist_ok=True)
with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as archive:
    for path in sorted(stage.rglob("*")):
        if path.is_file():
            archive.write(path, arcname=f"{NAME}/{path.relative_to(stage)}")
archive_digest = sha256(archive_path.read_bytes()).hexdigest()
print("Day 10 发布构建通过")
print(f"发布压缩包：{archive_path}")
print(f"压缩包 SHA-256：{archive_digest}")
print("模块化双进程冒烟：通过")
print("运行数据未进入制品：通过")
