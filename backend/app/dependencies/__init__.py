"""依赖注入层：统一提供 FastAPI 依赖，便于测试时替换。"""
from app.dependencies.db import get_db

__all__ = ["get_db"]
