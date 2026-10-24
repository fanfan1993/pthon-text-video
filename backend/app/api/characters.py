"""角色接口：创建（可传参考图）与列表。"""
from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app import models
from app.dependencies import get_db
from app.schemas import CharacterRead
from app.services.character_service import create_character

router = APIRouter(prefix="/projects", tags=["characters"])


@router.post("/{project_id}/characters", response_model=CharacterRead, status_code=201)
async def create(
    project_id: str,
    name: str = Form(...),
    description: str = Form(""),
    need_ai_image: bool = Form(False),
    file: UploadFile | None = File(None),
    db: Session = Depends(get_db),
) -> models.Character:
    """添加角色。

    - 上传 file：作为参考图（有图用图，流水线直接锁定）；
    - 不上传且 need_ai_image=True：流水线先 AI 出一张满意图再锁角色 ID。
    """
    project = db.get(models.Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="项目不存在")

    data = await file.read() if file is not None else None
    return create_character(
        db,
        project_id=project_id,
        name=name,
        description=description,
        image_bytes=data or None,
        filename=file.filename if file is not None else None,
        need_ai_image=need_ai_image,
    )


@router.get("/{project_id}/characters", response_model=list[CharacterRead])
def list_characters(project_id: str, db: Session = Depends(get_db)) -> list[models.Character]:
    return db.query(models.Character).filter_by(project_id=project_id).all()
