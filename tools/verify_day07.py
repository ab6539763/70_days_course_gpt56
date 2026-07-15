"""Day 7 阶段项目课件、周测、联系人服务与发布质量门禁。"""

from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
LESSON = ROOT / "course/day07/day07-lesson.md"
TESTS = [
    ROOT / "course/day07/tests/test_functions.py",
    ROOT / "course/day07/tests/test_cli.py",
    ROOT / "course/day07/tests/test_release.py",
]
MINIMUM_CHARACTERS = 30_000
MINIMUM_DIAGRAMS = 9
REQUIRED = [
    "开场旁白",
    "企业需求文档",
    "验收标准",
    "非功能要求",
    "架构设计",
    "第一周知识复习课堂笔记",
    "联系人核心函数解读",
    "周测笔试题",
    "周测答案与评分标准",
    "函数单测策略",
    "CLI 全链路测试",
    "发布、部署与回滚",
    "安全与隐私评审",
    "项目管理与团队协作",
    "常见错误与排障",
    "阶段项目路径覆盖实验室",
    "课后作业",
    "课后作业完整参考答案",
    "讲师逐字稿",
    "代码评审评分表",
    "第一周综合复盘",
]


def fail(message: str) -> None:
    raise SystemExit(f"Day 7 质量门禁失败：{message}")


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
    "Day 7 质量门禁通过："
    f"{len(content)} 字符，{diagram_count} 个 Mermaid 图，"
    f"{len(REQUIRED)} 项必备内容，"
    "周测、联系人 CRUD/搜索、制品隔离与部署恢复通过。"
)
