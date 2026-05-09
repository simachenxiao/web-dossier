from sqlalchemy import ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.base import TimestampMixin


class Conflict(Base, TimestampMixin):
    __tablename__ = "conflicts"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("cases.id"), index=True)
    task_id: Mapped[int | None] = mapped_column(ForeignKey("tasks.id"), index=True)
    source_draft_id: Mapped[int | None] = mapped_column(ForeignKey("drafts.id"), index=True)
    element_key: Mapped[str] = mapped_column(String(50), index=True)
    field: Mapped[str] = mapped_column(String(100), index=True)
    material_a_id: Mapped[int | None] = mapped_column(ForeignKey("materials.id"), index=True)
    material_b_id: Mapped[int | None] = mapped_column(ForeignKey("materials.id"), index=True)
    value_a: Mapped[str | None] = mapped_column(Text)
    value_b: Mapped[str | None] = mapped_column(Text)
    description: Mapped[str] = mapped_column(Text)
    suggested_action: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(50), default="open")
    resolution: Mapped[str | None] = mapped_column(Text)


class ConflictCheck(Base, TimestampMixin):
    __tablename__ = "conflict_checks"
    __table_args__ = (UniqueConstraint("case_id", "material_a_id", "material_b_id", "element_key", "field", name="uq_conflict_check_pair"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("cases.id"), index=True)
    material_a_id: Mapped[int] = mapped_column(ForeignKey("materials.id"), index=True)
    material_b_id: Mapped[int] = mapped_column(ForeignKey("materials.id"), index=True)
    conflict_id: Mapped[int | None] = mapped_column(ForeignKey("conflicts.id"), index=True)
    element_key: Mapped[str] = mapped_column(String(50), index=True)
    field: Mapped[str] = mapped_column(String(100), index=True)
    result: Mapped[str] = mapped_column(String(50))
