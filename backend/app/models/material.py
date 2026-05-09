from sqlalchemy import JSON, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin


class Material(Base, TimestampMixin):
    __tablename__ = "materials"
    __table_args__ = (UniqueConstraint("case_id", "idempotency_key", name="uq_material_case_idempotency"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("cases.id"), index=True)
    source_task_id: Mapped[int | None] = mapped_column(ForeignKey("tasks.id"), index=True)
    source_event_id: Mapped[int | None] = mapped_column(ForeignKey("conversation_events.id"), index=True)
    title: Mapped[str] = mapped_column(String(255), index=True)
    material_type: Mapped[str] = mapped_column(String(100), index=True)
    source: Mapped[str | None] = mapped_column(String(100))
    file_path: Mapped[str | None] = mapped_column(Text)
    owner: Mapped[str | None] = mapped_column(String(100))
    supports_elements: Mapped[list[str]] = mapped_column(JSON, default=list)
    extracted_facts: Mapped[dict] = mapped_column(JSON, default=dict)
    fact_status: Mapped[str] = mapped_column(String(50), default="pending")
    confirmed_by: Mapped[str | None] = mapped_column(String(100))
    confirmed_at: Mapped[str | None] = mapped_column(String(50))
    idempotency_key: Mapped[str] = mapped_column(String(128))

    case: Mapped["Case"] = relationship(back_populates="materials")
