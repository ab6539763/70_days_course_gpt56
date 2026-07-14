"""Day 3 全流程测试：校验、重试、治理、菜单和安全退出。"""

from pathlib import Path
import subprocess
import sys


SOLUTION = Path(__file__).parents[1] / "solution" / "validated_cleaner.py"


def run_cli(lines: list[str]) -> subprocess.CompletedProcess[str]:
    """用独立进程模拟完整终端会话。"""

    return subprocess.run(
        [sys.executable, str(SOLUTION)],
        input="\n".join(lines) + "\n",
        text=True,
        capture_output=True,
        check=False,
    )


secret = "DEMO-CONTACT-10086"
retry_result = run_cli(
    [
        "",                 # 员工编号：空
        "A10086",           # 员工编号：前缀错误
        " e 10086 ",        # 第三次有效
        "宇宙部",            # 部门：不在白名单
        "客服部",            # 部门别名
        "",                 # 岗位：空
        "support agent",
        "",                 # 工作描述：空
        f"  Handle   ORDER-7 and contact {secret}，then check order. ",
        "abc",              # 工单：非数字
        "0",                # 工单：越界
        "240",
        "20..5",            # 提效：格式错误
        "120",              # 提效：越界
        "20",
        "",                 # 敏感片段：空
        "DEMO-NOT-FOUND",   # 敏感片段：不存在
        secret,
        "",                 # 检索词：空
        "ORDER",
        "9",                # 菜单：非法
        "1",
        "2",
        "0",
    ]
)

assert retry_result.returncode == 0, retry_result.stderr
assert "员工编号不能为空" in retry_result.stdout
assert "员工编号必须以 E 开头" in retry_result.stdout
assert "员工编号校验通过" in retry_result.stdout
assert "部门不在当前试点白名单" in retry_result.stdout
assert "岗位不能为空" in retry_result.stdout
assert "工作描述不能为空" in retry_result.stdout
assert "工单量必须是正整数数字" in retry_result.stdout
assert "工单量必须在 1 到 10000 之间" in retry_result.stdout
assert "提效比例必须是数字" in retry_result.stdout
assert "提效比例必须在 0 到 100 之间" in retry_result.stdout
assert "模拟敏感片段不能为空" in retry_result.stdout
assert "任务中未找到该模拟片段" in retry_result.stdout
assert "检索词不能为空" in retry_result.stdout
assert secret not in retry_result.stdout, "模拟敏感片段泄漏到终端输出"
assert "员工编号        ：E10086" in retry_result.stdout
assert "客户服务部 / Support Agent" in retry_result.stdout
assert "Handle ORDER-7 and contact [已脱敏]" in retry_result.stdout
assert "预计辅助工单    ：48" in retry_result.stdout
assert "关键词命中      ：2" in retry_result.stdout
assert "存在关键词      ：True" in retry_result.stdout
assert "需要人工复核    ：False" in retry_result.stdout
assert "菜单错误：仅支持 0、1、2" in retry_result.stdout
assert "身份摘要：E10086｜客户服务部｜Support Agent" in retry_result.stdout
assert "检索诊断：命中 2 次" in retry_result.stdout
assert "已安全退出；本次模拟数据未持久化" in retry_result.stdout

# 关键词未命中或极高提效目标会进入人工复核路径。
review_result = run_cli(
    [
        "E20002",
        "财务部",
        "analyst",
        "复核 CASE-8，模拟凭据 DEMO-SECRET",
        "100",
        "85",
        "DEMO-SECRET",
        "退款",
        "2",
        "0",
    ]
)
assert review_result.returncode == 0, review_result.stderr
assert "关键词命中      ：0" in review_result.stdout
assert "首次命中索引    ：-1" in review_result.stdout
assert "存在关键词      ：False" in review_result.stdout
assert "需要人工复核    ：True" in review_result.stdout
assert "未命中，建议人工复核" in review_result.stdout
assert "DEMO-SECRET" not in review_result.stdout

# 连续三次员工编号失败必须以明确状态码退出，不能继续采集其他资料。
locked_result = run_cli(["", "A1", "E"])
assert locked_result.returncode == 2
assert locked_result.stdout.count("校验失败：") == 3
assert "连续三次无效" in locked_result.stdout
assert "部门（" not in locked_result.stdout

print("Day 3 全流程验收通过：重试、边界、人工复核、菜单和安全退出均正确。")
