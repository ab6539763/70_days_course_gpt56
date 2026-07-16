"""NexusAI 0.0.16 主入口：CLI / 多轮对话 / Web / OpenAPI。"""

import argparse

from nexus.http.config import bootstrap_env
from nexus.cli.app import run_cli
from nexus.cli.chat_assistant import run_chat_session
from nexus.constants import DATA_FILE
from nexus.exceptions import PersistenceError
from nexus.observability.logging import bind_trace_id
from nexus.persistence.storage import load_state, persist_change
from nexus.cli.prompts import prompt_owner
from nexus.web.server import run_web_server, resolve_web_host, resolve_web_port


def _ensure_owner(state, data_file):
    if state.owner is not None:
        return 0
    state.owner = prompt_owner()
    try:
        revision = persist_change(state, data_file)
    except PersistenceError as error:
        print(f"保存失败：{error.message}。")
        return 2
    print(f"维护人已保存｜revision={revision}。")
    return 0


def run_chat_only(data_file=DATA_FILE):
    bind_trace_id()
    bootstrap_env()
    try:
        state, status, error = load_state(data_file)
    except PersistenceError as error:
        print(f"持久化错误：{error.message}。")
        return 2
    if status == "rejected":
        print(f"数据拒绝：{error}。")
        return 3
    if status == "migrated":
        try:
            persist_change(state, data_file)
        except PersistenceError as error:
            print(f"迁移保存失败：{error.message}。")
            return 2
    owner_code = _ensure_owner(state, data_file)
    if owner_code != 0:
        return owner_code
    return run_chat_session(state, data_file)


def main():
    parser = argparse.ArgumentParser(description="智枢 NexusAI 0.0.16")
    parser.add_argument(
        "--chat",
        action="store_true",
        help="直接进入多轮对话助手（slash 命令）",
    )
    parser.add_argument(
        "--web",
        action="store_true",
        help="启动 Web 对话工作台（Flask）",
    )
    parser.add_argument(
        "--host",
        default=None,
        help="Web 监听地址（默认 NEXUS_WEB_HOST 或 127.0.0.1）",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="Web 端口（默认 NEXUS_WEB_PORT 或 8080）",
    )
    args = parser.parse_args()
    bootstrap_env()
    if args.web:
        try:
            run_web_server(
                data_file=DATA_FILE,
                host=args.host or resolve_web_host(),
                port=args.port or resolve_web_port(),
            )
        except ValueError as error:
            print(f"Web 配置错误：{error}。")
            raise SystemExit(1) from error
        raise SystemExit(0)
    if args.chat:
        raise SystemExit(run_chat_only())
    raise SystemExit(run_cli())


if __name__ == "__main__":
    main()
