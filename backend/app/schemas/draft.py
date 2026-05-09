from pydantic import BaseModel, ConfigDict


class DraftRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    case_id: int
    source_event_id: int
    draft_type: str
    title: str
    element_key: str | None = None
    payload: dict
    status: str
    generated_by: str
    reviewer: str | None = None
    review_reason: str | None = None
