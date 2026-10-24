"""Provider 工厂与对外导出。

``get_provider`` 是业务层唯一入口：未配置密钥时自动回退 mock，保证本地可运行。
"""
from __future__ import annotations

import logging

from app.config import get_settings
from app.services.providers.base import (
    HttpImageProvider,
    ImageProvider,
    ImageResult,
    ProviderError,
)

logger = logging.getLogger(__name__)

__all__ = [
    "ImageProvider",
    "ImageResult",
    "ProviderError",
    "HttpImageProvider",
    "VolcProvider",
    "JimengProvider",
    "KlingProvider",
    "MockImageProvider",
    "get_provider",
]


def get_provider(name: str | None = None) -> ImageProvider:
    """按名称返回 provider；缺密钥时回退 mock。"""
    from app.services.providers.kling import KlingProvider
    from app.services.providers.mock import MockImageProvider
    from app.services.providers.volc import JimengProvider, VolcProvider

    settings = get_settings()
    name = name or settings.DEFAULT_PROVIDER

    if name == "mock":
        return MockImageProvider()

    # 真实 provider 需要密钥，缺失则回退（保证可运行）
    # 即梦与火山同源（字节/火山方舟），有任一 key 即可启用
    key_map = {
        "jimeng": settings.JIMENG_API_KEY or settings.VOLC_API_KEY,
        "kling": settings.KLING_API_KEY,
        "volc": settings.VOLC_API_KEY,
    }
    if not key_map.get(name):
        logger.warning("provider=%s 未配置 API Key，回退到 mock（占位出图）", name)
        return MockImageProvider()

    if name == "jimeng":
        return JimengProvider()
    if name == "kling":
        return KlingProvider()
    if name == "volc":
        return VolcProvider()
    return MockImageProvider()
