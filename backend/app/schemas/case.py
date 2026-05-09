from pydantic import BaseModel, ConfigDict


class CaseCreate(BaseModel):
    case_no: str
    case_name: str
    case_type: str
    stage: str = "filing"


class CaseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    case_no: str
    case_name: str
    case_type: str
    stage: str
    fact_version: str
    fact_summary: str | None = None
