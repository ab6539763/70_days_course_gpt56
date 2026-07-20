"""Day 6 参考实现：函数化 JSON 任务服务与 CLI。

函数将数据规则、持久化和交互编排分开。所有业务函数通过参数接收数据并
返回明确结果，不依赖隐藏的全局可变状态，便于单元测试和后续模块拆分。
"""

import json
import os


PRODUCT_NAME = "智枢 NexusAI"
VERSION = "0.0.6"
SCHEMA_VERSION = 1
DATA_FILE = "nexus_tasks.json"
VALID_DEPARTMENTS = ("客户服务部", "销售部", "财务部")
VALID_PRIORITIES = {1, 2, 3, 4, 5}


def create_default_data():
    """返回一份全新的 Schema v1 文档，避免调用者共享可变对象。"""

    return {
        "schema_version": SCHEMA_VERSION,
        "revision": 0,
        "employee": None,
        "tasks": [],
    }


def normalize_identifier(raw_value, prefix):
    """清理标识符并验证前缀，返回 (是否有效, 标准值, 原因)。"""

    value = raw_value.strip().upper().replace(" ", "")
    if value == "":
        return False, value, "不能为空"
    if value[0:1] != prefix or len(value) < 2:
        return False, value, f"必须以 {prefix} 开头并包含后续编号"
    return True, value, ""


def normalize_department(raw_department):
    """标准化部门别名，返回 (是否有效, 标准部门)。"""

    department = " ".join(raw_department.split())
    aliases = {
        "客服部": "客户服务部",
        "客户服务中心": "客户服务部",
    }
    department = aliases.get(department, department)
    return department in VALID_DEPARTMENTS, department


def merge_tags(*tag_groups):
    """合并任意数量标签组，清理、转小写、去重并稳定排序。"""

    normalized = set()
    for group in tag_groups:
        for tag in group:
            clean_tag = tag.strip().lower()
            if clean_tag != "":
                normalized.add(clean_tag)
    return sorted(normalized)


def create_task(task_id, title, priority=3, tags=None, is_done=False):
    """创建任务字典；默认参数提供常用优先级和初始状态。"""

    if tags is None:
        tags = []
    return {
        "task_id": task_id,
        "title": " ".join(title.split()),
        "priority": priority,
        "is_done": is_done,
        "tags": merge_tags(tags),
    }


def update_task(task, **changes):
    """使用关键字参数更新允许字段，返回实际是否发生变化。"""

    allowed_fields = {"title", "priority", "is_done", "tags"}
    changed = False
    for key, value in changes.items():
        if key in allowed_fields and task.get(key) != value:
            task[key] = value
            changed = True
    return changed


def validate_data(data):
    """浅校验顶层数据契约，返回 (是否有效, 原因)。"""

    if not isinstance(data, dict):
        return False, "顶层必须是对象"
    if data.get("schema_version") != SCHEMA_VERSION:
        return False, "不支持的 schema_version"
    required = {"revision", "employee", "tasks"}
    if not required.issubset(data.keys()):
        return False, "缺少 revision/employee/tasks"
    if not isinstance(data["tasks"], list):
        return False, "tasks 必须是列表"
    return True, ""


def load_data(data_file=DATA_FILE):
    """加载数据，返回 (data, status, error)，不修改文件。"""

    if not os.path.exists(data_file):
        return create_default_data(), "new", ""
    with open(data_file, "r", encoding="utf-8") as file:
        raw_json = file.read().strip()
    if raw_json == "":
        return create_default_data(), "empty", ""
    data = json.loads(raw_json)
    valid, error = validate_data(data)
    if not valid:
        return data, "rejected", error
    return data, "loaded", ""


def save_data(data, data_file=DATA_FILE):
    """保存完整文档；成功后返回数据文件路径。"""

    with open(data_file, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2, sort_keys=True)
        file.write("\n")
    return data_file


def persist_change(data, data_file=DATA_FILE):
    """为真实变更增加 revision 并保存，返回新 revision。"""

    data["revision"] += 1
    save_data(data, data_file=data_file)
    return data["revision"]


def add_task(data, task):
    """新增唯一任务，返回 (是否改变, 消息)。"""

    existing_ids = {item["task_id"] for item in data["tasks"]}
    if task["task_id"] in existing_ids:
        return False, f"任务 {task['task_id']} 已存在"
    data["tasks"].append(task)
    return True, f"已新增 {task['task_id']}"


def complete_task(data, task_id):
    """幂等完成任务，返回 (是否改变, 消息)。"""

    for task in data["tasks"]:
        if task["task_id"] == task_id:
            if task["is_done"]:
                return False, f"任务 {task_id} 已经完成"
            update_task(task, is_done=True)
            return True, f"已完成 {task_id}"
    return False, f"未找到任务 {task_id}"


def delete_task(data, task_id):
    """按稳定编号删除任务，返回 (是否改变, 消息)。"""

    for index, task in enumerate(data["tasks"]):
        if task["task_id"] == task_id:
            removed = data["tasks"].pop(index)
            return True, f"已删除 {removed['task_id']}｜{removed['title']}"
    return False, f"未找到任务 {task_id}"


def cleanup_completed(data):
    """批量移除已完成任务，返回删除数量。"""

    before = len(data["tasks"])
    data["tasks"] = [
        task for task in data["tasks"] if not task["is_done"]
    ]
    return before - len(data["tasks"])


def ordered_tasks(tasks, limit=None):
    """返回按优先级/编号排序的新列表，可选限制数量。"""

    decorated = [
        [task["priority"], task["task_id"], task]
        for task in tasks
    ]
    decorated.sort()
    result = [item[2] for item in decorated]
    if limit is not None:
        return result[:limit]
    return result


def task_statistics(tasks):
    """以字典返回可复用统计结果，不负责打印。"""

    active = [task for task in tasks if not task["is_done"]]
    done = [task for task in tasks if task["is_done"]]
    high_priority = [
        task for task in active if task["priority"] <= 2
    ]
    all_tags = set()
    for task in tasks:
        all_tags.update(task["tags"])
    return {
        "total": len(tasks),
        "active": len(active),
        "done": len(done),
        "high_priority_active": len(high_priority),
        "tags": sorted(all_tags),
    }


def count_tasks_recursive(tasks, index=0):
    """递归统计任务数；教学递归边界，生产统计直接使用 len。"""

    if index >= len(tasks):
        return 0
    return 1 + count_tasks_recursive(tasks, index + 1)


def format_line(*parts, separator="｜"):
    """用 *args 接收任意展示片段，并支持关键字分隔符。"""

    return separator.join(str(part) for part in parts)


def prompt_employee():
    """交互采集员工，三次编号失败时返回 None。"""

    employee_id = None
    for attempt in range(1, 4):
        valid, value, reason = normalize_identifier(
            input(f"员工编号（第 {attempt}/3 次）："),
            "E",
        )
        if valid:
            employee_id = value
            break
        print(f"校验失败：员工编号{reason}。")
    if employee_id is None:
        return None

    while True:
        valid, department = normalize_department(input("部门："))
        if valid:
            return {
                "employee_id": employee_id,
                "department": department,
            }
        print(f"校验失败：部门必须是 {' / '.join(VALID_DEPARTMENTS)}。")


def prompt_new_task(existing_ids):
    """交互采集一条任务并返回字典。"""

    while True:
        valid, task_id, reason = normalize_identifier(
            input("任务编号（T 开头）："),
            "T",
        )
        if not valid:
            print(f"校验失败：任务编号{reason}。")
            continue
        if task_id in existing_ids:
            print("校验失败：任务编号已存在。")
            continue
        break
    while True:
        title = " ".join(input("任务标题：").split())
        if title:
            break
        print("校验失败：任务标题不能为空。")
    while True:
        text = input("优先级（1-5）：").strip()
        if text.isdigit() and int(text) in VALID_PRIORITIES:
            priority = int(text)
            break
        print("校验失败：优先级必须是 1-5 的整数。")
    tags = input("标签（逗号分隔）：").split(",")
    return create_task(task_id, title, priority=priority, tags=tags)


def run_cli(data_file=DATA_FILE):
    """编排加载、交互、业务函数与保存；返回进程语义状态码。"""

    print("=" * 74)
    print(f"{PRODUCT_NAME} {VERSION}｜函数化任务服务")
    print("=" * 74)
    data, status, error = load_data(data_file=data_file)
    if status == "rejected":
        print(f"数据拒绝：{error}。")
        return 3
    if status == "loaded":
        print(
            f"恢复成功：revision={data['revision']}，"
            f"任务 {len(data['tasks'])} 条。"
        )

    if data["employee"] is None:
        employee = prompt_employee()
        if employee is None:
            print("安全退出：员工编号连续三次无效。")
            return 2
        data["employee"] = employee
        revision = persist_change(data, data_file=data_file)
        print(
            f"身份已保存：{format_line(employee['employee_id'], employee['department'])}"
            f"｜revision={revision}。"
        )
    else:
        employee = data["employee"]
        print(
            f"身份已恢复："
            f"{format_line(employee['employee_id'], employee['department'])}。"
        )

    while True:
        print("\n1=新增 2=查看 3=完成 4=删除 5=统计 6=清理 7=摘要 0=退出")
        choice = input("请选择：").strip()
        if choice == "1":
            task = prompt_new_task(
                {item["task_id"] for item in data["tasks"]}
            )
            changed, message = add_task(data, task)
            if changed:
                revision = persist_change(data, data_file=data_file)
                print(f"{message}并保存｜revision={revision}。")
        elif choice == "2":
            items = ordered_tasks(data["tasks"])
            if not items:
                print("当前没有任务。")
                continue
            for position, task in enumerate(items, start=1):
                status_text = "已完成" if task["is_done"] else "进行中"
                print(
                    f"{position}. [{status_text}] P{task['priority']} "
                    f"{task['task_id']} {task['title']}｜"
                    f"标签：{', '.join(task['tags']) or '无'}"
                )
            print(
                f"首页预览："
                f"{[task['task_id'] for task in ordered_tasks(items, limit=3)]}"
            )
        elif choice == "3":
            _, task_id, _ = normalize_identifier(
                input("要完成的任务编号："),
                "T",
            )
            changed, message = complete_task(data, task_id)
            if changed:
                revision = persist_change(data, data_file=data_file)
                print(f"{message}并保存｜revision={revision}。")
            else:
                print(message)
        elif choice == "4":
            _, task_id, _ = normalize_identifier(
                input("要删除的任务编号："),
                "T",
            )
            changed, message = delete_task(data, task_id)
            if changed:
                revision = persist_change(data, data_file=data_file)
                print(f"{message}并保存｜revision={revision}。")
            else:
                print(message)
        elif choice == "5":
            stats = task_statistics(data["tasks"])
            print(
                "统计："
                f"总数={stats['total']}｜进行中={stats['active']}｜"
                f"已完成={stats['done']}｜"
                f"高优先级={stats['high_priority_active']}｜"
                f"标签={stats['tags']}"
            )
            print(f"递归校验总数：{count_tasks_recursive(data['tasks'])}")
        elif choice == "6":
            removed = cleanup_completed(data)
            if removed > 0:
                revision = persist_change(data, data_file=data_file)
            else:
                revision = data["revision"]
            print(f"清理：移除 {removed} 条｜revision={revision}。")
        elif choice == "7":
            print(
                f"摘要：schema={data['schema_version']}｜"
                f"revision={data['revision']}｜"
                f"tasks={len(data['tasks'])}｜file={data_file}"
            )
        elif choice == "0":
            print(
                f"安全退出：已持久化 {len(data['tasks'])} 条任务｜"
                f"revision={data['revision']}。"
            )
            return 0
        else:
            print("菜单错误：仅支持 0-7。")


if __name__ == "__main__":
    raise SystemExit(run_cli())
