"""Day 2 参考实现：智枢员工文本清洗与输入治理工作台。

运行方式：
    python3 course/day02/solution/text_cleaner.py

本实现有意限定在 Day 2 的知识边界内：变量、基础类型、运算符、字符串
索引/切片和常用字符串方法。函数、条件判断、正则表达式、JSON 与文件
持久化会在后续课程按业务需求继续重构。
"""


PRODUCT_NAME = "智枢 NexusAI"
CARD_WIDTH = 64
MASK = "[已脱敏]"

print("=" * CARD_WIDTH)
print(f"{PRODUCT_NAME}｜员工文本清洗与输入治理工作台")
print("=" * CARD_WIDTH)
print("本工具只处理模拟文本；请勿输入真实个人敏感信息。\n")

# 员工编号属于标识符而非数值。统一转大写并删除内部空格，
# 让 Day 1 的 “ e10086 ” 与平台标准格式 E10086 对齐。
raw_employee_id = input("员工编号（示例 e10086）：")
employee_id = raw_employee_id.strip().upper().replace(" ", "")

# 先保留原始文本，便于计算清洗前后的质量指标。原始值今天只存在内存，
# 不会在结果中输出，避免把未经治理的内容继续传播。
raw_department = input("部门：")
raw_job_title = input("岗位：")
raw_task_description = input("工作描述：")

# Day 2 尚未学习正则表达式。“先 split、再 join”可以把首尾空白、
# 连续空格、Tab 和换行等统一成单个半角空格。
department = " ".join(raw_department.split())
job_title = " ".join(raw_job_title.split())
task_description = " ".join(raw_task_description.split())

# 产品经理给出了试点期可确认的部门别名。replace 按顺序执行，
# 将旧称和简称统一为 Day 1 字段字典中的标准部门名。
department = department.replace("客户服务中心", "客户服务部")
department = department.replace("客服部", "客户服务部")

# 岗位文本中常出现英文大小写混用。title 让英文单词首字母大写，
# 中文字符不会因此损坏；这只是试点规则，生产词表将在 Day 5 引入。
job_title = job_title.title()

# 为避免在课件中处理真实隐私，用户输入一段“模拟敏感片段”。
# 提示中不展示具体样例值，避免提示文本本身与待检测片段相同而污染输出。
# replace 会把该片段的全部精确匹配替换为固定掩码。
sensitive_fragment = input("请输入任务中需要替换的模拟敏感片段：").strip()
task_description = task_description.replace(sensitive_fragment, MASK)

# 对明确的敏感字段标签做语义弱化，避免清洗结果继续鼓励输入凭据。
task_description = task_description.replace("密码", "凭据")
task_description = task_description.replace("身份证号", "证件标识")

# 检索词用于演示 lower、count、find、索引和切片。统一小写后，
# 英文搜索不受用户输入大小写影响，中文文本则保持原样。
search_keyword = input("预览检索词（示例 order）：").strip().lower()
searchable_task = task_description.lower()
keyword_count = searchable_task.count(search_keyword)
first_keyword_index = searchable_task.find(search_keyword)

# 用切片生成固定长度预览。字符串不足 30 个字符时不会报错，
# Python 会安全返回已有内容，因此无需提前学习条件判断。
task_preview = task_description[:30]
first_character = task_description[0:1]
last_character = task_description[-1:]

# 清洗收益采用字符数差值衡量。数值越大，表示删除或统一的冗余越多。
# 这里只是数据质量观测值，不代表文本语义质量。
raw_total_length = (
    len(raw_employee_id)
    + len(raw_department)
    + len(raw_job_title)
    + len(raw_task_description)
)
clean_total_length = (
    len(employee_id)
    + len(department)
    + len(job_title)
    + len(task_description)
)
normalized_character_count = raw_total_length - clean_total_length

# 完整性比例用于演示算术运算与格式化。当前验收假设原始文本非空；
# Day 3 将用条件判断处理空输入，避免除零并给用户明确反馈。
retention_percent = clean_total_length / raw_total_length * 100

print("\n" + "=" * CARD_WIDTH)
print(f"{PRODUCT_NAME}｜标准化结果")
print("-" * CARD_WIDTH)
print(f"员工编号        ：{employee_id}")
print(f"部门 / 岗位     ：{department} / {job_title}")
print(f"清洗后工作描述  ：{task_description}")
print(f"30 字符预览     ：{task_preview}")
print(f"首字符 / 尾字符 ：{first_character} / {last_character}")
print(f"检索词          ：{search_keyword}")
print(f"命中次数        ：{keyword_count}")
print(f"首次命中索引    ：{first_keyword_index}")
print(f"清洗字符差值    ：{normalized_character_count}")
print(f"字符保留比例    ：{retention_percent:.1f}%")
print("-" * CARD_WIDTH)
print("治理状态：模拟敏感片段已替换，原始文本未输出、未持久化。")
print("Day 3 将补充空值、范围和枚举校验；Day 5 将加载标准化词表。")
print("=" * CARD_WIDTH)
