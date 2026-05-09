from pydantic import BaseModel, ConfigDict


class MaterialCreate(BaseModel):
    title: str
    material_type: str
    source: str | None = None
    file_path: str | None = None
    owner: str | None = None
    supports_elements: list[str] = []
    extracted_facts: dict = {}
    idempotency_key: str | None = None


class MaterialRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    case_id: int
    title: str
    material_type: str
    source: str | None = None
    file_path: str | None = None
    owner: str | None = None
    supports_elements: list[str]
    extracted_facts: dict
    fact_status: str
