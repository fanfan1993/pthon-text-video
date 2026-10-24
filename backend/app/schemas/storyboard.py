"""分镜 / 资产 / 任务相关 Schema。"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import Field

from app.schemas.base import ORMModel


class StoryboardRead(ORMModel):
    id: str
    project_id: str
    index: int
    scene_description: str
    shot_type: str
    camera_movement: str
    character_ids: list[Any] = Field(default_factory=list)
    dialogue: str
    speaker_character_id: str | None
    image_prompt: str
    duration: float
    status: str
    keyframe_asset_id: str | None
    video_asset_id: str | None
    audio_asset_id: str | None


class AssetRead(ORMModel):
    id: str
    project_id: str
    shot_id: str | None
    type: str
    path: str
    source: str
    meta_json: dict[str, Any] = Field(default_factory=dict)


class TaskRead(ORMModel):
    id: str
    project_id: str
    shot_id: str | None
    stage: str
    status: str
    external_job_id: str | None
    retry_count: int
    error_msg: str | None
    updated_at: datetime
