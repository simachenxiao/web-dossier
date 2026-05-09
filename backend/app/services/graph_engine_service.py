from sqlalchemy.orm import Session

from app.models import Conflict, Element, Gap, Material, Task
from app.rules.dependencies import dependencies_for
from app.rules.priorities import priority_for
from app.rules.stage_blockers import is_stage_blocker
from app.rules.universal_gaps import UNIVERSAL_REQUIRED
from app.services.conflict_service import create_conflict_check_candidates
from app.services.fact_version_service import update_case_fact_trigger


def run_graph_loop(db: Session, case_id: int) -> dict[str, int | str]:
    gaps_created = generate_universal_gaps(db, case_id)
    gaps_closed = close_matching_gaps(db, case_id)
    elements_updated = recalculate_elements(db, case_id)
    conflict_checks_created = create_conflict_check_candidates(db, case_id)
    trigger = update_case_fact_trigger(db, case_id)
    db.commit()
    return {
        "status": "completed",
        "gaps_created": gaps_created,
        "gaps_closed": gaps_closed,
        "elements_updated": elements_updated,
        "conflict_checks_created": conflict_checks_created,
        "fact_version_trigger": trigger,
    }


def generate_universal_gaps(db: Session, case_id: int) -> int:
    created = 0
    for element_key, required_materials in UNIVERSAL_REQUIRED.items():
        for material_type in required_materials:
            if _material_exists(db, case_id, element_key, material_type):
                continue
            existing_gap = db.query(Gap).filter(
                Gap.case_id == case_id,
                Gap.element_key == element_key,
                Gap.missing_material == material_type,
                Gap.status == "open",
            ).one_or_none()
            if existing_gap:
                continue
            task = _create_gap_task(db, case_id, element_key, material_type)
            db.flush()
            db.add(Gap(
                case_id=case_id,
                task_id=task.id,
                element_key=element_key,
                missing_material=material_type,
                reason="法定必需",
                source="rule",
                status="open",
            ))
            created += 1
    return created


def close_matching_gaps(db: Session, case_id: int) -> int:
    closed = 0
    open_gaps = db.query(Gap).filter(Gap.case_id == case_id, Gap.status == "open").all()
    materials = db.query(Material).filter(Material.case_id == case_id).all()
    for gap in open_gaps:
        for material in materials:
            if gap.element_key not in material.supports_elements:
                continue
            if gap.missing_material not in material.material_type and gap.missing_material not in material.title:
                continue
            gap.status = "closed"
            gap.closed_by_material_id = material.id
            if gap.task_id:
                task = db.get(Task, gap.task_id)
                if task:
                    task.status = "completed"
            closed += 1
            break
    return closed


def recalculate_elements(db: Session, case_id: int) -> int:
    updated = 0
    elements = db.query(Element).filter(Element.case_id == case_id).all()
    materials = db.query(Material).filter(Material.case_id == case_id).all()
    for element in elements:
        material_count = sum(1 for material in materials if element.element_key in material.supports_elements)
        gap_count = db.query(Gap).filter(
            Gap.case_id == case_id,
            Gap.element_key == element.element_key,
            Gap.status == "open",
        ).count()
        conflict_count = db.query(Conflict).filter(
            Conflict.case_id == case_id,
            Conflict.element_key == element.element_key,
            Conflict.status == "open",
        ).count()
        element.material_count = material_count
        element.gap_count = gap_count
        element.conflict_count = conflict_count
        if conflict_count > 0:
            element.status = "conflict"
        elif gap_count > 0:
            element.status = "reinforcing"
        elif material_count > 0:
            element.status = "proved"
        else:
            element.status = "unknown"
        updated += 1
    return updated


def _material_exists(db: Session, case_id: int, element_key: str, material_type: str) -> bool:
    materials = db.query(Material).filter(Material.case_id == case_id).all()
    return any(
        element_key in material.supports_elements
        and (material_type in material.material_type or material_type in material.title)
        for material in materials
    )


def _create_gap_task(db: Session, case_id: int, element_key: str, material_type: str) -> Task:
    task_type = _task_type_for_missing_material(material_type)
    priority = "P0" if is_stage_blocker("filing", task_type) else priority_for(task_type)
    existing_tasks = db.query(Task).filter(
        Task.case_id == case_id,
        Task.element_key == element_key,
        Task.status != "completed",
    ).all()
    for existing in existing_tasks:
        if material_type in existing.expected_materials:
            return existing
    task = Task(
        case_id=case_id,
        title=f"补齐{material_type}",
        task_type=task_type,
        source="rule",
        element_key=element_key,
        priority=priority,
        expected_materials=[material_type],
        depends_on=dependencies_for(task_type),
        blocked_by=[],
        status="pending",
        idempotency_key=f"gap:{case_id}:{element_key}:{material_type}",
    )
    db.add(task)
    return task


def _task_type_for_missing_material(material_type: str) -> str:
    if material_type in ("立案登记表", "立案告知书", "接报审批表"):
        return "立案文书"
    if material_type == "询问笔录":
        return "询问笔录"
    if material_type == "陈述材料":
        return "嫌疑人陈述"
    return material_type
