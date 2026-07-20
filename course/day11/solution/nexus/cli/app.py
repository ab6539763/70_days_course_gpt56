"""命令行应用主循环。"""

import json
import shutil
from pathlib import Path

from nexus.constants import APP_VERSION, DATA_FILE
from nexus.exceptions import DocumentLoadError, InvalidMessageError, PersistenceError
from nexus.persistence.storage import load_state, persist_change
from nexus.cli.prompts import prompt_contact, prompt_model_switch, prompt_owner


def run_cli(data_file=DATA_FILE):
    print("=" * 76)
    print(f"智枢 NexusAI {APP_VERSION}｜语料导入与关键词统计")
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
            "6统计 7摘要 8模型信息 9模拟对话 10导入语料 11语料检索 0退出"
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
            elif choice == "0":
                print(f"安全退出｜revision={state.revision}。")
                return 0
            else:
                print("菜单错误：仅支持0-11。")
        except PersistenceError as error:
            print(f"持久化错误：{error.message}。")
            return 2
