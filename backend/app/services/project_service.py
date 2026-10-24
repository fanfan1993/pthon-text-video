"""项目流水线编排入口。

对外只暴露 ``run_pipeline``（保持原函数签名，兼容 API 与 Celery 派发）。
内部委托给 ``app.agents.coordinator.run_multiagent_pipeline``，由
编剧 / 角色设计师 / 分镜师 / 导演 / 视觉审校 多个 Agent 协作完成整条链路。

如需回退到旧的单编排器实现，可在此切换；当前多 Agent 编排即唯一实现。
"""
from __future__ import annotations

import logging

from app.agents.coordinator import run_multiagent_pipeline

logger = logging.getLogger(__name__)


async def run_pipeline(
    project_id: str,
    *,
    provider: str | None = None,
    tts_engine: str | None = None,
    do_i2v: bool = False,
    camera: str = "ken_burns",
) -> None:
    """执行一个项目的完整生成流水线（多 Agent 协作版）。"""
    await run_multiagent_pipeline(
        project_id,
        provider=provider,
        tts_engine=tts_engine,
        do_i2v=do_i2v,
        camera=camera,
    )
