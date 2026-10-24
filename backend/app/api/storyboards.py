"""分镜接口。"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import models
from app.dependencies import get_db
from app.schemas import StoryboardRead

router = APIRouter(prefix="/projects", tags=["storyboards"])


@router.get("/{project_id}/storyboards", response_model=list[StoryboardRead])
def list_storyboards(project_id: str, db: Session = Depends(get_db)) -> list[Any]:
    """按镜号返回该项目的全部分镜。"""
    return (
        db.query(models.Storyboard)
        .filter_by(project_id=project_id)
        .order_by(models.Storyboard.index)
        .all()
    )
