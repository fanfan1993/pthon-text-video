"""项目表：一个项目 = 一条小说/图文 → 一条成片。"""
from __future__ import annotations

from sqlalchemy import JSON, Enum as SAEnum, Float, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.enums import ProjectStatus, SourceType
from app.database import Base
from app.models.base import TimestampMixin, new_uuid


class Project(TimestampMixin, Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    title: Mapped[str] = mapped_column(String(255), default="未命名项目")
    source_type: Mapped[SourceType] = mapped_column(
        SAEnum(SourceType), default=SourceType.novel
    )
    raw_input: Mapped[str] = mapped_column(Text, default="")
    style_preset: Mapped[str] = mapped_column(String(64), default="anime")
    aspect_ratio: Mapped[str] = mapped_column(String(16), default="16:9")
    target_duration: Mapped[float] = mapped_column(Float, default=15.0)
    status: Mapped[ProjectStatus] = mapped_column(
        SAEnum(ProjectStatus), default=ProjectStatus.draft
    )
    settings_json: Mapped[dict] = mapped_column(JSON, default=dict)

    # 关系用字符串引用，类由 app.models.__init__ 统一导入后完成 mapper 绑定
    characters: Mapped[list["Character"]] = relationship(back_populates="project")  # noqa: F821
    storyboards: Mapped[list["Storyboard"]] = relationship(back_populates="project")  # noqa: F821
    assets: Mapped[list["Asset"]] = relationship(back_populates="project")  # noqa: F821
    tasks: Mapped[list["Task"]] = relationship(back_populates="project")  # noqa: F821
