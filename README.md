# 零基础大模型应用开发 70 天课程

本仓库以“智枢 NexusAI 企业智能协作平台”为单一项目主线，模拟业务、产品、开发、测试、安全与运维团队从需求到上线的完整协作过程。课程每天形成可运行增量，不使用彼此割裂的演示项目。

## 当前内容

- [70 天贯穿式项目蓝图](docs/course-blueprint.md)
- [Day 1 完整课件：从业务问题到第一段可验收代码](course/day01/day01-lesson.md)
- Day 1 [课堂起步代码](course/day01/starter/profile_card.py)
- Day 1 [带详细注释的参考实现](course/day01/solution/profile_card.py)
- Day 1 [自动验收脚本](course/day01/tests/test_profile_card.py)
- [Day 2 完整课件：字符串、运算符与输入治理](course/day02/day02-lesson.md)
- Day 2 [文本清洗参考实现](course/day02/solution/text_cleaner.py)
- Day 2 [端到端功能测试](course/day02/tests/test_text_cleaner.py)
- Day 2 [发布链路测试](course/day02/tests/test_release.py)

## Day 1 运行

```bash
python course/day01/solution/profile_card.py
python course/day01/tests/test_profile_card.py
python3 tools/verify_day01.py
```

课件中的 Mermaid 图可在支持 Mermaid 的 Markdown 阅读器中直接渲染。
质量门禁会检查 Day 1 课件不少于 30,000 个 Unicode 字符、必备教学章节、
Mermaid 图数量以及参考代码验收结果。

## Day 2 运行、测试与发布

```bash
python3 course/day02/solution/text_cleaner.py
python3 course/day02/tests/test_text_cleaner.py
python3 course/day02/tests/test_release.py
python3 tools/verify_day02.py
python3 course/day02/deploy/build_release.py --output artifacts/day02
```

Day 2 质量门禁同时执行真实 CLI 端到端测试和发布包的构建、SHA-256
校验、解压及独立目录部署冒烟测试。

## Day 3 校验、测试与发布

- [Day 3 完整课件：条件、循环与可恢复交互](course/day03/day03-lesson.md)
- [带详细注释的可校验治理 CLI](course/day03/solution/validated_cleaner.py)
- [控制流与锁定端到端测试](course/day03/tests/test_validated_cleaner.py)
- [发布部署链测试](course/day03/tests/test_release.py)

```bash
python3 course/day03/solution/validated_cleaner.py
python3 course/day03/tests/test_validated_cleaner.py
python3 course/day03/tests/test_release.py
python3 tools/verify_day03.py
python3 course/day03/deploy/build_release.py --output artifacts/day03
```

Day 3 门禁覆盖无效输入重试、三次身份失败退出码、部门白名单、数值范围、
空敏感片段防护、人工复核路由、菜单恢复、零泄漏、发布完整性及部署冒烟。

## Day 4 多任务台账、测试与发布

- [Day 4 完整课件：列表、元组、集合与任务台账](course/day04/day04-lesson.md)
- [带详细注释的任务台账 CLI](course/day04/solution/task_board.py)
- [CRUD 与一致性端到端测试](course/day04/tests/test_task_board.py)
- [发布部署链测试](course/day04/tests/test_release.py)

```bash
python3 course/day04/solution/task_board.py
python3 course/day04/tests/test_task_board.py
python3 course/day04/tests/test_release.py
python3 tools/verify_day04.py
python3 course/day04/deploy/build_release.py --output artifacts/day04
```

Day 4 门禁覆盖多任务 CRUD、优先级排序、前三条切片、标签标准化去重、
列表与编号集合一致性、批量清理、编号复用、身份锁定及独立部署后 CRUD。

## Day 5 字典、JSON 持久化与发布

- [Day 5 完整课件：字典、JSON Schema 与持久化](course/day05/day05-lesson.md)
- [JSON 持久化任务台账](course/day05/solution/persistent_task_board.py)
- [首次/恢复/版本拒绝测试](course/day05/tests/test_persistence.py)
- [无数据制品与部署恢复测试](course/day05/tests/test_release.py)

```bash
python3 course/day05/solution/persistent_task_board.py
python3 course/day05/tests/test_persistence.py
python3 course/day05/tests/test_release.py
python3 tools/verify_day05.py
python3 course/day05/deploy/build_release.py --output artifacts/day05
```

Day 5 门禁覆盖字典模型、UTF-8 JSON、schema_version、revision、首次初始化、
跨进程恢复、CRUD 落盘、未知版本拒绝、空文件初始化及运行数据不进入制品。

## Day 6 函数化服务、测试与发布

- [Day 6 完整课件：函数、参数、返回值与作用域](course/day06/day06-lesson.md)
- [函数化 JSON 任务服务](course/day06/solution/functional_task_board.py)
- [函数单元测试](course/day06/tests/test_functions.py)
- [CLI 双进程测试](course/day06/tests/test_cli.py)
- [发布部署测试](course/day06/tests/test_release.py)

```bash
python3 course/day06/solution/functional_task_board.py
python3 course/day06/tests/test_functions.py
python3 course/day06/tests/test_cli.py
python3 course/day06/tests/test_release.py
python3 tools/verify_day06.py
python3 course/day06/deploy/build_release.py --output artifacts/day06
```

Day 6 门禁覆盖位置/关键字/默认参数、`*args/**kwargs`、返回值、作用域、
可变默认隔离、CRUD 函数契约、递归边界、主入口、CLI 与部署恢复。

## Day 7 第一周阶段项目与周测

- [Day 7 完整课件：企业联系人目录与第一周周测](course/day07/day07-lesson.md)
- [联系人目录参考实现](course/day07/solution/contact_directory.py)
- [联系人函数单测](course/day07/tests/test_functions.py)
- [双进程 CLI 测试](course/day07/tests/test_cli.py)
- [发布部署测试](course/day07/tests/test_release.py)

```bash
python3 course/day07/solution/contact_directory.py
python3 course/day07/tests/test_functions.py
python3 course/day07/tests/test_cli.py
python3 course/day07/tests/test_release.py
python3 tools/verify_day07.py
python3 course/day07/deploy/build_release.py --output artifacts/day07
```

Day 7 综合门禁覆盖联系人编号/模拟邮箱双唯一、五字段搜索、岗位更新、
部门与技能统计、JSON 跨进程恢复、第一周周测、隐私边界和独立部署。

## Day 8 面向对象模型与 Schema 迁移

- [Day 8 完整课件：Contact、ChatMessage 与平台状态对象](course/day08/day08-lesson.md)
- [面向对象平台参考实现](course/day08/solution/oop_platform.py)
- [领域模型与迁移单测](course/day08/tests/test_models.py)
- [对象 CLI 双进程测试](course/day08/tests/test_cli.py)
- [发布部署测试](course/day08/tests/test_release.py)

```bash
python3 course/day08/solution/oop_platform.py
python3 course/day08/tests/test_models.py
python3 course/day08/tests/test_cli.py
python3 course/day08/tests/test_release.py
python3 tools/verify_day08.py
python3 course/day08/deploy/build_release.py --output artifacts/day08
```

Day 8 门禁覆盖类与实例、`__init__`、实例/类/静态方法、对象 JSON 往返、
Contact/ChatMessage 聚合、Schema v1→v2 迁移和部署后消息恢复。

## Day 9 模型继承、多态与 Schema v3

- [Day 9 完整课件：BaseModel、OpenAIModel 与 QwenModel](course/day09/day09-lesson.md)
- [多供应商模型平台参考实现](course/day09/solution/model_platform.py)
- [继承与多态单测](course/day09/tests/test_models.py)
- [模型 CLI 双进程测试](course/day09/tests/test_cli.py)
- [发布部署测试](course/day09/tests/test_release.py)

```bash
python3 course/day09/solution/model_platform.py
python3 course/day09/tests/test_models.py
python3 course/day09/tests/test_cli.py
python3 course/day09/tests/test_release.py
python3 tools/verify_day09.py
python3 course/day09/deploy/build_release.py --output artifacts/day09
```

Day 9 门禁覆盖继承、`super()`、多态、`@property`、`__str__`/`__repr__`/`__call__`、
`create_model` 工厂、Schema v2→v3 迁移、模型切换持久化、模拟对话与 Day1-8 历史回归。

## Day 10 模块化包、异常处理与发布

- [Day 10 完整课件：模块、包、异常与 requirements](course/day10/day10-lesson.md)
- [nexus 模块化平台参考实现](course/day10/solution/)
- [包结构与异常单测](course/day10/tests/test_modules.py)
- [模块化 CLI 双进程测试](course/day10/tests/test_cli.py)
- [包结构发布部署测试](course/day10/tests/test_release.py)

```bash
cd course/day10/solution && PYTHONPATH=. python3 main.py
cd course/day10/solution && PYTHONPATH=. python3 -m nexus
python3 course/day10/tests/test_modules.py
python3 course/day10/tests/test_cli.py
python3 course/day10/tests/test_release.py
python3 tools/verify_day10.py
python3 course/day10/deploy/build_release.py --output artifacts/day10
```

Day 10 门禁覆盖包结构拆分、绝对导入、`if __name__ == "__main__"`、五类自定义异常、
try/except 退出码、requirements.txt、发布无 pycache/运行数据与 Day1-9 历史回归。

## Day 11 文件操作、语料导入与 RAG 前置

- [Day 11 完整课件：pathlib、UTF-8、正则与批量语料](course/day11/day11-lesson.md)
- [语料平台参考实现](course/day11/solution/)
- [语料模块与迁移单测](course/day11/tests/test_documents.py)
- [语料 CLI 双进程测试](course/day11/tests/test_cli.py)
- [语料发布部署测试](course/day11/tests/test_release.py)

```bash
cd course/day11/solution && PYTHONPATH=. python3 main.py
python3 course/day11/tests/test_documents.py
python3 course/day11/tests/test_cli.py
python3 course/day11/tests/test_release.py
python3 tools/verify_day11.py
python3 course/day11/deploy/build_release.py --output artifacts/day11
```

Day 11 门禁覆盖 pathlib 语料发现、UTF-8/with 读取、csv/json 解析、re 关键词统计、
Schema v3→v4 迁移、CLI 语料导入检索、示例 corpus  fixtures 与 Day1-10 历史回归。

## Day 12 HTTP API 与首次模型调用

- [Day 12 完整课件：HTTP、requests 与 Chat Completions](course/day12/day12-lesson.md)
- [HTTP API 平台参考实现](course/day12/solution/)
- [API 与 Mock 服务器单测](course/day12/tests/test_api.py)
- [API CLI 双进程测试](course/day12/tests/test_cli.py)
- [API 发布部署测试](course/day12/tests/test_release.py)

```bash
pip install -r course/day12/solution/requirements.txt
export NEXUS_API_KEY=your-key   # 或 export NEXUS_USE_MOCK=1 演示
cd course/day12/solution && PYTHONPATH=. python3 main.py
python3 course/day12/tests/test_api.py
python3 course/day12/tests/test_cli.py
python3 course/day12/tests/test_release.py
python3 tools/verify_day12.py
python3 course/day12/deploy/build_release.py --output artifacts/day12
```

Day 12 门禁覆盖 HTTP/requests、Bearer 鉴权、Chat Completions 解析、Mock API 测试、
菜单 12 真实 API 对话、菜单 9 模拟回退、Key 不入库与 Day1-11 历史回归。

## Day 13 dotenv、装饰器重试与类型注解

- [Day 13 完整课件：dotenv、装饰器、生成器与 API 重试](course/day13/day13-lesson.md)
- [配置与重试平台参考实现](course/day13/solution/)
- [dotenv/装饰器/生成器单测](course/day13/tests/test_dotenv.py)
- [API 重试与 Mock 测试](course/day13/tests/test_api.py)
- [配置 CLI 与发布测试](course/day13/tests/test_cli.py)

```bash
pip install -r course/day13/solution/requirements.txt
cp course/day13/solution/.env.example course/day13/solution/.env
cd course/day13/solution && PYTHONPATH=. python3 main.py
python3 tools/verify_day13.py
python3 course/day13/deploy/build_release.py --output artifacts/day13
```

Day 13 门禁覆盖 python-dotenv、@retry_api_call、类型注解、yield 消息迭代、
菜单 13 配置脱敏、API 重试与 Day1-12 历史回归。

## Day 14 Phase1 收官：多轮对话助手与结构化日志

- [Day 14 完整课件：多轮对话、slash 命令、trace_id 与 Phase1 MVP](course/day14/day14-lesson.md)
- [多轮对话助手参考实现](course/day14/solution/)
- [日志与 trace 单测](course/day14/tests/test_logging.py)
- [多轮对话单测](course/day14/tests/test_chat.py)
- [CLI 与 --chat 测试](course/day14/tests/test_cli.py)
- [发布部署测试](course/day14/tests/test_release.py)

```bash
pip install -r course/day14/solution/requirements.txt
cp course/day14/solution/.env.example course/day14/solution/.env
cd course/day14/solution && PYTHONPATH=. python3 main.py --chat
python3 tools/verify_day14.py
python3 course/day14/deploy/build_release.py --output artifacts/day14
```

Day 14 门禁覆盖多轮 history 持久化、slash 命令、结构化日志 trace_id、
菜单 14 与 `--chat`、发布 ZIP 与 Day1-13 历史回归。

## Day 15 Phase2 开篇：Flask Web 对话工作台

- [Day 15 完整课件：Flask、REST API 与 Web 首屏](course/day15/day15-lesson.md)
- [Web 工作台参考实现](course/day15/solution/)
- [Flask Web API 单测](course/day15/tests/test_web.py)
- [CLI 与 --web 测试](course/day15/tests/test_cli.py)
- [Web 发布部署测试](course/day15/tests/test_release.py)

```bash
pip install -r course/day15/solution/requirements.txt
export NEXUS_USE_MOCK=1
cd course/day15/solution && PYTHONPATH=. python3 main.py --web
python3 tools/verify_day15.py
python3 course/day15/deploy/build_release.py --output artifacts/day15
```

Day 15 门禁覆盖 Flask Web 路由、REST 多轮 API、Jinja2 首屏、
`main.py --web`、发布 ZIP 与 Day1-14 历史回归。

## Day 16 API 契约、OpenAPI 与标准错误码

- [Day 16 完整课件：OpenAPI 3.0、ErrorResponse、Swagger UI](course/day16/day16-lesson.md)
- [API 契约参考实现](course/day16/solution/)
- [OpenAPI 与校验单测](course/day16/tests/test_contract.py)
- [Web API 集成测试](course/day16/tests/test_web.py)
- [发布部署测试](course/day16/tests/test_release.py)

```bash
pip install -r course/day16/solution/requirements.txt
export NEXUS_USE_MOCK=1
cd course/day16/solution && PYTHONPATH=. python3 main.py --web
# 浏览器访问 /docs 与 /api/openapi.json
python3 tools/verify_day16.py
python3 course/day16/deploy/build_release.py --output artifacts/day16
```

Day 16 门禁覆盖 OpenAPI 3.0、标准 error.code、请求校验、Swagger UI、
菜单 16 与 Day1-15 历史回归。

## Day 17 Token 窗口、take_last 与 history 治理

- [Day 17 完整课件：Token 窗口、max_history、NEXUS_HISTORY_WINDOW](course/day17/day17-lesson.md)
- [Token 窗口参考实现](course/day17/solution/)
- [窗口与粗估单测](course/day17/tests/test_window.py)
- [Web API 窗口集成测试](course/day17/tests/test_web.py)
- [发布部署测试](course/day17/tests/test_release.py)

```bash
pip install -r course/day17/solution/requirements.txt
export NEXUS_USE_MOCK=1
export NEXUS_HISTORY_WINDOW=20
cd course/day17/solution && PYTHONPATH=. python3 main.py --web
# GET /api/window 与 POST /api/chat max_history
python3 tools/verify_day17.py
python3 course/day17/deploy/build_release.py --output artifacts/day17
```

Day 17 门禁覆盖 take_last 窗口、token 粗估、持久化与发送分离、
max_history、GET /api/window、OpenAPI WindowMeta、菜单 17 与 Day1-16 历史回归。

## Day 18 SSE 流式、delta 与 Web 实时体验

- [Day 18 完整课件：SSE、text/event-stream、chat/stream](course/day18/day18-lesson.md)
- [SSE 流式参考实现](course/day18/solution/)
- [流式与 delta 单测](course/day18/tests/test_stream.py)
- [Web SSE 集成测试](course/day18/tests/test_web.py)
- [发布部署测试](course/day18/tests/test_release.py)

```bash
pip install -r course/day18/solution/requirements.txt
export NEXUS_USE_MOCK=1
cd course/day18/solution && PYTHONPATH=. python3 main.py --web
# 浏览器流式对话；curl -N POST /api/chat/stream
python3 tools/verify_day18.py
python3 course/day18/deploy/build_release.py --output artifacts/day18
```

Day 18 门禁覆盖 SSE 流式、delta、conversation_turn_stream、窗口约束叠加、
POST /api/chat/stream、OpenAPI StreamDoneEvent、菜单 18 与 Day1-17 历史回归。

## Day 19 会话隔离、X-Session-Id 与多用户 state

- [Day 19 完整课件：会话隔离、SessionRegistry、独立 JSON](course/day19/day19-lesson.md)
- [会话隔离参考实现](course/day19/solution/)
- [Session 与隔离单测](course/day19/tests/test_session.py)
- [Web 会话 API 集成测试](course/day19/tests/test_web.py)
- [发布部署测试](course/day19/tests/test_release.py)

```bash
pip install -r course/day19/solution/requirements.txt
export NEXUS_USE_MOCK=1
export NEXUS_SESSION_DIR=sessions
cd course/day19/solution && PYTHONPATH=. python3 main.py --web
# POST /api/session → X-Session-Id 请求头
python3 tools/verify_day19.py
python3 course/day19/deploy/build_release.py --output artifacts/day19
```

Day 19 门禁覆盖一会话一文件、X-Session-Id、SESSION_REQUIRED、
多用户隔离、GET /api/sessions、OpenAPI SessionHeader、菜单 19 与 Day1-18 历史回归。

## Day 20 SSE 断流恢复、resume_token 与续传

- [Day 20 完整课件：断流恢复、interrupted、StreamResumeStore](course/day20/day20-lesson.md)
- [断流恢复参考实现](course/day20/solution/)
- [断流恢复单测](course/day20/tests/test_resume.py)
- [Web 断流 API 集成测试](course/day20/tests/test_web.py)
- [发布部署测试](course/day20/tests/test_release.py)

```bash
pip install -r course/day20/solution/requirements.txt
export NEXUS_USE_MOCK=1
export NEXUS_SESSION_DIR=sessions
export NEXUS_STREAM_RESUME_TTL=300
cd course/day20/solution && PYTHONPATH=. python3 main.py --web
# X-Stream-Simulate-Interrupt: 1 模拟断流 → resume_token 续传
python3 tools/verify_day20.py
python3 course/day20/deploy/build_release.py --output artifacts/day20
```

Day 20 门禁覆盖 interrupted 事件、resume_token、GET /api/stream/resume、
INVALID_RESUME、RESUME_EXPIRED、OpenAPI StreamChatRequest、菜单 20 与 Day1-19 历史回归。

## 内容原则

1. 每天均包含业务上下文、需求文档、架构或流程图、课堂笔记、代码、测试、作业与答案。
2. 每个新增能力必须说明它如何承接前一天并成为后续平台能力的输入。
3. 代码量只统计有效源代码、测试和基础设施，不用重复或生成垃圾内容凑数。
4. 示例一律使用虚构数据；密钥和真实个人敏感信息不得进入仓库。
