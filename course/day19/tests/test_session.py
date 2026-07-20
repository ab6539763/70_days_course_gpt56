"""Day 19 会话隔离、Session ID 与独立 state 文件单测。"""

import os
import sys
import tempfile
from pathlib import Path


SOLUTION = Path(__file__).parents[1] / "solution"
sys.path.insert(0, str(SOLUTION))

os.environ["NEXUS_USE_MOCK"] = "1"

from nexus.config.session_config import (
    generate_session_id,
    session_file_path,
    validate_session_id,
)
from nexus.platform.state import PlatformState
from nexus.persistence.storage import persist_change
from nexus.web.session_registry import SessionRegistry


assert validate_session_id(generate_session_id()).startswith("nxs_")

try:
    validate_session_id("bad-id")
except ValueError:
    pass
else:
    raise AssertionError("应拒绝非法 Session ID")

with tempfile.TemporaryDirectory(prefix="nexus-day19-session-") as temporary:
    root = Path(temporary) / "sessions"
    registry = SessionRegistry(session_dir=root)

    first = registry.create_session(owner="用户甲")
    second = registry.create_session(owner="用户乙")
    assert first["session_id"] != second["session_id"]
    assert session_file_path(first["session_id"], root).exists()
    assert session_file_path(second["session_id"], root).exists()

    manager_a = registry.manager_for(first["session_id"])
    manager_b = registry.manager_for(second["session_id"])

    manager_a.chat("甲的专属问题", system_prompt="你是助手")
    manager_b.chat("乙的专属问题", system_prompt="你是助手")

    snap_a = manager_a.snapshot()
    snap_b = manager_b.snapshot()
    assert len(snap_a["messages"]) == 2
    assert len(snap_b["messages"]) == 2
    assert snap_a["messages"][0]["content"] == "甲的专属问题"
    assert snap_b["messages"][0]["content"] == "乙的专属问题"

    listed = registry.list_sessions()
    assert len(listed) == 2
    info = registry.session_info(first["session_id"])
    assert info["owner"] == "用户甲"
    assert info["messages"] == 2

    os.environ["NEXUS_USE_MOCK"] = "1"
    state = PlatformState.empty()
    extra_id = generate_session_id()
    extra_path = session_file_path(extra_id, root)
    persist_change(state, str(extra_path))
    assert extra_path.exists()

print("Day 19 会话隔离单测通过：独立 JSON、SessionRegistry 与 manager 均正确。")
