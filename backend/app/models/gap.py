from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.base import TimestampMixin


class Gap(Base, TimestampMixin):
    __tablename__ = "gaps"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("cases.id"), index=True)
    task_id: Mapped[int | None] = mapped_column(ForeignKey("tasks.id"), index=True)
    closed_by_material_id: Mapped[int | None] = mapped_column(ForeignKey("materials.id"), index=True)
    element_key: Mapped[str] = mapped_column(String(50), index=True)
    missing_material: Mapped[str] = mapped_column(String(100), index=True)
    reason: Mapped[str | None] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(50), default="rule")
    status: Mapped[str] = mapped_column(String(50), default="open")
