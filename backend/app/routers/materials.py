from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Case, Material
from app.schemas.material import MaterialCreate, MaterialRead
from app.services.material_service import ingest_material
from app.services.task_driver_service import unblock_ready_tasks

router = APIRouter(prefix="/api/cases/{case_id}/materials", tags=["materials"])


@router.get("", response_model=list[MaterialRead])
def list_materials(case_id: int, db: Session = Depends(get_db)) -> list[Material]:
    if not db.get(Case, case_id):
        raise HTTPException(status_code=404, detail="Case not found")
    return db.query(Material).filter(Material.case_id == case_id).order_by(Material.id).all()


@router.post("", response_model=MaterialRead)
def create_material(case_id: int, payload: MaterialCreate, db: Session = Depends(get_db)) -> Material:
    if not db.get(Case, case_id):
        raise HTTPException(status_code=404, detail="Case not found")
    material = ingest_material(db, case_id, payload)
    unblock_ready_tasks(db, case_id)
    db.commit()
    db.refresh(material)
    return material
