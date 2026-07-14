"""验证 Day 1 课件的结构、篇幅与可运行代码。

该脚本只使用 Python 标准库，可在仓库根目录执行：
    python3 tools/verify_day01.py

它不是对教学质量的唯一判断，但能防止后续编辑意外删除关键交付项。
"""

from pathlib import Path
import subprocess
import sys


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
LESSON_FILE = REPOSITORY_ROOT / "course/day01/day01-lesson.md"
ACCEPTANCE_FILE = REPOSITORY_ROOT / "course/day01/tests/test_profile_card.py"

# 用户要求每一天课件不少于 30,000 字。Markdown 中的中文、英文、代码、
# 标点和图表都是实际授课内容，因此按 Unicode 字符总数校验。
MINIMUM_CHARACTER_COUNT = 30_000
MINIMUM_MERMAID_DIAGRAMS = 6

# 这些标题对应每天课件必须具备的教学组成，不允许后续维护时静默丢失。
REQUIRED_CONTENT = [
    "开场旁白",
    "企业需求文档",
    "验收标准",
    "非功能要求",
    "架构",
    "课堂笔记",
    "课堂实操",
    "测试与验收",
    "Git 与团队协作",
    "讲师逐字稿",
    "课后作业",
    "课后作业完整参考答案",
    "复盘与次日衔接",
]


def fail(message: str) -> None:
    """输出可操作的失败原因并使用非零状态结束。"""

    raise SystemExit(f"Day 1 质量门禁失败：{message}")


if not LESSON_FILE.is_file():
    fail(f"找不到课件文件 {LESSON_FILE.relative_to(REPOSITORY_ROOT)}")

lesson = LESSON_FILE.read_text(encoding="utf-8")
character_count = len(lesson)
if character_count < MINIMUM_CHARACTER_COUNT:
    fail(
        f"课件只有 {character_count} 个字符，"
        f"低于 {MINIMUM_CHARACTER_COUNT} 个字符"
    )

missing_content = [item for item in REQUIRED_CONTENT if item not in lesson]
if missing_content:
    fail(f"缺少必备内容：{', '.join(missing_content)}")

diagram_count = lesson.count("```mermaid")
if diagram_count < MINIMUM_MERMAID_DIAGRAMS:
    fail(
        f"只有 {diagram_count} 个 Mermaid 图，"
        f"至少需要 {MINIMUM_MERMAID_DIAGRAMS} 个"
    )

# 使用当前解释器运行验收脚本，避免假设系统命令一定名为 python 或 python3。
acceptance = subprocess.run(
    [sys.executable, str(ACCEPTANCE_FILE)],
    cwd=REPOSITORY_ROOT,
    text=True,
    capture_output=True,
    check=False,
)
if acceptance.returncode != 0:
    fail(f"参考代码验收未通过：\n{acceptance.stdout}{acceptance.stderr}")

print(
    "Day 1 质量门禁通过："
    f"{character_count} 字符，"
    f"{diagram_count} 个 Mermaid 图，"
    f"{len(REQUIRED_CONTENT)} 项必备内容，"
    "参考代码验收通过。"
)
