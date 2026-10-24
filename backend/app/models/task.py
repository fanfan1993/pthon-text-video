"""任务表：记录每个项目 / 每个镜头在某个阶段的执行状态。"""
from __future__ import annotations

from sqlalchemy import Enum as SAEnum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.enums import TaskStage, TaskStatus
from app.database import Base
from app.models.base import TimestampMixin, new_uuid


class Task(TimestampMixin, Base):
    __tablename__ = "tasks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))
    shot_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    stage: Mapped[TaskStage] = mapped_column(SAEnum(TaskStage))
    status: Mapped[TaskStatus] = mapped_column(
        SAEnum(TaskStatus), default=TaskStatus.pending
    )
    external_job_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    error_msg: Mapped[str | None] = mapped_column(Text, nullable=True)

    project: Mapped["Project"] = relationship(back_populates="tasks")  # noqa: F821
