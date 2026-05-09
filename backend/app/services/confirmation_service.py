from datetime import UTC, datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import ConfirmationDecision, Conflict, Draft, Element, Task
from app.schemas.confirmation import DraftDecision
from app.schemas.material import MaterialCreate
from app.services.fact_version_service import record_fact_update
from app.services.material_service import ingest_material


def confirm_draft(db: Session, draft_id: int, payload: DraftDecision) -> Draft:
    draft = _get_pending_draft(db, draft_id)
    before_payload = dict(draft.payload)
    after_payload = payload.payload or before_payload
    draft.payload = after_payload
    draft.status = "confirmed"
    draft.reviewer = payload.reviewer
    draft.review_reason = payload.reason
    draft.reviewed_at = datetime.now(UTC).isoformat()

    _record_decision(db, draft, "confirmed", payload.reviewer, payload.reason, before_payload, after_payload)
    _apply_confirmed_draft(db, draft, after_payload, payload.reviewer)
    db.commit()
    db.refresh(draft)
    return draft


def reject_draft(db: Session, draft_id: int, payload: DraftDecision) -> Draft:
    draft = _get_pending_draft(db, draft_id)
    before_payload = dict(draft.payload)
    after_payload = payload.payload or {}
    draft.status = "rejected"
    draft.reviewer = payload.reviewer
    draft.review_reason = payload.reason
    draft.reviewed_at = datetime.now(UTC).isoformat()

    _record_decision(db, draft, "rejected", payload.reviewer, payload.reason, before_payload, after_payload)
    db.commit()
    db.refresh(draft)
    return draft


def _get_pending_draft(db: Session, draft_id: int) -> Draft:
    draft = db.get(Draft, draft_id)
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    if draft.status != "pending_confirmation":
        raise HTTPException(status_code=409, detail="Draft is not pending confirmation")
    return draft


def _record_decision(
    db: Session,
    draft: Draft,
    decision: str,
    reviewer: str,
    reason: str | None,
    before_payload: dict,
    after_payload: dict,
) -> None:
    db.add(ConfirmationDecision(
        case_id=draft.case_id,
        draft_id=draft.id,
        source_event_id=draft.source_event_id,
        decision=decision,
        reviewer=reviewer,
        reason=reason,
        before_payload=before_payload,
        after_payload=after_payload,
    ))


def _apply_confirmed_draft(db: Session, draft: Draft, payload: dict, reviewer: str) -> None:
    if draft.draft_type == "task":
        _create_task_from_draft(db, draft, payload)
    elif draft.draft_type == "fact_update":
        _apply_fact_update(db, draft, payload, reviewer)
    elif draft.draft_type == "material_binding":
        _apply_material_binding(db, draft, payload)
    elif draft.draft_type == "conflict_review":
        _apply_conflict_review(db, draft, payload)


def _create_task_from_draft(db: Session, draft: Draft, payload: dict) -> None:
    idempotency_key = payload.get("idempotency_key", f"draft:{draft.id}:task")
    existing = db.query(Task).filter(Task.case_id == draft.case_id, Task.idempotency_key == idempotency_key).one_or_none()
    if existing:
        return
    db.add(Task(
        case_id=draft.case_id,
        source_event_id=draft.source_event_id,
        source_draft_id=draft.id,
        title=payload.get("title", draft.title),
        task_type=payload.get("task_type", draft.title),
        source="ai",
        element_key=draft.element_key,
        priority=payload.get("priority", "P2"),
        expected_materials=payload.get("expected_materials", []),
        depends_on=payload.get("depends_on", []),
        blocked_by=[],
        status="pending",
        idempotency_key=idempotency_key,
    ))


def _apply_fact_update(db: Session, draft: Draft, payload: dict, reviewer: str) -> None:
    if draft.element_key:
        element = db.query(Element).filter(Element.case_id == draft.case_id, Element.element_key == draft.element_key).one_or_none()
        if element:
            element.key_fact = payload.get("fact_text", element.key_fact)
    record_fact_update(db, draft.case_id, payload.get("fact_text", draft.title), draft.id, reviewer)


def _apply_material_binding(db: Session, draft: Draft, payload: dict) -> None:
    ingest_material(db, draft.case_id, MaterialCreate(
        title=payload.get("title", draft.title),
        material_type=payload.get("material_type", payload.get("title", draft.title)),
        source="conversation_task_ai",
        file_path=payload.get("file_path"),
        owner=payload.get("owner"),
        supports_elements=payload.get("supports_elements", []),
        extracted_facts=payload.get("extracted_facts", {}),
        idempotency_key=payload.get("idempotency_key", f"draft:{draft.id}:material"),
    ))


def _apply_conflict_review(db: Session, draft: Draft, payload: dict) -> None:
    task_id = _create_conflict_task(db, draft, payload)
    db.flush()
    db.add(Conflict(
        case_id=draft.case_id,
        task_id=task_id,
        source_draft_id=draft.id,
        element_key=payload.get("element_key") or draft.element_key or "tool",
        field=payload.get("field", "action"),
        material_a_id=payload.get("material_a_id"),
        material_b_id=payload.get("material_b_id"),
        value_a=payload.get("value_a"),
        value_b=payload.get("value_b"),
        description=payload.get("description", draft.title),
        suggested_action=payload.get("suggested_action", "复核相关材料矛盾线索"),
        status="open",
    ))


def _create_conflict_task(db: Session, draft: Draft, payload: dict) -> int:
    idempotency_key = payload.get("task_idempotency_key", f"draft:{draft.id}:conflict-task")
    existing = db.query(Task).filter(Task.case_id == draft.case_id, Task.idempotency_key == idempotency_key).one_or_none()
    if existing:
        return existing.id
    task = Task(
        case_id=draft.case_id,
        source_event_id=draft.source_event_id,
        source_draft_id=draft.id,
        title=payload.get("task_title", "复核材料矛盾线索"),
        task_type="矛盾复核",
        source="ai",
        element_key=payload.get("element_key") or draft.element_key or "tool",
        priority="P0",
        expected_materials=payload.get("expected_materials", []),
        depends_on=[],
        blocked_by=[],
        status="pending",
        idempotency_key=idempotency_key,
    )
    db.add(task)
    db.flush()
    return task.id
