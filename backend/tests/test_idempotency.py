from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app


def create_case(client: TestClient) -> int:
    response = client.post("/api/cases", json={
        "case_no": f"CASE-IDEMPOTENCY-{uuid4()}",
        "case_name": "周枫殴打李江案",
        "case_type": "殴打他人",
    })
    assert response.status_code == 200
    return response.json()["id"]


def test_repeated_conversation_task_intent_does_not_create_duplicate_task() -> None:
    with TestClient(app) as client:
        case_id = create_case(client)
        message = {
            "source_role": "民警",
            "original_text": "请补齐医院诊断证明。",
            "idempotency_key": "same-task-intent",
        }

        first = client.post(f"/api/cases/{case_id}/conversations/messages", json=message)
        second = client.post(f"/api/cases/{case_id}/conversations/messages", json=message)
        assert first.status_code == 200
        assert second.status_code == 200
        assert first.json()["id"] == second.json()["id"]

        drafts = client.get(f"/api/cases/{case_id}/drafts").json()
        assert len(drafts) == 1

        draft = drafts[0]
        client.post(f"/api/drafts/{draft['id']}/confirm", json={"reviewer": "赵武"})
        repeated_confirm = client.post(f"/api/drafts/{draft['id']}/confirm", json={"reviewer": "赵武"})
        assert repeated_confirm.status_code == 409

        tasks = client.get(f"/api/cases/{case_id}/tasks").json()
        assert len(tasks) == 1


def test_repeated_material_ingest_uses_idempotency_key() -> None:
    with TestClient(app) as client:
        case_id = create_case(client)
        payload = {
            "title": "医院诊断证明",
            "material_type": "医院诊断证明",
            "source": "民警上传",
            "owner": "李江",
            "idempotency_key": "same-material",
        }

        first = client.post(f"/api/cases/{case_id}/materials", json=payload)
        second = client.post(f"/api/cases/{case_id}/materials", json=payload)
        assert first.status_code == 200
        assert second.status_code == 200
        assert first.json()["id"] == second.json()["id"]

        materials = client.get(f"/api/cases/{case_id}/materials").json()
        assert len(materials) == 1
