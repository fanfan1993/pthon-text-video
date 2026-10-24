"""项目接口：CRUD 与流水线触发。"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app import models
from app.config import get_settings
from app.dependencies import get_db
from app.schemas import GenerateRequest, ProjectCreate, ProjectRead
from app.services.project_service import run_pipeline
from app.utils.files import project_dir

settings = get_settings()
router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("", response_model=list[ProjectRead])
def list_projects(db: Session = Depends(get_db)) -> list[Any]:
    """项目列表（按创建时间倒序，供前端仪表盘使用）。"""
    return db.query(models.Project).order_by(models.Project.created_at.desc()).all()


@router.post("", response_model=ProjectRead, status_code=201)
def create_project(payload: ProjectCreate, db: Session = Depends(get_db)) -> models.Project:
    """创建项目（提交小说/图文 + 风格/时长）。"""
    project = models.Project(**payload.model_dump())
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@router.get("/{project_id}", response_model=ProjectRead)
def get_project(project_id: str, db: Session = Depends(get_db)) -> models.Project:
    project = db.get(models.Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="项目不存在")
    return project


@router.delete("/{project_id}")
def delete_project(project_id: str, db: Session = Depends(get_db)) -> dict:
    """删除项目及其子记录（资产文件保留在磁盘，便于误删排查）。"""
    project = db.get(models.Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="项目不存在")
    for model in (models.Asset, models.Task, models.Storyboard, models.Character):
        db.query(model).filter_by(project_id=project_id).delete()
    db.delete(project)
    db.commit()
    return {"project_id": project_id, "deleted": True}


@router.post("/{project_id}/generate", status_code=202)
def generate(
    project_id: str,
    payload: GenerateRequest,
    background: BackgroundTasks,
    db: Session = Depends(get_db),
) -> dict:
    """触发 MVP 生成流水线（分镜→出图→镜头→配音→合成）。

    - CELERY_ENABLED=True：通过 Celery 异步派发（需 Redis）。
    - 否则：用 FastAPI BackgroundTasks 在后台跑，请求立即返回。
    """
    project = db.get(models.Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="项目不存在")
    if not (project.raw_input or "").strip():
        raise HTTPException(status_code=400, detail="项目文案为空，无法生成分镜")

    opts = dict(
        provider=payload.provider,
        tts_engine=payload.tts_engine,
        do_i2v=payload.do_i2v,
        camera=payload.camera,
    )
    if settings.CELERY_ENABLED:
        from app.celery_app import launch_pipeline

        launch_pipeline(project_id, **opts)
    else:
        background.add_task(run_pipeline, project_id, **opts)

    return {"project_id": project_id, "status": "queued", "opts": opts}


@router.get("/{project_id}/agent-log")
def agent_log(project_id: str) -> JSONResponse:
    """回看本次生成里「多 Agent 协作」的消息记录（编剧/角色设计师/分镜师/导演/视觉审校）。"""
    import json

    path = project_dir(project_id) / "agent_transcript.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail="暂无 Agent 协作记录，请先运行一次生成")
    return JSONResponse(content=json.loads(path.read_text(encoding="utf-8")))
