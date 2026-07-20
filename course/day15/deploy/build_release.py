"""构建并验证 NexusAI 0.0.15 Web 对话工作台发布包。"""

from argparse import ArgumentParser
from hashlib import sha256
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile


ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "course/day15/solution"
FIXTURES = ROOT / "course/day15/fixtures/corpus"
NAME = "nexus-web-workbench-0.0.15"
WHITELIST = {"main.py", "requirements.txt", "README.txt", "SHA256SUMS", "nexus", "corpus", ".env.example"}
parser = ArgumentParser()
parser.add_argument("--output", type=Path, default=ROOT / "artifacts/day15")
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
shutil.copy2(SOURCE / ".env.example", stage / ".env.example")
corpus_stage = stage / "corpus"
corpus_stage.mkdir()
shutil.copytree(FIXTURES, corpus_stage, dirs_exist_ok=True)
(stage / "README.txt").write_text(
    "智枢 NexusAI Web 对话工作台 0.0.15\nPython 3.10+\n"
    "依赖：pip install -r requirements.txt\n"
    "配置：cp .env.example .env 并填写 NEXUS_API_KEY\n"
    "CLI：PYTHONPATH=. python3 main.py\n"
    "Web：PYTHONPATH=. python3 main.py --web\n",
    encoding="utf-8",
)
checksum_targets = [stage / "main.py", stage / "requirements.txt"]
lines = []
for target in checksum_targets:
    digest = sha256(target.read_bytes()).hexdigest()
    lines.append(f"{digest}  {target.name}\n")
(stage / "SHA256SUMS").write_text("".join(lines), encoding="utf-8")
env = {**dict(__import__("os").environ), "PYTHONPATH": str(stage), "NEXUS_USE_MOCK": "1"}
web_smoke = subprocess.run(
    [
        sys.executable,
        "-c",
        (
            "from nexus.web.app import create_app; "
            "app=create_app('nexus_platform.json'); "
            "c=app.test_client(); "
            "assert c.get('/api/health').get_json()['ok']; "
            "assert c.post('/api/chat', json={'prompt':'部署'}).get_json()['ok']"
        ),
    ],
    cwd=stage,
    env=env,
    text=True,
    capture_output=True,
    check=False,
)
cli_smoke = subprocess.run(
    [sys.executable, str(stage / "main.py")],
    cwd=stage,
    env=env,
    input="7\n0\n",
    text=True,
    capture_output=True,
    check=False,
)
if web_smoke.returncode != 0 or cli_smoke.returncode != 0 or "schema=4" not in cli_smoke.stdout:
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
print("Day 15 发布构建通过")
print(f"发布压缩包：{archive_path}")
print(f"压缩包 SHA-256：{archive_digest}")
print("Web + CLI 双进程冒烟：通过")
print("运行数据未进入制品：通过")
