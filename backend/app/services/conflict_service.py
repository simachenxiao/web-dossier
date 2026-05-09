from itertools import combinations

from sqlalchemy.orm import Session

from app.models import ConflictCheck, Material

STATEMENT_TYPES = ("询问笔录", "自书材料", "证人证言")
CONFLICT_FIELDS = ("time", "action", "consequence", "circumstance")


def create_conflict_check_candidates(db: Session, case_id: int) -> int:
    created = 0
    materials = db.query(Material).filter(Material.case_id == case_id, Material.fact_status == "confirmed").all()
    for element_key in _statement_elements(materials):
        statements = [
            material for material in materials
            if _is_statement(material) and element_key in material.supports_elements
        ]
        for material_a, material_b in combinations(statements, 2):
            for field in _shared_fact_fields(material_a, material_b):
                existing = db.query(ConflictCheck).filter(
                    ConflictCheck.case_id == case_id,
                    ConflictCheck.material_a_id == min(material_a.id, material_b.id),
                    ConflictCheck.material_b_id == max(material_a.id, material_b.id),
                    ConflictCheck.element_key == element_key,
                    ConflictCheck.field == field,
                ).one_or_none()
                if existing:
                    continue
                db.add(ConflictCheck(
                    case_id=case_id,
                    material_a_id=min(material_a.id, material_b.id),
                    material_b_id=max(material_a.id, material_b.id),
                    element_key=element_key,
                    field=field,
                    result="pending_ai",
                ))
                created += 1
    return created


def _is_statement(material: Material) -> bool:
    return any(statement_type in material.material_type for statement_type in STATEMENT_TYPES)


def _statement_elements(materials: list[Material]) -> set[str]:
    return {
        element_key
        for material in materials
        if _is_statement(material)
        for element_key in material.supports_elements
    }


def _shared_fact_fields(material_a: Material, material_b: Material) -> list[str]:
    fields = set(material_a.extracted_facts.keys()) & set(material_b.extracted_facts.keys())
    return [field for field in CONFLICT_FIELDS if field in fields] or ["action"]
