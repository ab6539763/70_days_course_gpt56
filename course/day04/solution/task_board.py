"""Day 4 参考实现：基于列表、元组和集合的 Agent 试点任务台账。

数据模型（嵌套列表）：
    [priority, task_id, title, is_done, tags_tuple]

Day 4 暂不使用函数和字典，目的是看清数据结构的底层增删改查。Day 5
会把位置字段重构为字典并保存 JSON，Day 6 再拆分为函数。
"""


PRODUCT_NAME = "智枢 NexusAI"
VERSION = "0.0.4"
WIDTH = 72

# 元组表达“本次版本固定支持的值”；集合用于高效成员检查。
VALID_DEPARTMENTS = ("客户服务部", "销售部", "财务部")
VALID_PRIORITIES = {1, 2, 3, 4, 5}

print("=" * WIDTH)
print(f"{PRODUCT_NAME} {VERSION}｜Agent 试点任务台账")
print("=" * WIDTH)
print("仅处理模拟任务；数据只在内存中，退出后不会保存。\n")

# 复用 Day 3 的有限身份重试。
employee_id = ""
for attempt in range(1, 4):
    employee_id = (
        input(f"员工编号（第 {attempt}/3 次）：")
        .strip()
        .upper()
        .replace(" ", "")
    )
    if employee_id == "":
        print("校验失败：员工编号不能为空。")
        continue
    if employee_id[0:1] != "E" or len(employee_id) < 2:
        print("校验失败：员工编号必须以 E 开头并包含后续编号。")
        continue
    break
else:
    print("安全退出：员工编号连续三次无效。")
    raise SystemExit(2)

while True:
    department = " ".join(input("部门：").split())
    if department == "客服部" or department == "客户服务中心":
        department = "客户服务部"
    if department in VALID_DEPARTMENTS:
        break
    print(f"校验失败：部门必须是 {' / '.join(VALID_DEPARTMENTS)}。")

# tasks 保留任务顺序和完整字段；task_ids 只保存唯一编号。
tasks = []
task_ids = set()

while True:
    print("\n操作菜单")
    print("1=新增  2=查看全部  3=完成  4=删除")
    print("5=统计  6=清理已完成  0=安全退出")
    menu_choice = input("请选择：").strip()

    if menu_choice == "1":
        while True:
            task_id = (
                input("任务编号（T 开头）：")
                .strip()
                .upper()
                .replace(" ", "")
            )
            if task_id == "":
                print("校验失败：任务编号不能为空。")
                continue
            if task_id[0:1] != "T" or len(task_id) < 2:
                print("校验失败：任务编号必须以 T 开头并包含后续编号。")
                continue
            if task_id in task_ids:
                print("校验失败：任务编号已存在，请使用新编号。")
                continue
            break

        while True:
            title = " ".join(input("任务标题：").split())
            if title != "":
                break
            print("校验失败：任务标题不能为空。")

        while True:
            priority_text = input("优先级（1 最高，5 最低）：").strip()
            if not priority_text.isdigit():
                print("校验失败：优先级必须是 1-5 的整数。")
                continue
            priority = int(priority_text)
            if priority not in VALID_PRIORITIES:
                print("校验失败：优先级必须在 1-5 之间。")
                continue
            break

        raw_tags = input("标签（英文逗号分隔，可留空）：")
        # 列表推导式完成拆分、清理、转小写和空标签过滤。
        tag_list = [
            tag.strip().lower()
            for tag in raw_tags.split(",")
            if tag.strip() != ""
        ]
        # set 去重，再排序保证展示稳定，最后转 tuple 表达任务标签快照。
        tags = tuple(sorted(set(tag_list)))

        task = [priority, task_id, title, False, tags]
        tasks.append(task)
        task_ids.add(task_id)
        print(f"新增成功：{task_id}｜P{priority}｜{title}｜标签 {tags}")

    elif menu_choice == "2":
        if len(tasks) == 0:
            print("当前没有任务。")
            continue

        # priority 位于索引 0，task_id 位于索引 1；默认列表排序先比较
        # 优先级，再比较编号，满足当前业务口径且不提前引入 lambda。
        tasks.sort()
        print(f"\n任务总数：{len(tasks)}")
        for position, task in enumerate(tasks, start=1):
            status = "已完成" if task[3] else "进行中"
            tag_text = ", ".join(task[4]) if len(task[4]) > 0 else "无"
            print(
                f"{position}. [{status}] P{task[0]} {task[1]} "
                f"{task[2]}｜标签：{tag_text}"
            )

        # 切片生成首页预览，不改变原列表。
        top_tasks = tasks[:3]
        print(f"首页预览：{[task[1] for task in top_tasks]}")

    elif menu_choice == "3":
        if len(tasks) == 0:
            print("完成失败：当前没有任务。")
            continue

        target_id = input("要完成的任务编号：").strip().upper().replace(" ", "")
        found = False
        for task in tasks:
            if task[1] == target_id:
                found = True
                if task[3]:
                    print(f"状态未变：{target_id} 已经完成。")
                else:
                    task[3] = True
                    print(f"完成成功：{target_id}。")
                break
        if not found:
            print(f"完成失败：未找到任务 {target_id}。")

    elif menu_choice == "4":
        if len(tasks) == 0:
            print("删除失败：当前没有任务。")
            continue

        target_id = input("要删除的任务编号：").strip().upper().replace(" ", "")
        removed = False
        for index in range(len(tasks)):
            if tasks[index][1] == target_id:
                removed_task = tasks.pop(index)
                task_ids.remove(target_id)
                removed = True
                print(f"删除成功：{removed_task[1]}｜{removed_task[2]}。")
                break
        if not removed:
            print(f"删除失败：未找到任务 {target_id}。")

    elif menu_choice == "5":
        done_tasks = [task for task in tasks if task[3]]
        active_tasks = [task for task in tasks if not task[3]]
        high_priority_tasks = [
            task for task in active_tasks if task[0] <= 2
        ]

        all_tags = set()
        for task in tasks:
            for tag in task[4]:
                all_tags.add(tag)

        print("任务统计")
        print(f"总数：{len(tasks)}")
        print(f"进行中：{len(active_tasks)}")
        print(f"已完成：{len(done_tasks)}")
        print(f"高优先级进行中：{len(high_priority_tasks)}")
        print(f"唯一标签：{sorted(all_tags)}")

    elif menu_choice == "6":
        before_count = len(tasks)
        # 先用列表推导式构造只含未完成任务的新列表。
        tasks = [task for task in tasks if not task[3]]
        # task_ids 必须与主列表同步重建，避免已删除编号仍被判重复。
        task_ids = {task[1] for task in tasks}
        removed_count = before_count - len(tasks)
        print(f"清理完成：移除 {removed_count} 条已完成任务。")

    elif menu_choice == "0":
        print(
            f"已安全退出：{employee_id}｜{department}｜"
            f"内存中剩余 {len(tasks)} 条任务，均未持久化。"
        )
        break

    else:
        print("菜单错误：仅支持 0-6，请重新选择。")
