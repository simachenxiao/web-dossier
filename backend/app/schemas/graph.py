from pydantic import BaseModel, ConfigDict


class ElementRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    element_key: str
    name: str
    status: str
    key_fact: str | None = None
    material_count: int
    gap_count: int
    conflict_count: int


class GraphRead(BaseModel):
    case_id: int
    elements: list[ElementRead]
