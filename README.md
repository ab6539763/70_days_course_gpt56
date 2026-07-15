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

## 内容原则

1. 每天均包含业务上下文、需求文档、架构或流程图、课堂笔记、代码、测试、作业与答案。
2. 每个新增能力必须说明它如何承接前一天并成为后续平台能力的输入。
3. 代码量只统计有效源代码、测试和基础设施，不用重复或生成垃圾内容凑数。
4. 示例一律使用虚构数据；密钥和真实个人敏感信息不得进入仓库。
