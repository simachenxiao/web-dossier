from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app


def create_case(client: TestClient) -> int:
    response = client.post("/api/cases", json={
        "case_no": f"CASE-RESULT-{uuid4()}",
        "case_name": "周枫殴打李江案",
        "case_type": "殴打他人",
    })
    assert response.status_code == 200
    return response.json()["id"]


def create_task(client: TestClient, case_id: int, message: str, payload: dict | None = None) -> dict:
    client.post(f"/api/cases/{case_id}/conversations/messages", json={
        "source_role": "民警",
        "original_text": message,
    })
    drafts = client.get(f"/api/cases/{case_id}/drafts").json()
    draft = next(item for item in drafts if item["status"] == "pending_confirmation")
    response = client.post(f"/api/drafts/{draft['id']}/confirm", json={
        "reviewer": "赵武",
        "payload": payload,
    })
    assert response.status_code == 200
    return client.get(f"/api/cases/{case_id}/tasks").json()[-1]


def test_task_material_result_flows_into_graph_and_completes_task() -> None:
    with TestClient(app) as client:
        case_id = create_case(client)
        task = create_task(client, case_id, "请上传医院诊断证明。")

        response = client.post(f"/api/tasks/{task['id']}/complete", json={
            "result_type": "material",
            "payload": {
                "title": "医院诊断证明",
                "material_type": "医院诊断证明",
                "source": "民警上传",
                "owner": "李江",
                "extracted_facts": {"consequence": "头皮挫裂伤"},
            },
        })
        assert response.status_code == 200
        assert response.json()["status"] == "completed"

        materials = client.get(f"/api/cases/{case_id}/materials").json()
        assert any(material["title"] == "医院诊断证明" for material in materials)

        graph = client.get(f"/api/cases/{case_id}/graph").json()
        consequence = next(element for element in graph["elements"] if element["element_key"] == "consequence")
        assert consequence["material_count"] == 1
        assert consequence["status"] == "proved"


def test_task_material_result_creates_conflict_check_once_for_statement_pair() -> None:
    with TestClient(app) as client:
        case_id = create_case(client)
        first = create_task(client, case_id, "请制作李江询问笔录。")
        second = create_task(client, case_id, "请制作周枫询问笔录。", {
            "title": "制作周枫询问笔录",
            "task_type": "询问笔录",
            "priority": "P1",
            "expected_materials": ["周枫询问笔录"],
            "depends_on": [],
        })

        for task, owner, action in ((first, "李江", "拳打"), (second, "周枫", "推搡")):
            response = client.post(f"/api/tasks/{task['id']}/complete", json={
                "result_type": "material",
                "payload": {
                    "title": f"{owner}询问笔录",
                    "material_type": "询问笔录",
                    "source": "笔录 Agent",
                    "owner": owner,
                    "supports_elements": ["victim" if owner == "李江" else "suspect", "tool", "consequence"],
                    "extracted_facts": {"action": action},
                },
            })
            assert response.status_code == 200

        first_checks = client.post(f"/api/cases/{case_id}/run-loop").json()["conflict_checks_created"]
        second_checks = client.post(f"/api/cases/{case_id}/run-loop").json()["conflict_checks_created"]
        assert first_checks == 0
        assert second_checks == 0


def test_task_fact_update_result_creates_fact_version() -> None:
    with TestClient(app) as client:
        case_id = create_case(client)
        task = create_task(client, case_id, "创建处罚事实更新任务。", {
            "title": "更新处罚事实",
            "task_type": "事实更新",
            "priority": "P1",
            "expected_materials": [],
            "depends_on": [],
        })

        response = client.post(f"/api/tasks/{task['id']}/complete", json={
            "result_type": "fact_update",
            "payload": {
                "fact_text": "周枫被处以行政拘留五日。",
                "reviewer": "赵武",
            },
        })
        assert response.status_code == 200
        assert response.json()["status"] == "completed"

        versions = client.get(f"/api/cases/{case_id}/fact-versions").json()
        assert len(versions) == 1
        assert versions[0]["fact_summary"] == "周枫被处以行政拘留五日。"


def test_approval_result_creates_conversation_event_and_completes_task() -> None:
    with TestClient(app) as client:
        case_id = create_case(client)
        task = create_task(client, case_id, "创建行政立案审批任务。", {
            "title": "行政立案",
            "task_type": "行政立案",
            "priority": "P0",
            "expected_materials": ["行政立案登记表"],
            "depends_on": [],
        })
        client.post(f"/api/tasks/{task['id']}/start")

        response = client.post(f"/api/tasks/{task['id']}/complete", json={
            "result_type": "approval",
            "payload": {
                "decision": "approved",
                "result_text": "领导审批通过行政立案。",
                "reviewer": "王所",
            },
        })
        assert response.status_code == 200
        assert response.json()["status"] == "completed"

        events = client.get(f"/api/cases/{case_id}/conversations/events").json()
        approval = events[-1]
        assert approval["event_type"] == "approval_result"
        assert approval["related_task_id"] == task["id"]
