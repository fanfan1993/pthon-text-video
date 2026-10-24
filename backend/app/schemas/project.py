"""项目相关 Schema。"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.schemas.base import ORMModel


class ProjectCreate(BaseModel):
    title: str = "未命名项目"
    source_type: str = "novel"
    raw_input: str = ""
    style_preset: str = "anime"
    aspect_ratio: str = "16:9"
    target_duration: float = 15.0
    settings_json: dict[str, Any] = Field(default_factory=dict)


class ProjectRead(ORMModel):
    id: str
    title: str
    source_type: str
    status: str
    target_duration: float
    aspect_ratio: str
    style_preset: str
    created_at: datetime


class GenerateRequest(BaseModel):
    """触发流水线的可选覆盖项。"""

    provider: str | None = None  # 覆盖默认出图 provider
    tts_engine: str | None = None  # 覆盖默认 TTS
    do_i2v: bool = False  # True=图生视频；False=FFmpeg 镜头运动
    camera: str = "ken_burns"  # ken_burns | pan | parallax | none
