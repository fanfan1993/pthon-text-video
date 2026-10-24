"""应用配置：通过环境变量 / .env 注入，所有模块共享单一 Settings 实例。

设计要点：
- 用 pydantic-settings 统一管理，避免散落的全局变量。
- 默认 provider=``mock``，保证无 API Key 也能跑通整条流水线（占位出图 + 静音/Edge 配音）。
- 当配置了真实 Key 时，编排层会优先选用对应的云 provider。
"""
from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """全局配置。"""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # 基础
    APP_NAME: str = "TextToVideo Agent"
    ENV: str = "local"

    # 存储
    DATABASE_URL: str = "sqlite:///./text_video.db"
    MEDIA_ROOT: str = "./media"  # 图片/音频/视频根目录（Docker 中挂载为卷）

    # 异步任务
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_ENABLED: bool = False  # 本地无 Redis 时设为 False，改用 BackgroundTasks 运行

    # 出图 provider：mock | jimeng | kling | volc
    DEFAULT_PROVIDER: str = "mock"
    # 配音引擎：edge | silent
    DEFAULT_TTS: str = "edge"

    # 即梦 / 火山 Seedance
    JIMENG_API_KEY: str = ""
    JIMENG_BASE_URL: str = "https://api.jimeng.jianying.com"
    # 可灵
    KLING_API_KEY: str = ""
    KLING_BASE_URL: str = "https://api.klingai.com"
    # 火山方舟（Seedream 出图 / Seedance 出视频 / DeepSeek 分镜，同一把 Ark API Key）
    VOLC_API_KEY: str = ""
    VOLC_BASE_URL: str = "https://ark.cn-beijing.volces.com/api/v3"
    # 模型 ID 逐个「开通管理」页复制，不要手写
    IMAGE_MODEL: str = "doubao-seedream-4-0-250828"
    VIDEO_MODEL: str = "doubao-seedance-1-0-lite-i2v-250428"

    # LLM（分镜）：mock | volc（火山方舟 OpenAI 兼容）| openai | deepseek
    LLM_PROVIDER: str = "mock"
    LLM_API_KEY: str = ""      # 留空时自动复用 VOLC_API_KEY
    LLM_BASE_URL: str = "https://ark.cn-beijing.volces.com/api/v3"
    LLM_MODEL: str = "deepseek-v4-1-flash-economy-261017"

    # ---------- 多 Agent 协作架构 ----------
    MULTIAGENT_ENABLED: bool = True      # 是否启用多 Agent 协作编排
    DIRECTOR_LLM: bool = False           # 导演是否用 LLM 统筹（默认规则式，零额外成本）
    VISION_REVIEW: bool = False          # 视觉审校是否调用视觉大模型（默认启发式）
    REVIEW_MAX_RETRIES: int = 2          # 审校不达标时最多重出次数
    # 视觉审校模型（可复用 LLM 配置；留空则关闭真实视觉审校）
    VISION_MODEL: str = ""
    VISION_BASE_URL: str = ""
    VISION_API_KEY: str = ""

    # 渲染默认参数
    ASPECT_RATIO: str = "16:9"
    DEFAULT_RESOLUTION: str = "1920x1080"


@lru_cache
def get_settings() -> Settings:
    """返回进程内唯一的 Settings 实例（带缓存）。"""
    return Settings()
