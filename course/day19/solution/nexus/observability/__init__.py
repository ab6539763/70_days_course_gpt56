"""可观测性：结构化日志与 trace_id。"""

from nexus.observability.logging import (
    bind_trace_id,
    current_trace_id,
    get_logger,
    log_event,
    new_trace_id,
)

__all__ = [
    "bind_trace_id",
    "current_trace_id",
    "get_logger",
    "log_event",
    "new_trace_id",
]
