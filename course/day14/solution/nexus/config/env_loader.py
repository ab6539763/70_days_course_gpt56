"""环境变量与 dotenv 加载。"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv


ENV_FILE = "NEXUS_ENV_FILE"
_loaded_path: Optional[str] = None


def reset_env_loader_state() -> None:
    """测试专用：重置加载状态。"""
    global _loaded_path
    _loaded_path = None


def load_env(env_path: Optional[str] = None, override: bool = False) -> str:
    """加载 .env 文件；已存在的环境变量默认不被覆盖。"""
    global _loaded_path
    candidate = env_path or os.environ.get(ENV_FILE, ".env")
    path = Path(candidate)
    if path.is_file():
        load_dotenv(path, override=override)
        _loaded_path = str(path.resolve())
    else:
        _loaded_path = ""
    return _loaded_path


def loaded_env_path() -> str:
    """返回最近一次成功加载的 .env 绝对路径，未加载则空字符串。"""
    return _loaded_path or ""


def mask_secret(value: str, visible: int = 4) -> str:
    """日志与 CLI 展示用密钥脱敏。"""
    text = value.strip()
    if text == "":
        return "(未设置)"
    if len(text) <= visible:
        return "*" * len(text)
    return f"{'*' * (len(text) - visible)}{text[-visible:]}"
