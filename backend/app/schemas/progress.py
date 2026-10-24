"""实时进度消息 Schema。"""
from __future__ import annotations

from pydantic import BaseModel


class ProgressMessage(BaseModel):
    stage: str
    shot_index: int | None = None
    status: str
    progress: float = 1.0
    message: str = ""
    output: str | None = None
