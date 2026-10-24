"""导演 Agent：统筹节奏，为每一镜拍板「用 I2V 图生视频」还是「静态关键帧 + 运镜」。

默认规则式决策（零额外成本）：
- I2V 可用（do_i2v 且 provider 支持 generate_video）：整片走图生视频，画面真正动起来；
- 不可用：静态关键帧 + LLM 给出的运镜（缺失则回退默认运镜）。
决策写入 ShotSpec.use_i2v / camera_movement，并作为「拍摄方案」广播到消息总线。
"""
from __future__ import annotations

import logging

from app.agents.base import Agent, AgentContext, MessageBus, PipelineState

logger = logging.getLogger(__name__)


class DirectorAgent(Agent):
    role = "导演"

    def pre_plan(self, ctx: AgentContext, state: PipelineState, bus: MessageBus) -> None:
        i2v_available = ctx.do_i2v and hasattr(ctx.provider, "generate_video")
        bus.publish(self.role, "start", f"统筹节奏：I2V 可用={'是' if i2v_available else '否'}")

        for spec in state.shots:
            if i2v_available:
                spec.use_i2v = True
                note = f"镜{spec.index}：用图生视频（I2V）让画面真正动起来"
            else:
                spec.use_i2v = False
                if not spec.camera_movement or spec.camera_movement == "none":
                    spec.camera_movement = ctx.default_camera
                note = f"镜{spec.index}：静态关键帧 + {spec.camera_movement} 运镜"
            bus.publish(self.role, "plan", note, shot_index=spec.index)

        bus.publish(self.role, "done", "拍摄方案已确定（每镜 I2V/运镜 已由导演拍板）")
