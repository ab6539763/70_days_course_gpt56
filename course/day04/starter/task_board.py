"""Day 4 课堂起步代码：用列表管理多条 Agent 试点任务。"""


print("=" * 66)
print("智枢 NexusAI｜试点任务台账")
print("=" * 66)

# tasks 保存多条任务；task_ids 专门用于快速判断编号是否重复。
tasks = []
task_ids = set()

while True:
    print("\n1=新增任务，2=查看任务，0=退出")
    choice = input("请选择：").strip()

    if choice == "1":
        task_id = input("任务编号：").strip().upper().replace(" ", "")
        if task_id in task_ids:
            print("新增失败：任务编号已存在。")
            continue

        title = " ".join(input("任务标题：").split())
        priority = int(input("优先级 1-5：").strip())

        # 每条任务暂用嵌套列表：[优先级, 编号, 标题, 是否完成]。
        task = [priority, task_id, title, False]
        tasks.append(task)
        task_ids.add(task_id)
        print("任务新增成功。")

    elif choice == "2":
        # 列表按优先级、编号依次比较，因此无需提前使用 lambda。
        tasks.sort()
        for task in tasks:
            print(task)

    elif choice == "0":
        print("已退出；任务仅存在于本次运行内存。")
        break

    else:
        print("菜单错误：仅支持 0、1、2。")
