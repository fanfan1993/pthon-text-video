"""编剧 Agent：把原始素材扩写/改编为更利于分镜的剧情脚本。"""
from __future__ import annotations

import logging

from app.agents.base import Agent, AgentContext, MessageBus, PipelineState
from app.services import llm_service as llm

logger = logging.getLogger(__name__)


class ScreenwriterAgent(Agent):
    role = "编剧"

    async def run(self, ctx: AgentContext, state: PipelineState, bus: MessageBus) -> None:
        bus.publish(
            self.role, "start",
            f"开始改编/扩写剧情（目标 {state.target_duration:.0f}s，风格 {state.style}）",
        )
        script = await llm.expand_script(
            state.raw_input, target_duration=state.target_duration, style=state.style
        )
        state.script = script
        bus.publish(self.role, "done", f"剧情定稿 {len(script)} 字，已作为分镜输入")
