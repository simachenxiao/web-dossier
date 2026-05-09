from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin


class Element(Base, TimestampMixin):
    __tablename__ = "elements"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("cases.id"), index=True)
    element_key: Mapped[str] = mapped_column(String(50), index=True)
    name: Mapped[str] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(50), default="unknown")
    key_fact: Mapped[str | None] = mapped_column(Text)
    material_count: Mapped[int] = mapped_column(default=0)
    gap_count: Mapped[int] = mapped_column(default=0)
    conflict_count: Mapped[int] = mapped_column(default=0)

    case: Mapped["Case"] = relationship(back_populates="elements")
