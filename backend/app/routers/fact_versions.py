from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Case, FactVersion
from app.schemas.fact_version import FactVersionRead

router = APIRouter(prefix="/api/cases/{case_id}/fact-versions", tags=["fact-versions"])


@router.get("", response_model=list[FactVersionRead])
def list_fact_versions(case_id: int, db: Session = Depends(get_db)) -> list[FactVersion]:
    if not db.get(Case, case_id):
        raise HTTPException(status_code=404, detail="Case not found")
    return db.query(FactVersion).filter(FactVersion.case_id == case_id).order_by(FactVersion.id).all()
