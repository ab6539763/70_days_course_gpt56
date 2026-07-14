"""Day 3 参考实现：带校验、重试和操作菜单的文本治理 CLI。

知识边界：if/elif/else、while、for、range、break、continue，以及
Day 1-2 的变量、类型转换、运算符和字符串方法。Day 6 会把重复校验
重构为函数，Day 10 再用异常处理覆盖更复杂的输入转换。
"""


PRODUCT_NAME = "智枢 NexusAI"
VERSION = "0.0.3"
MASK = "[已脱敏]"
WIDTH = 68

print("=" * WIDTH)
print(f"{PRODUCT_NAME} {VERSION}｜可校验文本治理工作台")
print("=" * WIDTH)
print("仅使用模拟数据。输入不落盘、不联网，退出后从内存释放。\n")

# 员工编号最多尝试三次。for + range 适合已知次数的重试策略；
# break 表示校验成功，continue 表示本次无效并进入下一次尝试。
employee_id = ""
for attempt in range(1, 4):
    raw_employee_id = input(f"员工编号（第 {attempt}/3 次）：")
    employee_id = raw_employee_id.strip().upper().replace(" ", "")

    if employee_id == "":
        print("校验失败：员工编号不能为空。")
        continue
    if employee_id[0:1] != "E":
        print("校验失败：员工编号必须以 E 开头。")
        continue
    if len(employee_id) < 2:
        print("校验失败：E 后面必须包含编号。")
        continue

    print("员工编号校验通过。")
    break
else:
    # for 的 else 只在循环没有被 break 时执行，表示三次均失败。
    print("安全退出：员工编号连续三次无效，请联系试点管理员。")
    raise SystemExit(2)

# 部门必须来自试点白名单。当前尚未学习列表，先用清晰的逻辑表达式；
# Day 4/5 会改为集合或字典，使规则更易扩展。
while True:
    raw_department = input("部门（客户服务部/销售部/财务部）：")
    department = " ".join(raw_department.split())
    if department == "客服部" or department == "客户服务中心":
        department = "客户服务部"

    if (
        department == "客户服务部"
        or department == "销售部"
        or department == "财务部"
    ):
        break

    print("校验失败：部门不在当前试点白名单，请重新输入。")

# 岗位和任务描述属于必填自然语言。while 适合次数未知的交互重试。
while True:
    job_title = " ".join(input("岗位：").split()).title()
    if job_title != "":
        break
    print("校验失败：岗位不能为空。")

while True:
    raw_task_description = input("工作描述：")
    task_description = " ".join(raw_task_description.split())
    if task_description != "":
        break
    print("校验失败：工作描述不能为空。")

# Day 10 才学习 try/except。今天先用字符串规则判断能否安全转为整数，
# 避免直接 int("abc") 导致程序退出。
while True:
    ticket_text = input("月均工单量（1-10000 的整数）：").strip()
    if not ticket_text.isdigit():
        print("校验失败：工单量必须是正整数数字。")
        continue

    monthly_ticket_count = int(ticket_text)
    if monthly_ticket_count < 1 or monthly_ticket_count > 10000:
        print("校验失败：工单量必须在 1 到 10000 之间。")
        continue
    break

# 浮点字符串可能只包含一个小数点。删除一个小数点后再判断其余字符，
# 能覆盖 20 和 20.5；负数、多个小数点和科学计数法留到异常处理阶段。
while True:
    efficiency_text = input("目标提效比例（0-100）：").strip()
    if not efficiency_text.replace(".", "", 1).isdigit():
        print("校验失败：提效比例必须是数字。")
        continue

    target_efficiency_percent = float(efficiency_text)
    if target_efficiency_percent < 0 or target_efficiency_percent > 100:
        print("校验失败：提效比例必须在 0 到 100 之间。")
        continue
    break

# 指定片段必须非空且确实存在于清洗后的任务中。这样既修复 Day 2 的
# 空字符串 replace 风险，也避免界面声称“已脱敏”但实际没有匹配。
while True:
    sensitive_fragment = input("任务中需要替换的模拟敏感片段：").strip()
    if sensitive_fragment == "":
        print("校验失败：模拟敏感片段不能为空。")
        continue
    if sensitive_fragment not in task_description:
        print("校验失败：任务中未找到该模拟片段，请核对后重试。")
        continue
    break

task_description = task_description.replace(sensitive_fragment, MASK)
task_description = task_description.replace("密码", "凭据")
task_description = task_description.replace("身份证号", "证件标识")

while True:
    search_keyword = input("检索词：").strip().lower()
    if search_keyword != "":
        break
    print("校验失败：检索词不能为空。")

searchable_task = task_description.lower()
keyword_count = searchable_task.count(search_keyword)
first_keyword_index = searchable_task.find(search_keyword)
task_preview = task_description[:30]
estimated_assisted_tickets = int(
    monthly_ticket_count * target_efficiency_percent / 100
)

# 布尔变量把检索结果转为后续 Agent 可以使用的明确状态。
has_keyword = keyword_count > 0
requires_manual_review = not has_keyword or target_efficiency_percent > 80

print("\n" + "=" * WIDTH)
print(f"{PRODUCT_NAME}｜校验与治理结果")
print("-" * WIDTH)
print(f"员工编号        ：{employee_id}")
print(f"部门 / 岗位     ：{department} / {job_title}")
print(f"清洗后工作描述  ：{task_description}")
print(f"30 字符预览     ：{task_preview}")
print(f"月均工单量      ：{monthly_ticket_count}")
print(f"目标提效比例    ：{target_efficiency_percent:.1f}%")
print(f"预计辅助工单    ：{estimated_assisted_tickets}")
print(f"关键词命中      ：{keyword_count}")
print(f"首次命中索引    ：{first_keyword_index}")
print(f"存在关键词      ：{has_keyword}")
print(f"需要人工复核    ：{requires_manual_review}")
print("-" * WIDTH)
print("全部必填字段校验通过；模拟敏感片段已替换。")

# 菜单循环模拟企业工作台持续接收操作。无效选项不会结束程序；
# 0 明确退出，1 查看摘要，2 查看检索诊断。
while True:
    print("\n操作菜单：1=查看身份摘要，2=查看检索诊断，0=安全退出")
    menu_choice = input("请选择：").strip()

    if menu_choice == "1":
        print(f"身份摘要：{employee_id}｜{department}｜{job_title}")
    elif menu_choice == "2":
        if has_keyword:
            print(
                f"检索诊断：命中 {keyword_count} 次，"
                f"首次位于索引 {first_keyword_index}。"
            )
        else:
            print("检索诊断：未命中，建议人工复核或调整检索词。")
    elif menu_choice == "0":
        print("已安全退出；本次模拟数据未持久化。")
        break
    else:
        print("菜单错误：仅支持 0、1、2，请重新选择。")
