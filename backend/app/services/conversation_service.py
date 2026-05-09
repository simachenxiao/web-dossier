from hashlib import sha256

from sqlalchemy.orm import Session

from app.ai.conversation_task_ai import ConversationTaskAI
from app.models import ConversationEvent
from app.schemas.conversation import ConversationMessageCreate

conversation_task_ai = ConversationTaskAI()


def ingest_conversation_message(db: Session, case_id: int, payload: ConversationMessageCreate) -> ConversationEvent:
    analysis = conversation_task_ai.analyze(payload.original_text)
    key = payload.idempotency_key or sha256(f"{case_id}:{payload.source_role}:{analysis.normalized_text}".encode("utf-8")).hexdigest()
    existing = db.query(ConversationEvent).filter(
        ConversationEvent.case_id == case_id,
        ConversationEvent.idempotency_key == key,
    ).one_or_none()
    if existing:
        return existing
    event = ConversationEvent(
        case_id=case_id,
        source_role=payload.source_role,
        source_name=payload.source_name,
        event_type=analysis.event_type,
        original_text=payload.original_text,
        normalized_text=analysis.normalized_text,
        related_person=analysis.related_person,
        related_material_title=analysis.related_material_title,
        related_task_id=payload.related_task_id,
        related_material_id=payload.related_material_id,
        metadata_json=analysis.metadata or {},
        confidence="rule",
        idempotency_key=key,
    )
    db.add(event)
    db.flush()
    conversation_task_ai.generate_drafts(db, event)
    db.commit()
    db.refresh(event)
    return event
