"""Web 服务器启动入口。"""

from __future__ import annotations

import os

from nexus.constants import DATA_FILE
from nexus.http.config import bootstrap_env
from nexus.observability.logging import bind_trace_id, current_trace_id, get_logger, log_event
from nexus.web.app import create_app


_web_logger = get_logger("web")


def resolve_web_host():
    return os.environ.get("NEXUS_WEB_HOST", "127.0.0.1").strip() or "127.0.0.1"


def resolve_web_port():
    raw = os.environ.get("NEXUS_WEB_PORT", "8080").strip()
    try:
        port = int(raw)
    except ValueError as error:
        raise ValueError(f"NEXUS_WEB_PORT 必须是整数：{raw}") from error
    if port <= 0 or port > 65535:
        raise ValueError(f"NEXUS_WEB_PORT 超出范围：{port}")
    return port


def run_web_server(data_file=DATA_FILE, host=None, port=None):
    """启动 Flask 开发服务器（阻塞）。"""
    bootstrap_env()
    bind_trace_id()
    host = host or resolve_web_host()
    port = port or resolve_web_port()
    app = create_app(data_file=data_file)
    url = f"http://{host}:{port}"
    log_event(_web_logger, 20, "web_server_start", url=url, trace_id=current_trace_id())
    print("=" * 76)
    print(f"智枢 NexusAI Web 对话工作台｜trace_id={current_trace_id()}")
    print(f"访问地址：{url}")
    print(f"API 文档：{url}/docs ｜ OpenAPI：{url}/api/openapi.json")
    print("API：GET /api/health  POST /api/chat  POST /api/clear  GET /api/messages")
    print("按 Ctrl+C 停止服务")
    print("=" * 76)
    app.run(host=host, port=port, debug=False, use_reloader=False)
