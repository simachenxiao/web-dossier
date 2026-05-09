from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Draft
from app.schemas.confirmation import DraftDecision
from app.schemas.draft import DraftRead
from app.services.confirmation_service import confirm_draft as confirm_draft_service
from app.services.confirmation_service import reject_draft as reject_draft_service

router = APIRouter(tags=["drafts"])


@router.get("/api/cases/{case_id}/drafts", response_model=list[DraftRead])
def list_drafts(case_id: int, db: Session = Depends(get_db)) -> list[Draft]:
    return db.query(Draft).filter(Draft.case_id == case_id).order_by(Draft.id).all()


@router.post("/api/drafts/{draft_id}/confirm", response_model=DraftRead)
def confirm_draft(draft_id: int, payload: DraftDecision, db: Session = Depends(get_db)) -> Draft:
    return confirm_draft_service(db, draft_id, payload)


@router.post("/api/drafts/{draft_id}/reject", response_model=DraftRead)
def reject_draft(draft_id: int, payload: DraftDecision, db: Session = Depends(get_db)) -> Draft:
    return reject_draft_service(db, draft_id, payload)
