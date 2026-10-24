"""角色服务：创建角色、锁定云角色、以及「出图结果 → 角色设定」的沉淀。

核心作用：把一张满意的人物图变成项目里可复用的角色（参考图 + 云端锁定 ID），
后续每一镜都带同一组参考图，从而实现跨镜 / 跨集一致。
"""
from __future__ import annotations

import logging
import uuid
from pathlib import Path

from sqlalchemy.orm import Session

from app import models
from app.common.constants import MEDIA_DIR_IMAGES, PROVIDER_LOCK_TYPE
from app.schemas.image_job import SaveAsCharacterRequest
from app.services.providers import get_provider
from app.utils.files import media_root, save_upload

logger = logging.getLogger(__name__)


def lock_type_for(provider_name: str) -> models.CloudLockType:
    """provider 名 → 云端锁定类型（写入 character.cloud_lock_type 供前端展示）。"""
    return PROVIDER_LOCK_TYPE.get(provider_name, models.CloudLockType.none)


def create_character(
    db: Session,
    *,
    project_id: str,
    name: str,
    description: str = "",
    image_bytes: bytes | None = None,
    filename: str | None = None,
    need_ai_image: bool = False,
) -> models.Character:
    """新建角色；传入图片字节则作为参考图落盘。"""
    reference_images: list[str] = []
    if image_bytes:
        ext = Path(filename or "img.png").suffix or ".png"
        stored = f"{uuid.uuid4().hex}{ext}"
        rel = save_upload(project_id, MEDIA_DIR_IMAGES, stored, image_bytes)
        reference_images.append(rel)

    char = models.Character(
        project_id=project_id,
        name=name or "角色",
        description=description or "",
        need_ai_image=need_ai_image and not reference_images,
        reference_images=reference_images,
    )
    db.add(char)
    db.commit()
    db.refresh(char)
    return char


def _resolve_or_create_project(
    db: Session, req: SaveAsCharacterRequest
) -> tuple[models.Project, bool]:
    """复用已有项目，或按请求新建一个（返回项目与是否新建）。"""
    if req.project_id:
        project = db.get(models.Project, req.project_id)
        if project is None:
            raise ValueError("目标项目不存在")
        return project, False

    title = (req.project_title or "").strip() or "出图转视频"
    project = models.Project(
        title=title[:255],
        raw_input=(req.project_input or "").strip(),
        source_type=models.SourceType.novel,
        style_preset="anime",
        aspect_ratio="16:9",
        target_duration=15.0,
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project, True


async def save_from_image_job(
    db: Session,
    job: models.ImageJob,
    req: SaveAsCharacterRequest,
) -> tuple[models.Character, models.Project, str, bool]:
    """把出图任务里的某张图落成角色设定。

    返回 ``(角色, 项目, 图片相对路径, 是否已锁云角色)``。
    调用方负责在 ``req.start_pipeline`` 时触发流水线。
    """
    # 1) 校验图片来源
    if job.status != models.ImageJobStatus.completed or not job.result_paths:
        raise ValueError("该出图任务还没有可用结果，请等待生成完成")
    idx = max(0, min(int(req.image_index or 0), len(job.result_paths) - 1))
    src_rel = job.result_paths[idx]
    src_path = media_root() / src_rel
    if not src_path.exists():
        raise ValueError(f"图片文件不存在: {src_rel}")

    # 2) 解析目标项目
    project, created = _resolve_or_create_project(db, req)
    if req.start_pipeline and not (project.raw_input or "").strip():
        raise ValueError("该项目还没有文案，无法生成视频：请先填写文案，或选择已有文案的项目")

    # 3) 图片复制进项目目录（项目资产自包含，便于整体迁移/备份）
    data = src_path.read_bytes()
    ext = src_path.suffix or ".png"
    stored = f"ref_{uuid.uuid4().hex[:12]}{ext}"
    image_rel = save_upload(project.id, MEDIA_DIR_IMAGES, stored, data)

    # 4) 创建角色（参考图即锚点）
    description = (req.description or "").strip() or job.prompt
    char = models.Character(
        project_id=project.id,
        name=(req.name or "角色").strip()[:128],
        description=description,
        reference_images=[image_rel],
        need_ai_image=False,
    )
    db.add(char)
    db.commit()
    db.refresh(char)

    # 5) 立即锁定云角色（失败不阻塞：流水线阶段0 会自动重试锁定）
    locked = False
    if req.lock_role:
        provider = get_provider(req.provider)
        try:
            lock_id = await provider.lock_role([(media_root() / image_rel).resolve()], char.name)
            char.cloud_lock_id = lock_id
            char.cloud_lock_type = lock_type_for(getattr(provider, "name", "mock"))
            db.commit()
            db.refresh(char)
            locked = True
        except Exception as exc:  # noqa: BLE001
            logger.warning("角色云锁定失败（流水线会自动重试）: %s", exc)

    return char, project, image_rel, locked
