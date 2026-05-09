from sqlalchemy import JSON, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.base import TimestampMixin


class TaskExecutionResult(Base, TimestampMixin):
    __tablename__ = "task_execution_results"
    __table_args__ = (UniqueConstraint("task_id", "idempotency_key", name="uq_task_result_idempotency"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("cases.id"), index=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id"), index=True)
    result_type: Mapped[str] = mapped_column(String(50), index=True)
    status: Mapped[str] = mapped_column(String(50), default="received")
    executor_type: Mapped[str | None] = mapped_column(String(50))
    executor_name: Mapped[str | None] = mapped_column(String(100))
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    generated_material_ids: Mapped[list[int]] = mapped_column(JSON, default=list)
    generated_event_id: Mapped[int | None] = mapped_column(ForeignKey("conversation_events.id"), index=True)
    error_message: Mapped[str | None] = mapped_column(Text)
    idempotency_key: Mapped[str] = mapped_column(String(128))
