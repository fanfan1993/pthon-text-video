"""Celery 应用与流水线派发。

- CELERY_ENABLED=True：用 Redis broker 异步派发（适合多 worker / 生产）。
- CELERY_ENABLED=False（本地默认）：API 路由改用 FastAPI BackgroundTasks 直接跑，
  无需 Redis 也能运行整条流水线。

run_pipeline 是 async 函数，Celery 任务内用 asyncio.run 驱动。
"""
from __future__ import annotations

import asyncio

from celery import Celery

from app.config import get_settings
from app.services.project_service import run_pipeline

settings = get_settings()

celery_app = Celery(
    "textvideo",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)
celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_track_started=True,
)


@celery_app.task(name="run_project_pipeline", bind=True, max_retries=2)
def run_project_pipeline(
    self,
    project_id: str,
    provider: str | None = None,
    tts_engine: str | None = None,
    do_i2v: bool = False,
    camera: str = "ken_burns",
) -> None:
    """Celery 包装：驱动编排层。失败自动重试（指数退避）。"""
    try:
        asyncio.run(
            run_pipeline(
                project_id,
                provider=provider,
                tts_engine=tts_engine,
                do_i2v=do_i2v,
                camera=camera,
            )
        )
    except Exception as exc:  # noqa: BLE001
        raise self.retry(exc=exc, countdown=10)


def launch_pipeline(
    project_id: str,
    *,
    provider: str | None = None,
    tts_engine: str | None = None,
    do_i2v: bool = False,
    camera: str = "ken_burns",
) -> None:
    """根据配置派发流水线：Celery 或本地后台执行。"""
    if settings.CELERY_ENABLED:
        run_project_pipeline.delay(
            project_id, provider, tts_engine, do_i2v, camera
        )
    else:
        # 本地：直接同步执行（调用方应在 BackgroundTasks 中运行，避免阻塞请求）
        asyncio.run(
            run_pipeline(
                project_id,
                provider=provider,
                tts_engine=tts_engine,
                do_i2v=do_i2v,
                camera=camera,
            )
        )
