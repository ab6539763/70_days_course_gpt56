"""Day 1 验收脚本。

学员此时还不需要掌握自动化测试语法。讲师运行本文件，用真实结果说明：
“验收标准”可以被转换为机器可重复执行的检查。Day 6 学习函数、Day 10
学习模块与异常后，学员会把当前脚本重构成标准单元测试。
"""

from pathlib import Path
import subprocess
import sys


# 根据当前测试文件的位置计算参考实现路径，避免依赖操作者所在目录。
solution_file = Path(__file__).parents[1] / "solution" / "profile_card.py"

# 每一行对应一次 input。最后的换行模拟用户按下回车。
simulated_input = "\n".join(
    [
        "E10086",
        "张伟",
        "客户服务部",
        "客服专员",
        "3",
        "240",
        "20",
        "是",
    ]
) + "\n"

# 使用当前 Python 解释器启动程序，并一次性传入模拟输入。
# capture_output=True 会保留终端输出，方便下面依据验收标准检查。
result = subprocess.run(
    [sys.executable, str(solution_file)],
    input=simulated_input,
    text=True,
    capture_output=True,
    check=False,
)

# 使用 assert 表达最小验收标准。条件不满足时，脚本立即失败并显示原因。
assert result.returncode == 0, f"程序异常退出：{result.stderr}"
assert "E10086" in result.stdout, "卡片中缺少员工编号"
assert "张伟" in result.stdout, "卡片中缺少姓名"
assert "客户服务部 / 客服专员" in result.stdout, "部门与岗位展示不正确"
assert "48 单/月" in result.stdout, "预计辅助工单计算错误：240 × 20% 应为 48"
assert "试点意愿      ：True" in result.stdout, "试点意愿未转换为布尔值"

print("Day 1 验收通过：核心字段、业务计算和试点标记均符合要求。")
