"""JSON 持久化与 revision 管理。"""

import json
import os

from nexus.constants import DATA_FILE
from nexus.exceptions import PersistenceError, SchemaValidationError
from nexus.persistence.revision_guard import assert_revision_on_disk
from nexus.observability.logging import get_logger, log_event
from nexus.platform.state import PlatformState


_persist_logger = get_logger("persistence")


def load_state(data_file=DATA_FILE):
    """加载平台状态；磁盘/JSON/schema 错误转换为明确异常。"""
    if not os.path.exists(data_file):
        log_event(_persist_logger, 20, "load_new", data_file=data_file)
        return PlatformState.empty(), "new", ""
    try:
        with open(data_file, "r", encoding="utf-8") as file:
            raw = file.read().strip()
    except OSError as error:
        log_event(_persist_logger, 40, "load_read_failed", data_file=data_file)
        raise PersistenceError(f"无法读取数据文件：{error}") from error
    if raw == "":
        return PlatformState.empty(), "empty", ""
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as error:
        log_event(_persist_logger, 40, "load_json_failed", data_file=data_file)
        raise PersistenceError(f"JSON 解析失败：{error}") from error
    try:
        state, migrated = PlatformState.from_dict(payload)
    except SchemaValidationError as error:
        log_event(_persist_logger, 30, "load_rejected", reason=error.message)
        return None, "rejected", error.message
    status = "migrated" if migrated else "loaded"
    log_event(
        _persist_logger,
        20,
        "load_ok",
        data_file=data_file,
        status=status,
        revision=state.revision,
    )
    return state, status, ""


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
        log_event(_persist_logger, 40, "save_failed", data_file=data_file)
        raise PersistenceError(f"无法写入数据文件：{error}") from error
    log_event(_persist_logger, 20, "save_ok", data_file=data_file, revision=state.revision)


def persist_change(state, data_file=DATA_FILE, expected_revision=None):
    """持久化变更；可选 expected_revision 乐观锁校验。"""
    if expected_revision is not None:
        assert_revision_on_disk(data_file, expected_revision)
    state.revision += 1
    save_state(state, data_file)
    log_event(_persist_logger, 20, "persist_change", revision=state.revision)
    return state.revision
