from pydantic import BaseModel, ConfigDict


class FactVersionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    case_id: int
    version: str
    fact_summary: str
    changes_from_previous: str | None = None
    trigger_hash: str
    confirmed_by: str | None = None
    facts_snapshot: dict
