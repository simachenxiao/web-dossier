from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app


def create_case(client: TestClient) -> int:
    response = client.post("/api/cases", json={
        "case_no": f"CASE-TASK-{uuid4()}",
        "case_name": "周枫殴打李江案",
        "case_type": "殴打他人",
    })
    assert response.status_code == 200
    return response.json()["id"]


def create_task_from_message(client: TestClient, case_id: int, message: str, payload: dict | None = None) -> dict:
    client.post(f"/api/cases/{case_id}/conversations/messages", json={
        "source_role": "民警",
        "original_text": message,
    })
    draft = client.get(f"/api/cases/{case_id}/drafts").json()[0]
    response = client.post(f"/api/drafts/{draft['id']}/confirm", json={
        "reviewer": "赵武",
        "payload": payload,
    })
    assert response.status_code == 200
    tasks = client.get(f"/api/cases/{case_id}/tasks").json()
    return tasks[-1]


def test_start_transcript_task_routes_to_mock_transcript_agent() -> None:
    with TestClient(app) as client:
        case_id = create_case(client)
        task = create_task_from_message(client, case_id, "请制作李江询问笔录。")

        response = client.post(f"/api/tasks/{task['id']}/start")
        assert response.status_code == 200
        started = response.json()
        assert started["status"] == "in_progress"
        assert started["assignee_type"] == "agent"
        assert started["assignee_name"] == "笔录 Agent"


def test_start_document_task_generates_material_and_completes() -> None:
    with TestClient(app) as client:
        case_id = create_case(client)
        task = create_task_from_message(client, case_id, "请开具发还清单。")

        response = client.post(f"/api/tasks/{task['id']}/start")
        assert response.status_code == 200
        started = response.json()
        assert started["status"] == "completed"
        assert started["assignee_type"] == "system"

        materials = client.get(f"/api/cases/{case_id}/materials").json()
        assert any(material["title"] == "发还清单" for material in materials)


def test_start_human_upload_task_waits_for_upload() -> None:
    with TestClient(app) as client:
        case_id = create_case(client)
        task = create_task_from_message(client, case_id, "请上传医院诊断证明。")

        response = client.post(f"/api/tasks/{task['id']}/start")
        assert response.status_code == 200
        started = response.json()
        assert started["status"] == "waiting_upload"
        assert started["assignee_type"] == "human"
        assert started["assignee_name"] == "民警"


def test_start_approval_task_waits_for_leader_approval() -> None:
    with TestClient(app) as client:
        case_id = create_case(client)
        task = create_task_from_message(client, case_id, "创建行政立案审批任务。", {
            "title": "行政立案",
            "task_type": "行政立案",
            "priority": "P0",
            "expected_materials": ["行政立案登记表", "行政立案告知书", "接报审批表"],
            "depends_on": [],
        })

        response = client.post(f"/api/tasks/{task['id']}/start")
        assert response.status_code == 200
        started = response.json()
        assert started["status"] == "pending_approval"
        assert started["assignee_type"] == "approval"
        assert started["assignee_name"] == "领导"


def test_blocked_task_unblocks_after_dependency_material_arrives() -> None:
    with TestClient(app) as client:
        case_id = create_case(client)
        task = create_task_from_message(client, case_id, "请制作嫌疑人供述。", {
            "title": "嫌疑人供述",
            "task_type": "嫌疑人供述",
            "priority": "P1",
            "expected_materials": ["嫌疑人供述"],
            "depends_on": ["传唤证"],
        })

        blocked_response = client.post(f"/api/tasks/{task['id']}/start")
        assert blocked_response.status_code == 200
        assert blocked_response.json()["status"] == "blocked"
        assert blocked_response.json()["blocked_by"] == ["传唤证"]

        material_response = client.post(f"/api/cases/{case_id}/materials", json={
            "title": "传唤证",
            "material_type": "传唤证",
            "source": "文书生成器",
            "owner": "周枫",
        })
        assert material_response.status_code == 200

        tasks = client.get(f"/api/cases/{case_id}/tasks").json()
        updated = next(item for item in tasks if item["id"] == task["id"])
        assert updated["status"] == "pending"
        assert updated["blocked_by"] == []
