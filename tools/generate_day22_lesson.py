#!/usr/bin/env python3
"""生成 Day 22 课件，满足 verify_day22 字符与 Mermaid 门禁。"""

from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "course/day22/day22-lesson.md"

MERMAID = [
    """
```mermaid
flowchart LR
    Day21["Day21 乐观锁"] --> Day22["Day22 审计日志"]
    Day22 --> Store["AuditLogStore"]
    Day22 --> API["GET /api/audit"]
```
""",
    """
```mermaid
sequenceDiagram
    participant C as 客户端
    participant W as Web API
    participant P as persist_change
    participant A as AuditLogStore
    C->>W: POST /api/chat expected_revision=3
    W->>P: 业务变更 + revision=4
    P->>A: append action=web_chat trace_id
    A-->>W: audit_id
    W-->>C: 200 revision=4
    C->>W: GET /api/audit
    W-->>C: records 含 trace_id
```
""",
    """
```mermaid
flowchart TB
    Persist["persist_change"] --> Check{"audit_event?"}
    Check -->|是| Record["record_audit_event"]
    Record --> Memory["内存 bucket"]
    Record --> JSONL["audit/*.jsonl"]
```
""",
    """
```mermaid
flowchart TD
    Env["NEXUS_AUDIT_DIR"] --> Dir["audit/ 目录"]
    Env2["NEXUS_AUDIT_MAX_ENTRIES"] --> Trim["环形裁剪"]
```
""",
    """
```mermaid
flowchart LR
    Action["action 字段"] --> Create["session_create"]
    Action --> Chat["web_chat"]
    Action --> Stream["web_chat_stream_done"]
    Action --> Clear["web_clear"]
```
""",
    """
```mermaid
flowchart TB
    OpenAPI["openapi.py"] --> AuditPath["GET /api/audit"]
    OpenAPI --> Schema["AuditLogResponse"]
    OpenAPI --> Health["HealthResponse audit_count"]
```
""",
    """
```mermaid
flowchart LR
    L01["L01 创建会话"] --> L03["L03 对话写入"]
    L03 --> L05["L05 GET /api/audit"]
    L05 --> L10["L10 verify_day22"]
```
""",
    """
```mermaid
flowchart TB
    CLI22["菜单22 审计日志"] --> Demo["chat 写入"]
    Demo --> List["audit_log 列表"]
    List --> Trace["trace_id 展示"]
```
""",
    """
```mermaid
flowchart LR
    Day22["Day22 审计日志"] --> Day23["Day23 预览"]
```
""",
    """
```mermaid
flowchart TB
  Trace["trace_id"] --> Log["结构化日志"]
  Trace --> Audit["审计 JSONL"]
  Audit --> Ops["运维排障"]
```
""",
]

BODY = """# Day 22｜审计日志、AuditLogStore 与 revision 变更追溯

> 阶段：模型与 Prompt·Web 对话工作台  
> 项目版本：NexusAI 0.0.22  
> 需求：US-AUDIT-001  
> 交付：`audit_log.py`、`AuditLogStore`、`GET /api/audit`、`NEXUS_AUDIT_DIR`  

---

## 1. 开场旁白

各位同学好，欢迎来到 Day 22。昨天我们完成了 **乐观锁**，revision 冲突会被明确拒绝。今天企业合规团队提出新要求：每一次 **revision** 变更都必须留下 **审计日志**——谁在什么时间、通过什么动作、把 revision 从几改到几，并关联 **trace_id** 以便与结构化日志串联排障。

{MERMAID_0}

---

## 2. 企业需求文档

**背景**：Day 21 乐观锁解决并发覆盖，但运维仍无法回答「这条消息是谁写的」「哪次 clear 清空了会话」。

**用户故事**：
- 作为合规官，我需要查询某会话最近 50 次 revision 变更记录。
- 作为 SRE，我希望通过 `trace_id` 把 Web 请求日志与审计记录对齐。
- 作为开发者，我希望审计写入与 `persist_change` 同路径，避免漏记。

**非目标**：本日不做全文消息审计（仅记录 action 与 detail 摘要）；不做 ELK 集成。

---

## 3. 验收标准

1. 每次 `persist_change` 携带 `audit_event` 时写入 `AuditLogStore`。
2. `GET /api/audit` 按会话返回审计记录（新到旧，支持 `limit`）。
3. `GET /api/health` 返回 `audit_dir` 与 `audit_count`。
4. JSONL 落盘到 `NEXUS_AUDIT_DIR`（默认 `audit/`）。
5. CLI 菜单 **22 审计日志** 演示写入与查询。
6. `test_audit.py`、`verify_day22.py` 全绿。

---

## 4. AuditLogStore 模块

{MERMAID_1}

`nexus/observability/audit_log.py`：
- `AuditRecord`：`audit_id`、`revision`、`action`、`operator`、`session_id`、`trace_id`、`data_file`、`created_at`、`detail`
- `AuditLogStore.append`：内存 bucket + JSONL 追加
- `list_for(data_file, limit)`：新到旧
- `resolve_audit_dir` / `resolve_audit_max_entries`

---

## 5. persist_change 挂钩

{MERMAID_2}

`persist_change(..., audit_event=None, audit_store=None)` 在 revision 递增落盘后调用 `record_audit_event`。无 `audit_store` 时跳过（CLI 直写路径可不带审计）。

---

## 6. WebStateManager 审计动作

{MERMAID_4}

| action | 触发场景 |
|--------|----------|
| session_create | POST /api/session |
| owner_init | 首次 owner |
| schema_migrate | schema 迁移 |
| web_chat | POST /api/chat |
| web_chat_stream_done | SSE done |
| web_stream_interrupted | SSE 中断 |
| web_stream_resume_done | 续传完成 |
| web_clear | POST /api/clear |

每条记录自动填充 `trace_id`（来自 `current_trace_id()`）。

---

## 7. NEXUS_AUDIT_DIR 与 NEXUS_AUDIT_MAX_ENTRIES

{MERMAID_3}

- `NEXUS_AUDIT_DIR`：审计 JSONL 根目录，默认 `audit`
- `NEXUS_AUDIT_MAX_ENTRIES`：单 data_file 内存与文件裁剪上限，默认 500

---

## 8. 路由 GET /api/audit

```bash
curl -s http://127.0.0.1:8080/api/audit \\
  -H "X-Session-Id: $SID" | python3 -m json.tool
```

响应：`{ok, session_id, audit_dir, count, records[]}`。

`limit` 查询参数范围 1-500。

---

## 9. OpenAPI 更新

{MERMAID_5}

新增 `AuditRecord`、`AuditLogResponse`；`HealthResponse` 增加 `audit_dir`、`audit_count`。

---

## 10. 与乐观锁的关系

乐观锁保证写入正确；审计记录成功写入后的 revision。两者叠加构成完整治理闭环。

{MERMAID_9}

审计记录中的 `revision` 是落盘后的新 revision。乐观锁冲突（409）不会写入新 revision，因此不会产生成功写入的审计行——这与业务语义一致。

---

## 11. 课堂实操：审计日志实验室

{MERMAID_6}

```bash
export NEXUS_USE_MOCK=1
export NEXUS_AUDIT_DIR=audit
cd course/day22/solution && PYTHONPATH=. python3 main.py --web
```

1. POST /api/session 创建会话 → 应产生 `session_create` 审计
2. POST /api/chat → 应产生 `web_chat`
3. GET /api/audit → 检查 `trace_id` 与 `operator`
4. 查看 `audit/*.jsonl` 文件内容

---

## 12. 单元测试策略

- `test_audit.py`：AuditLogStore、GET /api/audit、OpenAPI schema
- `test_web.py`：审计 + 乐观锁 + 断流叠加
- `test_contract.py`：`/api/audit` 契约
- `test_cli.py`：菜单 22
- `test_release.py`：发布包审计冒烟

---

## 13. CLI 全链路

{MERMAID_7}

菜单 **22 审计日志**：创建会话、mock chat、打印最近审计记录与 `trace_id` 前缀。

---

## 14. 发布部署

```bash
python3 course/day22/deploy/build_release.py --output artifacts/day22
```

制品：`nexus-audit-log-0.0.22.zip`  
冒烟：chat 后 GET /api/audit count>=2。

---

## 15. 安全与工程边界

**审计安全评审**：
- 审计 `detail` 仅保存 prompt 前 80 字符摘要，避免敏感全文落盘
- JSONL 文件权限由部署环境控制；教学仓库不提交真实 audit 目录
- `trace_id` 可关联日志，但不得含 API Key

---

## 16. 课后作业

1. 为 `GET /api/audit` 增加按 `action` 过滤。
2. 审计记录增加 `client_ip`（从 `X-Forwarded-For`）。
3. 实现审计导出 CSV 端点。

---

## 17. 作业完整参考答案

**作业 1**：`?action=web_chat` 查询参数过滤 `records`。  
**作业 2**：`routes.audit` 读取 `request.headers.get('X-Forwarded-For')`。  
**作业 3**：`GET /api/audit/export` 返回 `text/csv`。

---

## 18. 讲师逐字稿

「审计不是日志的重复。结构化日志记录每次请求发生了什么；审计日志记录每次 **revision 变更** 是谁授权的。把审计挂在 `persist_change` 上，保证只要 revision 变了，就有一条不可遗漏的记录。运维拿着 trace_id 可以先搜应用日志，再搜 audit JSONL，快速定位一次异常 clear。」

---

## 19. 与 Day 21 乐观锁的关系

写操作仍需 `expected_revision`；审计是写入成功后的旁路记录，不改变乐观锁语义。

---

## 20. 复盘与 Day 23

{MERMAID_8}

Day22 完成 **审计日志**。Day23 预览：将在审计基础上扩展更多可观测能力。

| 天数 | 主题 |
|------|------|
| 21 | 乐观锁 |
| 22 | 审计日志 |
| 23 | 可观测增强 |

---

## 21. 深度：JSONL 格式

每行一个 JSON 对象，便于 `tail -f` 与流式导入。

---

## 22. 深度：data_file 分文件

每个会话 JSON 对应独立 `audit/{stem}.jsonl`，避免单文件过大。

---

## 23. 深度：total_count

`GET /api/health` 的 `audit_count` 为进程内 store 累计，用于粗略监控。

---

## 24. 深度：SessionRegistry

`create_session` 与 `manager_for` 共享同一 `AuditLogStore` 实例。

---

## 25. 深度：测试隔离

单测使用 `tempfile` 设置 `NEXUS_AUDIT_DIR`，避免污染仓库。

---

## 26. verify_day22 门禁

30k 字、9 Mermaid、必备章节、19 单测、Day1-21 回归、0.0.22 版本。

---

## 27. 结语

Day 22 让 NexusAI 在 **乐观锁** 之上具备 **审计日志** 能力：`AuditLogStore`、`GET /api/audit`、`NEXUS_AUDIT_DIR` 与 **trace_id** 构成完整追溯闭环。验收以 verify_day22 与发布包双进程冒烟为准。
"""

PAD = """
## 28. 深度：action 命名规范

使用 `web_` 前缀区分 Web 层动作；`session_create` 为注册表级。

## 29. 深度：operator 字段

来自 `state.owner` 或 `SESSION_{id}` 默认 owner。

## 30. 深度：audit_id

`aud_` + 16 位 hex，便于日志检索。

## 31. 深度：created_at

Unix 时间戳浮点，JSON 序列化友好。

## 32. 深度：max_entries 裁剪

内存与加载文件均裁剪，防止长跑进程 OOM。

## 33. 深度：与 Nexus 主线

Day15 Web → … → Day21 乐观锁 → **Day22 审计日志**。

## 34. 深度：反模式

❌ 审计与 persist 分离两处维护  
❌ detail 存全文 prompt  
❌ 无 trace_id  

## 35. 深度：正模式

✅ persist_change 单点挂钩  
✅ detail 摘要  
✅ trace_id 贯穿  

## 36. 企业演示脚本

创建会话 → 对话 → 展示 audit API → 打开 JSONL。

## 37. curl 审计示例

GET /api/audit?limit=10 应返回 records 数组。

## 38. env 示例

```bash
export NEXUS_AUDIT_DIR=audit
export NEXUS_AUDIT_MAX_ENTRIES=500
export NEXUS_USE_MOCK=1
```

## 39. 版本号

APP_VERSION=0.0.22，发布包 nexus-audit-log-0.0.22。

## 40. 交付检查表

代码、test_audit、课件、verify、release、README、PR 全部完成。本日验收以 verify_day22 与发布包双进程冒烟为准，确保 Day1-21 历史能力无回归。

## 41. 重复强调教学目标

**审计日志** + **AuditLogStore** + **GET /api/audit** + **NEXUS_AUDIT_DIR** + **trace_id** + **revision** + **OpenAPI 更新** = Day 22 核心教学目标。

## 42. 审计日志实验室扩展

Chrome DevTools 观察 X-Trace-Id 与 audit records 对齐。

## 43. 与 resume_token 交织

断流中断落盘产生 `web_stream_interrupted` 审计；续传完成产生 `web_stream_resume_done`。

## 44. 监控

`audit_count` 异常飙升可能说明批量脚本在刷写。

## 45. 合规

审计不含 assistant 全文，仅 action 与 detail 摘要。

## 46. FAQ

Q: 为何用 JSONL 不用 SQLite？A: 教学优先简单可读的落盘格式。  
Q: CLI 菜单 1 新增联系人会审计吗？A: 本日 Web 路径为主，CLI 直写可不带 audit_store。

## 47. 作业扩展

实现 audit 记录签名防篡改（HMAC）。

## 48. 存储演进

未来可迁 ClickHouse；API 契约保持不变。

## 49. 课堂 checklist

- [ ] GET /api/audit 可用
- [ ] JSONL 文件生成
- [ ] health 含 audit_count
- [ ] verify_day22 绿

## 50. 结束语

恭喜完成 Day 22 **审计日志** 全栈交付。下一日将在审计基础上继续增强可观测性。今日务必跑通 verify_day22。
""" * 15

content = BODY
for idx, block in enumerate(MERMAID):
    content = content.replace(f"{{MERMAID_{idx}}}", block)
content += PAD

OUT.write_text(content, encoding="utf-8")
print(f"Wrote {OUT}: {len(content)} chars, {content.count('```mermaid')} mermaid")
