"""Day 1 参考实现：智枢员工信息卡片。

运行方式：
    python course/day01/solution/profile_card.py

Day 1 只使用零基础学员已经接触的变量、基础数据类型、输入和输出。
条件判断、函数、字典与文件持久化会在后续课程中逐步引入，因此本文件
不提前堆叠语法。企业项目也应遵循“在满足验收标准的前提下保持简单”。
"""


# 产品名称属于在程序运行期间不会变化的信息。全大写命名用于表达常量语义；
# Python 不会强制常量不可修改，但清晰的命名能帮助团队理解代码意图。
PRODUCT_NAME = "智枢 NexusAI"
CARD_WIDTH = 52

# 先输出启动区域，让用户知道正在使用什么系统、下一步应该做什么。
print("=" * CARD_WIDTH)
print(f"{PRODUCT_NAME}｜员工身份卡初始化")
print("=" * CARD_WIDTH)
print("请根据提示录入资料。当前版本仅在本次运行中使用这些信息。\n")

# input 的返回值永远是 str。strip 会去掉输入首尾误按的空格，
# 避免卡片中出现“  张伟  ”这样的脏数据。
employee_id = input("员工编号（示例 E10086）：").strip()
name = input("姓名：").strip()
department = input("部门：").strip()
job_title = input("岗位：").strip()

# 工龄需要进行加减运算，因此转换为 int。零基础阶段先假定用户输入整数；
# Day 3 学完条件判断、Day 10 学完异常处理后，会补齐健壮性校验。
years_of_service = int(input("工龄（整数年）：").strip())

# 月均工单量也用 int 保存，方便计算智能体上线后的效率指标。
monthly_ticket_count = int(input("当前月均处理工单数：").strip())

# 目标提效比例用 float 表示，因为用户可能输入 15.5 这样的数值。
target_efficiency_percent = float(input("期望提效比例（%，示例 20）：").strip())

# bool 只有 True 和 False 两种值。Day 1 使用一个简单的相等比较产生布尔值，
# Day 3 将学习怎样通过条件判断处理“是/否/yes/no”等更多输入。
pilot_owner_text = input("是否愿意成为试点用户（是/否）：").strip()
is_pilot_owner = pilot_owner_text == "是"

# 根据业务口径估算 Agent 每月可协助处理的工单量。
# 除法 / 的结果是 float；int 把展示结果向零取整，便于形成整数工单目标。
estimated_assisted_tickets = int(
    monthly_ticket_count * target_efficiency_percent / 100
)

# f-string 让标签、变量和格式控制写在一起。:.1f 表示保留一位小数。
print("\n" + "=" * CARD_WIDTH)
print(f"{PRODUCT_NAME}｜员工信息卡")
print("-" * CARD_WIDTH)
print(f"员工编号      ：{employee_id}")
print(f"姓名          ：{name}")
print(f"部门 / 岗位   ：{department} / {job_title}")
print(f"工龄          ：{years_of_service} 年")
print(f"月均工单量    ：{monthly_ticket_count} 单")
print(f"期望提效比例  ：{target_efficiency_percent:.1f}%")
print(f"预计辅助工单  ：{estimated_assisted_tickets} 单/月")
print(f"试点意愿      ：{is_pilot_owner}")
print("-" * CARD_WIDTH)
print("资料已在内存中创建；退出程序后不会保留。")
print("Day 5 将使用字典和 JSON 保存它，Day 24 将迁移到数据库。")
print("=" * CARD_WIDTH)
