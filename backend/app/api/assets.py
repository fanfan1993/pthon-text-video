"""资产接口：项目下已生成的图片 / 视频 / 音频索引。"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import models
from app.dependencies import get_db
from app.schemas import AssetRead

router = APIRouter(prefix="/projects", tags=["assets"])


@router.get("/{project_id}/assets", response_model=list[AssetRead])
def list_assets(project_id: str, db: Session = Depends(get_db)) -> list[Any]:
    return db.query(models.Asset).filter_by(project_id=project_id).all()
