from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app


def create_case(client: TestClient) -> int:
    response = client.post("/api/cases", json={
        "case_no": f"CASE-CONFIRM-{uuid4()}",
        "case_name": "周枫殴打李江案",
        "case_type": "殴打他人",
    })
    assert response.status_code == 200
    return response.json()["id"]


def first_draft(client: TestClient, case_id: int) -> dict:
    drafts = client.get(f"/api/cases/{case_id}/drafts").json()
    assert len(drafts) == 1
    return drafts[0]


def test_confirm_material_binding_draft_creates_material() -> None:
    with TestClient(app) as client:
        case_id = create_case(client)
        client.post(f"/api/cases/{case_id}/conversations/messages", json={
            "source_role": "笔录 Agent",
            "original_text": "李江询问笔录已完成并回写。",
        })
        draft = first_draft(client, case_id)

        response = client.post(f"/api/drafts/{draft['id']}/confirm", json={"reviewer": "赵武"})
        assert response.status_code == 200

        materials = client.get(f"/api/cases/{case_id}/materials").json()
        assert len(materials) == 1
        assert materials[0]["title"] == "询问笔录"
        assert materials[0]["supports_elements"] == ["victim", "tool", "consequence"]


def test_confirm_fact_update_draft_creates_fact_version() -> None:
    with TestClient(app) as client:
        case_id = create_case(client)
        client.post(f"/api/cases/{case_id}/conversations/messages", json={
            "source_role": "民警",
            "original_text": "医院诊断证明已上传，伤势结果为头皮挫裂伤。",
        })
        draft = first_draft(client, case_id)
        assert draft["draft_type"] == "material_binding"

        response = client.post(f"/api/drafts/{draft['id']}/confirm", json={
            "reviewer": "赵武",
            "payload": {
                "fact_text": "伤势结果为头皮挫裂伤。",
            },
        })
        assert response.status_code == 200

        fact_versions = client.get(f"/api/cases/{case_id}/fact-versions").json()
        assert fact_versions == []


def test_confirm_conflict_review_creates_conflict_task() -> None:
    with TestClient(app) as client:
        case_id = create_case(client)
        client.post(f"/api/cases/{case_id}/conversations/messages", json={
            "source_role": "办案 Agent",
            "original_text": "周枫自书材料与李江询问笔录存在矛盾。",
        })
        draft = first_draft(client, case_id)

        response = client.post(f"/api/drafts/{draft['id']}/confirm", json={"reviewer": "赵武"})
        assert response.status_code == 200

        tasks = client.get(f"/api/cases/{case_id}/tasks").json()
        assert any(task["task_type"] == "矛盾复核" and task["priority"] == "P0" for task in tasks)


def test_reject_draft_has_no_task_side_effect() -> None:
    with TestClient(app) as client:
        case_id = create_case(client)
        client.post(f"/api/cases/{case_id}/conversations/messages", json={
            "source_role": "民警",
            "original_text": "请补齐医院诊断证明。",
        })
        draft = first_draft(client, case_id)

        response = client.post(f"/api/drafts/{draft['id']}/reject", json={
            "reviewer": "赵武",
            "reason": "已有材料",
        })
        assert response.status_code == 200
        assert response.json()["status"] == "rejected"

        tasks = client.get(f"/api/cases/{case_id}/tasks").json()
        assert tasks == []
