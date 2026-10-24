"""Pydantic Schema 聚合入口（按领域拆分，这里统一 re-export）。

约定：
- 响应模型统一 ``from_attributes=True``，可直接由 ORM 对象序列化；
- 枚举字段用 ``str`` 输出，前端拿到即字符串。
"""
from app.common.enums import (
    AssetSource,
    AssetType,
    CameraMovement,
    CloudLockType,
    ImageJobStatus,
    ProjectStatus,
    ShotStatus,
    SourceType,
    TaskStage,
    TaskStatus,
)
from app.schemas.base import ORMModel
from app.schemas.character import CharacterCreate, CharacterRead
from app.schemas.image_job import (
    ImageJobRead,
    SaveAsCharacterRequest,
    SaveAsCharacterResult,
)
from app.schemas.progress import ProgressMessage
from app.schemas.project import GenerateRequest, ProjectCreate, ProjectRead
from app.schemas.storyboard import AssetRead, StoryboardRead, TaskRead

__all__ = [
    "ORMModel",
    "ProjectCreate",
    "ProjectRead",
    "GenerateRequest",
    "CharacterCreate",
    "CharacterRead",
    "StoryboardRead",
    "AssetRead",
    "TaskRead",
    "ImageJobRead",
    "SaveAsCharacterRequest",
    "SaveAsCharacterResult",
    "ProgressMessage",
    # 枚举（历史导入路径兼容）
    "SourceType",
    "ProjectStatus",
    "CloudLockType",
    "CameraMovement",
    "ShotStatus",
    "AssetType",
    "AssetSource",
    "TaskStage",
    "TaskStatus",
    "ImageJobStatus",
]
