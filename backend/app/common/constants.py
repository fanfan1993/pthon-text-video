"""公共常量与映射表。

只放纯数据，不放逻辑；需要计算时放到对应 service。
"""
from __future__ import annotations

from app.common.enums import CloudLockType

# ---------- 画幅 / 分辨率 ----------
ASPECT_TO_RESOLUTION: dict[str, str] = {
    "16:9": "1920x1080",
    "9:16": "1080x1920",
    "1:1": "1024x1024",
}

# 项目内分辨率 → 方舟 Seedream 显式宽高（总像素需落在 [921600, 4624220]）
SEEDREAM_SIZE_MAP: dict[str, str] = {
    "1920x1080": "2048x1152",   # 16:9
    "1080x1920": "1152x2048",   # 9:16
    "1024x1024": "2048x2048",   # 1:1
}

# Seedream 5.0 直接支持的档位字符串
SEEDREAM_TIERS: tuple[str, ...] = ("1K", "1.5K", "2K")

# 参考图降采样边长上限，控制请求体体积
REF_MAX_EDGE = 768

# 单次独立出图的最大张数
IMAGE_JOB_MAX_COUNT = 4

# ---------- 角色锁定 ----------
# provider 名 → 云端锁定类型（写进 character.cloud_lock_type，供前端展示）
PROVIDER_LOCK_TYPE: dict[str, CloudLockType] = {
    "kling": CloudLockType.kling_subject,
    "jimeng": CloudLockType.jimeng_role_id,
    "volc": CloudLockType.jimeng_role_id,
}

# 云端角色 token 前缀（mock/伪 ID，解析时应视为「无参考图」）
PSEUDO_ROLE_PREFIXES: tuple[str, ...] = ("MOCK-", "NAME-")

# ---------- 媒体子目录 ----------
MEDIA_DIR_IMAGES = "images"
MEDIA_DIR_VIDEO = "video"
MEDIA_DIR_AUDIO = "audio"
MEDIA_DIR_IMAGE_JOBS = "image_jobs"
MEDIA_DIR_REFS = "refs"
