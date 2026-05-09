from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app


def create_case(client: TestClient) -> int:
    response = client.post("/api/cases", json={
        "case_no": f"CASE-AI-{uuid4()}",
        "case_name": "周枫殴打李江案",
        "case_type": "殴打他人",
    })
    assert response.status_code == 200
    return response.json()["id"]


def test_task_intent_message_creates_pending_task_draft() -> None:
    with TestClient(app) as client:
        case_id = create_case(client)

        event_response = client.post(f"/api/cases/{case_id}/conversations/messages", json={
            "source_role": "民警",
            "original_text": "请补齐医院诊断证明。",
        })
        assert event_response.status_code == 200
        assert event_response.json()["event_type"] == "task_intent"

        drafts_response = client.get(f"/api/cases/{case_id}/drafts")
        assert drafts_response.status_code == 200
        drafts = drafts_response.json()
        assert len(drafts) == 1
        assert drafts[0]["draft_type"] == "task"
        assert drafts[0]["status"] == "pending_confirmation"
        assert drafts[0]["element_key"] == "consequence"

        confirm_response = client.post(f"/api/drafts/{drafts[0]['id']}/confirm", json={
            "reviewer": "赵武",
        })
        assert confirm_response.status_code == 200

        tasks_response = client.get(f"/api/cases/{case_id}/tasks")
        assert tasks_response.status_code == 200
        assert any(task["source"] == "ai" and task["element_key"] == "consequence" for task in tasks_response.json())


def test_agent_completion_message_creates_material_binding_draft() -> None:
    with TestClient(app) as client:
        case_id = create_case(client)

        event_response = client.post(f"/api/cases/{case_id}/conversations/messages", json={
            "source_role": "笔录 Agent",
            "original_text": "李江询问笔录已完成并回写。",
        })
        assert event_response.status_code == 200
        assert event_response.json()["event_type"] == "material_result"
        assert event_response.json()["related_person"] == "李江"

        drafts = client.get(f"/api/cases/{case_id}/drafts").json()
        assert drafts[0]["draft_type"] == "material_binding"
        assert drafts[0]["payload"]["supports_elements"] == ["victim", "tool", "consequence"]


def test_conflict_message_creates_conflict_review_draft() -> None:
    with TestClient(app) as client:
        case_id = create_case(client)

        event_response = client.post(f"/api/cases/{case_id}/conversations/messages", json={
            "source_role": "办案 Agent",
            "original_text": "周枫自书材料与李江询问笔录存在矛盾。",
        })
        assert event_response.status_code == 200
        assert event_response.json()["event_type"] == "conflict_clue"

        drafts = client.get(f"/api/cases/{case_id}/drafts").json()
        assert drafts[0]["draft_type"] == "conflict_review"
        assert drafts[0]["payload"]["priority"] == "P0"
