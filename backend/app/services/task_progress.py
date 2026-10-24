"""阶段任务状态与进度推送（供 Coordinator 与各 Agent 复用）。

从 ``project_service`` 抽离，避免 Coordinator 与 ``project_service`` 形成循环依赖。
"""
from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from app import models
from app.common.constants import ASPECT_TO_RESOLUTION
from app.common.realtime import publish
from app.schemas import ProgressMessage, TaskStage, TaskStatus

logger = logging.getLogger(__name__)


def resolution_for(aspect_ratio: str) -> str:
    """根据画幅返回分辨率。"""
    return ASPECT_TO_RESOLUTION.get((aspect_ratio or "").strip(), "1920x1080")


def _shot_index_of(shot_id) -> int | None:
    try:
        return int(str(shot_id)[-4:], 16)
    except Exception:  # noqa: BLE001
        return None


async def set_task(
    db: Session,
    project_id: str,
    shot_id: str | None,
    stage: TaskStage,
    status: TaskStatus,
    *,
    msg: str = "",
    external_job_id: str | None = None,
) -> None:
    """创建/更新某阶段的任务记录，并推送进度。"""
    task = (
        db.query(models.Task)
        .filter_by(project_id=project_id, shot_id=shot_id, stage=stage)
        .first()
    )
    if task is None:
        task = models.Task(project_id=project_id, shot_id=shot_id, stage=stage)
        db.add(task)
    task.status = status
    if external_job_id:
        task.external_job_id = external_job_id
    if status == TaskStatus.failed:
        task.error_msg = msg
    db.commit()

    await publish(
        project_id,
        ProgressMessage(
            stage=stage.value,
            shot_index=_shot_index_of(shot_id),
            status=status.value,
            progress=1.0 if status in (TaskStatus.success, TaskStatus.failed) else 0.5,
            message=msg,
        ),
    )
