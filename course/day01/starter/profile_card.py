"""Day 1 课堂起步代码：最小可运行的员工信息卡片。

这个版本故意只使用变量、字符串、print 和 input。
学员将在课堂中逐行输入，而不是直接复制完整答案。
"""


# print 会把括号中的文本输出到终端。
print("=" * 46)
print("智枢 NexusAI｜员工信息卡片创建向导")
print("=" * 46)

# input 会暂停程序并等待用户输入；返回值始终是字符串。
name = input("请输入姓名：").strip()
department = input("请输入部门：").strip()
role = input("请输入岗位：").strip()
skill = input("请输入最希望 Agent 帮助你的工作：").strip()

# f-string 可把变量放进文本。花括号内填写变量名。
print("\n" + "-" * 46)
print(f"姓名：{name}")
print(f"部门：{department}")
print(f"岗位：{role}")
print(f"Agent 期待：{skill}")
print("-" * 46)
print("创建完成。欢迎加入智枢企业智能协作平台！")
