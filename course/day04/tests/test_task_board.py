"""Day 4 端到端测试：多任务 CRUD、排序、去重、统计与清理。"""

from pathlib import Path
import subprocess
import sys


SOLUTION = Path(__file__).parents[1] / "solution" / "task_board.py"


def run_board(lines: list[str]) -> subprocess.CompletedProcess[str]:
    """启动真实 CLI 并执行一段完整团队操作会话。"""

    return subprocess.run(
        [sys.executable, str(SOLUTION)],
        input="\n".join(lines) + "\n",
        text=True,
        capture_output=True,
        check=False,
    )


result = run_board(
    [
        "A1", "E40004",             # 身份重试
        "未知部", "客服部",          # 部门重试与别名
        "2",                        # 空列表查看
        "3",                        # 空列表完成
        "4",                        # 空列表删除
        "1",                        # 新增 T2
        "", "A2", "t 2",           # 编号空、前缀错、有效
        "", "编写 RAG 评估报告",     # 标题空后有效
        "x", "0", "2",             # 优先级格式、范围、有效
        "rag, urgent, RAG, ,",
        "1",                        # 新增 T1，先触发重复 T2
        "T2", "T1",
        "设计 Agent 审批流程",
        "1",
        "agent, urgent",
        "1",                        # 新增 T3
        "T3",
        "整理会议纪要",
        "5",
        "",
        "2",                        # 排序和前三条预览
        "3", "T9",                  # 完成不存在
        "3", "T2",                  # 完成 T2
        "3", "T2",                  # 重复完成
        "5",                        # 三条任务统计
        "4", "T9",                  # 删除不存在
        "4", "T1",                  # 删除 T1
        "5",                        # 两条任务统计
        "6",                        # 清理已完成 T2
        "1",                        # T2 编号应可重新使用
        "T2",
        "重新评审 RAG 报告",
        "3",
        "",
        "2",
        "9",                        # 非法菜单
        "0",
    ]
)

assert result.returncode == 0, result.stderr
assert "员工编号必须以 E 开头" in result.stdout
assert "部门必须是 客户服务部 / 销售部 / 财务部" in result.stdout
assert "当前没有任务" in result.stdout
assert "完成失败：当前没有任务" in result.stdout
assert "删除失败：当前没有任务" in result.stdout
assert "任务编号不能为空" in result.stdout
assert "任务编号必须以 T 开头" in result.stdout
assert "任务编号已存在" in result.stdout
assert "任务标题不能为空" in result.stdout
assert "优先级必须是 1-5 的整数" in result.stdout
assert "优先级必须在 1-5 之间" in result.stdout
assert "标签 ('rag', 'urgent')" in result.stdout
assert result.stdout.index("P1 T1") < result.stdout.index("P2 T2")
assert "首页预览：['T1', 'T2', 'T3']" in result.stdout
assert "完成失败：未找到任务 T9" in result.stdout
assert "完成成功：T2" in result.stdout
assert "状态未变：T2 已经完成" in result.stdout
assert "总数：3" in result.stdout
assert "进行中：2" in result.stdout
assert "已完成：1" in result.stdout
assert "高优先级进行中：1" in result.stdout
assert "唯一标签：['agent', 'rag', 'urgent']" in result.stdout
assert "删除失败：未找到任务 T9" in result.stdout
assert "删除成功：T1｜设计 Agent 审批流程" in result.stdout
assert "清理完成：移除 1 条已完成任务" in result.stdout
assert "新增成功：T2｜P3｜重新评审 RAG 报告" in result.stdout
assert "菜单错误：仅支持 0-6" in result.stdout
assert "内存中剩余 2 条任务，均未持久化" in result.stdout

# 三次身份失败沿用 Day 3 的安全退出契约。
locked = run_board(["", "A1", "E"])
assert locked.returncode == 2
assert "连续三次无效" in locked.stdout
assert "部门：" not in locked.stdout
assert "操作菜单" not in locked.stdout

print("Day 4 端到端验收通过：CRUD、排序、去重、统计、清理和锁定均正确。")
