from datetime import UTC, datetime
from hashlib import sha256

from sqlalchemy.orm import Session

from app.models import ConversationEvent, Element, Material, Task, TaskExecutionResult
from app.schemas.material import MaterialCreate
from app.schemas.task import TaskComplete
from app.services.conflict_service import create_conflict_check_candidates
from app.services.fact_version_service import record_fact_update
from app.services.material_service import ingest_material

DOCUMENT_KEYWORDS = ("文书", "决定书", "清单", "审批表", "告知书", "传唤证", "发还清单", "登记表", "接报审批表")
TRANSCRIPT_KEYWORDS = ("笔录",)
HUMAN_UPLOAD_KEYWORDS = ("上传", "医院诊断证明")
APPROVAL_KEYWORDS = ("审批", "行政立案", "行政快办")


def start_task(db: Session, task_id: int) -> Task:
    task = db.get(Task, task_id)
    if not task:
        raise ValueError("Task not found")
    if task.status not in ("pending", "blocked"):
        raise ValueError("Task cannot be started")

    missing = missing_dependencies(db, task)
    if missing:
        task.status = "blocked"
        task.blocked_by = missing
        task.blocked_reason = "前置条件未满足"
        db.commit()
        db.refresh(task)
        return task

    route = select_execution_route(task)
    if route == "transcript_agent":
        _dispatch(task, "agent", "笔录 Agent")
    elif route == "document_generator":
        _dispatch(task, "system", "文书生成器")
        _generate_documents(db, task)
        task.status = "completed"
    elif route == "human_upload":
        _dispatch(task, "human", "民警")
        task.status = "waiting_upload"
    elif route == "approval":
        _dispatch(task, "approval", "领导")
        task.status = "pending_approval"
    else:
        _dispatch(task, "agent", "办案 Agent")

    db.commit()
    db.refresh(task)
    return task


def complete_task(db: Session, task_id: int, payload: TaskComplete) -> Task:
    task = db.get(Task, task_id)
    if not task:
        raise ValueError("Task not found")
    if task.status == "completed":
        raise ValueError("Task cannot be completed")

    key = payload.idempotency_key or sha256(f"task:{task.id}:{payload.result_type}:{payload.payload}".encode("utf-8")).hexdigest()
    existing = db.query(TaskExecutionResult).filter(
        TaskExecutionResult.task_id == task.id,
        TaskExecutionResult.idempotency_key == key,
    ).one_or_none()
    if not existing:
        material_ids, event_id = _apply_task_result(db, task, payload)
        db.add(TaskExecutionResult(
            case_id=task.case_id,
            task_id=task.id,
            result_type=payload.result_type,
            status="processed",
            executor_type=task.assignee_type,
            executor_name=task.assignee_name,
            payload=payload.payload,
            generated_material_ids=material_ids,
            generated_event_id=event_id,
            idempotency_key=key,
        ))

    task.status = "completed"
    task.blocked_by = []
    task.blocked_reason = None
    db.commit()
    db.refresh(task)
    return task


def missing_dependencies(db: Session, task: Task) -> list[str]:
    return [dependency for dependency in task.depends_on if not dependency_satisfied(db, task.case_id, dependency)]


def dependency_satisfied(db: Session, case_id: int, dependency: str) -> bool:
    if dependency == "所有核心要素proved":
        proved = db.query(Element).filter(
            Element.case_id == case_id,
            Element.element_key.in_(["suspect", "tool", "consequence"]),
            Element.status == "proved",
        ).count()
        return proved == 3
    materials = db.query(Material).filter(Material.case_id == case_id).all()
    if dependency == "嫌疑人身份核验":
        return any("身份核验" in material.material_type and "suspect" in material.supports_elements for material in materials)
    return any(dependency in material.material_type or dependency in material.title for material in materials)


def select_execution_route(task: Task) -> str:
    text = f"{task.title} {task.task_type} {' '.join(task.expected_materials)}"
    if any(keyword in text for keyword in APPROVAL_KEYWORDS):
        return "approval"
    if any(keyword in text for keyword in HUMAN_UPLOAD_KEYWORDS):
        return "human_upload"
    if any(keyword in text for keyword in TRANSCRIPT_KEYWORDS):
        return "transcript_agent"
    if any(keyword in text for keyword in DOCUMENT_KEYWORDS):
        return "document_generator"
    return "case_agent"


def unblock_ready_tasks(db: Session, case_id: int) -> int:
    updated = 0
    tasks = db.query(Task).filter(Task.case_id == case_id, Task.status == "blocked").all()
    for task in tasks:
        missing = missing_dependencies(db, task)
        task.blocked_by = missing
        if not missing:
            task.status = "pending"
            task.blocked_reason = None
            updated += 1
    return updated


def _apply_task_result(db: Session, task: Task, result: TaskComplete) -> tuple[list[int], int | None]:
    if result.result_type == "material":
        return _apply_material_result(db, task, result.payload), None
    if result.result_type == "approval":
        return [], _apply_approval_result(db, task, result.payload)
    if result.result_type == "fact_update":
        _apply_fact_update_result(db, task, result.payload)
    return [], None


def _apply_material_result(db: Session, task: Task, payload: dict) -> list[int]:
    title = payload.get("title") or (task.expected_materials[0] if task.expected_materials else task.task_type)
    material_type = payload.get("material_type", title)
    material = ingest_material(db, task.case_id, MaterialCreate(
        title=title,
        material_type=material_type,
        source=payload.get("source", task.assignee_name),
        file_path=payload.get("file_path"),
        owner=payload.get("owner"),
        supports_elements=payload.get("supports_elements", [task.element_key] if task.element_key else []),
        extracted_facts=payload.get("extracted_facts", {}),
        idempotency_key=payload.get("idempotency_key", f"task:{task.id}:material:{title}"),
    ))
    material.source_task_id = task.id
    material.fact_status = payload.get("fact_status", "confirmed")
    material.confirmed_by = payload.get("confirmed_by") or payload.get("reviewer") or task.assignee_name
    material.confirmed_at = datetime.now(UTC).isoformat()
    db.flush()
    create_conflict_check_candidates(db, task.case_id)
    unblock_ready_tasks(db, task.case_id)
    return [material.id]


def _apply_approval_result(db: Session, task: Task, payload: dict) -> int:
    text = payload.get("result_text") or payload.get("decision") or "审批结果已回写。"
    key = payload.get("event_idempotency_key", f"task:{task.id}:approval:{payload.get('decision', text)}")
    existing = db.query(ConversationEvent).filter(
        ConversationEvent.case_id == task.case_id,
        ConversationEvent.idempotency_key == key,
    ).one_or_none()
    if existing:
        return existing.id
    event = ConversationEvent(
        case_id=task.case_id,
        source_role="领导",
        source_name=payload.get("reviewer"),
        event_type="approval_result",
        original_text=text,
        normalized_text=" ".join(text.split()),
        related_person=None,
        related_material_title=None,
        related_task_id=task.id,
        metadata_json=payload,
        confidence="rule",
        idempotency_key=key,
    )
    db.add(event)
    db.flush()
    return event.id


def _apply_fact_update_result(db: Session, task: Task, payload: dict) -> None:
    fact_text = payload.get("fact_text") or payload.get("summary") or str(payload)
    if task.element_key:
        element = db.query(Element).filter(Element.case_id == task.case_id, Element.element_key == task.element_key).one_or_none()
        if element:
            element.key_fact = fact_text
    record_fact_update(db, task.case_id, fact_text, task.source_draft_id, payload.get("reviewer"))


def _dispatch(task: Task, assignee_type: str, assignee_name: str) -> None:
    task.assignee_type = assignee_type
    task.assignee_name = assignee_name
    task.status = "in_progress"


def _generate_documents(db: Session, task: Task) -> None:
    material_ids: list[int] = []
    for material_title in task.expected_materials or [task.task_type]:
        material = ingest_material(db, task.case_id, MaterialCreate(
            title=material_title,
            material_type=material_title,
            source="文书生成器",
            owner=None,
            supports_elements=[task.element_key] if task.element_key else [],
            extracted_facts={},
            idempotency_key=f"task:{task.id}:material:{material_title}",
        ))
        material_ids.append(material.id)
    _record_execution_result(db, task, "document_generation", "completed", {"generated_material_ids": material_ids}, material_ids)


def _record_execution_result(db: Session, task: Task, result_type: str, status: str, payload: dict, material_ids: list[int] | None = None) -> None:
    key = sha256(f"task:{task.id}:{result_type}:{payload}".encode("utf-8")).hexdigest()
    existing = db.query(TaskExecutionResult).filter(
        TaskExecutionResult.task_id == task.id,
        TaskExecutionResult.idempotency_key == key,
    ).one_or_none()
    if existing:
        return
    db.add(TaskExecutionResult(
        case_id=task.case_id,
        task_id=task.id,
        result_type=result_type,
        status=status,
        executor_type=task.assignee_type,
        executor_name=task.assignee_name,
        payload=payload,
        generated_material_ids=material_ids or [],
        idempotency_key=key,
    ))
