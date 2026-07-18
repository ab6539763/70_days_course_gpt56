"""命令行应用主循环。"""

import json
import shutil
from pathlib import Path

from nexus.constants import APP_VERSION, DATA_FILE
from nexus.exceptions import DocumentLoadError, InvalidMessageError, PersistenceError, ApiCallError
from nexus.config.env_loader import loaded_env_path, mask_secret
from nexus.http.config import bootstrap_env, resolve_api_key, resolve_base_url, use_mock_mode
from nexus.observability.logging import bind_trace_id, current_trace_id
from nexus.persistence.storage import load_state, persist_change
from nexus.cli.prompts import prompt_contact, prompt_model_switch, prompt_owner
from nexus.cli.chat_assistant import run_chat_session
from nexus.config.window_config import resolve_history_window
from nexus.constants import DEFAULT_HISTORY_WINDOW, MAX_HISTORY_WINDOW
from nexus.config.session_config import ensure_session_dir, resolve_session_dir
from nexus.web.session_registry import SessionRegistry
from nexus.web.server import resolve_web_host, resolve_web_port, run_web_server


def run_cli(data_file=DATA_FILE):
    bind_trace_id()
    print("=" * 76)
    print(f"智枢 NexusAI {APP_VERSION}｜Phase2 断流恢复与 SSE resume")
    print(f"trace_id={current_trace_id()}")
    print("=" * 76)
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
            revision = persist_change(state, data_file)
        except PersistenceError as error:
            print(f"迁移保存失败：{error.message}。")
            return 2
        saved = json.loads(open(data_file, encoding="utf-8").read())
        version = saved.get("schema_version")
        print(
            f"Schema 已迁移至 v{version}｜revision={revision}｜"
            f"model={state.active_model()}。"
        )
    elif status == "loaded":
        print(
            f"恢复成功：revision={state.revision}｜"
            f"联系人={len(state.contacts)}｜消息={len(state.messages)}｜"
            f"语料={len(state.document_index.get('documents', []))}｜"
            f"模型={state.active_model()}。"
        )

    if state.owner is None:
        state.owner = prompt_owner()
        try:
            revision = persist_change(state, data_file)
        except PersistenceError as error:
            print(f"保存失败：{error.message}。")
            return 2
        print(f"维护人已保存｜revision={revision}。")

    while True:
        print(
            "\n1新增联系人 2查看联系人 3搜索 4新增消息 5消息历史 "
            "6统计 7摘要 8模型信息 9模拟对话 10导入语料 11语料检索 "
            "12API对话 13配置 14多轮助手 15Web工作台 16API契约 17Token窗口 18SSE流式 19会话隔离 20断流恢复 0退出"
        )
        choice = input("请选择：").strip()
        try:
            if choice == "1":
                changed, message = state.add_contact(prompt_contact())
                if changed:
                    revision = persist_change(state, data_file)
                    print(f"{message}｜revision={revision}。")
                else:
                    print(message)
            elif choice == "2":
                for contact in state.search_contacts("@"):
                    print(
                        f"{contact.contact_id}｜{contact.name}｜"
                        f"{contact.department}｜{contact.role}｜{contact.email}"
                    )
            elif choice == "3":
                matched = state.search_contacts(input("关键词："))
                print(f"搜索结果：{len(matched)} 名。")
                for contact in matched:
                    print(f"{contact.contact_id}｜{contact.name}｜{contact.role}")
            elif choice == "4":
                try:
                    changed, message = state.add_message(
                        input("角色："),
                        input("内容："),
                    )
                except InvalidMessageError as error:
                    print(error.message)
                    continue
                if changed:
                    revision = persist_change(state, data_file)
                    print(f"{message}｜revision={revision}。")
            elif choice == "5":
                print(f"消息总数：{len(state.messages)}。")
                for index, message in enumerate(state.messages, start=1):
                    print(f"{index}. {message.role}｜{message.preview()}")
            elif choice == "6":
                print(f"统计：{state.statistics()}")
            elif choice == "7":
                docs = len(state.document_index.get("documents", []))
                print(
                    f"摘要：schema=4｜revision={state.revision}｜"
                    f"contacts={len(state.contacts)}｜messages={len(state.messages)}｜"
                    f"documents={docs}｜model={state.active_model()}"
                )
            elif choice == "8":
                model = state.active_model()
                print(f"当前模型：{model}")
                print(f"repr：{model!r}")
                print(
                    "请求样例："
                    f"{model.format_request([{'role': 'user', 'content': 'ping'}])}"
                )
                switch = input("是否切换模型？(y/N)：").strip().lower()
                if switch == "y":
                    changed, message = prompt_model_switch(state)
                    if changed:
                        revision = persist_change(state, data_file)
                        print(f"{message}｜revision={revision}。")
                    else:
                        print(message)
            elif choice == "9":
                user_prompt = input("用户问题：").strip()
                if user_prompt == "":
                    print("用户问题不能为空。")
                    continue
                try:
                    changed, message, assistant_text = state.simulate_chat(user_prompt)
                except InvalidMessageError as error:
                    print(error.message)
                    continue
                if changed:
                    revision = persist_change(state, data_file)
                    print(f"{message}｜revision={revision}。")
                    print(f"assistant：{assistant_text}")
            elif choice == "10":
                corpus_dir = input("语料目录（默认 corpus）：").strip() or "corpus"
                keywords = input("关键词（逗号分隔）：").strip()
                try:
                    changed, message = state.ingest_corpus(corpus_dir, keywords)
                except DocumentLoadError as error:
                    print(error.message)
                    continue
                if changed:
                    corpus_path = Path(corpus_dir)
                    corpus_path.mkdir(parents=True, exist_ok=True)
                    revision = persist_change(state, data_file)
                    print(f"{message}｜revision={revision}。")
            elif choice == "11":
                keyword = input("检索关键词：").strip()
                if keyword == "":
                    print("关键词不能为空。")
                    continue
                matched = state.search_corpus(keyword)
                print(f"语料命中：{len(matched)} 份。")
                for record, hits in matched:
                    print(f"{record.doc_id}｜{record.filename}｜命中={hits}")
            elif choice == "12":
                user_prompt = input("API 用户问题：").strip()
                if user_prompt == "":
                    print("用户问题不能为空。")
                    continue
                if not use_mock_mode() and resolve_api_key() == "":
                    print("未设置 NEXUS_API_KEY。可 export NEXUS_USE_MOCK=1 做本地演示。")
                    continue
                try:
                    changed, message, assistant_text = state.api_chat(user_prompt)
                except (InvalidMessageError, ApiCallError) as error:
                    print(error.message)
                    continue
                if changed:
                    revision = persist_change(state, data_file)
                    print(f"{message}｜revision={revision}。")
                    print(f"assistant：{assistant_text}")
            elif choice == "13":
                bootstrap_env()
                model = state.active_model()
                print(
                    f"配置摘要：app={APP_VERSION}｜mock={use_mock_mode()}｜"
                    f"provider={model.PROVIDER}｜base={resolve_base_url(model.PROVIDER)}"
                )
                print(f"API Key：{mask_secret(resolve_api_key())}")
                env_path = loaded_env_path()
                print(f".env：{env_path if env_path else '未找到（可用 export 或 .env.example）'}")
            elif choice == "14":
                code = run_chat_session(state, data_file)
                if code != 0:
                    return code
            elif choice == "15":
                host = resolve_web_host()
                port = resolve_web_port()
                print(f"即将启动 Web 工作台：http://{host}:{port}")
                print(f"提示：也可使用 python main.py --web --port {port}")
                run_web_server(data_file=data_file, host=host, port=port)
            elif choice == "16":
                host = resolve_web_host()
                port = resolve_web_port()
                print(f"API 契约摘要：OpenAPI 3.0｜标准 error.code + error.message")
                print(f"文档地址：http://{host}:{port}/docs")
                print(f"规范 JSON：http://{host}:{port}/api/openapi.json")
                print("错误码：EMPTY_PROMPT / API_KEY_MISSING / UPSTREAM_API / PERSISTENCE 等")
                print("提示：先菜单15或 python main.py --web 启动服务后浏览器访问 /docs")
            elif choice == "17":
                snapshot = state.window_snapshot()
                print(
                    f"Token 窗口：默认={resolve_history_window()}｜"
                    f"上限={MAX_HISTORY_WINDOW}｜存储消息={len(state.messages)}"
                )
                print(
                    f"粗估 token：全量={snapshot['tokens_estimated_full']}｜"
                    f"窗口内={snapshot['tokens_estimated_sent']}｜"
                    f"window_applied={snapshot['window_applied']}"
                )
                print(
                    f"非 system：存储={snapshot['non_system_total']}｜"
                    f"发送={snapshot['non_system_sent']}｜history_window={snapshot['history_window']}"
                )
                print("环境变量：NEXUS_HISTORY_WINDOW｜Web API：max_history / GET /api/window")
            elif choice == "18":
                host = resolve_web_host()
                port = resolve_web_port()
                print("SSE 流式摘要：POST /api/chat/stream｜Content-Type text/event-stream")
                print("事件：chunk（delta 增量）→ done（revision/messages/window）")
                print(f"Web 工作台：http://{host}:{port}（chat.js 默认走流式端点）")
                print("Mock：NEXUS_USE_MOCK=1 按 NEXUS_STREAM_CHUNK_SIZE 切片模拟流式")
                if use_mock_mode():
                    state.add_message("user", "流式演示")
                    parts = []
                    model = state.active_model()
                    request_messages, window_meta = state.build_conversation_request()
                    for delta in model.iter_stream_deltas(request_messages, force_mock=True):
                        parts.append(delta)
                        print(f"  chunk: {delta!r}")
                    assistant = "".join(parts)
                    state.add_message("assistant", assistant)
                    revision = persist_change(state, data_file)
                    print(
                        f"演示完成：assistant 长度={len(assistant)}｜"
                        f"window_applied={window_meta.get('window_applied')}｜revision={revision}"
                    )
                else:
                    print("提示：设置 NEXUS_USE_MOCK=1 可在 CLI 本地演示 chunk 输出")
            elif choice == "19":
                session_dir = ensure_session_dir(resolve_session_dir())
                registry = SessionRegistry(session_dir=session_dir)
                print(f"会话隔离摘要：目录={session_dir}｜请求头 X-Session-Id")
                print("Web：POST /api/session 创建｜GET /api/sessions 列举")
                created = registry.create_session(owner="CLI_DEMO")
                print(
                    f"已创建演示会话：{created['session_id']}｜"
                    f"owner={created['owner']}｜revision={created['revision']}"
                )
                sessions = registry.list_sessions()
                print(f"当前会话数：{len(sessions)}")
                for item in sessions[:5]:
                    print(
                        f"  {item['session_id'][:20]}…｜owner={item['owner']}｜"
                        f"messages={item['messages']}｜revision={item['revision']}"
                    )
                if len(sessions) > 5:
                    print(f"  … 另有 {len(sessions) - 5} 个会话")
            elif choice == "20":
                from nexus.web.stream_resume import StreamResumeStore
                from nexus.web.state_manager import WebStateManager

                session_dir = ensure_session_dir(resolve_session_dir())
                registry = SessionRegistry(session_dir=session_dir)
                created = registry.create_session(owner="CLI_RESUME")
                session_id = created["session_id"]
                data_file = created["data_file"]
                store = StreamResumeStore()
                manager = WebStateManager(data_file=data_file, session_id=session_id)
                print(
                    f"断流恢复演示：session={session_id[:20]}…｜"
                    f"POST /api/chat/stream + resume_token"
                )
                if not use_mock_mode():
                    print("提示：设置 NEXUS_USE_MOCK=1 可在 CLI 本地演示断流与续传")
                else:
                    events = list(
                        manager.chat_stream(
                            "断流恢复演示",
                            resume_store=store,
                            interrupt_after=1,
                        )
                    )
                    interrupted = next(
                        (item for item in events if item["event"] == "interrupted"),
                        None,
                    )
                    if interrupted is None:
                        print("未触发断流")
                    else:
                        token = interrupted["payload"]["resume_token"]
                        partial = interrupted["payload"]["partial"]
                        print(
                            f"已中断：partial 长度={len(partial)}｜"
                            f"resume_token={token[:24]}…"
                        )
                        resumed = list(
                            manager.chat_stream(
                                resume_token=token,
                                resume_store=store,
                            )
                        )
                        done = next(
                            (item for item in resumed if item["event"] == "done"),
                            None,
                        )
                        if done:
                            assistant = done["payload"]["assistant"]
                            print(
                                f"续传完成：assistant 长度={len(assistant)}｜"
                                f"resumed={done['payload'].get('resumed')}"
                            )
                        else:
                            print("续传未完成")
            elif choice == "0":
                print(f"安全退出｜revision={state.revision}。")
                return 0
            else:
                print("菜单错误：仅支持0-20。")
        except PersistenceError as error:
            print(f"持久化错误：{error.message}。")
            return 2
