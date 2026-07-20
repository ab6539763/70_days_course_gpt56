"""Day 14 Phase1 多轮对话助手、结构化日志与发布质量门禁。"""

from pathlib import Path
import re
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
LESSON = ROOT / "course/day14/day14-lesson.md"
TESTS = [
    ROOT / "course/day14/tests/test_logging.py",
    ROOT / "course/day14/tests/test_chat.py",
    ROOT / "course/day14/tests/test_dotenv.py",
    ROOT / "course/day14/tests/test_decorators.py",
    ROOT / "course/day14/tests/test_generators.py",
    ROOT / "course/day14/tests/test_api.py",
    ROOT / "course/day14/tests/test_documents.py",
    ROOT / "course/day14/tests/test_cli.py",
    ROOT / "course/day14/tests/test_release.py",
]
FIXTURES = ROOT / "course/day14/fixtures/corpus"
MINIMUM_CHARACTERS = 30_000
MINIMUM_DIAGRAMS = 9
REQUIRED = [
    "开场旁白",
    "企业需求文档",
    "验收标准",
    "结构化日志",
    "trace_id",
    "多轮对话",
    "slash 命令",
    "会话持久化",
    "异常处理",
    "Phase1 阶段总结",
    "课堂实操",
    "单元测试策略",
    "CLI 全链路",
    "发布部署",
    "安全与工程边界",
    "课后作业",
    "作业完整参考答案",
    "讲师逐字稿",
    "多轮对话实验室",
    "日志安全评审",
    "复盘与 Day 15",
]
HISTORICAL = [
    ROOT / "tools/verify_day01.py",
    ROOT / "tools/verify_day02.py",
    ROOT / "tools/verify_day03.py",
    ROOT / "tools/verify_day04.py",
    ROOT / "tools/verify_day05.py",
    ROOT / "tools/verify_day06.py",
    ROOT / "tools/verify_day07.py",
    ROOT / "tools/verify_day08.py",
    ROOT / "tools/verify_day09.py",
    ROOT / "tools/verify_day10.py",
    ROOT / "tools/verify_day11.py",
    ROOT / "tools/verify_day12.py",
    ROOT / "tools/verify_day13.py",
]
PACKAGE_FILES = [
    ROOT / "course/day14/solution/nexus/observability/logging.py",
    ROOT / "course/day14/solution/nexus/cli/chat_assistant.py",
    ROOT / "course/day14/solution/nexus/platform/state.py",
    ROOT / "course/day14/solution/nexus/http/client.py",
    ROOT / "course/day14/solution/nexus/persistence/storage.py",
    ROOT / "course/day14/solution/.env.example",
    ROOT / "course/day14/solution/requirements.txt",
    ROOT / "course/day14/solution/main.py",
]


def fail(message):
    raise SystemExit(f"Day 14 质量门禁失败：{message}")


if not FIXTURES.exists():
    fail("缺少 fixtures/corpus")
if not (ROOT / "course/day14/solution/.env.example").exists():
    fail("缺少 .env.example")

content = LESSON.read_text(encoding="utf-8")
if len(content) < MINIMUM_CHARACTERS:
    fail(f"课件只有 {len(content)} 字符，要求至少 {MINIMUM_CHARACTERS}")
mermaid_blocks = re.findall(
    r"```mermaid\s*\n(.*?)```",
    content,
    flags=re.DOTALL,
)
for block in mermaid_blocks:
    if re.search(r"\b\w+\[[^\"\n\]]*=\[\]", block):
        fail("Mermaid 节点标签包含未加引号的空列表，会与节点方括号冲突")
missing = [item for item in REQUIRED if item not in content]
if missing:
    fail(f"缺少内容：{', '.join(missing)}")
diagrams = content.count("```mermaid")
if diagrams < MINIMUM_DIAGRAMS:
    fail(f"Mermaid 图只有 {diagrams} 个，要求至少 {MINIMUM_DIAGRAMS}")
req_text = (ROOT / "course/day14/solution/requirements.txt").read_text(encoding="utf-8")
if "python-dotenv>=" not in req_text:
    fail("requirements.txt 缺少 python-dotenv")
if "requests>=" not in req_text:
    fail("requirements.txt 缺少 requests")
version = (ROOT / "course/day14/solution/nexus/constants.py").read_text(encoding="utf-8")
if 'APP_VERSION = "0.0.14"' not in version:
    fail("APP_VERSION 必须为 0.0.14")
for path in PACKAGE_FILES:
    if not path.exists():
        fail(f"缺少包文件：{path}")
for test in TESTS:
    result = subprocess.run(
        [sys.executable, str(test)], cwd=ROOT,
        text=True, capture_output=True, check=False,
    )
    if result.returncode != 0:
        fail(f"{test.name} 失败：\n{result.stdout}{result.stderr}")
for gate in HISTORICAL:
    result = subprocess.run(
        [sys.executable, str(gate)], cwd=ROOT,
        text=True, capture_output=True, check=False,
    )
    if result.returncode != 0:
        fail(f"历史回归 {gate.name} 失败：\n{result.stdout}{result.stderr}")
print(
    f"Day 14 质量门禁通过：{len(content)} 字符，{diagrams} 个 Mermaid 图，"
    f"{len(REQUIRED)} 项必备内容，多轮助手、日志、CLI、部署与 Day1-13 回归均通过。"
)
