"""Day 2 端到端验收：从模拟输入到标准化、脱敏和检索输出。"""

from pathlib import Path
import subprocess
import sys


SOLUTION = Path(__file__).parents[1] / "solution" / "text_cleaner.py"


def run_cleaner(input_lines: list[str]) -> subprocess.CompletedProcess[str]:
    """启动真实 CLI 进程，模拟用户逐行输入并捕获完整输出。"""

    return subprocess.run(
        [sys.executable, str(SOLUTION)],
        input="\n".join(input_lines) + "\n",
        text=True,
        capture_output=True,
        check=False,
    )


# 场景一覆盖员工编号、空白、部门别名、英文大小写、精确脱敏和检索。
sensitive_demo = "DEMO-13800000000"
normal_result = run_cleaner(
    [
        " e 10086 ",
        "  客户服务中心  ",
        " ai support engineer ",
        f"  Customer reports   ORDER-A100，手机号 {sensitive_demo}，请查询 order 状态。 ",
        sensitive_demo,
        "ORDER",
    ]
)

assert normal_result.returncode == 0, normal_result.stderr
assert "员工编号        ：E10086" in normal_result.stdout
assert "客户服务部 / Ai Support Engineer" in normal_result.stdout
assert "Customer reports ORDER-A100" in normal_result.stdout
assert sensitive_demo not in normal_result.stdout, "模拟敏感片段泄漏到输出"
assert "[已脱敏]" in normal_result.stdout
assert "检索词          ：order" in normal_result.stdout
assert "命中次数        ：2" in normal_result.stdout
assert "首次命中索引    ：17" in normal_result.stdout
assert "治理状态：模拟敏感片段已替换" in normal_result.stdout

# 场景二验证短字符串切片安全、Tab 清理、部门简称和关键词未命中语义。
edge_result = run_cleaner(
    [
        "e20002",
        "\t客服部\t",
        "客服专员",
        "  查件  ",
        "不存在的模拟片段",
        "退款",
    ]
)

assert edge_result.returncode == 0, edge_result.stderr
assert "员工编号        ：E20002" in edge_result.stdout
assert "客户服务部 / 客服专员" in edge_result.stdout
assert "清洗后工作描述  ：查件" in edge_result.stdout
assert "30 字符预览     ：查件" in edge_result.stdout
assert "首字符 / 尾字符 ：查 / 件" in edge_result.stdout
assert "命中次数        ：0" in edge_result.stdout
assert "首次命中索引    ：-1" in edge_result.stdout

print("Day 2 端到端验收通过：标准化、脱敏、检索、切片和边界场景均正确。")
