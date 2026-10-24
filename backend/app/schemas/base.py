"""Schema 公共基类。"""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class ORMModel(BaseModel):
    """允许从 ORM 对象直接构造（``model_validate(orm_obj)``）。"""

    model_config = ConfigDict(from_attributes=True)


# 历史命名兼容
_ORM = ORMModel
