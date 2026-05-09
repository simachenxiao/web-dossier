from pydantic import BaseModel


class DraftDecision(BaseModel):
    reviewer: str
    reason: str | None = None
    payload: dict | None = None
