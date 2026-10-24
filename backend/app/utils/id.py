"""ID 与通用小工具。"""
from __future__ import annotations

import uuid


def new_id() -> str:
    """生成字符串 UUID。"""
    return str(uuid.uuid4())
