"""模型多态工厂与注册表。"""

from nexus.exceptions import ModelConfigError
from nexus.models.openai_model import OpenAIModel
from nexus.models.qwen_model import QwenModel


MODEL_REGISTRY = {
    "openai": OpenAIModel,
    "qwen": QwenModel,
}


def create_model(config):
    """多态工厂：根据 provider 创建对应子类实例。"""
    provider = config.get("provider", "").strip().lower()
    model_cls = MODEL_REGISTRY.get(provider)
    if model_cls is None:
        raise ModelConfigError(f"不支持的模型供应商：{provider}")
    return model_cls(
        config.get("model_id", ""),
        config.get("temperature", 0.7),
        config.get("max_tokens", 1024),
    )
