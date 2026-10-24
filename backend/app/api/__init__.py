"""API 路由聚合（扁平结构：一个资源一个文件）。

对外统一挂载在 ``/api/v1`` 前缀下（见 ``app/main.py``），
前端与脚本的调用路径保持不变。
"""
from fastapi import APIRouter

from app.api import (
    assets,
    characters,
    image_gen,
    progress,
    projects,
    storyboards,
    tasks,
)

router = APIRouter()
router.include_router(projects.router)
router.include_router(characters.router)
router.include_router(storyboards.router)
router.include_router(assets.router)
router.include_router(tasks.router)
router.include_router(image_gen.router)
router.include_router(progress.router)
