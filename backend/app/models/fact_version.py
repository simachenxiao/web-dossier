from sqlalchemy import JSON, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.base import TimestampMixin


class FactVersion(Base, TimestampMixin):
    __tablename__ = "fact_versions"
    __table_args__ = (UniqueConstraint("case_id", "trigger_hash", name="uq_fact_version_trigger"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("cases.id"), index=True)
    version: Mapped[str] = mapped_column(String(20), index=True)
    fact_summary: Mapped[str] = mapped_column(Text)
    changes_from_previous: Mapped[str | None] = mapped_column(Text)
    trigger_hash: Mapped[str] = mapped_column(String(128), index=True)
    source_draft_id: Mapped[int | None] = mapped_column(ForeignKey("drafts.id"), index=True)
    confirmed_by: Mapped[str | None] = mapped_column(String(100))
    facts_snapshot: Mapped[dict] = mapped_column(JSON, default=dict)
