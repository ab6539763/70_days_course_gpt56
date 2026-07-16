"""Day 11 语料处理、pathlib 与发布质量门禁。"""

from pathlib import Path
import re
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
LESSON = ROOT / "course/day11/day11-lesson.md"
TESTS = [
    ROOT / "course/day11/tests/test_documents.py",
    ROOT / "course/day11/tests/test_cli.py",
    ROOT / "course/day11/tests/test_release.py",
]
FIXTURES = ROOT / "course/day11/fixtures/corpus"
MINIMUM_CHARACTERS = 30_000
MINIMUM_DIAGRAMS = 9
REQUIRED = [
    "开场旁白",
    "企业需求文档",
    "验收标准",
    "pathlib 与文件发现",
    "UTF-8 与 with 上下文",
    "正则关键词统计",
    "语料模块设计",
    "Schema 迁移",
    "课堂实操",
    "单元测试策略",
    "CLI 全链路",
    "发布部署",
    "安全与工程边界",
    "课后作业",
    "作业完整参考答案",
    "讲师逐字稿",
    "语料路径覆盖实验室",
    "RAG 前置评审",
    "复盘与 Day 12",
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
]
PACKAGE_FILES = [
    ROOT / "course/day11/solution/nexus/documents/loader.py",
    ROOT / "course/day11/solution/nexus/documents/keywords.py",
    ROOT / "course/day11/solution/nexus/documents/corpus.py",
    ROOT / "course/day11/solution/nexus/platform/state.py",
    ROOT / "course/day11/solution/main.py",
]


def fail(message):
    raise SystemExit(f"Day 11 质量门禁失败：{message}")


if not FIXTURES.exists():
    fail("缺少 fixtures/corpus 示例语料")
for sample in ("policy.txt", "faq.md", "contacts.csv", "meta.json"):
    if not (FIXTURES / sample).exists():
        fail(f"缺少语料样例：{sample}")

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
    f"Day 11 质量门禁通过：{len(content)} 字符，{diagrams} 个 Mermaid 图，"
    f"{len(REQUIRED)} 项必备内容，语料、迁移、CLI、部署与 Day1-10 回归均通过。"
)
