"""结构化日志：trace_id 贯穿 CLI、HTTP 与持久化。"""

from __future__ import annotations

import logging
import uuid
from contextvars import ContextVar
from typing import Any, Dict


trace_id_var: ContextVar[str] = ContextVar("nexus_trace_id", default="")
_configured = False


def new_trace_id() -> str:
    """生成 16 位十六进制 trace_id。"""
    return uuid.uuid4().hex[:16]


def bind_trace_id(trace_id: str | None = None) -> str:
    """绑定当前上下文 trace_id，供日志与 HTTP 关联。"""
    value = trace_id or new_trace_id()
    trace_id_var.set(value)
    return value


def current_trace_id() -> str:
    """读取当前 trace_id；未绑定时返回占位符。"""
    value = trace_id_var.get()
    return value if value else "no-trace"


def _configure_root_once() -> None:
    global _configured
    if _configured:
        return
    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s trace_id=%(trace_id)s level=%(levelname)s "
            "logger=%(name)s event=%(message)s"
        )
    )
    root = logging.getLogger("nexus")
    root.setLevel(logging.INFO)
    if not root.handlers:
        root.addHandler(handler)
    root.propagate = False
    _configured = True


class TraceContextFilter(logging.Filter):
    """把 trace_id 注入 LogRecord，供 Formatter 使用。"""

    def filter(self, record: logging.LogRecord) -> bool:
        record.trace_id = current_trace_id()
        return True


def get_logger(name: str) -> logging.Logger:
    """获取带 trace_id 过滤器的 nexus 子 logger。"""
    _configure_root_once()
    logger = logging.getLogger(f"nexus.{name}")
    if not any(isinstance(item, TraceContextFilter) for item in logger.filters):
        logger.addFilter(TraceContextFilter())
    return logger


def _sanitize_fields(fields: Dict[str, Any]) -> Dict[str, Any]:
    """移除可能含密钥的字段，避免日志泄漏。"""
    blocked = {"api_key", "authorization", "password", "secret", "token"}
    cleaned: Dict[str, Any] = {}
    for key, value in fields.items():
        lowered = key.lower()
        if any(part in lowered for part in blocked):
            cleaned[key] = "(redacted)"
        else:
            cleaned[key] = value
    return cleaned


def log_event(logger: logging.Logger, level: int, event: str, **fields: Any) -> None:
    """记录 key=value 结构化事件；敏感字段自动脱敏。"""
    safe = _sanitize_fields(fields)
    parts = [f"{key}={value}" for key, value in safe.items()]
    message = event if not parts else f"{event} | " + " ".join(parts)
    logger.log(level, message)


def format_trace_prefix() -> str:
    """供 CLI 打印的 trace 前缀。"""
    return f"[trace:{current_trace_id()}]"
