"""Day 2 课件、功能与发布链路质量门禁。"""

from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
LESSON = ROOT / "course/day02/day02-lesson.md"
FUNCTION_TEST = ROOT / "course/day02/tests/test_text_cleaner.py"
RELEASE_TEST = ROOT / "course/day02/tests/test_release.py"
MINIMUM_CHARACTERS = 30_000
MINIMUM_DIAGRAMS = 7
REQUIRED_CONTENT = [
    "开场旁白",
    "企业需求文档",
    "验收标准",
    "非功能要求",
    "架构设计与数据流",
    "运算符课堂笔记",
    "字符串索引与切片课堂笔记",
    "课堂实操",
    "测试策略与全链路验收",
    "构建、部署与回滚演练",
    "安全与隐私评审",
    "团队协作模拟",
    "课后作业",
    "课后作业完整参考答案",
    "讲师逐字稿",
    "复盘与次日衔接",
]


def fail(message: str) -> None:
    """用清晰原因终止门禁，便于课程维护者直接定位。"""

    raise SystemExit(f"Day 2 质量门禁失败：{message}")


if not LESSON.is_file():
    fail("课件文件不存在")

content = LESSON.read_text(encoding="utf-8")
if len(content) < MINIMUM_CHARACTERS:
    fail(f"课件只有 {len(content)} 字符，要求至少 {MINIMUM_CHARACTERS}")

missing = [title for title in REQUIRED_CONTENT if title not in content]
if missing:
    fail(f"缺少必备内容：{', '.join(missing)}")

diagram_count = content.count("```mermaid")
if diagram_count < MINIMUM_DIAGRAMS:
    fail(f"Mermaid 图只有 {diagram_count} 个，要求至少 {MINIMUM_DIAGRAMS}")

for test_file in [FUNCTION_TEST, RELEASE_TEST]:
    result = subprocess.run(
        [sys.executable, str(test_file)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        fail(f"{test_file.name} 未通过：\n{result.stdout}{result.stderr}")

print(
    "Day 2 质量门禁通过："
    f"{len(content)} 字符，{diagram_count} 个 Mermaid 图，"
    f"{len(REQUIRED_CONTENT)} 项必备内容，"
    "功能端到端与发布链路测试通过。"
)
