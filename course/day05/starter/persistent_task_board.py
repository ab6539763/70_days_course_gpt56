"""Day 5 课堂起步代码：把字典任务保存为 JSON。"""

import json


DATA_FILE = "nexus_tasks.json"

# 字典用字段名表达含义，不再依赖 Day 4 的位置索引。
data = {
    "schema_version": 1,
    "employee": {
        "employee_id": "E50005",
        "department": "客户服务部",
    },
    "tasks": [],
}

task = {
    "task_id": "T1",
    "title": "设计 Agent 审批流程",
    "priority": 1,
    "is_done": False,
    "tags": ["agent", "approval"],
}
data["tasks"].append(task)

# ensure_ascii=False 让中文直接可读；indent=2 便于人工评审。
with open(DATA_FILE, "w", encoding="utf-8") as file:
    json.dump(data, file, ensure_ascii=False, indent=2)
    file.write("\n")

print(f"已保存 {len(data['tasks'])} 条任务到 {DATA_FILE}")
