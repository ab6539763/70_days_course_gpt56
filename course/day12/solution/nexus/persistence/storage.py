"""JSON 持久化与 revision 管理。"""

import json
import os

from nexus.constants import DATA_FILE
from nexus.exceptions import PersistenceError, SchemaValidationError
from nexus.platform.state import PlatformState


def load_state(data_file=DATA_FILE):
    """加载平台状态；磁盘/JSON/schema 错误转换为明确异常。"""
    if not os.path.exists(data_file):
        return PlatformState.empty(), "new", ""
    try:
        with open(data_file, "r", encoding="utf-8") as file:
            raw = file.read().strip()
    except OSError as error:
        raise PersistenceError(f"无法读取数据文件：{error}") from error
    if raw == "":
        return PlatformState.empty(), "empty", ""
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as error:
        raise PersistenceError(f"JSON 解析失败：{error}") from error
    try:
        state, migrated = PlatformState.from_dict(payload)
    except SchemaValidationError as error:
        return None, "rejected", error.message
    return state, "migrated" if migrated else "loaded", ""


def save_state(state, data_file=DATA_FILE):
    """原子写入平台状态；失败时抛 PersistenceError。"""
    try:
        with open(data_file, "w", encoding="utf-8") as file:
            json.dump(
                state.to_dict(),
                file,
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
            file.write("\n")
    except OSError as error:
        raise PersistenceError(f"无法写入数据文件：{error}") from error


def persist_change(state, data_file=DATA_FILE):
    state.revision += 1
    save_state(state, data_file)
    return state.revision
