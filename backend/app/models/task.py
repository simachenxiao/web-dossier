from sqlalchemy import JSON, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin


class Task(Base, TimestampMixin):
    __tablename__ = "tasks"
    __table_args__ = (UniqueConstraint("case_id", "idempotency_key", name="uq_task_case_idempotency"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("cases.id"), index=True)
    source_event_id: Mapped[int | None] = mapped_column(ForeignKey("conversation_events.id"), index=True)
    source_draft_id: Mapped[int | None] = mapped_column(ForeignKey("drafts.id"), index=True)
    title: Mapped[str] = mapped_column(String(255))
    task_type: Mapped[str] = mapped_column(String(100), index=True)
    source: Mapped[str] = mapped_column(String(50), default="rule")
    element_key: Mapped[str | None] = mapped_column(String(50), index=True)
    priority: Mapped[str] = mapped_column(String(10), default="P2")
    expected_materials: Mapped[list[str]] = mapped_column(JSON, default=list)
    depends_on: Mapped[list[str]] = mapped_column(JSON, default=list)
    blocked_by: Mapped[list[str]] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String(50), default="pending")
    assignee_type: Mapped[str | None] = mapped_column(String(50))
    assignee_name: Mapped[str | None] = mapped_column(String(100))
    blocked_reason: Mapped[str | None] = mapped_column(Text)
    idempotency_key: Mapped[str] = mapped_column(String(128))

    case: Mapped["Case"] = relationship(back_populates="tasks")
