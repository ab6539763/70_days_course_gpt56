"""HTTP 调用装饰器：重试与超时治理。"""

from __future__ import annotations

import functools
import os
import time
from typing import Any, Callable, TypeVar

from nexus.exceptions import ApiCallError


F = TypeVar("F", bound=Callable[..., Any])

ENV_RETRY = "NEXUS_API_RETRY"
ENV_BACKOFF = "NEXUS_API_BACKOFF"


def retry_api_call(
    max_attempts: int | None = None,
    backoff_seconds: float | None = None,
) -> Callable[[F], F]:
    """对 ApiCallError 进行有限次重试（指数退避）。"""

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            attempts = max_attempts or int(os.environ.get(ENV_RETRY, "3"))
            backoff = backoff_seconds or float(os.environ.get(ENV_BACKOFF, "0.05"))
            last_error: ApiCallError | None = None
            for attempt in range(1, attempts + 1):
                try:
                    return func(*args, **kwargs)
                except ApiCallError as error:
                    last_error = error
                    if attempt >= attempts:
                        raise
                    time.sleep(backoff * attempt)
            if last_error is not None:
                raise last_error
            raise ApiCallError("重试装饰器异常退出")

        return wrapper  # type: ignore[misc]

    return decorator
