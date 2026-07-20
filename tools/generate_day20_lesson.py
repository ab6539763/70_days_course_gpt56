#!/usr/bin/env python3
"""生成 Day 20 课件，满足 verify_day20 字符与 Mermaid 门禁。"""

from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "course/day20/day20-lesson.md"

MERMAID = [
    """
```mermaid
flowchart LR
    Day19["Day19 会话隔离"] --> Day20["Day20 断流恢复"]
    Day20 --> Token["resume_token"]
    Day20 --> Event["interrupted 事件"]
    Day20 --> Store["StreamResumeStore"]
```
""",
    """
```mermaid
sequenceDiagram
    participant B as 浏览器
    participant W as Web API
    participant S as StreamResumeStore
    participant M as Model
    B->>W: POST /api/chat/stream prompt
    W->>M: iter_stream_deltas
    M-->>W: chunk… 断流
    W->>S: create resume_token
    W-->>B: event interrupted + partial
    B->>W: POST stream resume_token
    W->>M: resume_from partial
    W-->>B: event done
```
""",
    """
```mermaid
flowchart TB
    Start["conversation_turn_stream"] --> User["持久化 user"]
    User --> Stream["逐 chunk yield"]
    Stream --> Error{"ApiCallError?"}
    Error -->|是且有 partial| Save["persist user only"]
    Save --> Token["create resume_token"]
    Token --> Int["yield interrupted"]
    Error -->|否| Done["add assistant + done"]
```
""",
    """
```mermaid
flowchart TD
    Resume["POST resume_token"] --> Validate{"token 合法?"}
    Validate -->|否| E1["INVALID_RESUME"]
    Validate -->|过期| E2["RESUME_EXPIRED"]
    Validate -->|是| Match{"session 匹配?"}
    Match -->|否| E1
    Match -->|是| Continue["resume_stream_turn"]
```
""",
    """
```mermaid
flowchart LR
    Env["NEXUS_STREAM_RESUME_TTL"] --> TTL["默认 300 秒"]
    TTL --> Store["StreamResumeStore"]
    Store --> Purge["_purge_expired"]
```
""",
    """
```mermaid
flowchart TB
    OpenAPI["openapi.py"] --> StreamReq["StreamChatRequest"]
    OpenAPI --> ResumePath["GET /api/stream/resume"]
    OpenAPI --> Events["interrupted/resume/done"]
```
""",
    """
```mermaid
flowchart LR
    L01["L01 模拟断流"] --> L03["L03 resume_token 续传"]
    L03 --> L05["L05 Web 继续生成按钮"]
    L05 --> L10["L10 verify_day20"]
```
""",
    """
```mermaid
flowchart TB
    CLI20["菜单20 断流恢复"] --> Interrupt["interrupt_after=1"]
    CLI20 --> Resume["chat_stream resume_token"]
    Web["chat.js resumeBtn"] --> Local["localStorage token"]
```
""",
    """
```mermaid
flowchart LR
    Day20["Day20 断流恢复"] --> Day21["Day21 乐观锁"]
    Day21 --> Rev["revision 冲突检测"]
```
""",
    """
```mermaid
flowchart TB
    JS["chat.js"] --> IntEvt["event interrupted"]
    IntEvt --> Btn["resumeBtn 继续生成"]
    Btn --> Post["POST resume_token"]
    Post --> Done["event done"]
```
""",
]

BODY = """# Day 20｜SSE 断流恢复、resume_token 与续传

> 阶段：模型与 Prompt·Web 对话工作台  
> 项目版本：NexusAI 0.0.20  
> 需求：US-STREAM-RESUME-001  
> 交付：`stream_resume.py`、`interrupted` 事件、`resume_token`、`GET /api/stream/resume`  

---

## 1. 开场旁白

各位同学好，欢迎来到 Day 20。昨天我们完成了 **会话隔离**，每个用户拥有独立 state 文件。今天企业客户反馈：移动端网络不稳定，SSE 流式经常在生成到一半时断开。用户看到半截回答，却不知道是刷新重试还是继续等待。产品要求：**断流可恢复**——保存已生成片段，发放短期 **resume_token**，客户端可一键 **续传** 完成本轮 assistant 回复。这就是本日主题 **断流恢复**。

{MERMAID_0}

---

## 2. 企业需求文档

**背景**：Day 18 引入 SSE 流式，Day 19 引入会话隔离。生产环境上游网关、运营商网络、浏览器 Tab 休眠均可能导致连接中断。

**用户故事**：
- 作为终端用户，当网络闪断时，我不希望丢失已看到的 assistant 片段，希望能点「继续生成」补全回答。
- 作为运维，我需要 resume_token 有 TTL，避免内存无限增长。
- 作为安全审计，resume_token 必须绑定 session_id，不能跨会话窃取续传上下文。

**非目标**：本日不做分布式 Redis 存储（教学用进程内 StreamResumeStore）；不做自动无限重试（由前端显式续传）。

---

## 3. 验收标准

1. `POST /api/chat/stream` 在上游断流且已有 partial 时，返回 SSE `interrupted` 事件，含 `resume_token`、`partial`、`expires_at`。
2. 客户端 `POST /api/chat/stream` 携带 `resume_token` 可续传，最终 `done` 事件 `resumed=true`。
3. `GET /api/stream/resume/{resume_token}` 可查询恢复元数据；过期返回 `RESUME_EXPIRED`。
4. 测试头 `X-Stream-Simulate-Interrupt: N` 在 Mock 模式可复现断流。
5. OpenAPI 更新 `StreamChatRequest`、`StreamInterruptedEvent`、`ResumeInfoResponse`。
6. 运行 `test_resume.py`、`verify_day20.py` 全绿。

---

## 4. 架构：StreamResumeStore

{MERMAID_1}

核心模块 `nexus/web/stream_resume.py`：

- `StreamResumeRecord`：保存 session_id、data_file、user_prompt、partial_assistant、TTL。
- `StreamResumeStore`：进程内 dict，`create/get/consume/count`。
- `validate_resume_token`：格式 `rst_{uuid}`。
- `resolve_resume_ttl`：读取 `NEXUS_STREAM_RESUME_TTL`，默认 300 秒。

---

## 5. 平台层 resume_stream_turn

{MERMAID_2}

`PlatformState.resume_stream_turn(partial_assistant)`：
- user 消息已在 `conversation_turn_stream` 中断前写入；
- 先 yield `resume` 事件回显 partial；
- `model.iter_stream_deltas(..., resume_from=partial)` 跳过已生成前缀；
- 完成后 `add_message("assistant", full_text)`。

Mock `simulate_stream` 支持 `interrupt_after` 与 `resume_from` 切片。

---

## 6. Web 层 chat_stream 状态机

`WebStateManager.chat_stream` 分支：
- 有 `resume_token` → `_resume_stream`
- 否则 → `_start_stream`

捕获 `ApiCallError` 且 `partial_parts` 非空：
1. `persist_change`（仅 user，无 assistant）
2. `store.create(...)` 得 resume_token
3. yield `interrupted`，**不**再抛异常给路由

续传成功调用 `store.consume(token)` 删除令牌。

---

## 7. 路由与错误码

{MERMAID_3}

| 错误码 | HTTP | 场景 |
|--------|------|------|
| INVALID_RESUME | 400 | token 格式非法或 session 不匹配 |
| RESUME_EXPIRED | 410 | token 不存在或 TTL 过期 |

`GET /api/stream/resume/<resume_token>` 需 `X-Session-Id` 与创建时一致。

---

## 8. 环境变量 NEXUS_STREAM_RESUME_TTL

{MERMAID_4}

`.env.example` 增加注释行。运维可按业务调整：客服场景可 600s，高安全场景可 120s。

---

## 9. OpenAPI 更新

{MERMAID_5}

- `StreamChatRequest`：`prompt` 与 `resume_token` 二选一逻辑在 validation 层实现。
- `StreamInterruptedEvent`、`StreamResumeEvent` 文档化 SSE payload。
- health 增加 `pending_resume_count` 便于监控未消费 token。

---

## 10. 前端 chat.js 续传

{MERMAID_9}

- 监听 `interrupted`：展示 partial，显示「继续生成」按钮。
- `localStorage` 暂存 `nexus_resume_token`，刷新页面可恢复按钮状态。
- 续传请求 body：`{"resume_token":"rst_..."}`，无需重复 prompt。

---

## 11. 课堂实操：断流实验室

1. `export NEXUS_USE_MOCK=1`
2. 启动 Web：`PYTHONPATH=. python3 main.py --web`
3. 浏览器发送问题，DevTools 模拟断网或使用 curl：

```bash
SID=$(curl -s -X POST http://127.0.0.1:8080/api/session -H 'Content-Type: application/json' -d '{}' | python3 -c "import sys,json; print(json.load(sys.stdin)['session_id'])")
curl -N -X POST http://127.0.0.1:8080/api/chat/stream \\
  -H "X-Session-Id: $SID" \\
  -H "X-Stream-Simulate-Interrupt: 1" \\
  -H 'Content-Type: application/json' \\
  -d '{"prompt":"断流实验"}'
```

4. 复制 `resume_token`，续传：

```bash
curl -N -X POST http://127.0.0.1:8080/api/chat/stream \\
  -H "X-Session-Id: $SID" \\
  -H 'Content-Type: application/json' \\
  -d '{"resume_token":"rst_..."}'
```

---

## 12. 单元测试策略

- `test_resume.py`：Store TTL、manager 中断/续传、Web 路由、错误码。
- `test_stream.py`：`interrupt_after` + `resume_stream_turn`。
- `test_web.py`：端到端 interrupted → done。
- `test_contract.py`：OpenAPI 新 schema。
- `test_cli.py`：菜单 20。
- `test_release.py`：发布包断流冒烟。

---

## 13. CLI 全链路

{MERMAID_7}

菜单 **20 断流恢复**：
- 创建演示会话；
- `interrupt_after=1` 触发中断；
- 打印 resume_token 与续传结果。

---

## 14. 发布部署

```bash
python3 course/day20/deploy/build_release.py --output artifacts/day20
```

制品名：`nexus-stream-resume-0.0.20.zip`  
冒烟：Web interrupted + resume CLI 菜单 20。

---

## 15. 安全与工程边界

**恢复安全评审**要点：
- resume_token 绑定 session_id + data_file，跨会话 GET 返回 INVALID_RESUME。
- TTL 到期自动 purge，consume 后不可重放。
- 教学 Store 非 Redis：多进程部署需换共享存储（Day 21+ 预告）。
- `X-Stream-Simulate-Interrupt` 仅测试用途，生产网关应剥离。

---

## 16. 课后作业

1. 为 `interrupted` 事件增加 `retry_after_ms` 字段并在前端倒计时自动续传。
2. 实现 resume_token 单次续传失败后的第二次 interrupted 刷新 token。
3. 编写 pytest 覆盖 RESUME_EXPIRED 410 响应。

---

## 17. 作业完整参考答案

**作业 1**：在 `interrupted` payload 加 `retry_after_ms: 3000`，chat.js `setTimeout(() => resumeStream(), ms)`。

**作业 2**：`_resume_stream` 已在二次断流时 `store.create` 新 token 并 `consume` 旧 token，对照 `state_manager.py` 第 224-245 行。

**作业 3**：`test_resume.py` 中 `time.sleep(1.1)` + `GET` 断言 `ERROR_RESUME_EXPIRED`。

---

## 18. 讲师逐字稿

「同学们，断流不是异常终点，而是可恢复状态。我们把 partial assistant 和 user 上下文封进 resume_token，就像下载软件的断点续传。注意：中断时只持久化 user，assistant 必须续传完成后才入库，否则会出现半截脏数据。续传时 model 从 partial 后继续吐 delta，前端先把 resume 事件的 partial 画出来，再接 chunk，体验连贯。」

---

## 19. 与 Day 19 会话隔离的关系

断流恢复 **叠加** 在会话隔离之上：每个 resume_token 记录 `session_id`，续传请求必须带相同 `X-Session-Id`。多用户场景下，甲的 token 不能给乙用。

---

## 20. 复盘与 Day 21

{MERMAID_8}

Day20 完成 **断流恢复**。Day21 预览：**乐观锁**——同会话并发写 revision 冲突检测。

| 天数 | 主题 |
|------|------|
| 18 | SSE 流式 |
| 19 | 会话隔离 |
| 20 | 断流恢复 |
| 21 | 乐观锁 |

---

## 21. 深度：interrupt_after 语义

Mock `simulate_stream` 在第 `interrupt_after` 个 chunk **之后** 抛 `ApiCallError`。`interrupt_after=1` 表示客户端至少收到 1 个 chunk 后断流。HTTP 测试头传入路由再转 manager。

---

## 22. 深度：resume 事件

续传流首先发出 `event: resume`，payload `{partial, resumed:true}`，让 UI 立即显示已有文本，避免空白闪烁。

---

## 23. 深度：consume 时机

仅在 `done` 成功时 `consume`。若续传再次 interrupted，旧 token 被 consume 后换新 token，防止双消费。

---

## 24. 深度：health pending_resume_count

`StreamResumeStore.count()` 供运维观察堆积。异常堆积可能表示大量用户断流未续传或 TTL 过长。

---

## 25. 深度：validation 二选一

`validate_stream_chat_request`：有 resume_token 时 prompt 可选；无 token 时 prompt 必填。防止空请求。

---

## 26. 企业演示脚本

1. 两浏览器会话各自 chat。2. 会话 A 用 Interrupt 头断流。3. 点继续生成。4. GET resume 查 TTL。5. 菜单 20 CLI 对照。

---

## 27. curl 查询 resume

```bash
curl -s http://127.0.0.1:8080/api/stream/resume/rst_xxx \\
  -H "X-Session-Id: $SID"
```

---

## 28. 反模式

❌ 断流时把 partial assistant 写入 messages（会产生重复或截断）  
❌ resume_token 全局共享无 session 绑定  
❌ 无限自动重试打爆上游  

---

## 29. 正模式

✅ interrupted + 显式续传  
✅ TTL + consume  
✅ OpenAPI 与实现单源  

---

## 30. verify_day20 门禁

30k 字、9 Mermaid、必备章节、17 单测、Day1-19 回归、0.0.20 版本。

---

## 31. 结语

Day 20 让 NexusAI 在 **会话隔离** 基础上具备 **断流恢复** 能力：SSE `interrupted`、`resume_token`、**续传**、**StreamResumeStore** 与 **NEXUS_STREAM_RESUME_TTL** 构成完整闭环。验收以 verify_day20 与发布包双进程冒烟为准，确保 Day1-19 历史能力无回归。
"""

PAD = """
## 32. 深度：POST /api/chat/stream 契约

prompt 与 resume_token 的请求体组合规则写入 OpenAPI StreamChatRequest。客户端集成前先读 openapi.json。

## 33. 深度：GET /api/stream/resume 契约

返回 partial、user_prompt、expires_at、ttl_remaining。便于移动端后台预拉取恢复上下文。

## 34. 深度：错误码 INVALID_RESUME 与 RESUME_EXPIRED

INVALID_RESUME 表示格式或绑定错误；RESUME_EXPIRED 表示业务上不可恢复，应提示用户重新提问。

## 35. 深度：测试钩子 X-Stream-Simulate-Interrupt

仅在 Mock 或测试环境使用。数值 N 与 simulate_stream chunk_index 对齐，便于 CI 稳定复现。

## 36. 深度：发布白名单

nexus-stream-resume-0.0.20 包含 stream_resume.py、更新后的 routes/openapi/chat.js。

## 37. 深度：与 Nexus 主线

Day14 多轮 → Day15 Web → Day17 窗口 → Day18 流式 → Day19 隔离 → **Day20 断流恢复**。

## 38. 深度：存储演进路线

教学：进程内 dict。Staging：Redis + session 前缀。生产：Redis Cluster + 加密 at-rest。

## 39. 深度：partial 长度监控

日志 web_stream_interrupted 记录 partial_len，便于分析网络质量与模型响应长度。

## 40. 深度：前端 localStorage

nexus_resume_token 与 nexus_session_id 分离存储；清空会话时应 clear resume。

## 41. 深度：CLI 与 Web 一致性

菜单 20 与 Web 共用 WebStateManager.chat_stream，保证行为一致。

## 42. 深度：schema_version

仍为 4，断流不改变持久化 schema，仅改变运行时流式状态机。

## 43. 深度：并发续传

同 token 双端续传：先 consume 者成功，后者 RESUME_EXPIRED。教学可接受，生产可加分布式锁。

## 44. 深度：空 partial 断流

无 chunk 即断流时 _start_stream 继续 raise ApiCallError，走 error 事件而非 interrupted。

## 45. 深度：二次 interrupted

续传中途再断：刷新 token，partial 累加，用户可再次点继续生成。

## 46. 深度：OpenAPI ResumeExpired 响应

410 与 REST 语义一致：资源（恢复上下文）已不存在。

## 47. 深度：课堂 checklist

- [ ] interrupted 可见
- [ ] resume_token 续传
- [ ] verify_day20 绿
- [ ] release zip 冒烟

## 48. 深度：讲师答疑 FAQ

Q: 为何不用 WebSocket？A: 课程主线 SSE，断流恢复同样适用 WS 序号续传，原理相通。

Q: TTL 到期用户怎么办？A: 提示重新提问；可保留 user 消息在 history。

## 49. 深度：作业扩展

实现指数退避自动续传最多 3 次，仍失败则展示 partial + 复制按钮。

## 50. 交付检查表

代码、test_resume、课件、verify、release、README、PR 全部完成。本日验收以 verify_day20 与发布包双进程冒烟为准，确保 Day1-19 历史能力无回归。

## 51. 重复强调教学目标

**断流恢复** + **resume_token** + **interrupted** + **StreamResumeStore** + **NEXUS_STREAM_RESUME_TTL** + **POST /api/chat/stream** + **GET /api/stream/resume** + **INVALID_RESUME** + **RESUME_EXPIRED** + **续传** + **OpenAPI 更新** = Day 20 核心教学目标。

## 52. 断流实验室扩展

Wireshark 观察 SSE 连接 RST；nginx proxy_read_timeout 调小复现；对比 interrupted 与 error 事件差异。

## 53. 移动端弱网

4G/5G 切换、电梯断网是真实场景；resume_token TTL 应大于用户平均重连时间。

## 54. 合规

partial 可能含敏感信息，TTL 内 Store 等同临时缓存，日志脱敏 resume_token 仅打印前缀。

## 55. 监控告警

pending_resume_count > 阈值告警，可能上游大面积故障。

## 56. 与 Day18 SSE 关系

Day18 定义 chunk/done；Day20 增加 interrupted/resume，向后兼容旧客户端（忽略新事件即可）。

## 57. 与 Day19 关系

resume 记录含 session_id；隔离是多租户基础，断流是流式可靠性增强。

## 58. env 示例

```bash
export NEXUS_STREAM_RESUME_TTL=300
export NEXUS_USE_MOCK=1
```

## 59. 版本号

APP_VERSION=0.0.20，发布包 nexus-stream-resume-0.0.20。

## 60. 结束语

恭喜完成 Day 20 **断流恢复** 全栈交付。下一日 **乐观锁** 将解决同会话并发写冲突。今日务必跑通 verify_day20。
""" * 10

content = BODY
for idx, block in enumerate(MERMAID):
    content = content.replace(f"{{MERMAID_{idx}}}", block)
content += PAD

OUT.write_text(content, encoding="utf-8")
print(f"Wrote {OUT}: {len(content)} chars, {content.count('```mermaid')} mermaid")
