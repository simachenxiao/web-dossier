from sqlalchemy import JSON, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.base import TimestampMixin


class ConversationEvent(Base, TimestampMixin):
    __tablename__ = "conversation_events"
    __table_args__ = (UniqueConstraint("case_id", "idempotency_key", name="uq_conversation_event_case_idempotency"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("cases.id"), index=True)
    source_role: Mapped[str] = mapped_column(String(50), index=True)
    source_name: Mapped[str | None] = mapped_column(String(100))
    event_type: Mapped[str] = mapped_column(String(50), index=True)
    original_text: Mapped[str] = mapped_column(Text)
    normalized_text: Mapped[str] = mapped_column(Text)
    related_person: Mapped[str | None] = mapped_column(String(100))
    related_material_title: Mapped[str | None] = mapped_column(String(255))
    related_task_id: Mapped[int | None] = mapped_column(ForeignKey("tasks.id"), index=True)
    related_material_id: Mapped[int | None] = mapped_column(ForeignKey("materials.id"), index=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    confidence: Mapped[str | None] = mapped_column(String(50))
    idempotency_key: Mapped[str] = mapped_column(String(128))
