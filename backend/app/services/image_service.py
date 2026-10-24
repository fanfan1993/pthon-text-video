"""独立出图服务：把 ImageJob 跑完（调用 Provider 出图并回写结果）。

与视频流水线解耦，`api/image_gen.py` 只负责收发，具体执行都在这里。
"""
from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from sqlalchemy.orm import Session

from app import models
from app.common.enums import ImageJobStatus
from app.database import SessionLocal
from app.services.providers import get_provider
from app.utils.files import image_job_dir, media_root

logger = logging.getLogger(__name__)


async def run_image_job(job_id: str) -> None:
    """执行出图：更新状态 → 调用 provider → 回写结果路径。"""
    db: Session = SessionLocal()
    try:
        job = db.get(models.ImageJob, job_id)
        if job is None:
            return
        job.status = ImageJobStatus.running
        db.commit()

        provider = get_provider(job.provider or None)
        root = media_root()

        # 参考图：构建角色 token，使多张出图共享同一参考 → 跨图一致
        role_id: str | None = None
        ref_paths = [Path(root / r) for r in (job.ref_paths or []) if r]
        if ref_paths:
            role_id = await provider.lock_role(ref_paths, "ref")

        results: list[str] = []
        for i in range(job.count):
            out_path = image_job_dir(job_id, "images") / f"{i + 1}.png"
            res = await provider.generate_image(
                prompt=job.prompt,
                role_id=role_id,
                resolution=job.resolution,
                out_path=out_path,
            )
            results.append(str(Path(res.path).relative_to(root)))

        job.result_paths = results
        job.status = ImageJobStatus.completed
        db.commit()
    except Exception as exc:  # noqa: BLE001
        logger.exception("出图任务失败: %s", job_id)
        job = db.get(models.ImageJob, job_id)
        if job is not None:
            job.status = ImageJobStatus.failed
            job.error_msg = str(exc)[:1000]
            db.commit()
    finally:
        db.close()


def run_image_job_sync(job_id: str) -> None:
    """供 BackgroundTasks 使用：内部用 asyncio.run 驱动异步出图。"""
    asyncio.run(run_image_job(job_id))
