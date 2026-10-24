"""独立出图任务表：文本 / 参考图 → 一组图（不依赖视频流水线）。"""
from __future__ import annotations

from sqlalchemy import JSON, Enum as SAEnum, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.common.enums import ImageJobStatus
from app.database import Base
from app.models.base import CreatedAtMixin, new_uuid


class ImageJob(CreatedAtMixin, Base):
    __tablename__ = "image_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    prompt: Mapped[str] = mapped_column(Text, default="")
    negative_prompt: Mapped[str] = mapped_column(Text, default="")
    resolution: Mapped[str] = mapped_column(String(32), default="2K")  # 1K/1.5K/2K 或像素
    count: Mapped[int] = mapped_column(Integer, default=1)
    provider: Mapped[str] = mapped_column(String(32), default="")  # 空=用默认 provider
    status: Mapped[ImageJobStatus] = mapped_column(
        SAEnum(ImageJobStatus), default=ImageJobStatus.pending
    )
    result_paths: Mapped[list] = mapped_column(JSON, default=list)  # 生成图相对路径
    ref_paths: Mapped[list] = mapped_column(JSON, default=list)  # 参考图相对路径
    error_msg: Mapped[str | None] = mapped_column(Text, nullable=True)
