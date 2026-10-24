"""ORM 模型聚合入口。

按领域拆分文件（project / character / storyboard / asset / task / image_job / setting），
这里统一 re-export，使得：
- 业务代码可以 ``from app import models`` 后直接用 ``models.Project``；
- ``Base.metadata`` 在导入本包时登记全部表（建表依赖此行为）。
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
from app.models.asset import Asset
from app.models.character import Character
from app.models.image_job import ImageJob
from app.models.project import Project
from app.models.setting import SettingsRow
from app.models.storyboard import Storyboard
from app.models.task import Task

__all__ = [
    # 表
    "Project",
    "Character",
    "Storyboard",
    "Asset",
    "Task",
    "ImageJob",
    "SettingsRow",
    # 枚举（保持历史导入路径可用）
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
