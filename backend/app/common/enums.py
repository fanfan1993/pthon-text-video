"""领域枚举。

集中定义，避免 models / schemas / services 各自定义一份导致取值漂移。
- 继承 ``str`` 便于直接 JSON 序列化（Pydantic 与前端都用字符串值）。
- 数据库列统一用 ``SAEnum(<枚举>)``，因此枚举成员名与值保持一致。
"""
from __future__ import annotations

import enum


class SourceType(str, enum.Enum):
    """项目输入形态：小说文本 / 图文。"""

    novel = "novel"
    image_text = "image_text"


class ProjectStatus(str, enum.Enum):
    """项目生命周期状态。"""

    draft = "draft"
    generating = "generating"
    completed = "completed"
    failed = "failed"


class CloudLockType(str, enum.Enum):
    """角色云端锁定方式：即梦角色 ID / 可灵主体 / 未锁定。"""

    jimeng_role_id = "jimeng_role_id"
    kling_subject = "kling_subject"
    none = "none"


class CameraMovement(str, enum.Enum):
    """镜头运动方式（FFmpeg 运镜或 I2V）。"""

    ken_burns = "ken_burns"
    pan = "pan"
    parallax = "parallax"
    none = "none"


class ShotStatus(str, enum.Enum):
    """单镜头生成状态。"""

    pending = "pending"
    done = "done"
    failed = "failed"


class AssetType(str, enum.Enum):
    """资产类型。"""

    image = "image"
    video = "video"
    audio = "audio"


class AssetSource(str, enum.Enum):
    """资产来源：流水线生成 / 用户上传。"""

    generated = "generated"
    uploaded = "uploaded"


class TaskStage(str, enum.Enum):
    """流水线阶段。"""

    storyboard = "storyboard"
    imagen = "imagen"
    animation = "animation"
    tts = "tts"
    composite = "composite"


class TaskStatus(str, enum.Enum):
    """阶段任务状态。"""

    pending = "pending"
    running = "running"
    success = "success"
    failed = "failed"
    manual_review = "manual_review"
    cancelled = "cancelled"


class ImageJobStatus(str, enum.Enum):
    """独立出图任务状态。"""

    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"
