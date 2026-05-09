from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Case, ConversationEvent
from app.schemas.conversation import ConversationEventRead, ConversationMessageCreate
from app.services.conversation_service import ingest_conversation_message

router = APIRouter(prefix="/api/cases/{case_id}/conversations", tags=["conversations"])


@router.post("/messages", response_model=ConversationEventRead)
def ingest_message(case_id: int, payload: ConversationMessageCreate, db: Session = Depends(get_db)) -> ConversationEvent:
    if not db.get(Case, case_id):
        raise HTTPException(status_code=404, detail="Case not found")
    return ingest_conversation_message(db, case_id, payload)


@router.get("/events", response_model=list[ConversationEventRead])
def list_events(case_id: int, db: Session = Depends(get_db)) -> list[ConversationEvent]:
    if not db.get(Case, case_id):
        raise HTTPException(status_code=404, detail="Case not found")
    return db.query(ConversationEvent).filter(ConversationEvent.case_id == case_id).order_by(ConversationEvent.id).all()
