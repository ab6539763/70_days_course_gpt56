"""Day 7 阶段项目端到端测试：双进程联系人 CRUD。"""

from pathlib import Path
import json
import subprocess
import sys
import tempfile


SOLUTION = Path(__file__).parents[1] / "solution" / "contact_directory.py"


def run_cli(directory: Path, lines: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SOLUTION)],
        cwd=directory,
        input="\n".join(lines) + "\n",
        text=True,
        capture_output=True,
        check=False,
    )


with tempfile.TemporaryDirectory(prefix="nexus-day07-cli-") as temporary:
    working = Path(temporary)
    first = run_cli(
        working,
        [
            "E70007", "客服部",
            "1", "C2", "李梅", "研发部", "AI 工程师",
            "limei@example.test", "python, rag, PYTHON",
            "1", "C1", "王芳", "销售部", "销售经理",
            "wangfang@example.test", "sales, crm",
            "1", "C3", "重复邮箱", "产品部", "产品经理",
            "LIMEI@example.test", "product",
            "2",
            "3", "PYTHON",
            "4", "C2", "高级 AI 工程师",
            "6",
            "7",
            "0",
        ],
    )
    assert first.returncode == 0, first.stderr
    assert "维护人已保存：E70007｜客户服务部｜revision=1" in first.stdout
    assert "已新增 C2｜李梅并保存｜revision=2" in first.stdout
    assert "已新增 C1｜王芳并保存｜revision=3" in first.stdout
    assert "邮箱 limei@example.test 已存在" in first.stdout
    assert first.stdout.index("C2｜李梅") < first.stdout.index("C1｜王芳")
    assert "搜索结果：1 名" in first.stdout
    assert "C2｜李梅｜技术部｜AI 工程师" in first.stdout
    assert "已更新 C2并保存｜revision=4" in first.stdout
    assert "总数=2" in first.stdout
    assert "'技术部': 1" in first.stdout
    assert "'销售部': 1" in first.stdout
    assert "摘要：schema=1｜revision=4｜contacts=2" in first.stdout

    second = run_cli(
        working,
        [
            "5", "C1",
            "1", "C1", "周宁", "产品部", "产品经理",
            "zhouning@example.test", "product, agent",
            "3", "产品",
            "6",
            "0",
        ],
    )
    assert second.returncode == 0, second.stderr
    assert "恢复成功：revision=4，联系人 2 名" in second.stdout
    assert "维护人已恢复：E70007｜客户服务部" in second.stdout
    assert "维护人员工编号（" not in second.stdout
    assert "已删除 C1｜王芳并保存｜revision=5" in second.stdout
    assert "已新增 C1｜周宁并保存｜revision=6" in second.stdout
    assert "C1｜周宁｜产品部｜产品经理" in second.stdout
    final_data = json.loads(
        (working / "nexus_contacts.json").read_text(encoding="utf-8")
    )
    assert final_data["revision"] == 6
    assert {item["contact_id"] for item in final_data["contacts"]} == {"C1", "C2"}
    assert {item["email"] for item in final_data["contacts"]} == {
        "zhouning@example.test",
        "limei@example.test",
    }

with tempfile.TemporaryDirectory(prefix="nexus-day07-lock-") as temporary:
    locked = run_cli(Path(temporary), ["", "A1", "E"])
    assert locked.returncode == 2
    assert "连续三次无效" in locked.stdout
    assert not (Path(temporary) / "nexus_contacts.json").exists()

with tempfile.TemporaryDirectory(prefix="nexus-day07-schema-") as temporary:
    working = Path(temporary)
    path = working / "nexus_contacts.json"
    original = '{"schema_version": 9, "revision": 0, "owner": null, "contacts": []}\n'
    path.write_text(original, encoding="utf-8")
    rejected = run_cli(working, [])
    assert rejected.returncode == 3
    assert "不支持的 schema_version" in rejected.stdout
    assert path.read_text(encoding="utf-8") == original

print("Day 7 CLI 验收通过：联系人 CRUD、搜索、唯一性和跨进程恢复均正确。")
