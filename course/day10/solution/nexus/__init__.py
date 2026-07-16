"""智枢 NexusAI 模块化平台包。"""

from nexus.constants import APP_VERSION, DATA_FILE, SCHEMA_VERSION
from nexus.cli.app import run_cli
from nexus.domain import Contact, ChatMessage
from nexus.exceptions import (
    InvalidMessageError,
    ModelConfigError,
    NexusError,
    PersistenceError,
    SchemaValidationError,
)
from nexus.models import BaseModel, OpenAIModel, QwenModel, create_model
from nexus.persistence import load_state, persist_change, save_state
from nexus.platform import PlatformState

__all__ = [
    "APP_VERSION",
    "DATA_FILE",
    "SCHEMA_VERSION",
    "Contact",
    "ChatMessage",
    "BaseModel",
    "OpenAIModel",
    "QwenModel",
    "create_model",
    "PlatformState",
    "load_state",
    "save_state",
    "persist_change",
    "run_cli",
    "NexusError",
    "SchemaValidationError",
    "ModelConfigError",
    "PersistenceError",
    "InvalidMessageError",
]

__version__ = APP_VERSION
