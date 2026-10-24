"""独立出图接口：文本 / 参考图 → 一组关键帧图，并支持沉淀为角色。

- POST /image-gen                      创建任务（multipart），后台异步出图，立即返回
- GET  /image-gen                      任务历史（倒序）
- GET  /image-gen/{job_id}             任务详情（轮询）
- POST /image-gen/{job_id}/to-character  把某张结果存为角色 / 喂进视频项目
"""
from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app import models
from app.common.constants import IMAGE_JOB_MAX_COUNT
from app.dependencies import get_db
from app.schemas import (
    ImageJobRead,
    SaveAsCharacterRequest,
    SaveAsCharacterResult,
)
from app.services.character_service import save_from_image_job
from app.services.image_service import run_image_job_sync
from app.services.project_service import run_pipeline
from app.utils.files import save_image_job_file

router = APIRouter(prefix="/image-gen", tags=["image-gen"])


@router.post("", response_model=ImageJobRead, status_code=202)
async def create_image_job(
    background: BackgroundTasks,
    prompt: str = Form(..., min_length=1, description="出图提示词"),
    resolution: str = Form("2K"),
    count: int = Form(1),
    provider: str | None = Form(None),
    ref_images: list[UploadFile] | None = File(None),
    db: Session = Depends(get_db),
) -> models.ImageJob:
    """创建出图任务并后台异步执行。

    - resolution：Seedream 5.0 支持 "1K"/"1.5K"/"2K"，或像素值（如 2048x1152）。
    - ref_images：可选参考图（角色设定图）。传入后多张出图会复用参考，保证一致。
    - count：出图张数（1~4）。
    """
    count = max(1, min(int(count or 1), IMAGE_JOB_MAX_COUNT))
    job = models.ImageJob(
        prompt=prompt,
        resolution=resolution,
        count=count,
        provider=provider or "",
        status=models.ImageJobStatus.pending,
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    ref_paths: list[str] = []
    for f in ref_images or []:
        data = await f.read()
        if not data:
            continue
        ext = Path(f.filename or "ref.png").suffix or ".png"
        ref_paths.append(save_image_job_file(job.id, "refs", f"{uuid.uuid4().hex}{ext}", data))
    if ref_paths:
        job.ref_paths = ref_paths
        db.commit()

    background.add_task(run_image_job_sync, job.id)
    return job


@router.get("", response_model=list[ImageJobRead])
def list_image_jobs(db: Session = Depends(get_db)) -> list[models.ImageJob]:
    """出图任务历史（最新在前）。"""
    return db.query(models.ImageJob).order_by(models.ImageJob.created_at.desc()).all()


@router.get("/{job_id}", response_model=ImageJobRead)
def get_image_job(job_id: str, db: Session = Depends(get_db)) -> models.ImageJob:
    job = db.get(models.ImageJob, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="出图任务不存在")
    return job


@router.post("/{job_id}/to-character", response_model=SaveAsCharacterResult, status_code=201)
async def to_character(
    job_id: str,
    payload: SaveAsCharacterRequest,
    background: BackgroundTasks,
    db: Session = Depends(get_db),
) -> SaveAsCharacterResult:
    """把出图结果沉淀为角色设定，并可选立刻生成视频。

    - 不传 project_id：自动新建项目（title/prompt 取请求或出图提示词）；
    - 传 project_id：追加到已有项目，作为该项目的角色；
    - start_pipeline=True：存完角色立刻跑视频流水线（项目需已有文案）。
    """
    job = db.get(models.ImageJob, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="出图任务不存在")

    try:
        char, project, image_path, locked = await save_from_image_job(db, job, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    queued = False
    if payload.start_pipeline:
        opts = dict(
            provider=payload.provider,
            tts_engine=None,
            do_i2v=payload.do_i2v,
            camera=payload.camera,
        )
        background.add_task(run_pipeline, project.id, **opts)
        queued = True

    return SaveAsCharacterResult(
        project_id=project.id,
        project_title=project.title,
        character=char,
        image_path=image_path,
        locked=locked,
        pipeline_queued=queued,
        created_project=not bool(payload.project_id),
    )
