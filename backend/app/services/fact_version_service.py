from hashlib import sha256

from sqlalchemy.orm import Session

from app.models import Case, Element, FactVersion


def calculate_fact_version_trigger(db: Session, case_id: int) -> str:
    elements = db.query(Element).filter(Element.case_id == case_id).order_by(Element.element_key).all()
    basis = "|".join(
        f"{element.element_key}:{element.status}:{element.key_fact or ''}:{element.material_count}:{element.gap_count}:{element.conflict_count}"
        for element in elements
    )
    return sha256(basis.encode("utf-8")).hexdigest()


def update_case_fact_trigger(db: Session, case_id: int) -> str:
    trigger = calculate_fact_version_trigger(db, case_id)
    case = db.get(Case, case_id)
    if case and case.fact_version_trigger != trigger:
        case.fact_version_trigger = trigger
    return trigger


def record_fact_update(db: Session, case_id: int, fact_text: str, source_draft_id: int | None, reviewer: str | None) -> FactVersion:
    trigger = calculate_fact_version_trigger(db, case_id)
    existing = db.query(FactVersion).filter(FactVersion.case_id == case_id, FactVersion.trigger_hash == trigger).one_or_none()
    if existing:
        return existing
    case = db.get(Case, case_id)
    if not case:
        raise ValueError("Case not found")
    current_number = int(case.fact_version.lstrip("v") or "1") if case.fact_version.startswith("v") else 1
    version = f"v{current_number + 1}"
    fact_version = FactVersion(
        case_id=case_id,
        version=version,
        fact_summary=fact_text,
        changes_from_previous="confirmed fact update",
        trigger_hash=trigger,
        source_draft_id=source_draft_id,
        confirmed_by=reviewer,
        facts_snapshot={"fact_text": fact_text},
    )
    case.fact_version = version
    case.fact_summary = fact_text
    case.fact_version_trigger = trigger
    db.add(fact_version)
    return fact_version
