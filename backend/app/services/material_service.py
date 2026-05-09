from hashlib import sha256

from sqlalchemy.orm import Session

from app.models import Material
from app.rules.material_element_mapping import resolve_material_elements
from app.schemas.material import MaterialCreate
from app.services.graph_engine_service import close_matching_gaps, recalculate_elements
from app.services.fact_version_service import update_case_fact_trigger


def ingest_material(db: Session, case_id: int, payload: MaterialCreate) -> Material:
    key = payload.idempotency_key or sha256(f"material:{case_id}:{payload.title}:{payload.material_type}".encode("utf-8")).hexdigest()
    existing = db.query(Material).filter(Material.case_id == case_id, Material.idempotency_key == key).one_or_none()
    if existing:
        return existing
    material = Material(
        case_id=case_id,
        title=payload.title,
        material_type=payload.material_type,
        source=payload.source,
        file_path=payload.file_path,
        owner=payload.owner,
        supports_elements=resolve_material_elements(payload.material_type, payload.owner, payload.supports_elements),
        extracted_facts=payload.extracted_facts,
        idempotency_key=key,
    )
    db.add(material)
    db.flush()
    close_matching_gaps(db, case_id)
    recalculate_elements(db, case_id)
    update_case_fact_trigger(db, case_id)
    db.commit()
    db.refresh(material)
    return material
