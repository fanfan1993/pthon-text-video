"""模型层公共基元：主键工厂与时间戳 mixin。"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime
from sqlalchemy.orm import Mapped, mapped_column


def new_uuid() -> str:
    """生成字符串 UUID，便于 JSON 序列化与前端直接使用。"""
    return str(uuid.uuid4())


class CreatedAtMixin:
    """仅需创建时间的表。"""

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class TimestampMixin:
    """需要创建 / 更新时间（onupdate 自动维护）的表。"""

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
