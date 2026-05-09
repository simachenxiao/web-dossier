from sqlalchemy import JSON, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.base import TimestampMixin


class Draft(Base, TimestampMixin):
    __tablename__ = "drafts"
    __table_args__ = (UniqueConstraint("case_id", "idempotency_key", name="uq_draft_case_idempotency"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("cases.id"), index=True)
    source_event_id: Mapped[int] = mapped_column(ForeignKey("conversation_events.id"), index=True)
    draft_type: Mapped[str] = mapped_column(String(50), index=True)
    title: Mapped[str] = mapped_column(String(255))
    element_key: Mapped[str | None] = mapped_column(String(50), index=True)
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(50), default="pending_confirmation")
    generated_by: Mapped[str] = mapped_column(String(100), default="conversation_task_ai")
    reviewer: Mapped[str | None] = mapped_column(String(100))
    reviewed_at: Mapped[str | None] = mapped_column(String(50))
    review_reason: Mapped[str | None] = mapped_column(Text)
    idempotency_key: Mapped[str] = mapped_column(String(128))
