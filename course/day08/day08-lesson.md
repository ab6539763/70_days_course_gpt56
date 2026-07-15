# Day 8｜让数据拥有行为：Contact、ChatMessage 与平台状态对象

> 阶段：Python 进阶·面向对象上  
> 项目版本：NexusAI 0.0.8  
> 需求：US-OOP-001  
> 交付：三个领域类、Schema v1→v2 迁移、对象持久化与部署  

---

## 0. 开场旁白

Day 7 的联系人由字典表示，规范化、搜索和更新散落在多个函数中。未来对话消息也不能只是一段字符串：模型 API 需要 role 与 content 始终成对，system/user/assistant 角色必须受控，消息需要预览和 JSON 往返。

今天用类把“数据”和“属于这类数据的行为”放在一起：

- `Contact` 管理联系人属性、搜索、岗位更新和序列化。
- `ChatMessage` 管理角色、内容、预览和消息工厂。
- `PlatformState` 聚合联系人、消息、维护人和 revision。

```mermaid
flowchart LR
    Dict[Day7 字典+函数] --> Contact[Contact对象]
    Dict --> State[PlatformState]
    Text[普通字符串] --> Message[ChatMessage]
    Contact --> JSON[Schema v2]
    Message --> JSON
    JSON --> Agent[未来模型 messages]
```

面向对象不是把所有函数塞进 class，也不是“真实世界都有对象”。它用于维护不变量、表达职责和提供稳定接口。今天还会真正执行 Day 5 设计过的 Schema 迁移：v1 联系人目录加载为对象，增加空 messages，保存为 v2。

---

## 1. 学习成果与完成定义

学员能够：

1. 区分类、对象、实例、属性和方法。
2. 使用 `__init__` 初始化实例状态。
3. 理解 `self` 指向当前实例。
4. 设计实例方法、类方法和静态方法。
5. 使用类属性表达所有实例共享规则。
6. 在对象与 JSON 字典间往返。
7. 聚合多个领域对象。
8. 迁移 Schema v1 到 v2。
9. 测试不同实例状态隔离。
10. 保持 CLI 和发布跨进程恢复。

完成定义：

- [ ] ChatMessage 角色校验和内容清洗。
- [ ] ChatMessage `to_dict/from_dict/system/preview`。
- [ ] Contact 属性标准化、搜索、更新、序列化。
- [ ] PlatformState 联系人和消息聚合。
- [ ] 编号/邮箱唯一约束在聚合内。
- [ ] v1 数据迁移至 v2 并 revision+1。
- [ ] v2 跨进程恢复消息。
- [ ] 未知 schema exit3。
- [ ] 单测、CLI、发布部署通过。
- [ ] 课件不少于30000字符。

今日不做：继承、多态、魔术方法和property安排Day9；模块包与异常Day10；类型注解Day13。

---

## 2. 企业需求文档

### 2.1 用户故事

> 作为 Agent 平台开发者，我希望联系人和对话消息成为具备自身规则的领域对象，并让旧联系人数据安全升级，从而为多模型对话和权限上下文建立稳定基础。

### 2.2 Schema v2

```json
{
  "schema_version": 2,
  "revision": 5,
  "owner": {
    "employee_id": "E70007",
    "department": "技术部"
  },
  "contacts": [],
  "messages": [
    {"role": "system", "content": "你是企业助手"},
    {"role": "user", "content": "查询制度"}
  ]
}
```

### 2.3 业务规则

**ChatMessage**

- role 标准化小写。
- 允许 system/user/assistant。
- content 折叠空白且非空。
- preview 默认30字符。

**Contact**

- 编号大写去空格。
- 邮箱小写。
- 技能去重排序。
- `matches` 搜索五字段。
- `update_role` 相同或空值不改变。

**PlatformState**

- 保存 Contact/ChatMessage 对象列表。
- 联系人编号、邮箱唯一。
- 消息角色/内容合法才增加。
- 统计联系人、消息和各角色数。

**迁移**

- v1 的 owner/contacts/revision 保留。
- messages 初始化为空。
- 保存为 v2。
- 迁移算一次变更，revision+1。
- 未知版本拒绝。

### 2.4 验收标准

1. `ChatMessage(" USER "," 查询   制度 ")` 得 user/`查询 制度`。
2. tool角色拒绝，空内容拒绝。
3. Contact C1/email/skills标准化。
4. 对象字典往返相等。
5. 两个实例状态互不污染。
6. v1 revision4迁移后v2 revision5/messages空。
7. 新系统消息、用户消息、助手消息分别持久化。
8. 第二进程恢复3条消息。
9. 发布包无运行JSON。

### 2.5 非功能要求

- 只使用模拟联系人和消息。
- 对象内部规则集中。
- 序列化结果为纯JSON类型。
- 类导入不启动CLI。
- Python3.10+标准库。

---

## 3. 架构与对象关系

```mermaid
classDiagram
    class Contact {
      +contact_id
      +name
      +department
      +role
      +email
      +skills
      +to_dict()
      +matches(keyword)
      +update_role(role)
      +from_dict(data)
      +is_valid_email(email)
    }
    class ChatMessage {
      +ALLOWED_ROLES
      +role
      +content
      +to_dict()
      +preview(limit)
      +from_dict(data)
      +system(content)
      +is_valid_role(role)
    }
    class PlatformState {
      +owner
      +contacts
      +messages
      +revision
      +to_dict()
      +add_contact(contact)
      +search_contacts(keyword)
      +add_message(role, content)
      +statistics()
      +from_dict(data)
    }
    PlatformState "1" o-- "*" Contact
    PlatformState "1" o-- "*" ChatMessage
```

```mermaid
sequenceDiagram
    participant J as v1 JSON
    participant P as PlatformState.from_dict
    participant C as Contact.from_dict
    participant S as save_state
    J->>P: schema1
    P->>C: 每条联系人字典
    C-->>P: Contact对象
    P->>P: messages=[]
    P-->>S: state,migrated=True
    S->>S: revision+1/schema2
```

对象关系是聚合：平台状态“拥有”联系人和消息。删除状态后对象若无其他引用可释放。今天不使用继承。

---

## 4. 类与对象课堂笔记

### 4.1 类是蓝图

```python
class ChatMessage:
    pass
```

类定义一种对象的属性和行为。对象是类创建的具体实例。

```python
a = ChatMessage("user", "你好")
b = ChatMessage("assistant", "您好")
```

a/b属于同一类但状态独立。

### 4.2 `__init__`

构造实例后自动调用，负责建立有效初始状态：

```python
def __init__(self, role, content):
    self.role = role
    self.content = content
```

`__init__` 不返回新对象，不应显式return其他值。

### 4.3 self

self 是当前实例。`a.preview()` 等价于类把a作为第一个参数调用实例方法。名字约定必须用self以保持可读性。

### 4.4 实例属性

`self.role` 每个对象一份。修改a不影响b，除非错误共享可变对象。

### 4.5 类属性

`ALLOWED_ROLES` 属于类，所有消息共享同一规则。实例可读取，但不应为单个实例修改共享规则。

### 4.6 实例方法

需要当前对象状态：

- `message.preview()`
- `contact.matches()`
- `state.add_message()`

### 4.7 类方法

第一个参数cls，使用 `@classmethod`。适合替代构造器：

```python
@classmethod
def from_dict(cls, data):
    return cls(data["role"], data["content"])
```

使用cls而非硬编码类名，后续子类可复用。

### 4.8 静态方法

不依赖实例或类状态，但概念上属于该类：

```python
@staticmethod
def is_valid_role(role):
    ...
```

如果逻辑不属于类领域，应保留普通函数，不要为了“面向对象”强塞。

---

## 5. ChatMessage 设计

### 5.1 为什么不能只用字符串

`"你好"`没有角色。模型API需要：

```json
{"role":"user","content":"你好"}
```

对象让两字段始终一起。

### 5.2 角色

类属性元组共享。静态方法只验证，不创建实例。聚合的 `add_message` 先验证再构造。

### 5.3 内容治理

静态 `normalize_content` 折叠空白。真实Prompt是否保留换行需重新评审，当前用于短消息。

### 5.4 预览

实例方法读取当前content，limit默认30。返回切片不修改。

### 5.5 工厂

`system` 类方法让常见角色更明确：

```python
ChatMessage.system("你是企业助手")
```

### 5.6 序列化

to_dict只返回role/content，不泄漏内部实现。from_dict负责恢复。

---

## 6. Contact 设计

构造器清理编号、姓名、岗位、邮箱和技能。`matches` 将搜索行为放回联系人。`update_role` 守住空值和幂等。`from_dict`/`to_dict`保持JSON边界。

静态邮箱校验是教学版。为什么不用实例方法？校验候选邮箱时对象可能还不存在，也不需要已有属性。

技能使用静态方法，返回新排序列表，避免调用者列表共享。

---

## 7. PlatformState 聚合

### 7.1 为什么需要聚合根

联系人唯一性无法由单个Contact判断，它需要看到整个集合；消息列表和revision也属于平台状态。

### 7.2 防共享默认

构造器参数 contacts/messages 默认None，内部 `list(contacts or [])` 创建新列表。

### 7.3 联系人新增

使用 `any` 检查对象属性。成功append，失败返回消息。

### 7.4 消息新增

先角色，再内容。只有成功对象进入列表。空消息不增加revision。

### 7.5 统计

角色计数从类属性生成，保证即使某角色0也有键。

### 7.6 JSON边界

state.to_dict遍历对象调用to_dict；from_dict遍历字典调用类方法。对象不会直接交给json.dump。

---

## 8. Schema 迁移

```mermaid
flowchart TD
    Load[读取JSON] --> Version{版本}
    Version -->|1| V1[恢复owner/contacts]
    V1 --> EmptyMessages[messages=[]]
    EmptyMessages --> Migrated[migrated=True]
    Migrated --> Revision[revision+1]
    Revision --> SaveV2[保存schema2]
    Version -->|2| V2[正常恢复]
    Version -->|其他| Reject[exit3不覆盖]
```

迁移不能伪造历史消息。v1没有messages，正确值是空列表。迁移保存一次，revision增加。原文件当前直接覆盖，生产需先备份和原子替换。

---

## 9. 课堂实操

1. 编写ChatMessage最小类。
2. 创建两个实例验证隔离。
3. 添加to_dict/from_dict往返。
4. 添加system类方法和角色静态方法。
5. 把Day7联系人字典重构为Contact。
6. 添加matches/update_role。
7. 创建PlatformState聚合。
8. 完成对象序列化。
9. 实现v1/v2加载。
10. 改造CLI与测试。

每一步先单测后接CLI。

---

## 10. 单元测试策略

- ChatMessage角色、内容、预览、字典往返、system工厂。
- Contact属性、技能、搜索、更新、邮箱、往返。
- PlatformState唯一联系人、消息拒绝、统计。
- 两个空state列表隔离。
- v1迁移、v2加载、未知拒绝。
- 自定义临时路径保存恢复。

```mermaid
graph TB
    Model[对象单测] --> State[聚合单测]
    State --> Migration[迁移集成]
    Migration --> CLI[双进程CLI]
    CLI --> Release[部署]
```

---

## 11. CLI 全链路

首进程：

- owner revision1。
- Contact C1 revision2。
- tool消息拒绝不变。
- system/user/assistant revision3/4/5。
- 消息历史、统计、摘要。

第二进程恢复联系人1、消息3，按python搜索。

迁移进程：v1 revision4→v2 revision5，messages空。

---

## 12. 发布部署

构建：

```bash
python3 course/day08/deploy/build_release.py --output artifacts/day08
```

制品：脚本、README、SHA256SUMS。构建双进程新增用户消息并恢复；删除运行JSON。解压后system/user两消息跨进程恢复。

---

## 13. 安全与工程边界

- ChatMessage 不保存思维链或隐藏推理。
- system消息未来由受控配置产生，不信任普通用户。
- 联系人仍为模拟数据和 `.test` 邮箱。
- 对象封装不是权限控制。
- from_dict 当前浅信任字段，异常与模型验证后续实现。
- v1迁移生产需备份。
- 发布包不得含平台JSON。

---

## 14. 常见错误

1. 忘self，方法调用TypeError。  
2. `self`属性拼写错，新建错误属性。  
3. 把实例属性写成类属性，所有对象共享。  
4. 构造器默认列表共享。  
5. classmethod缺cls。  
6. staticmethod错误访问self。  
7. from_dict硬编码类名。  
8. 直接json.dump对象TypeError。  
9. 迁移伪造消息。  
10. 未知schema覆盖。  
11. 空消息仍持久化。  
12. 查询修改对象。  
13. 类过大承担所有I/O。  
14. 把工具函数都放类里。  
15. 导入时运行CLI。

---

## 15. 随堂练习与答案

1. 类与对象区别？蓝图与实例。  
2. self是什么？当前实例引用。  
3. `__init__`何时？实例创建后初始化。  
4. 类属性适合？共享规则。  
5. 实例方法何时？依赖对象状态。  
6. 类方法首参？cls。  
7. 静态方法依赖实例吗？不。  
8. from_dict为何类方法？替代构造。  
9. to_dict为何实例方法？读取实例状态。  
10. 空默认列表风险？实例共享。  
11. 聚合根为何检查唯一？能看到集合。  
12. 对象可直接JSON吗？默认不能。  
13. v1无消息迁移为何空？不伪造事实。  
14. 迁移是否增加revision？当前契约是。  
15. 封装等于权限吗？不是。

---

## 16. 课后作业

### 基础

给ChatMessage增加字符数和是否为空方法，补单测。

### 进阶

实现 `Conversation` 类：messages、add、last、window(limit)、to_dict/from_dict。

### 企业挑战

设计Schema v3：多会话 `conversations`，每个有session_id和messages；写迁移方案。

### 测试

覆盖不同实例隔离、错误角色、空内容、窗口边界和往返。

### 发布

构建后验证导入不运行、双进程恢复、zip无JSON。

---

## 17. 作业完整参考答案

```python
class Conversation:
    def __init__(self, session_id, messages=None):
        self.session_id = session_id
        self.messages = list(messages or [])

    def add(self, message):
        self.messages.append(message)

    def last(self):
        if not self.messages:
            return None
        return self.messages[-1]

    def window(self, limit=10):
        if limit <= 0:
            return []
        return self.messages[-limit:]

    def to_dict(self):
        return {
            "session_id": self.session_id,
            "messages": [item.to_dict() for item in self.messages],
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            data["session_id"],
            [ChatMessage.from_dict(item) for item in data["messages"]],
        )
```

测试空last、limit0、超过长度、对象往返、两个Conversation列表隔离。

Schema v3迁移：v2 messages放入默认session，生成明确迁移session_id；保留contacts/owner/revision；备份、转换、验证消息数与角色、保存、回滚。

---

## 18. 讲师逐字稿

### 开场

“字典把数据放一起，类把数据和行为放一起。只有行为真正属于数据时才放进类。”

### self

“a.preview 调用的是a自己的content。self不是魔法关键字，而是约定的实例参数。”

### 三类方法

“问三个问题：是否需要具体实例？是否需要类本身？都不需要但属于概念？分别实例、类、静态。”

### 聚合

“单个联系人无法知道邮箱是否与别人重复，聚合状态负责跨对象规则。”

### 迁移

“旧数据没有消息，就保持空。迁移不能编造历史。”

### 测试

“对象测试不仅看值，还看不同实例是否共享状态。”

### 发布

“内部从字典变对象，外部JSON契约仍需验证。部署测试才证明边界。”

---

## 19. 对象路径覆盖实验室

1. 两个message状态独立。  
2. role清理小写。  
3. tool角色拒绝。  
4. content空白清理。  
5. preview短/长/0。  
6. message字典往返。  
7. system工厂。  
8. 两个contact技能不共享。  
9. contact编号标准化。  
10. 邮箱小写。  
11. 技能去重。  
12. matches姓名。  
13. matches技能。  
14. 空搜索false。  
15. update_role变化。  
16. update_role相同。  
17. 邮箱合法/非法。  
18. Contact往返。  
19. 两个state列表隔离。  
20. 新联系人成功。  
21. 重复编号。  
22. 重复邮箱。  
23. user消息成功。  
24. 空消息拒绝。  
25. 各角色统计。  
26. state to_dict。  
27. schema1迁移。  
28. schema2恢复。  
29. schema99拒绝。  
30. 首进程revision1-5。  
31. 第二进程消息3。  
32. 迁移revision4→5。  
33. 发布数据清理。  
34. zip白名单。  
35. 哈希。  
36. 解压双进程。  
37. 导入不运行。  
38. Day1-7回归。

---

## 20. OOP 设计评审

### 20.1 贫血模型

若Contact只有属性，所有行为仍在外部函数，类价值有限。matches/update_role/to_dict属于联系人行为。

### 20.2 上帝对象

若PlatformState处理终端、文件、所有校验和发布，会过大。I/O仍保留普通函数。

### 20.3 静态方法滥用

任意工具放类里只增加命名层级。必须属于领域概念。

### 20.4 公开属性

今天属性公开，外部可绕过update直接修改。Day9 property讨论保护。

### 20.5 不变量

构造器应建立有效状态，但当前仍允许非法role直接构造ChatMessage；聚合add先校验。Day9/10改进异常策略。

### 20.6 对象身份

两个字段相同的Contact仍是两个对象。今天未实现eq，Day9魔术方法讨论。

---

## 21. 第一周模型到对象迁移对照

| Day7 | Day8 |
|---|---|
| contact["name"] | contact.name |
| search_contacts函数 | contact.matches |
| update_contact role | contact.update_role |
| create_contact函数 | Contact(...) |
| dict恢复 | Contact.from_dict |
| data顶层字典 | PlatformState |
| 新messages字段 | ChatMessage对象 |

不是所有函数都变方法：load/save/persist和CLI仍是外部边界函数。

---

## 22. 对象内存模型与实例隔离实验室

### 22.1 两个消息实例

```python
a = ChatMessage("user", "问题A")
b = ChatMessage("user", "问题B")
a.content = "已修改"
```

b仍为问题B。实例属性存放在各自对象。若错误把content写成类属性，修改共享值会影响没有实例覆盖的对象。

### 22.2 类属性共享规则

`ChatMessage.ALLOWED_ROLES`由所有实例读取。它表达平台级角色集合。不要在某个实例上做：

```python
message.ALLOWED_ROLES = ("user",)
```

这会在实例上创建同名属性遮蔽类属性，导致行为难以理解。共享规则由类管理。

### 22.3 默认列表隔离

`PlatformState(contacts=None)` 内部创建新列表。连续两个state，向一个添加Contact，另一个必须为空。若构造器参数写 `contacts=[]`，多个实例共享。

### 22.4 `list(contacts or [])`

传入已有列表时创建浅的新外层列表，防调用者append影响state列表长度；其中Contact对象仍共享引用。契约要准确：容器隔离，不是深复制对象。

### 22.5 属性绑定

`contact.name` 从实例读取。赋值会改变该对象。Day8属性公开，任何调用者可绕过方法写空岗位，Day9用property讨论。

### 22.6 方法绑定

```python
method = contact.matches
```

这是绑定方法，已经记住contact实例，后续 `method("python")` 等价于 `contact.matches("python")`。

### 22.7 类调用实例方法

```python
Contact.matches(contact, "python")
```

也能工作，显式把contact作为self。日常使用实例调用更清晰。

### 22.8 对象身份

两个Contact字段完全相同，`a is b`仍False；未实现`__eq__`时相等比较通常按身份。Day9讨论相等语义。

### 22.9 垃圾回收边界

对象没有引用后可被回收。JSON文件不是对象本身，只是可恢复状态。重新加载得到新对象身份，但业务字段相同。

### 22.10 聚合引用

PlatformState.contacts持有Contact引用。即使局部变量删除，state仍引用对象。删除列表元素后若无其他引用，对象才可释放。

### 22.11 浅序列化

`to_dict`创建新字典和skills列表引用？Contact当前返回self.skills本身，调用者修改返回字典中的skills会影响对象。这是潜在边界。更严格可返回 `list(self.skills)`。课件记录为代码评审点。

### 22.12 对象与快照

JSON是保存时快照。保存后修改对象但不persist，文件仍旧值；第二进程恢复旧状态。对象存在不等于已持久化。

```mermaid
graph LR
    A[Contact实例A] --> AData[实例属性]
    B[Contact实例B] --> BData[实例属性]
    A -.共享类规则.-> Class[Contact类]
    B -.共享类规则.-> Class
    State[PlatformState] --> A
    State --> B
    State --> Messages[ChatMessage实例列表]
```

### 实验记录

```text
实例：
类：
实例属性：
类属性：
修改操作：
其他实例是否变化：
容器是否共享：
对象是否持久化：
```

---

## 23. 实例方法、类方法、静态方法决策工作坊

### 23.1 决策问题

1. 是否需要读取或修改某个实例？用实例方法。
2. 是否要创建实例且希望支持子类？用类方法。
3. 不需要实例/类状态，但逻辑明显属于该领域？静态方法。
4. 都不属于？普通函数。

### 23.2 `preview` 为什么是实例方法

它读取当前消息content。不同消息预览不同。limit是调用参数，但核心状态来自self。

### 23.3 `to_dict` 为什么是实例方法

序列化当前对象属性。没有实例就没有具体字典。

### 23.4 `from_dict` 为什么是类方法

它根据字典创建新实例。用cls调用构造器，未来子类继承时返回子类。

### 23.5 `system` 为什么是类方法

是命名构造器，预填role并创建实例。相比 `ChatMessage("system",...)` 更表达意图。

### 23.6 `is_valid_role` 为什么静态

只检查候选文本与共享角色。它可读取 `ChatMessage.ALLOWED_ROLES`；若希望多态支持子类角色，更适合类方法读取cls。当前静态选择是教学简化。

### 23.7 `normalize_content` 为什么静态

不依赖实例已有状态，属于Message文本规范。也可做模块函数；放类中便于发现。

### 23.8 `Contact.matches` 为什么实例

搜索当前联系人五字段。query是外部参数，字段来自self。

### 23.9 `Contact.is_valid_email` 为什么静态

创建Contact之前就要校验候选邮箱，不需要已有实例。

### 23.10 `PlatformState.empty` 为什么类方法

命名构造一个空聚合。当前直接 `cls()` 即可，但命名表达业务意图，未来默认值变化只改一处。

### 23.11 `load_state` 为什么普通函数

它涉及文件系统与JSON边界，不是PlatformState内在领域行为。也可设计Repository类，Day10再模块化。

### 23.12 `persist_change` 为什么普通函数

组合revision与文件I/O。把它放state会让领域对象依赖具体存储路径。当前保持边界分离。

```mermaid
flowchart TD
    Behavior[一个行为] --> Instance{需要具体实例状态?}
    Instance -->|是| IM[实例方法 self]
    Instance -->|否| Class{创建实例或需要类?}
    Class -->|是| CM[类方法 cls]
    Class -->|否| Domain{逻辑属于该领域概念?}
    Domain -->|是| SM[静态方法]
    Domain -->|否| Function[普通函数/服务]
```

### 23.13 反例：所有方法都static

若每个方法都接contact参数，类只是命名空间，失去实例行为。应让依赖对象状态的行为成为实例方法。

### 23.14 反例：所有函数都塞PlatformState

文件构建、zip、终端都变方法，形成上帝对象。职责边界比“面向对象纯度”重要。

### 23.15 决策练习答案

| 行为 | 选择 | 理由 |
|---|---|---|
| 修改联系人岗位 | 实例 | 修改self.role |
| 从JSON恢复联系人 | 类 | 构造实例 |
| 校验邮箱文本 | 静态 | 无实例状态 |
| 保存平台文件 | 普通/仓储 | I/O边界 |
| 新建system消息 | 类 | 命名构造 |
| 统计平台消息 | 实例 | 读取聚合状态 |
| 计算文件哈希 | 普通 | 不属于领域对象 |

---

## 24. `__init__` 与有效状态专题

### 24.1 构造器职责

构造器应让对象创建后可用。Contact完成基础标准化，ChatMessage清理角色/内容。但当前允许直接构造tool角色，这是已知不变量缺口。

### 24.2 验证位置策略

方案A：构造器拒绝无效值，需异常（Day10）。  
方案B：类方法create返回结果。  
方案C：聚合添加前校验。  
当前采用C，便于Day8不提前异常，但直接构造仍需调用者自律。

### 24.3 参数过多

Contact六参数容易顺序错。关键字调用更清晰；Day13类型注解，后续Pydantic模型。

### 24.4 默认值

skills=None而非[]。owner/contacts/messages同理。默认参数定义时求值规则仍适用类构造器。

### 24.5 标准化与原始值

构造器只保留标准值，不保留原始输入。若审计需要原始值，必须另设计字段和隐私策略，不能隐藏缓存。

### 24.6 派生属性

消息字符数可每次 `len(content)` 计算，不必存第二份。避免内容变化后计数不同步。

### 24.7 构造副作用

`__init__` 不读文件、不发送请求、不print。创建对象应可预测、易测试。I/O交给边界函数。

### 24.8 不返回值

显式从 `__init__` 返回非None会TypeError。对象由`__new__`创建，init负责初始化。Day8不深入new。

---

## 25. ChatMessage 企业级上下文设计

### 25.1 system

定义行为和边界，通常由平台控制。不能让普通用户随意冒充system。

### 25.2 user

用户输入。进入对象前仍需治理、权限和内容安全。role只是结构，不是认证。

### 25.3 assistant

模型输出。保存时应关联模型、时间、token、finish_reason，当前Schema仅最小字段。

### 25.4 tool预告

Day19工具调用会增加tool消息。当前拒绝tool是版本契约，不代表工具角色永远非法。扩展角色要升级测试和Schema策略。

### 25.5 消息顺序

列表顺序就是对话顺序。排序消息会破坏语义。联系人可以排序，消息不能按role排序。

### 25.6 预览

预览只是UI，不能替代完整content保存。切片可能截断语义和敏感片段，日志中需谨慎。

### 25.7 空白

当前折叠所有连续空白，适合短问答；代码、Markdown和Prompt可能需要换行，后续重新设计。

### 25.8 metadata

未来可包含message_id、created_at、model、token usage、references。每个字段需Schema迁移。

### 25.9 消息不保存隐藏推理

只保存面向用户内容，不要求或记录模型内部思维链。审计关注输入、输出、工具和引用。

### 25.10 对话窗口

作业Conversation.window用切片返回最近N条。生产还需token预算、摘要和系统消息保留。

```mermaid
sequenceDiagram
    participant Config as 平台配置
    participant User as 用户
    participant Model as 模型
    participant History as 消息历史
    Config->>History: system message
    User->>History: user message
    History->>Model: 有序messages
    Model-->>History: assistant message
    Note over History: 只保存结构化可见内容
```

---

## 26. Contact 对象深入评审

### 26.1 对象职责

保存单个联系人状态、序列化、匹配、更新自身岗位。跨联系人唯一性不属于单个对象。

### 26.2 email验证

静态方法可在构造前用。格式通过不证明归属。继续使用 `.test`。

### 26.3 skills

构造器调用静态方法得到排序新列表。传入列表后修改原列表不应影响对象，因为集合推导创建新结果。

### 26.4 matches

实例方法封装五字段。未来字段增加时只改对象；但权限过滤仍在聚合/服务。

### 26.5 update_role

幂等：相同返回False；空值返回False；变化修改并True。revision由编排决定。

### 26.6 to_dict暴露

返回数据传输对象。建议复制skills，防止外部修改。当前测试未覆盖，作为进阶修复。

### 26.7 from_dict兼容

`data.get("skills",[])` 支持旧联系人缺skills。但过度默认可能掩盖损坏，需要Schema策略。

### 26.8 身份与相等

contact_id是业务标识，但对象相等尚未重写。集合中不能直接依赖Contact去重。Day9实现或讨论`__eq__/__hash__`。

---

## 27. PlatformState 聚合根专题

### 27.1 聚合边界

联系人唯一、邮箱唯一、消息列表、revision在同一状态。一次保存形成一致快照。

### 27.2 add_contact

`any`短路扫描。数据量大时数据库唯一索引，当前列表足够。

### 27.3 search_contacts

把匹配委托给Contact，排序由聚合决定。职责协作而非重复字段逻辑。

### 27.4 add_message

聚合负责角色和空内容门禁。成功后消息对象进入顺序列表。

### 27.5 statistics

角色字典始终包含三角色0值，输出稳定。联系人和消息数来自对象列表。

### 27.6 to_dict

递归调用每个对象的序列化接口，形成纯dict/list。json模块不认识领域对象，但认识转换结果。

### 27.7 from_dict

对象图重建入口。它同时承担版本判断，未来迁移服务可独立，避免类方法过大。

### 27.8 revision

对象持有revision，persist_change修改后保存。业务方法本身不自动revision，允许批量操作。

---

## 28. Schema v1→v2 迁移桌面演练

### 28.1 前置检查

- 顶层dict。
- schema1。
- revision/owner/contacts存在。
- contacts列表。
- 每条可Contact.from_dict。

### 28.2 转换

- owner原样。
- contacts字典→Contact对象。
- messages=[]。
- state revision保留4。
- migrated=True。

### 28.3 持久化

run_cli识别migrated，调用persist，revision5，to_dict输出schema2。

### 28.4 验证

- 联系人数不变。
- 编号/邮箱集合不变。
- messages空。
- schema2。
- revision+1。
- 第二次加载status loaded，不重复迁移。

### 28.5 失败

未知schema返回None/error，不写。字段缺失拒绝。JSON语法错误Day10。

### 28.6 回滚

当前教学直接覆盖。生产先备份v1；若v2运行后新增消息，再回滚v1会丢消息，需要逆迁移或禁止回滚。

```mermaid
flowchart LR
    V1[v1 revision4] --> Parse[恢复Contact对象]
    Parse --> AddField[messages空]
    AddField --> State[PlatformState]
    State --> Increment[revision5]
    Increment --> V2[v2 JSON]
    V2 --> Reload[再次加载]
    Reload --> Loaded[loaded非migrated]
```

### 28.7 迁移测试为什么独立

普通新建测试不能证明旧数据兼容。必须构造真实v1文档，从磁盘加载并检查字节结果。

---

## 29. 面向对象测试矩阵

| 类/函数 | 正常 | 边界 | 失败 | 隔离 |
|---|---|---|---|---|
| ChatMessage | 三角色 | 预览0/长 | tool/空 | 两实例 |
| Contact | 标准化 | 空skills | 邮箱非法 | skills不共享 |
| PlatformState | 添加统计 | 空列表 | 重复/错误消息 | 两state |
| from_dict | v1/v2 | 缺skills | schema99 | 往返 |
| CLI | 首次恢复 | 无联系人 | 错菜单 | 进程 |
| Release | 双进程 | 空数据 | 哈希/白名单 | 临时目录 |

### 29.1 对象状态断言

不只检查类型，还检查属性标准化。

### 29.2 行为断言

matches/update_role/preview返回与副作用。

### 29.3 往返断言

`from_dict(to_dict(obj)).to_dict() == obj.to_dict()`。

### 29.4 实例隔离

修改一个实例列表不影响另一个。

### 29.5 聚合规则

重复联系人和非法消息不进入列表。

### 29.6 迁移

v1→对象→v2→再次加载。

### 29.7 E2E

三个角色顺序和revision。

### 29.8 发布

脚本哈希、zip无JSON、解压消息恢复。

---

## 30. 课堂分镜与讲师手册

### 30.1 09:00-09:30 字典痛点

让学员列出Day7哪些函数总是接触contact字典。讨论哪些行为真正属于联系人。

### 30.2 09:30-10:00 第一个类

只写ChatMessage和两个实例。打印id/属性，修改一个观察隔离。

### 30.3 10:10-10:40 self与实例方法

手动调用类方法形式，理解绑定。故意漏self观察TypeError。

### 30.4 10:40-11:10 类属性

比较实例属性和ALLOWED_ROLES。禁止用可变类属性存每个对象消息。

### 30.5 11:10-11:40 三类方法

用决策图为preview/from_dict/is_valid_role分类。每组给理由。

### 30.6 11:40-12:00 JSON往返

对象不能直接dump，先to_dict。加载后from_dict。

### 30.7 14:00-14:40 Contact重构

把Day7工厂/搜索/更新迁入类，运行旧业务例子。

### 30.8 14:40-15:20 PlatformState

实现聚合唯一与消息规则，写单测。

### 30.9 15:30-16:00 Schema迁移

先画v1/v2差异，禁止编造messages。实现from_dict返回migrated。

### 30.10 16:00-16:30 CLI

新菜单添加消息/历史。联系人不需重新实现全部Day7 CRUD，聚焦对象。

### 30.11 16:30-17:00 测试

模型单测、迁移磁盘测试、双进程。

### 30.12 17:00-17:30 发布

构建/解压双进程消息恢复。检查运行JSON删除。

### 30.13 晚自习评审

每组指出一个应是实例方法、一个类方法、一个静态方法、一个应留普通函数的行为。

---

## 31. OOP 周测题与答案

1. `self`由谁传？实例调用时Python传当前对象。  
2. `cls`是什么？当前类。  
3. 类属性和实例属性区别？共享规则与对象状态。  
4. `__init__`返回？应None。  
5. 类方法装饰器？`@classmethod`。  
6. 静态方法装饰器？`@staticmethod`。  
7. from_dict选择？类方法。  
8. preview选择？实例方法。  
9. 邮箱候选校验？静态或普通函数。  
10. save_state？普通仓储函数。  
11. 默认messages=[]风险？实例共享。  
12. 对象可直接JSON？默认不。  
13. to_dict返回什么？纯JSON兼容结构。  
14. v1没有messages怎么办？迁移为空。  
15. 迁移后revision？+1。  
16. 未知版本？拒绝不覆盖。  
17. 聚合根作用？跨对象规则和一致边界。  
18. Contact能检查全局邮箱唯一吗？单独不能。  
19. 对象字段相同是否同一对象？不是。  
20. 封装是否权限？不是。  
21. role类属性为何元组？共享固定候选。  
22. 查询可修改对象吗？不应隐藏副作用。  
23. list浅复制后对象共享吗？共享内部引用。  
24. 类过大风险？上帝对象。  
25. 静态方法滥用？类成为命名空间。  
26. 继承今天使用吗？不，Day9。  
27. property今天使用吗？Day9。  
28. 对象迁移为何要测试磁盘？证明真实边界。  
29. 消息顺序能排序吗？不能，语义有序。  
30. system角色由谁控制？平台受控配置。

评分：每题2分，共60；设计题40：

31. 设计Conversation类（10）。  
32. 设计v3迁移（10）。  
33. 说明对象与字典边界（10）。  
34. 说明聚合和仓储职责（10）。

完整答案：Conversation参考见作业；v3将v2 messages放默认会话，不编造其他会话；对象承载行为、字典用于传输；聚合管跨对象规则、仓储管I/O。

---

## 32. 安全威胁建模

```mermaid
flowchart TD
    Message[ChatMessage] --> M1[用户伪装system]
    Message --> M2[敏感内容持久化]
    Contact[Contact] --> C1[真实个人数据]
    Migration[迁移] --> G1[旧数据覆盖]
    Object[公开属性] --> O1[绕过方法]
    Release[发布] --> R1[JSON泄漏]
    Control[控制] --> X1[角色白名单]
    Control --> X2[模拟数据]
    Control --> X3[迁移版本拒绝]
    Control --> X4[制品白名单]
```

当前角色白名单只校验文本，不认证调用者。公开属性可绕过方法。真实系统需要API边界、权限、模型验证和审计。

---

## 33. 项目代码评审清单

- [ ] 每类职责一句话。
- [ ] 构造器无I/O。
- [ ] 默认可变对象隔离。
- [ ] 三类方法选择有理由。
- [ ] Contact行为不重复在聚合。
- [ ] 跨对象唯一在PlatformState。
- [ ] 对象to_dict纯JSON。
- [ ] from_dict支持v1/v2。
- [ ] 迁移不编造消息。
- [ ] 未知版本不写。
- [ ] 消息顺序保留。
- [ ] CLI只在changed持久化。
- [ ] 导入不运行。
- [ ] 发布无数据。

---

## 34. 复盘与 Day 9

保持：类职责、实例隔离、三类方法、对象JSON边界、迁移证据。  
停止：所有代码塞class、共享默认列表、对象直接dump、迁移编造数据。  

技术债：

| 债务 | Day9 |
|---|---|
| 属性可绕过修改 | property |
| 对象展示默认难读 | `__str__/__repr__` |
| 模型接口无基类 | 继承/多态 |
| 对象相等未定义 | 魔术方法讨论 |

Day9 将设计 `BaseModel → OpenAIModel/QwenModel`，用继承、多态、super、property和魔术方法建立多供应商模型接口。

---

## 35. 教学质量门禁

| 指标 | 目标 |
|---|---:|
| 课件字符 | ≥30000 |
| Mermaid | ≥9 |
| 必备内容 | 全部 |
| 类/实例隔离 | 通过 |
| 三类方法 | 通过 |
| 对象JSON往返 | 通过 |
| v1→v2迁移 | 通过 |
| CLI双进程 | 通过 |
| 制品无数据 | 通过 |
| Day1-7回归 | 通过 |

---

## 36. 今日交付

```text
course/day08/day08-lesson.md
course/day08/starter/chat_message.py
course/day08/solution/oop_platform.py
course/day08/tests/test_models.py
course/day08/tests/test_cli.py
course/day08/deploy/build_release.py
course/day08/tests/test_release.py
tools/verify_day08.py
```

【收尾旁白】

“今天联系人和消息不再只是字典。Contact守住协作者行为，ChatMessage守住模型消息结构，PlatformState守住跨对象唯一和持久化。Schema迁移让新对象模型承接旧数据，而不是重新开始。”
