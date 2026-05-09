from pydantic import BaseModel, ConfigDict


class TaskCreate(BaseModel):
    title: str
    task_type: str
    source: str = "rule"
    element_key: str | None = None
    priority: str = "P2"
    expected_materials: list[str] = []
    depends_on: list[str] = []
    idempotency_key: str | None = None


class TaskRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    case_id: int
    title: str
    task_type: str
    source: str
    element_key: str | None = None
    priority: str
    expected_materials: list[str]
    depends_on: list[str]
    blocked_by: list[str]
    status: str
    assignee_type: str | None = None
    assignee_name: str | None = None
    blocked_reason: str | None = None


class TaskBlock(BaseModel):
    blocked_by: list[str]
    blocked_reason: str | None = None


class TaskComplete(BaseModel):
    result_type: str = "status"
    payload: dict = {}
    idempotency_key: str | None = None
