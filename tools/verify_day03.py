"""Day 3 课件、控制流、发布和部署质量门禁。"""

from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
LESSON = ROOT / "course/day03/day03-lesson.md"
TESTS = [
    ROOT / "course/day03/tests/test_validated_cleaner.py",
    ROOT / "course/day03/tests/test_release.py",
]
MINIMUM_CHARACTERS = 30_000
MINIMUM_DIAGRAMS = 8
REQUIRED = [
    "开场旁白",
    "企业需求文档",
    "验收标准",
    "非功能要求",
    "架构与状态设计",
    "条件判断课堂笔记",
    "while 循环课堂笔记",
    "for、range 与循环 else",
    "课堂实操",
    "测试策略与全方位检测",
    "发布、部署与回滚",
    "安全与可靠性评审",
    "团队协作模拟",
    "课后作业",
    "课后作业完整参考答案",
    "讲师逐字稿",
    "企业故障注入推演",
    "复盘与次日衔接",
]


def fail(message: str) -> None:
    """终止门禁并给出可操作原因。"""

    raise SystemExit(f"Day 3 质量门禁失败：{message}")


if not LESSON.is_file():
    fail("课件不存在")

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
    "Day 3 质量门禁通过："
    f"{len(content)} 字符，{diagram_count} 个 Mermaid 图，"
    f"{len(REQUIRED)} 项必备内容，"
    "控制流、锁定、泄漏、发布与部署测试通过。"
)
