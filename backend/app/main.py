"""FastAPI 应用入口。

- lifespan 启动时建表（SQLite 幂等）。
- 允许跨域（本地前端从 localhost 不同端口访问）。
- 挂载 /api/v1 路由与 /ws 进度推送。
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api import router as api_router
from app.config import get_settings
from app.database import init_db
from app.utils.files import media_root

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()  # 首次启动建表
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")

# 静态服务生成物（视频/图片/音频），供前端直接加载
app.mount(
    "/media",
    StaticFiles(directory=str(media_root()), html=False),
    name="media",
)


@app.get("/health")
def health() -> dict:
    """健康检查。"""
    return {"status": "ok", "app": settings.APP_NAME}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
