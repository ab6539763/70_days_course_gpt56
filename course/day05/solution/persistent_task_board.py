"""Day 5 参考实现：字典数据模型与 JSON 持久化任务台账。

数据文件固定写入当前工作目录的 nexus_tasks.json。测试和部署可在独立
临时目录运行，从而不会污染仓库。Day 5 聚焦字典与 JSON，因此保存代码
有意重复；Day 6 学习函数后会统一封装 load/save。
"""

import json
import os


PRODUCT_NAME = "智枢 NexusAI"
VERSION = "0.0.5"
SCHEMA_VERSION = 1
DATA_FILE = "nexus_tasks.json"
VALID_DEPARTMENTS = ("客户服务部", "销售部", "财务部")
VALID_PRIORITIES = {1, 2, 3, 4, 5}
WIDTH = 74

print("=" * WIDTH)
print(f"{PRODUCT_NAME} {VERSION}｜JSON 持久化任务台账")
print("=" * WIDTH)
print(f"数据文件：{DATA_FILE}（仅允许模拟业务数据）\n")

# 默认文档同时定义当前 JSON 的顶层结构和首次运行状态。
data = {
    "schema_version": SCHEMA_VERSION,
    "revision": 0,
    "employee": None,
    "tasks": [],
}

# os.path.exists 的系统讲解安排在 Day 11；此处只用于区分首次与恢复运行。
# 空文件被视为尚未初始化，避免 json.loads("") 失败。
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r", encoding="utf-8") as file:
        raw_json = file.read().strip()
    if raw_json != "":
        data = json.loads(raw_json)

        # 未知版本或关键结构缺失时拒绝继续，防止用错误结构覆盖文件。
        if data.get("schema_version") != SCHEMA_VERSION:
            print(
                "数据拒绝：不支持的 schema_version，"
                f"当前程序只支持 {SCHEMA_VERSION}。"
            )
            raise SystemExit(3)
        if (
            "revision" not in data
            or "employee" not in data
            or "tasks" not in data
            or not isinstance(data["tasks"], list)
        ):
            print("数据拒绝：JSON 缺少 revision/employee/tasks 关键结构。")
            raise SystemExit(3)

        print(
            f"恢复成功：revision={data['revision']}，"
            f"任务 {len(data['tasks'])} 条。"
        )

# 首次运行采集员工上下文；恢复运行直接使用持久化身份。
if data["employee"] is None:
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

    data["employee"] = {
        "employee_id": employee_id,
        "department": department,
    }
    data["revision"] = data["revision"] + 1
    with open(DATA_FILE, "w", encoding="utf-8") as file:
        json.dump(
            data,
            file,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        file.write("\n")
    print(f"身份已保存：{employee_id}｜{department}。")
else:
    employee_id = data["employee"]["employee_id"]
    department = data["employee"]["department"]
    print(f"身份已恢复：{employee_id}｜{department}。")

tasks = data["tasks"]
task_ids = {task["task_id"] for task in tasks}

while True:
    print("\n操作菜单")
    print("1=新增  2=查看全部  3=完成  4=删除")
    print("5=统计  6=清理已完成  7=JSON 摘要  0=退出")
    choice = input("请选择：").strip()

    if choice == "1":
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
        tags = sorted(
            {
                tag.strip().lower()
                for tag in raw_tags.split(",")
                if tag.strip() != ""
            }
        )

        task = {
            "task_id": task_id,
            "title": title,
            "priority": priority,
            "is_done": False,
            "tags": tags,
        }
        tasks.append(task)
        task_ids.add(task_id)
        data["revision"] = data["revision"] + 1
        with open(DATA_FILE, "w", encoding="utf-8") as file:
            json.dump(
                data,
                file,
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
            file.write("\n")
        print(
            f"新增并保存：{task_id}｜P{priority}｜{title}｜"
            f"revision={data['revision']}"
        )

    elif choice == "2":
        if len(tasks) == 0:
            print("当前没有任务。")
            continue

        # 装饰列表让字典按 priority/task_id 排序，不提前使用 lambda。
        decorated = [
            [task["priority"], task["task_id"], task]
            for task in tasks
        ]
        decorated.sort()
        ordered_tasks = [item[2] for item in decorated]

        print(f"\n任务总数：{len(ordered_tasks)}")
        for position, task in enumerate(ordered_tasks, start=1):
            status = "已完成" if task["is_done"] else "进行中"
            tag_text = ", ".join(task["tags"]) if task["tags"] else "无"
            print(
                f"{position}. [{status}] P{task['priority']} "
                f"{task['task_id']} {task['title']}｜标签：{tag_text}"
            )
        print(
            "首页预览："
            f"{[task['task_id'] for task in ordered_tasks[:3]]}"
        )

    elif choice == "3":
        if len(tasks) == 0:
            print("完成失败：当前没有任务。")
            continue
        target_id = input("要完成的任务编号：").strip().upper().replace(" ", "")
        found = False
        changed = False
        for task in tasks:
            if task["task_id"] == target_id:
                found = True
                if task["is_done"]:
                    print(f"状态未变：{target_id} 已经完成。")
                else:
                    task["is_done"] = True
                    changed = True
                break
        if not found:
            print(f"完成失败：未找到任务 {target_id}。")
        elif changed:
            data["revision"] = data["revision"] + 1
            with open(DATA_FILE, "w", encoding="utf-8") as file:
                json.dump(
                    data,
                    file,
                    ensure_ascii=False,
                    indent=2,
                    sort_keys=True,
                )
                file.write("\n")
            print(
                f"完成并保存：{target_id}｜revision={data['revision']}。"
            )

    elif choice == "4":
        if len(tasks) == 0:
            print("删除失败：当前没有任务。")
            continue
        target_id = input("要删除的任务编号：").strip().upper().replace(" ", "")
        removed_task = None
        for index in range(len(tasks)):
            if tasks[index]["task_id"] == target_id:
                removed_task = tasks.pop(index)
                task_ids.remove(target_id)
                break
        if removed_task is None:
            print(f"删除失败：未找到任务 {target_id}。")
        else:
            data["revision"] = data["revision"] + 1
            with open(DATA_FILE, "w", encoding="utf-8") as file:
                json.dump(
                    data,
                    file,
                    ensure_ascii=False,
                    indent=2,
                    sort_keys=True,
                )
                file.write("\n")
            print(
                f"删除并保存：{removed_task['task_id']}｜"
                f"{removed_task['title']}｜revision={data['revision']}。"
            )

    elif choice == "5":
        done_tasks = [task for task in tasks if task["is_done"]]
        active_tasks = [task for task in tasks if not task["is_done"]]
        high_priority_tasks = [
            task
            for task in active_tasks
            if task["priority"] <= 2
        ]
        all_tags = set()
        for task in tasks:
            all_tags.update(task["tags"])
        print("任务统计")
        print(f"总数：{len(tasks)}")
        print(f"进行中：{len(active_tasks)}")
        print(f"已完成：{len(done_tasks)}")
        print(f"高优先级进行中：{len(high_priority_tasks)}")
        print(f"唯一标签：{sorted(all_tags)}")

    elif choice == "6":
        before_count = len(tasks)
        tasks = [task for task in tasks if not task["is_done"]]
        data["tasks"] = tasks
        task_ids = {task["task_id"] for task in tasks}
        removed_count = before_count - len(tasks)
        if removed_count > 0:
            data["revision"] = data["revision"] + 1
            with open(DATA_FILE, "w", encoding="utf-8") as file:
                json.dump(
                    data,
                    file,
                    ensure_ascii=False,
                    indent=2,
                    sort_keys=True,
                )
                file.write("\n")
        print(
            f"清理完成：移除 {removed_count} 条，"
            f"revision={data['revision']}。"
        )

    elif choice == "7":
        print("JSON 摘要")
        print(f"schema_version：{data['schema_version']}")
        print(f"revision：{data['revision']}")
        print(f"employee keys：{sorted(data['employee'].keys())}")
        print(f"task_count：{len(data['tasks'])}")
        print(f"file：{DATA_FILE}")

    elif choice == "0":
        print(
            f"已安全退出：{employee_id}｜{department}｜"
            f"已持久化 {len(tasks)} 条任务｜revision={data['revision']}。"
        )
        break

    else:
        print("菜单错误：仅支持 0-7，请重新选择。")
