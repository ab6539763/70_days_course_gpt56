"""Day 22 审计日志、AuditLogStore 与 GET /api/audit 单测。"""

import os
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1] / "solution"
sys.path.insert(0, str(ROOT))
os.environ.setdefault("NEXUS_USE_MOCK", "1")

from nexus.observability.audit_log import AuditLogStore, record_audit_event, resolve_audit_dir
from nexus.web.app import create_app


with tempfile.TemporaryDirectory(prefix="nexus-day22-audit-") as temporary:
    audit_dir = Path(temporary) / "audit"
    os.environ["NEXUS_AUDIT_DIR"] = str(audit_dir)
    store = AuditLogStore(audit_dir=audit_dir, max_entries=10)
    data_file = str(Path(temporary) / "demo.json")
    record = store.append(
        data_file=data_file,
        revision=1,
        action="session_create",
        operator="TESTER",
        session_id="nxs_demo",
        trace_id="trace-demo",
        detail="unit test",
    )
    assert record.audit_id.startswith("aud_")
    assert record.revision == 1
    assert record.action == "session_create"
    listed = store.list_for(data_file, limit=5)
    assert len(listed) == 1
    assert listed[0].operator == "TESTER"
    assert resolve_audit_dir() == str(audit_dir)
    assert record_audit_event(
        data_file,
        2,
        "web_chat",
        operator="TESTER",
        audit_store=store,
    ) is not None

    app = create_app(session_dir=str(Path(temporary) / "sessions"))
    client = app.test_client()
    health = client.get("/api/health")
    assert health.status_code == 200
    health_payload = health.get_json()
    assert health_payload["audit_dir"] == str(audit_dir)
    assert health_payload["audit_count"] >= 0

    created = client.post("/api/session", json={"owner": "审计用户"})
    session_id = created.get_json()["session_id"]
    headers = {"X-Session-Id": session_id, "X-Trace-Id": "trace-audit-web"}
    revision = client.get("/api/revision", headers=headers)
    rev = revision.get_json()["revision"]
    chat = client.post(
        "/api/chat",
        json={"prompt": "审计测试", "expected_revision": rev},
        headers=headers,
    )
    assert chat.status_code == 200

    audit = client.get("/api/audit", headers=headers)
    assert audit.status_code == 200
    payload = audit.get_json()
    assert payload["count"] >= 2
    assert payload["session_id"] == session_id
    actions = {item["action"] for item in payload["records"]}
    assert "session_create" in actions
    assert "web_chat" in actions
    assert any(item["trace_id"] for item in payload["records"])

    openapi = client.get("/api/openapi.json")
    spec = openapi.get_json()
    assert "/api/audit" in spec["paths"]
    assert "AuditLogResponse" in spec["components"]["schemas"]

print("Day 22 审计日志单测通过：AuditLogStore、GET /api/audit 与 OpenAPI 均正确。")
