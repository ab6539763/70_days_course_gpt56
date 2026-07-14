# 零基础大模型应用开发 70 天课程

本仓库以“智枢 NexusAI 企业智能协作平台”为单一项目主线，模拟业务、产品、开发、测试、安全与运维团队从需求到上线的完整协作过程。课程每天形成可运行增量，不使用彼此割裂的演示项目。

## 当前内容

- [70 天贯穿式项目蓝图](docs/course-blueprint.md)
- [Day 1 完整课件：从业务问题到第一段可验收代码](course/day01/day01-lesson.md)
- Day 1 [课堂起步代码](course/day01/starter/profile_card.py)
- Day 1 [带详细注释的参考实现](course/day01/solution/profile_card.py)
- Day 1 [自动验收脚本](course/day01/tests/test_profile_card.py)

## Day 1 运行

```bash
python course/day01/solution/profile_card.py
python course/day01/tests/test_profile_card.py
```

课件中的 Mermaid 图可在支持 Mermaid 的 Markdown 阅读器中直接渲染。

## 内容原则

1. 每天均包含业务上下文、需求文档、架构或流程图、课堂笔记、代码、测试、作业与答案。
2. 每个新增能力必须说明它如何承接前一天并成为后续平台能力的输入。
3. 代码量只统计有效源代码、测试和基础设施，不用重复或生成垃圾内容凑数。
4. 示例一律使用虚构数据；密钥和真实个人敏感信息不得进入仓库。
