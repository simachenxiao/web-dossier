from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Case, Element
from app.schemas.case import CaseCreate, CaseRead
from app.schemas.graph import GraphRead
from app.services.graph_engine_service import run_graph_loop

router = APIRouter(prefix="/api/cases", tags=["cases"])

DEFAULT_ELEMENTS = [
    ("time", "时间地点"),
    ("consequence", "后果"),
    ("tool", "工具/手段"),
    ("witness", "证人"),
    ("victim", "受害人"),
    ("suspect", "嫌疑人"),
    ("circumstance", "情节"),
]


@router.post("", response_model=CaseRead)
def create_case(payload: CaseCreate, db: Session = Depends(get_db)) -> Case:
    case = Case(
        case_no=payload.case_no,
        case_name=payload.case_name,
        case_type=payload.case_type,
        stage=payload.stage,
    )
    db.add(case)
    db.flush()
    for key, name in DEFAULT_ELEMENTS:
        db.add(Element(case_id=case.id, element_key=key, name=name))
    db.commit()
    db.refresh(case)
    return case


@router.get("/{case_id}", response_model=CaseRead)
def get_case(case_id: int, db: Session = Depends(get_db)) -> Case:
    case = db.get(Case, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return case


@router.get("/{case_id}/graph", response_model=GraphRead)
def get_graph(case_id: int, db: Session = Depends(get_db)) -> GraphRead:
    if not db.get(Case, case_id):
        raise HTTPException(status_code=404, detail="Case not found")
    elements = db.query(Element).filter(Element.case_id == case_id).all()
    return GraphRead(case_id=case_id, elements=elements)


@router.post("/{case_id}/run-loop")
def run_loop_endpoint(case_id: int, db: Session = Depends(get_db)) -> dict[str, str | int]:
    if not db.get(Case, case_id):
        raise HTTPException(status_code=404, detail="Case not found")
    result = run_graph_loop(db, case_id)
    return {"case_id": case_id, **result}
