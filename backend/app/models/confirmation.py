from sqlalchemy import JSON, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.base import TimestampMixin


class ConfirmationDecision(Base, TimestampMixin):
    __tablename__ = "confirmation_decisions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("cases.id"), index=True)
    draft_id: Mapped[int] = mapped_column(ForeignKey("drafts.id"), index=True)
    source_event_id: Mapped[int | None] = mapped_column(ForeignKey("conversation_events.id"), index=True)
    decision: Mapped[str] = mapped_column(String(50), index=True)
    reviewer: Mapped[str] = mapped_column(String(100))
    reason: Mapped[str | None] = mapped_column(Text)
    before_payload: Mapped[dict] = mapped_column(JSON, default=dict)
    after_payload: Mapped[dict] = mapped_column(JSON, default=dict)
