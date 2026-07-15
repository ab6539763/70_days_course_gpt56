"""Day 6 课件、函数契约、CLI 与发布部署质量门禁。"""

from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
LESSON = ROOT / "course/day06/day06-lesson.md"
TESTS = [
    ROOT / "course/day06/tests/test_functions.py",
    ROOT / "course/day06/tests/test_cli.py",
    ROOT / "course/day06/tests/test_release.py",
]
MINIMUM_CHARACTERS = 30_000
MINIMUM_DIAGRAMS = 9
REQUIRED = [
    "开场旁白",
    "企业需求文档",
    "验收标准",
    "非功能要求",
    "架构设计",
    "函数基础课堂笔记",
    "参数课堂笔记",
    "作用域课堂笔记",
    "函数边界与副作用",
    "递归课堂笔记",
    "主入口保护",
    "课堂重构步骤",
    "单元测试设计",
    "CLI 与全链路测试",
    "发布、部署与回滚",
    "安全与工程评审",
    "团队协作模拟",
    "课后作业",
    "课后作业完整参考答案",
    "讲师逐字稿",
    "函数契约与故障注入实验室",
    "重构事故推演",
    "复盘与次日衔接",
]


def fail(message: str) -> None:
    raise SystemExit(f"Day 6 质量门禁失败：{message}")


content = LESSON.read_text(encoding="utf-8")
if len(content) < MINIMUM_CHARACTERS:
    fail(f"课件只有 {len(content)} 字符，要求至少 {MINIMUM_CHARACTERS}")
missing = [item for item in REQUIRED if item not in content]
if missing:
    fail(f"缺少内容：{', '.join(missing)}")
diagram_count = content.count("```mermaid")
if diagram_count < MINIMUM_DIAGRAMS:
    fail(f"Mermaid 图只有 {diagram_count} 个，要求至少 {MINIMUM_DIAGRAMS}")

for test in TESTS:
    result = subprocess.run(
        [sys.executable, str(test)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        fail(f"{test.name} 失败：\n{result.stdout}{result.stderr}")

print(
    "Day 6 质量门禁通过："
    f"{len(content)} 字符，{diagram_count} 个 Mermaid 图，"
    f"{len(REQUIRED)} 项必备内容，"
    "函数单测、CLI、制品隔离与部署恢复通过。"
)
