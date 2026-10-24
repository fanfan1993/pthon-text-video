"""独立出图相关 Schema：任务、以及「出图 → 角色 / 视频项目」联动请求。"""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.base import ORMModel
from app.schemas.character import CharacterRead


class ImageJobRead(ORMModel):
    id: str
    prompt: str
    negative_prompt: str
    resolution: str
    count: int
    provider: str
    status: str
    result_paths: list[str] = Field(default_factory=list)
    ref_paths: list[str] = Field(default_factory=list)
    error_msg: str | None
    created_at: datetime


class SaveAsCharacterRequest(BaseModel):
    """把某张出图结果落成「角色设定」，并可选喂进视频流水线。"""

    image_index: int = 0  # 用任务里的第几张（0-based）
    # 目标项目：传 project_id 复用；都不传则用 project_title 新建
    project_id: str | None = None
    project_title: str | None = None
    project_input: str | None = None  # 新建项目时的文案（生成视频必需）
    # 角色信息
    name: str = "角色"
    description: str = ""  # 留空则用出图提示词
    lock_role: bool = True  # 立即锁定云角色 ID（用同一张图做锚点）
    # 随后立即生成视频
    start_pipeline: bool = False
    provider: str | None = None
    camera: str = "ken_burns"
    do_i2v: bool = False


class SaveAsCharacterResult(BaseModel):
    project_id: str
    project_title: str
    character: CharacterRead
    image_path: str  # 落进项目的图片相对路径
    locked: bool  # 是否已写入 cloud_lock_id
    pipeline_queued: bool
    created_project: bool
