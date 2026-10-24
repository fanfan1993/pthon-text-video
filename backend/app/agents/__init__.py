"""多 Agent 协作包。

对外暴露 ``run_multiagent_pipeline``（由 ``project_service.run_pipeline`` 委托调用）。
"""
from app.agents.coordinator import run_multiagent_pipeline

__all__ = ["run_multiagent_pipeline"]
