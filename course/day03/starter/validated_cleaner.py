"""Day 3 课堂起步代码：为 Day 2 清洗器增加条件和重试。"""


print("=" * 60)
print("智枢 NexusAI｜可校验文本治理工作台")
print("=" * 60)

# while True 表示持续询问；只有输入有效时才通过 break 离开循环。
while True:
    employee_id = input("员工编号：").strip().upper().replace(" ", "")
    if employee_id == "":
        print("校验失败：员工编号不能为空。")
        continue
    if employee_id[0:1] != "E":
        print("校验失败：员工编号必须以 E 开头。")
        continue
    break

while True:
    department = " ".join(input("部门：").split())
    if department == "客服部" or department == "客户服务中心":
        department = "客户服务部"
    if department == "客户服务部" or department == "销售部":
        break
    print("校验失败：当前仅支持客户服务部或销售部。")

print(f"\n员工编号：{employee_id}")
print(f"标准部门：{department}")
print("基础校验通过。课堂中继续补齐数值、任务和菜单流程。")
