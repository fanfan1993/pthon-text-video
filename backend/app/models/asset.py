"""资产表：图片 / 视频 / 音频的落盘索引（项目级或镜头级）。"""
from __future__ import annotations

from sqlalchemy import JSON, Enum as SAEnum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.enums import AssetSource, AssetType
from app.database import Base
from app.models.base import CreatedAtMixin, new_uuid


class Asset(CreatedAtMixin, Base):
    __tablename__ = "assets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))
    shot_id: Mapped[str | None] = mapped_column(String(36), nullable=True)  # 项目级资产可空
    type: Mapped[AssetType] = mapped_column(SAEnum(AssetType))
    path: Mapped[str] = mapped_column(String(512))  # 相对 MEDIA_ROOT 的路径
    source: Mapped[AssetSource] = mapped_column(
        SAEnum(AssetSource), default=AssetSource.generated
    )
    meta_json: Mapped[dict] = mapped_column(JSON, default=dict)

    project: Mapped["Project"] = relationship(back_populates="assets")  # noqa: F821
