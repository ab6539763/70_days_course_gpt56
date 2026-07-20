"""Day 6 课堂起步代码：把重复逻辑提取为函数。"""

import json


def create_task(task_id, title, priority=3):
    """根据输入返回一条具名字典任务。"""

    return {
        "task_id": task_id.strip().upper(),
        "title": " ".join(title.split()),
        "priority": priority,
        "is_done": False,
        "tags": [],
    }


def save_data(data, data_file="nexus_tasks.json"):
    """把完整业务文档保存为稳定 UTF-8 JSON。"""

    with open(data_file, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2, sort_keys=True)
        file.write("\n")


data = {
    "schema_version": 1,
    "revision": 1,
    "employee": {"employee_id": "E60006", "department": "客户服务部"},
    "tasks": [],
}
data["tasks"].append(create_task("t1", "  重构任务服务  ", priority=1))
save_data(data)
print("Day 6 起步版已保存一条函数化任务。")
