"""数据库引擎与会话管理（SQLAlchemy 2.0）。

- SQLite 用于个人版（设计稿 1 明确：个人用 SQLite 代替 PostgreSQL）。
- ``check_same_thread=False`` 允许 FastAPI 的线程池访问（开发便捷，生产建议换 PostgreSQL）。
"""
from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import get_settings

settings = get_settings()

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False},
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    """所有 ORM 模型的基类。"""


def init_db() -> None:
    """建表（幂等）。在应用 lifespan 启动时调用一次。"""
    # 延迟导入，避免循环依赖
    from app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
