"""任务状态接口。"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models
from app.dependencies import get_db
from app.schemas import TaskRead

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("/{task_id}", response_model=TaskRead)
def get_task(task_id: str, db: Session = Depends(get_db)) -> models.Task:
    task = db.get(models.Task, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="任务不存在")
    return task
