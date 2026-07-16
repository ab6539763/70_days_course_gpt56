"""多轮对话助手：slash 命令与持久化会话。"""

from __future__ import annotations

from nexus.exceptions import ApiCallError, InvalidMessageError, PersistenceError
from nexus.http.config import resolve_api_key, use_mock_mode
from nexus.observability.logging import bind_trace_id, format_trace_prefix, get_logger, log_event
from nexus.persistence.storage import persist_change


CHAT_PROMPT = "你> "
SLASH_COMMANDS = ("/help", "/clear", "/save", "/exit", "/history")
HELP_TEXT = (
    "多轮对话助手命令：\n"
    "  /help    显示帮助\n"
    "  /clear   清空对话历史（保留 system 可选）\n"
    "  /save    立即持久化当前会话\n"
    "  /history 查看最近消息摘要\n"
    "  /exit    退出对话模式\n"
    "直接输入文字将与 AI 多轮对话；会话自动写入 nexus_platform.json。"
)


def _print_history(state, limit=10):
    messages = state.messages[-limit:]
    print(f"最近 {len(messages)} 条消息（共 {len(state.messages)} 条）：")
    for index, message in enumerate(messages, start=1):
        print(f"  {index}. {message.role}｜{message.preview()}")


def _handle_slash(command, state, data_file, logger):
    if command == "/help":
        print(HELP_TEXT)
        return "continue", None
    if command == "/clear":
        changed, message = state.clear_messages(keep_system=True)
        log_event(logger, 20, "chat_clear", keep_system=True, count=len(state.messages))
        print(message)
        return "continue", None
    if command == "/save":
        try:
            revision = persist_change(state, data_file)
        except PersistenceError as error:
            log_event(logger, 40, "chat_save_failed", error=error.message)
            return "error", error.message
        log_event(logger, 20, "chat_save", revision=revision)
        print(f"会话已保存｜revision={revision}。")
        return "continue", None
    if command == "/history":
        _print_history(state)
        return "continue", None
    if command == "/exit":
        log_event(logger, 20, "chat_exit", messages=len(state.messages))
        print(f"退出对话模式｜{format_trace_prefix()}｜消息={len(state.messages)}。")
        return "exit", None
    print(f"未知命令：{command}。输入 /help 查看可用命令。")
    return "continue", None


def run_chat_session(state, data_file, system_prompt="你是企业助手"):
    """进入多轮对话 REPL；返回进程退出码。"""
    trace_id = bind_trace_id()
    logger = get_logger("chat")
    log_event(
        logger,
        20,
        "chat_start",
        trace_id=trace_id,
        mock=use_mock_mode(),
        messages=len(state.messages),
    )
    print("=" * 76)
    print(f"智枢 NexusAI 多轮对话助手｜{format_trace_prefix()}")
    print("=" * 76)
    print(HELP_TEXT)
    if not use_mock_mode() and resolve_api_key() == "":
        print("提示：未设置 NEXUS_API_KEY，请 export NEXUS_USE_MOCK=1 做本地演示。")

    while True:
        try:
            user_input = input(CHAT_PROMPT).strip()
        except EOFError:
            log_event(logger, 20, "chat_eof")
            print("\n输入结束，退出对话。")
            return 0
        if user_input == "":
            continue
        if user_input.startswith("/"):
            action, error_message = _handle_slash(user_input.split()[0], state, data_file, logger)
            if action == "exit":
                return 0
            if action == "error":
                print(f"保存失败：{error_message}。")
            continue
        if not use_mock_mode() and resolve_api_key() == "":
            print("未设置 NEXUS_API_KEY。可 export NEXUS_USE_MOCK=1 做本地演示。")
            continue
        try:
            changed, message, assistant_text = state.conversation_turn(
                user_input,
                system_prompt=system_prompt,
            )
        except InvalidMessageError as error:
            log_event(logger, 30, "chat_invalid", error=error.message)
            print(error.message)
            continue
        except ApiCallError as error:
            log_event(logger, 40, "chat_api_error", error=error.message)
            print(error.message)
            continue
        if changed:
            try:
                revision = persist_change(state, data_file)
            except PersistenceError as error:
                log_event(logger, 40, "chat_persist_failed", error=error.message)
                print(f"持久化错误：{error.message}。")
                return 2
            log_event(
                logger,
                20,
                "chat_turn",
                revision=revision,
                user_len=len(user_input),
                assistant_len=len(assistant_text),
            )
            print(f"{message}｜revision={revision}。")
            print(f"assistant> {assistant_text}")
