"""分镜师 Agent：把编剧定稿拆成结构化分镜 JSON，并落库 / 写入共享状态。"""
from __future__ import annotations

import logging

from app.agents.base import Agent, AgentContext, MessageBus, PipelineState, ShotSpec
from app import models
from app.services import llm_service as llm

logger = logging.getLogger(__name__)

_KNOWN = {
    "index", "scene_description", "shot_type", "camera_movement",
    "character_ids", "dialogue", "speaker_character_id",
    "image_prompt", "duration", "status",
}


def _clean_shot(s: dict) -> dict:
    data = {k: v for k, v in s.items() if k in _KNOWN}
    data.setdefault("status", models.ShotStatus.pending.value)
    return data


def _shot_to_spec(s: dict) -> ShotSpec:
    return ShotSpec(
        index=int(s.get("index", 0)),
        scene_description=s.get("scene_description", ""),
        shot_type=s.get("shot_type", "medium"),
        camera_movement=s.get("camera_movement", "ken_burns"),
        character_ids=list(s.get("character_ids") or []),
        dialogue=s.get("dialogue", ""),
        speaker_character_id=s.get("speaker_character_id"),
        image_prompt=s.get("image_prompt", ""),
        duration=float(s.get("duration", 5.0)),
    )


class StoryboardAgent(Agent):
    role = "分镜师"

    async def run(self, ctx: AgentContext, state: PipelineState, bus: MessageBus) -> None:
        bus.publish(self.role, "start", "根据编剧定稿拆分分镜")
        chars = [{"id": c.id, "name": c.name} for c in state.characters]
        shots = await llm.split_storyboard(
            state.script, chars,
            target_duration=state.target_duration, style=state.style,
        )
        # 重置旧分镜（重跑不产生重复行）
        ctx.db.query(models.Storyboard).filter_by(project_id=state.project_id).delete()
        for s in shots:
            sb = models.Storyboard(project_id=state.project_id, **_clean_shot(s))
            ctx.db.add(sb)
        ctx.db.commit()
        state.shots = [_shot_to_spec(s) for s in shots]
        bus.publish(self.role, "done", f"拆出 {len(state.shots)} 镜")
