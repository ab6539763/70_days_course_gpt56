"""HTTP 调用配置：从环境变量读取 API Key 与 Base URL。"""

import os


ENV_API_KEY = "NEXUS_API_KEY"
ENV_API_BASE = "NEXUS_API_BASE_URL"
ENV_USE_MOCK = "NEXUS_USE_MOCK"
DEFAULT_OPENAI_BASE = "https://api.openai.com/v1"
DEFAULT_QWEN_BASE = "https://dashscope.aliyuncs.com/compatible-mode/v1"


def use_mock_mode():
    """测试或演示模式下走本地模拟，不发真实 HTTP。"""
    value = os.environ.get(ENV_USE_MOCK, "").strip().lower()
    return value in ("1", "true", "yes", "on")


def resolve_api_key(explicit_key=None):
    key = (explicit_key or os.environ.get(ENV_API_KEY, "")).strip()
    return key


def resolve_base_url(provider, explicit_base=None):
    if explicit_base:
        return explicit_base.rstrip("/")
    env_base = os.environ.get(ENV_API_BASE, "").strip()
    if env_base:
        return env_base.rstrip("/")
    if provider == "qwen":
        return DEFAULT_QWEN_BASE
    return DEFAULT_OPENAI_BASE


def resolve_api_credentials(provider, api_key=None, base_url=None):
    """合并显式参数与环境变量，返回 (key, base)。"""
    key = resolve_api_key(api_key)
    base = resolve_base_url(provider, base_url)
    return key, base
