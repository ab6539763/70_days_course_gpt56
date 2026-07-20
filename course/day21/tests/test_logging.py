"""Day 14 结构化日志与 trace_id 单测。"""

import logging
import os
import sys
from io import StringIO
from pathlib import Path


SOLUTION = Path(__file__).parents[1] / "solution"
sys.path.insert(0, str(SOLUTION))

from nexus.config.env_loader import mask_secret
from nexus.observability.logging import (
    bind_trace_id,
    current_trace_id,
    get_logger,
    log_event,
    new_trace_id,
)


trace = bind_trace_id("testtrace00123456")
assert trace == "testtrace00123456"
assert current_trace_id() == "testtrace00123456"
assert len(new_trace_id()) == 16

logger = get_logger("test")
stream = StringIO()
handler = logging.StreamHandler(stream)
handler.setFormatter(
    logging.Formatter(
        "%(asctime)s trace_id=%(trace_id)s level=%(levelname)s "
        "logger=%(name)s event=%(message)s"
    )
)
logger.handlers.clear()
logger.addHandler(handler)
logger.addFilter(logging.Filter())

from nexus.observability.logging import TraceContextFilter

logger.addFilter(TraceContextFilter())
log_event(logger, 20, "unit_event", revision=3, api_key="must-not-leak")
output = stream.getvalue()
assert "trace_id=testtrace00123456" in output
assert "unit_event" in output
assert "must-not-leak" not in output
assert "(redacted)" in output

assert mask_secret("sk-abcdef1234") == "*********1234"

print("Day 14 日志单测通过：trace_id 绑定与敏感字段脱敏均正确。")
