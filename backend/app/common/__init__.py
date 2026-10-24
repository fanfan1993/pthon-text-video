"""公共层：跨模块复用的枚举、常量与实时通道。

不放任何依赖 ORM / FastAPI 的业务逻辑，避免循环导入。
"""
from app.common import constants, enums

__all__ = ["constants", "enums"]
