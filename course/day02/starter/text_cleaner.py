"""Day 2 课堂起步代码：员工文本清洗工作台。

只使用 Day 1 已学内容和 Day 2 新增的字符串方法。课堂中会逐步补齐
标准化、脱敏、检索预览和质量指标，不要直接复制参考答案。
"""


print("=" * 58)
print("智枢 NexusAI｜员工文本清洗工作台")
print("=" * 58)

employee_id = input("员工编号：").strip().upper().replace(" ", "")
department = input("部门：").strip()
job_title = input("岗位：").strip()
task_description = input("工作描述：").strip()

# split 不传参数时会按连续空白切开；join 再用一个空格连接，
# 可以把重复空格、制表符等统一为单个空格。
department = " ".join(department.split())
job_title = " ".join(job_title.split())
task_description = " ".join(task_description.split())

print("\n清洗预览")
print(f"员工编号：{employee_id}")
print(f"部门 / 岗位：{department} / {job_title}")
print(f"工作描述：{task_description}")
