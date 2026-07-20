"""NexusAI 平台自定义异常：统一错误语义与 fail-closed 边界。"""


class NexusError(Exception):
    """NexusAI 平台所有业务异常的基类。"""

    def __init__(self, message, code="NEXUS_ERROR"):
        super().__init__(message)
        self.message = message
        self.code = code


class SchemaValidationError(NexusError):
    """持久化 JSON 不符合 schema 规则。"""

    def __init__(self, message):
        super().__init__(message, code="SCHEMA_VALIDATION")


class ModelConfigError(NexusError):
    """模型供应商或参数配置非法。"""

    def __init__(self, message):
        super().__init__(message, code="MODEL_CONFIG")


class PersistenceError(NexusError):
    """读写磁盘或 JSON 解析失败。"""

    def __init__(self, message):
        super().__init__(message, code="PERSISTENCE")


class InvalidMessageError(NexusError):
    """消息角色或内容不符合平台规则。"""

    def __init__(self, message):
        super().__init__(message, code="INVALID_MESSAGE")
