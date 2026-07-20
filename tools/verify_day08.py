"""Day 8 面向对象课件、模型、迁移与发布质量门禁。"""

from pathlib import Path
import re
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
LESSON = ROOT / "course/day08/day08-lesson.md"
TESTS = [
    ROOT / "course/day08/tests/test_models.py",
    ROOT / "course/day08/tests/test_cli.py",
    ROOT / "course/day08/tests/test_release.py",
]
MINIMUM_CHARACTERS = 30_000
MINIMUM_DIAGRAMS = 9
REQUIRED = [
    "开场旁白",
    "企业需求文档",
    "验收标准",
    "架构与对象关系",
    "类与对象课堂笔记",
    "ChatMessage 设计",
    "Contact 设计",
    "PlatformState 聚合",
    "Schema 迁移",
    "课堂实操",
    "单元测试策略",
    "CLI 全链路",
    "发布部署",
    "安全与工程边界",
    "课后作业",
    "作业完整参考答案",
    "讲师逐字稿",
    "对象路径覆盖实验室",
    "OOP 设计评审",
    "复盘与 Day 9",
]


def fail(message):
    raise SystemExit(f"Day 8 质量门禁失败：{message}")


content = LESSON.read_text(encoding="utf-8")
if len(content) < MINIMUM_CHARACTERS:
    fail(f"课件只有 {len(content)} 字符，要求至少 {MINIMUM_CHARACTERS}")
# Mermaid 使用 [] 表示节点边界。只扫描 Mermaid 代码块，避免把正文中的
# Python 示例误判；节点标签以引号开头时允许包含 []。
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
for test in TESTS:
    result = subprocess.run(
        [sys.executable, str(test)], cwd=ROOT,
        text=True, capture_output=True, check=False,
    )
    if result.returncode != 0:
        fail(f"{test.name} 失败：\n{result.stdout}{result.stderr}")
print(
    f"Day 8 质量门禁通过：{len(content)} 字符，{diagrams} 个 Mermaid 图，"
    f"{len(REQUIRED)} 项必备内容，对象、迁移、CLI 与部署测试通过。"
)
