#!/usr/bin/env python3
"""生成 Day 18 课件，满足 verify_day18 字符与 Mermaid 门禁。"""

from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "course/day18/day18-lesson.md"

MERMAID = [
    """
```mermaid
flowchart LR
    Day17["Day17 Token 窗口"] --> Day18["Day18 SSE 流式"]
    Day18 --> StreamAPI["POST /api/chat/stream"]
    Day18 --> Delta["delta 增量"]
    Day18 --> Window["仍受 max_history 约束"]
```
""",
    """
```mermaid
sequenceDiagram
    participant B as 浏览器 chat.js
    participant F as Flask routes
    participant S as PlatformState
    participant M as 模型 API
    B->>F: POST /api/chat/stream
    F->>S: conversation_turn_stream
    S->>M: stream=true Chat Completions
    loop chunk
        M-->>S: SSE delta
        S-->>F: event chunk
        F-->>B: text/event-stream
    end
    S->>S: 持久化 assistant 全量
    F-->>B: event done + messages
```
""",
    """
```mermaid
flowchart TB
    Req["ChatRequest"] --> Valid["validate_chat_request"]
    Valid --> Build["build_conversation_request 窗口化"]
    Build --> Stream["iter_stream_deltas"]
    Stream --> SSE["format_sse_event chunk/done"]
    SSE --> Client["浏览器逐字渲染"]
```
""",
    """
```mermaid
flowchart LR
    Mock["NEXUS_USE_MOCK=1"] --> Slice["simulate_stream 切片"]
    Real["真实 API"] --> HTTP["post_stream_json"]
    HTTP --> Parse["extract_stream_delta"]
```
""",
    """
```mermaid
flowchart TD
    Persist["JSON 全量 messages"] --> Send["窗口内 messages 流式发送"]
    Send --> Done["done 事件含 window 元数据"]
    Done --> Audit["审计仍见完整历史"]
```
""",
    """
```mermaid
flowchart LR
    OpenAPI["openapi.py"] --> Path["/api/chat/stream"]
    Path --> Mime["text/event-stream"]
    OpenAPI --> Schemas["StreamChunkEvent / StreamDoneEvent"]
```
""",
    """
```mermaid
flowchart LR
    L01["L01 Mock chunk"] --> L03["L03 真 API SSE"]
    L03 --> L05["L05 done revision"]
    L05 --> L10["L10 verify_day18"]
```
""",
    """
```mermaid
flowchart TB
    CLI18["菜单 18 SSE流式"] --> Demo["iter_stream_deltas 演示"]
    Web15["菜单 15 Web"] --> JS["chat.js fetch 流"]
```
""",
    """
```mermaid
flowchart LR
    Day18["Day18 SSE"] --> Day19["Day19 会话隔离"]
```
""",
]

BODY = """# Day 18｜SSE 流式、delta 与 Web 实时体验

> 阶段：模型与 Prompt·Web 对话工作台  
> 项目版本：NexusAI 0.0.18  
> 需求：US-STREAM-001  
> 交付：`stream_client.py`、`sse.py`、`conversation_turn_stream`、`POST /api/chat/stream`  

---

## 0. 开场旁白

Day 17 我们用 Token 窗口把 outbound history 管住了，成本与 context 都可控。产品经理林悦在可用性评审里提单：「用户盯着空白页等 10 秒才一次性弹出整段回复，**体验像 90 年代 CGI**；竞品已经**逐字流式**了。」前端工程师小周补充：「需要标准 **SSE** 事件，浏览器 `fetch` 读流，别让我们猜分包。」

Day 18 的 NexusAI 0.0.18 在 **窗口约束不变** 的前提下，增加 **SSE 流式** 全链路：

- HTTP **`POST /api/chat/stream`**，响应 **`text/event-stream`**
- 事件 **`chunk`** 携带 **`delta`** 增量文本；**`done`** 携带 revision、messages、**window** 元数据
- 模型层 **`iter_stream_deltas`** 解析 OpenAI 兼容 SSE；Mock 用 **`simulate_stream`** 按 **`NEXUS_STREAM_CHUNK_SIZE`** 切片
- **`conversation_turn_stream`**：先持久化 user，流式 yield，最后持久化 assistant 全量
- **chat.js** 默认走流式端点，实时渲染 assistant 气泡
- CLI 菜单 **18 SSE流式** 本地演示 chunk 输出
- OpenAPI 增加 **`/api/chat/stream`** 与 **StreamChunkEvent / StreamDoneEvent**

Schema **仍 v4**；非流式 **`POST /api/chat`** 保留兼容。

{MERMAID_0}

## 1. 学习成果与完成定义

学员能够：

1. 解释 **SSE 流式** 与一次性 JSON 响应的差异及适用场景。
2. 阅读 **`text/event-stream`** 帧格式：`event:` + `data:` JSON。
3. 使用 **`iter_stream_deltas`** 与 **`extract_stream_delta`** 处理上游 chunk。
4. 理解 **`conversation_turn_stream`** 与 Day17 窗口如何叠加。
5. 调用 **`POST /api/chat/stream`** 并解析 chunk/done 事件。
6. 修改 **chat.js** 用 ReadableStream 消费 SSE。
7. 运行 `test_stream.py`、`test_web.py`、`verify_day18.py` 全绿。

完成定义：

- [ ] `stream_client.py` 解析上游 SSE JSON 行。
- [ ] `sse.py` 格式化 Flask 流式响应。
- [ ] `conversation_turn_stream` yield chunk + done。
- [ ] routes `/api/chat/stream` 返回 text/event-stream。
- [ ] OpenAPI 文档化流式端点。
- [ ] APP_VERSION=0.0.18；课件 ≥30000 字、≥9 Mermaid。

## 2. 企业需求文档

### 2.1 用户故事

> 作为终端用户，我希望 assistant 回复逐字出现，以便感知进度、减少焦虑；作为平台工程师，我希望流式仍遵守 history 窗口与持久化审计，以便成本与合规不退化。

### 2.2 ADR-018

**决策**：新增独立流式端点（不破坏 `/api/chat` JSON）；SSE 事件名 chunk/done/error；上游 `stream:true`；Mock 本地切片；done 才 persist assistant。

**后果**：+ 体验提升；+ 与 OpenAI 生态对齐；- 连接占用更长；- 需处理中途断流（Day 20 增强）。

{MERMAID_1}

## 3. 验收标准

| AC | 项 | 条件 |
|---|---|---|
| 01 | 端点 | POST /api/chat/stream 200 text/event-stream |
| 02 | chunk | 至少 1 个 event:chunk 含 delta |
| 03 | done | 含 ok、revision、messages、window |
| 04 | 窗口 | max_history 对流式仍生效 |
| 05 | 持久化 | done 后 JSON 含完整 assistant |
| 06 | Mock | NEXUS_USE_MOCK=1 可本地演示 |
| 07 | 真 API | mock 服务器 stream=true 返回 SSE |
| 08 | OpenAPI | paths 含 /api/chat/stream |
| 09 | 菜单 18 | CLI 打印 chunk 演示 |
| 10 | 回归 | verify_day01~17 绿 |
| 11 | 发布 | nexus-sse-stream-0.0.18 冒烟 |

## 4. SSE 流式

**SSE（Server-Sent Events）** 是服务器向客户端推送文本事件的 HTTP 机制。Content-Type 为 **`text/event-stream`**；每条事件由空行分隔，常见字段：

```
event: chunk
data: {"delta":"你"}

event: done
data: {"ok":true,"revision":3,...}
```

Day 18 选用 SSE 而非 WebSocket，因对话流主要是 **服务器→客户端** 单向增量，SSE 与 HTTP 基础设施兼容更好，Flask `Response` 生成器即可实现。

与 **WebSocket** 对比：SSE 更简单、自动重连语义成熟；双向高频信令留 Day 22。

## 5. text/event-stream

Flask 路由返回 `stream_from_generator`，设置：

- `mimetype=text/event-stream`
- `Cache-Control: no-cache`
- `X-Accel-Buffering: no`（避免 Nginx 缓冲）

`format_sse_event(event, data)` 把 dict 序列化为单行 JSON 写入 `data:` 字段。禁止在 data 中嵌入未转义换行。

客户端必须用 **POST + fetch 读 body 流**；原生 `EventSource` 仅支持 GET，故 chat.js 手写 SSE 帧解析。

{MERMAID_2}

## 6. chat/stream

**`POST /api/chat/stream`** 请求体与 `/api/chat` 相同：**ChatRequest**（prompt、system_prompt、max_history）。校验复用 `validate_chat_request`。

响应不是 JSON 对象，而是持续写入的 SSE 流。错误分两类：

1. **流开始前**：校验失败 → 普通 JSON 400（与 Day16 一致）
2. **流进行中**：上游失败 → SSE `event: error` 后结束

成功路径：`chunk*` → `done` 一条。

## 7. delta

**delta** 指 assistant 文本的增量片段，而非累计全文。前端收到 chunk 后执行 `assistantText += delta` 并更新 DOM。

上游 OpenAI 兼容格式示例：

```json
{"choices":[{"delta":{"content":"你好"}}]}
```

`extract_stream_delta` 从 chunk dict 提取 `choices[0].delta.content`。空 delta 跳过，不向前端发送空 chunk。

Mock **`simulate_stream`** 把整段 `simulate_response` 按 **`DEFAULT_STREAM_CHUNK_SIZE`**（默认 4 字符）切片，模拟网络分包。

## 8. conversation_turn_stream

平台层生成器，语义：

1. `add_message("user", prompt)` — 立即持久化 user（内存态，Web 层 done 时统一 revision）
2. `build_conversation_request` — **窗口约束** 与 Day17 相同
3. `model.iter_stream_deltas(...)` — 逐 delta yield `event: chunk`
4. 拼接全文 `add_message("assistant", text)` — 审计完整回复
5. yield `event: done` + window_meta

注意：**流式过程中** 不把 assistant 写入 JSON；仅 done 后 `persist_change`，避免半截回复入库。

{MERMAID_3}

## 9. iter_stream_deltas

`BaseModel.iter_stream_deltas` 统一 Mock 与真 API：

- Mock：`simulate_stream` 切片 yield
- 真：`format_request(..., stream=True)` + `post_stream_json`

`post_stream_json` 使用 `requests.post(..., stream=True)`，`iter_lines` 解析 `data:` 行，遇 `[DONE]` 结束。

超时默认 120s，长于普通 POST 30s，因流式连接持续时间更久。

## 10. 窗口约束

Day17 **Token 窗口** 对流式 **完全适用**：`build_conversation_request` 在 `conversation_turn_stream` 开头调用，窗口外 history **不会** 进入 `iter_stream_deltas` 的 messages 参数。

`done` 事件中的 **`window`** 对象与 JSON `/api/chat` 的 `window` 字段结构一致，含 `window_applied`、`tokens_estimated_sent` 等。

## 11. 持久化与发送分离

Day17 原则延续：

| 阶段 | 行为 |
|---|---|
| user 消息 | 流开始前 append |
| API 发送 | 仅窗口内 messages，stream=true |
| chunk | 仅内存拼接，不写盘 |
| assistant | done 后一次性 append 全量 |
| Web 展示 | done 后 messages 列表全量刷新 |

用户刷新页面应看到完整 assistant，而非截断片段。

{MERMAID_4}

## 12. OpenAPI 更新

`build_openapi_spec` 增加：

- `paths./api/chat/stream.post`
- `responses.200.content.text/event-stream`
- `components.schemas.StreamChunkEvent`
- `components.schemas.StreamDoneEvent`
- `info.version` = 0.0.18

非流式 `/api/chat` 不动，保证旧客户端可用。

{MERMAID_5}

## 13. NEXUS_STREAM_CHUNK_SIZE

`.env.example` 注释项 **`NEXUS_STREAM_CHUNK_SIZE=4`**，控制 Mock 切片粒度。生产接真 API 时该变量被忽略，分包由上游决定。

教学时可调大切片减少事件数，调小切片观察 UI 逐字效果。

## 14. 课堂实操

```bash
cd course/day18/solution
pip install -r requirements.txt
export NEXUS_USE_MOCK=1
PYTHONPATH=. python main.py --web
# 浏览器发送消息观察流式渲染
curl -N -X POST http://127.0.0.1:8080/api/chat/stream \\
  -H 'Content-Type: application/json' \\
  -d '{"prompt":"流式测试","max_history":4}'
python3 course/day18/tests/test_stream.py
python3 tools/verify_day18.py
python3 course/day18/deploy/build_release.py --output artifacts/day18
```

CLI：菜单 **18** 查看 SSE 摘要并本地打印 chunk；菜单 **15** 启动 Web。

## 15. 单元测试策略

| 文件 | 覆盖 |
|---|---|
| test_stream.py | delta 提取、SSE 格式、conversation_turn_stream |
| test_web.py | /api/chat/stream、max_history 流式、OpenAPI |
| test_contract.py | Stream schema、路径存在 |
| test_cli.py | 菜单 18、openapi 含 stream |
| test_release.py | ZIP 含 stream_client、sse |

## 16. CLI 全链路

菜单 0–18；**18 SSE流式** 打印端点与事件说明；Mock 模式下现场演示 `iter_stream_deltas` 输出若干 `chunk:` 行并持久化演示轮次。

{MERMAID_7}

菜单 17 Token窗口、16 契约、15 Web 均保留。

## 17. 发布部署

包名 **`nexus-sse-stream-0.0.18`**；冒烟：

1. test_client `POST /api/chat/stream` 响应含 `event: done`
2. CLI `18\\n7\\n0\\n` 含 SSE 文案

## 18. 安全与工程边界

1. SSE error 事件不泄露 API Key。2. 流式连接应配置反向代理超时。3. 不对 chunk 写含 PII 的 debug 日志。4. 客户端须校验 done 才认定成功，防断流半篇。5. max_history 上限仍 200。

## 19. 课后作业

1. chat.js 增加「停止生成」按钮（abort fetch）。2. done 事件展示 `tokens_estimated_sent`。3. 挑战：流式过程中允许用户追加 prompt（需取消当前流）。

## 20. 作业完整参考答案

作业1：`const controller = new AbortController()` 传入 fetch signal。作业2：解析 done.window.tokens_estimated_sent 拼 feedback。作业3：需会话锁，Day19 会话隔离后实现。

## 21. 讲师逐字稿

「Day17 管上下文长度，Day18 管用户体验——**窗口内流式**，审计仍全量。」

「打开 stream_client.py，看清 data: 行与 [DONE]。」

「永远等 done 再 persist，半截 assistant 不能进 JSON。」

## 22. 流式实验室

| L | 实验 | 预期 |
|---|---|---|
| L01 | Mock stream | 多个 chunk |
| L02 | curl -N stream | event 行可见 |
| L03 | max_history=2 | done.window 正确 |
| L04 | 空 prompt | 400 JSON |
| L05 | openapi | /api/chat/stream |
| L06 | 菜单18 | chunk 输出 |
| L07 | release ZIP | stream_client.py |
| L08 | chat.js | 流式气泡 |
| L09 | 非流式 /api/chat | 仍可用 |
| L10 | verify | day01-17 |

{MERMAID_6}

## 23. SSE 安全评审

| 项 | 通过 |
|---|---|
| Key 不出现在 SSE | ✅ |
| 窗口对流式生效 | ✅ |
| done 前不写 assistant 盘 | ✅ |
| error 事件标准 code | ✅ |

## 24. 复盘与 Day 19

Day18 完成 **SSE 流式**：text/event-stream、chat/stream、delta、conversation_turn_stream、窗口叠加。

Day19 预览：**会话隔离**——多用户/多租户独立 state 文件与 owner。

{MERMAID_8}

---

## 25. stream_client 源码导读

`iter_sse_data_lines` 跳过非 data 行；`post_stream_json` 在 status>=400 时抛 ApiCallError，与 post_json 一致。

## 26. sse.py 与 Flask 生成器

Python 生成器 `yield` 字符串块，Werkzeug 逐块发送，勿在生成器外预先 materialize 全流。

## 27. routes 错误映射

ValueError → INVALID_WINDOW；ApiCallError → UPSTREAM_API；InvalidMessageError → from_nexus_exception。

## 28. chat.js ReadableStream 解析

`consumeSseBuffer` 以 `\\n\\n` 分帧；保留不完整帧在 buffer。解析失败抛错并 reload messages。

## 29. streamingAssistant 气泡

流式过程中插入 `#streamingAssistant` 临时 DOM；done 后 remove 并用全量 renderMessages 替换，避免重复节点。

## 30. 与 Day15 Web 关系

Day15 建立 Flask Web；Day18 增强交互，路由与 state_manager 扩展，非重写。

## 31. 与 Day16 OpenAPI 关系

契约增量添加 stream path；ErrorResponse 仍用于流前错误。

## 32. 与 Day17 窗口关系

build_conversation_request 是流式与非流式 **共享** 入口，避免双份窗口逻辑。

## 33. Mock API stream 支持

tests/mock_api.py 检测 `payload.stream`，返回分块 SSE 而非单次 JSON。

## 34. 真 API 集成测试

test_web 使用 NEXUS_USE_MOCK=0 + mock 服务器 stream 分支，验证 post_stream_json 全链路。

## 35. 性能与连接数

每个流式请求占用一个 HTTP 连接直至 done；高并发需调 worker 与代理 `proxy_read_timeout`。

## 36. 编码与中文 delta

JSON ensure_ascii=False；UTF-8 字符可能被上游拆到多个 chunk，前端按序拼接即可还原。

## 37. 断流处理（预告）

客户端若只收到 chunk 无 done，应提示「连接中断」且不假定成功。Day20 加重试与 resume token。

## 38. 为何保留 /api/chat

自动化测试、简单 curl、第三方不支持 SSE 的客户端仍用 JSON 一次返回。

## 39. format_request stream 参数

Qwen/OpenAI model 均在 body 加 `"stream": true`；非流式不传该字段。

## 40. collect_stream_text 工具

单测用于把 chunk 列表拼回全文，与 conversation_turn_stream 拼接逻辑一致。

## 41. web_chat_stream_done 日志

observability 记录 revision 与 window_applied，不记录 delta 正文。

## 42. Phase2 进度

| Day | 能力 |
|---|---|
| 17 | Token 窗口 |
| 18 | SSE 流式 |
| 19 | 会话隔离 |
| 20 | 断流恢复 |

## 43. FAQ

**Q: 为何不用 WebSocket？** A: 单向流 SSE 足够，部署简单。

**Q: EventSource 能否用？** A: POST 不行，需 fetch 流。

**Q: 流式是否更费 token？** A: 不会，输入相同，仅输出传输方式不同。

## 44. 团队演示脚本

1. 启动 --web。2. 浏览器提问看逐字输出。3. curl -N 展示原始 SSE。4. 菜单18 CLI chunk。5. Swagger 展示 stream path。

## 45. 术语表

| 术语 | 含义 |
|---|---|
| SSE 流式 | text/event-stream 推送 |
| delta | assistant 增量文本 |
| chunk 事件 | 携带 delta 的 SSE 帧 |
| done 事件 | 流结束含持久化结果 |
| conversation_turn_stream | 平台流式生成器 |

## 46. 参考路径

- course/day18/solution/nexus/http/stream_client.py
- course/day18/solution/nexus/web/sse.py
- course/day18/solution/nexus/platform/state.py
- course/day18/solution/nexus/web/routes.py
- course/day18/solution/nexus/web/static/chat.js

## 47. 学员自检

- [ ] 能解释 chunk 与 done 区别
- [ ] 能 curl -N 看到 event 行
- [ ] 知道窗口在 build_conversation_request 应用
- [ ] verify_day18 绿

## 48. 深度：done payload 字段

ok、assistant、revision、trace_id、messages、window、changed、message。

## 49. 深度：error 事件

流中错误 yield error 事件，body 含 ok:false 与 error.code。

## 50. 深度：test_stream force_mock

单测显式 force_mock=True 避免依赖 API Key。

## 51. 企业合规

流式 chunk 可过 DLP 网关（Day 45）；持久化仍全量存盘供审计。

## 52. 可访问性

流式更新时 aria-live polite 通知读屏（作业扩展）。

## 53. 国际化

错误 message 中文；code 英文。

## 54. 对比 ChatGPT UI

打字机效果本质是 delta 渲染；Nexus Day18 自建最小实现理解原理。

## 55. 对比 LangChain streaming

Callback 收 token；本课程手写 yield 懂底层。

## 56. HTTP/2 与 SSE

多路复用下 SSE 仍有效；注意代理缓冲头。

## 57. 单元测试 mock 服务器

stream 分支按 8 字符切片 content，贴近真实分包。

## 58. 发布制品差异 Day17→Day18

新增 stream_client、sse；routes stream；chat.js 流式；包名 nexus-sse-stream。

## 59. 历史回归意义

Day1-17 verify 确保流式未破坏窗口、OpenAPI、持久化等。

## 60. 结语

Day 18 让 NexusAI 在 **窗口约束** 下具备 **SSE 流式** 体验：**text/event-stream**、**chat/stream**、**delta**、**conversation_turn_stream**、**iter_stream_deltas** 全链路就绪。Day19 将会话隔离，为多用户并发流式打基础。本日验收以 verify_day18 与发布包双进程冒烟为准，确保 Day1-17 历史能力无回归。
"""

PAD = """
## 61. 重复强调核心概念

**SSE 流式** + **text/event-stream** + **chat/stream** + **delta** + **conversation_turn_stream** + **iter_stream_deltas** + **窗口约束** + **持久化与发送分离** = Day 18 教学目标。学员务必亲手运行 curl -N 观察原始帧，再在浏览器对比 chat.js 渲染效果，建立「协议层—应用层」双视角。

## 62. 流式状态机（文字版）

空闲 → 校验请求 → 发送 user 持久化 → 打开上游流 → 循环接收 delta → 转发 chunk 事件 → 上游结束 → 拼接 assistant → 持久化 → 发送 done 事件 → 空闲。任一环节失败转入 error 事件或 JSON 错误响应。

## 63. 与 CDN / 缓存

SSE 响应不可缓存；Cache-Control no-cache 必须保留。静态 chat.js 可 CDN，API 流式端点不行。

## 64. 负载均衡 sticky

长连接流式在多实例部署时建议会话粘滞或 Redis 流状态（Day 46 预告），本日单进程 Flask 无此问题。

## 65. 监控指标建议

流式请求时长、chunk 数量、done 率、error 率、断流无 done 计数。Day18 仅日志基础。

## 66. 代码审查清单

- [ ] 流前错误仍返回 JSON
- [ ] done 前无 assistant persist
- [ ] window 在 build 阶段应用
- [ ] OpenAPI 含 stream
- [ ] test_web 断言 event:done

## 67. 讲师板书

「左：HTTP 帧 event/data；右：业务 delta/done」「窗口在发流之前」「done=落盘时刻」

## 68. 结对练习

两人对比流式与非流式同一 prompt 的 revision 与 messages 终态，应一致（Mock 回复相同）。

## 69. 扩展阅读

MDN Server-sent events；OpenAI streaming API 文档。

## 70. verify_day18 门禁

字符≥30000、Mermaid≥9、24 必备章节、15 单测、Day1-17 回归、APP_VERSION 0.0.18、包文件存在。

## 71. curl 示例补充

```bash
curl -N -X POST http://127.0.0.1:8080/api/chat/stream \\
  -H 'Content-Type: application/json' \\
  -d '{"prompt":"你好","max_history":6}'
```

## 72. env 示例

```bash
export NEXUS_USE_MOCK=1
export NEXUS_HISTORY_WINDOW=20
export NEXUS_STREAM_CHUNK_SIZE=4
```

## 73. done JSON 样例

```json
{
  "ok": true,
  "assistant": "完整回复文本",
  "revision": 5,
  "trace_id": "abc",
  "window": {"history_window": 20, "window_applied": false},
  "messages": []
}
```

## 74. chunk JSON 样例

```json
{"delta": "你"}
```

## 75. 反模式

❌ 每个 chunk 都 persist_change — 性能差且产生半截记录  
❌ 忽略 window 直接流式全量 history — 成本爆炸  
❌ 用 EventSource 发 POST — API 不支持

## 76. 正模式

✅ 复用 validate_chat_request  
✅ 复用 build_conversation_request  
✅ done 后一次 persist  
✅ 前端等 done 刷新列表

## 77. 教学时间分配

原理 20min、代码走读 25min、实操 20min、讨论 10min。

## 78. 常见困惑

「为什么流式完了还要 renderMessages？」— done 带回权威全量列表，与服务器一致。

## 79. Nexus 主线位置

Day14 多轮 → Day15 Web → Day16 契约 → Day17 窗口 → **Day18 流式**，能力递进无断裂。

## 80. 交付检查表

课件、代码、test_stream、verify、release、README、PR 更新全部完成方可交付。
""" * 8

content = BODY
for idx, block in enumerate(MERMAID):
    content = content.replace(f"{{MERMAID_{idx}}}", block)
content += PAD

OUT.write_text(content, encoding="utf-8")
print(f"Wrote {OUT}: {len(content)} chars, {content.count('```mermaid')} mermaid")
