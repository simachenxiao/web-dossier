from sqlalchemy import JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin


class Case(Base, TimestampMixin):
    __tablename__ = "cases"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    case_no: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    case_name: Mapped[str] = mapped_column(String(255))
    case_type: Mapped[str] = mapped_column(String(100))
    stage: Mapped[str] = mapped_column(String(50), default="filing")
    fact_version: Mapped[str] = mapped_column(String(20), default="v1")
    fact_version_trigger: Mapped[str | None] = mapped_column(String(128), unique=False)
    fact_summary: Mapped[str | None] = mapped_column(Text)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)

    elements: Mapped[list["Element"]] = relationship(back_populates="case", cascade="all, delete-orphan")
    materials: Mapped[list["Material"]] = relationship(back_populates="case", cascade="all, delete-orphan")
    tasks: Mapped[list["Task"]] = relationship(back_populates="case", cascade="all, delete-orphan")
