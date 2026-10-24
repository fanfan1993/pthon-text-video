"""角色表：人设 + 参考图 + 云端锁定 ID（跨镜/跨集一致性的锚点）。"""
from __future__ import annotations

from sqlalchemy import JSON, Enum as SAEnum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.enums import CloudLockType
from app.database import Base
from app.models.base import CreatedAtMixin, new_uuid


class Character(CreatedAtMixin, Base):
    __tablename__ = "characters"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(128))
    description: Mapped[str] = mapped_column(Text, default="")  # 结构化人设提示词
    # 参考图相对 MEDIA_ROOT 的路径数组；有图即锁图，保证跨镜一致
    reference_images: Mapped[list] = mapped_column(JSON, default=list)
    cloud_lock_type: Mapped[CloudLockType] = mapped_column(
        SAEnum(CloudLockType), default=CloudLockType.none
    )
    cloud_lock_id: Mapped[str | None] = mapped_column(String(128), nullable=True)  # RM-XXXXXX / 主体ID
    need_ai_image: Mapped[bool] = mapped_column(default=False)  # 无参考图时需 AI 出图再锁

    project: Mapped["Project"] = relationship(back_populates="characters")  # noqa: F821
