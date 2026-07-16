"""HTTP 调用配置：环境变量与 dotenv。"""

from __future__ import annotations

import os
from typing import Optional, Tuple

from nexus.config.env_loader import load_env


ENV_API_KEY = "NEXUS_API_KEY"
ENV_API_BASE = "NEXUS_API_BASE_URL"
ENV_USE_MOCK = "NEXUS_USE_MOCK"
DEFAULT_OPENAI_BASE = "https://api.openai.com/v1"
DEFAULT_QWEN_BASE = "https://dashscope.aliyuncs.com/compatible-mode/v1"
_dotenv_bootstrapped = False


def reset_bootstrap() -> None:
    """测试专用：允许重新 bootstrap。"""
    global _dotenv_bootstrapped
    _dotenv_bootstrapped = False


def bootstrap_env(env_path: Optional[str] = None) -> str:
    """首次调用时加载 .env；返回加载路径或空字符串。"""
    global _dotenv_bootstrapped
    if not _dotenv_bootstrapped:
        load_env(env_path)
        _dotenv_bootstrapped = True
    from nexus.config.env_loader import loaded_env_path

    return loaded_env_path()


def use_mock_mode() -> bool:
    bootstrap_env()
    value = os.environ.get(ENV_USE_MOCK, "").strip().lower()
    return value in ("1", "true", "yes", "on")


def resolve_api_key(explicit_key: Optional[str] = None) -> str:
    bootstrap_env()
    key = (explicit_key or os.environ.get(ENV_API_KEY, "")).strip()
    return key


def resolve_base_url(provider: str, explicit_base: Optional[str] = None) -> str:
    bootstrap_env()
    if explicit_base:
        return explicit_base.rstrip("/")
    env_base = os.environ.get(ENV_API_BASE, "").strip()
    if env_base:
        return env_base.rstrip("/")
    if provider == "qwen":
        return DEFAULT_QWEN_BASE
    return DEFAULT_OPENAI_BASE


def resolve_api_credentials(
    provider: str,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
) -> Tuple[str, str]:
    key = resolve_api_key(api_key)
    base = resolve_base_url(provider, base_url)
    return key, base
