"""角色相关 Schema。"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from app.schemas.base import ORMModel


class CharacterCreate(BaseModel):
    name: str
    description: str = ""
    need_ai_image: bool = False  # True=无参考图，由流水线 AI 出图并锁角色


class CharacterRead(ORMModel):
    id: str
    project_id: str
    name: str
    description: str
    reference_images: list[Any] = Field(default_factory=list)
    cloud_lock_type: str
    cloud_lock_id: str | None
    need_ai_image: bool
