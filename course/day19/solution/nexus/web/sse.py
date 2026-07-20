"""Server-Sent Events (SSE) 响应构造。"""

from __future__ import annotations

import json
from typing import Any, Dict, Generator, Iterable

from flask import Response


def format_sse_event(event: str, data: Dict[str, Any]) -> str:
    """格式化单条 SSE 事件。"""
    encoded = json.dumps(data, ensure_ascii=False)
    return f"event: {event}\ndata: {encoded}\n\n"


def sse_response(events: Iterable[str]) -> Response:
    """把已格式化的 SSE 字符串序列包装为 Flask Response。"""
    def generate() -> Generator[str, None, None]:
        for item in events:
            yield item

    return Response(
        generate(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


def stream_from_generator(generator: Iterable[str]) -> Response:
    """从 SSE 字符串生成器创建 Response。"""
    return sse_response(generator)
