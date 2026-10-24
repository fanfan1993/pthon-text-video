"""全局配置表（单用户场景始终只有一行）。"""
from __future__ import annotations

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class SettingsRow(Base):
    __tablename__ = "settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    provider: Mapped[str] = mapped_column(String(32), default="mock")
    api_key_encrypted: Mapped[str | None] = mapped_column(String(512), nullable=True)
    default_tts: Mapped[str] = mapped_column(String(32), default="edge")
    storage_path: Mapped[str] = mapped_column(String(512), default="./media")
