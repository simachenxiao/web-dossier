from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app


def test_case_graph_conversation_material_task_flow() -> None:
    with TestClient(app) as client:
        case_response = client.post("/api/cases", json={
            "case_no": f"CASE-TEST-{uuid4()}",
            "case_name": "周枫殴打李江案",
            "case_type": "殴打他人",
        })
        assert case_response.status_code == 200
        case_id = case_response.json()["id"]

        graph_response = client.get(f"/api/cases/{case_id}/graph")
        assert graph_response.status_code == 200
        assert len(graph_response.json()["elements"]) == 7

        event_response = client.post(f"/api/cases/{case_id}/conversations/messages", json={
            "source_role": "笔录 Agent",
            "original_text": "李江询问笔录已完成并回写。",
        })
        assert event_response.status_code == 200
        assert event_response.json()["event_type"] == "material_result"

        material_response = client.post(f"/api/cases/{case_id}/materials", json={
            "title": "李江询问笔录",
            "material_type": "询问笔录",
            "source": "笔录 Agent",
            "owner": "李江",
            "supports_elements": ["victim", "tool", "consequence"],
        })
        assert material_response.status_code == 200
        assert material_response.json()["title"] == "李江询问笔录"

        graph_after_material = client.get(f"/api/cases/{case_id}/graph")
        assert graph_after_material.status_code == 200
        victim = next(element for element in graph_after_material.json()["elements"] if element["element_key"] == "victim")
        assert victim["material_count"] == 1
        assert victim["status"] == "proved"

        loop_response = client.post(f"/api/cases/{case_id}/run-loop")
        assert loop_response.status_code == 200
        assert loop_response.json()["status"] == "completed"
        assert loop_response.json()["gaps_created"] > 0

        tasks_response = client.get(f"/api/cases/{case_id}/tasks")
        assert tasks_response.status_code == 200
        assert any(task["element_key"] == "suspect" for task in tasks_response.json())
