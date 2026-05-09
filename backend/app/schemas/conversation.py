from pydantic import BaseModel, ConfigDict


class ConversationMessageCreate(BaseModel):
    source_role: str
    original_text: str
    source_name: str | None = None
    related_task_id: int | None = None
    related_material_id: int | None = None
    idempotency_key: str | None = None


class ConversationEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    case_id: int
    source_role: str
    source_name: str | None = None
    event_type: str
    original_text: str
    normalized_text: str
    related_person: str | None = None
    related_material_title: str | None = None
    related_task_id: int | None = None
    related_material_id: int | None = None
    metadata_json: dict
    confidence: str | None = None
