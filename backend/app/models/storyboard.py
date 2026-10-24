"""分镜表：一镜 = 场景 + 机位 + 对白 + 三个资产外键。"""
from __future__ import annotations

from sqlalchemy import JSON, Enum as SAEnum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.enums import CameraMovement, ShotStatus
from app.database import Base
from app.models.base import new_uuid


class Storyboard(Base):
    __tablename__ = "storyboards"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))
    index: Mapped[int] = mapped_column(Integer, default=0)
    scene_description: Mapped[str] = mapped_column(Text, default="")
    shot_type: Mapped[str] = mapped_column(String(32), default="medium")
    camera_movement: Mapped[CameraMovement] = mapped_column(
        SAEnum(CameraMovement), default=CameraMovement.ken_burns
    )
    character_ids: Mapped[list] = mapped_column(JSON, default=list)  # 本镜出现的角色 id
    dialogue: Mapped[str] = mapped_column(Text, default="")
    speaker_character_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    image_prompt: Mapped[str] = mapped_column(Text, default="")
    duration: Mapped[float] = mapped_column(Float, default=15.0)
    status: Mapped[ShotStatus] = mapped_column(SAEnum(ShotStatus), default=ShotStatus.pending)

    keyframe_asset_id: Mapped[str | None] = mapped_column(String(36), nullable=True)  # 关键帧图
    video_asset_id: Mapped[str | None] = mapped_column(String(36), nullable=True)  # I2V 视频
    audio_asset_id: Mapped[str | None] = mapped_column(String(36), nullable=True)  # 配音

    project: Mapped["Project"] = relationship(back_populates="storyboards")  # noqa: F821
