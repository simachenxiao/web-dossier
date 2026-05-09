from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Case, Task
from app.schemas.task import TaskBlock, TaskComplete, TaskRead
from app.services.task_driver_service import complete_task as complete_task_service
from app.services.task_driver_service import start_task as start_task_service

router = APIRouter(tags=["tasks"])


@router.get("/api/cases/{case_id}/tasks", response_model=list[TaskRead])
def list_tasks(case_id: int, db: Session = Depends(get_db)) -> list[Task]:
    if not db.get(Case, case_id):
        raise HTTPException(status_code=404, detail="Case not found")
    return db.query(Task).filter(Task.case_id == case_id).order_by(Task.id).all()


@router.post("/api/tasks/{task_id}/start", response_model=TaskRead)
def start_task(task_id: int, db: Session = Depends(get_db)) -> Task:
    try:
        return start_task_service(db, task_id)
    except ValueError as exc:
        detail = str(exc)
        status_code = 404 if detail == "Task not found" else 409
        raise HTTPException(status_code=status_code, detail=detail) from exc


@router.post("/api/tasks/{task_id}/block", response_model=TaskRead)
def block_task(task_id: int, payload: TaskBlock, db: Session = Depends(get_db)) -> Task:
    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    task.status = "blocked"
    task.blocked_by = payload.blocked_by
    task.blocked_reason = payload.blocked_reason
    db.commit()
    db.refresh(task)
    return task


@router.post("/api/tasks/{task_id}/complete", response_model=TaskRead)
def complete_task(task_id: int, payload: TaskComplete, db: Session = Depends(get_db)) -> Task:
    try:
        return complete_task_service(db, task_id, payload)
    except ValueError as exc:
        detail = str(exc)
        status_code = 404 if detail == "Task not found" else 409
        raise HTTPException(status_code=status_code, detail=detail) from exc
