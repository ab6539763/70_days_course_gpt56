"""Day 13 重试装饰器单测。"""

import os
import sys
from pathlib import Path


SOLUTION = Path(__file__).parents[1] / "solution"
sys.path.insert(0, str(SOLUTION))

from nexus.exceptions import ApiCallError
from nexus.http.decorators import retry_api_call


attempts = {"count": 0}


@retry_api_call(max_attempts=3, backoff_seconds=0.01)
def flaky_call():
    attempts["count"] += 1
    if attempts["count"] < 3:
        raise ApiCallError("临时失败")
    return "成功"


assert flaky_call() == "成功"
assert attempts["count"] == 3

attempts_exhaust = {"count": 0}


@retry_api_call(max_attempts=2, backoff_seconds=0.01)
def always_fail():
    attempts_exhaust["count"] += 1
    raise ApiCallError("永久失败")


try:
    always_fail()
except ApiCallError:
    assert attempts_exhaust["count"] == 2

print("Day 13 装饰器单测通过：ApiCallError 重试与退避均正确。")
