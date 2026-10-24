"""文件与媒体目录工具。

- 所有生成物统一落在 ``settings.MEDIA_ROOT`` 下，按项目 + 类型分目录。
- 使用 pathlib，跨平台安全，避免裸字符串拼接路径。
"""
from __future__ import annotations

from pathlib import Path

from app.config import get_settings

settings = get_settings()


def media_root() -> Path:
    """返回媒体根目录并确保存在。"""
    root = Path(settings.MEDIA_ROOT)
    root.mkdir(parents=True, exist_ok=True)
    return root


def project_dir(project_id: str) -> Path:
    """项目专属目录：``MEDIA_ROOT/<project_id>/``。"""
    d = media_root() / project_id
    d.mkdir(parents=True, exist_ok=True)
    return d


def asset_path(project_id: str, kind: str, filename: str) -> Path:
    """按类型（images/audio/video）落盘，返回完整路径。"""
    d = project_dir(project_id) / kind
    d.mkdir(parents=True, exist_ok=True)
    return d / filename


def save_upload(project_id: str, kind: str, filename: str, data: bytes) -> str:
    """保存上传字节，返回相对 MEDIA_ROOT 的路径字符串。"""
    path = asset_path(project_id, kind, filename)
    path.write_bytes(data)
    # 存相对路径，便于迁移
    return str(path.relative_to(media_root()))


# ---------- 独立出图任务目录 ----------
def image_job_dir(job_id: str, kind: str) -> Path:
    """出图任务的专属子目录：``MEDIA_ROOT/image_jobs/<job_id>/<kind>/``。"""
    d = media_root() / "image_jobs" / job_id / kind
    d.mkdir(parents=True, exist_ok=True)
    return d


def save_image_job_file(job_id: str, kind: str, filename: str, data: bytes) -> str:
    """保存出图任务的参考图/结果图，返回相对 MEDIA_ROOT 的路径字符串。"""
    path = image_job_dir(job_id, kind) / filename
    path.write_bytes(data)
    return str(path.relative_to(media_root()))
