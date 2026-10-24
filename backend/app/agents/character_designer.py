"""角色设计师 Agent：为每个角色产出参考图并锁定云端角色 ID（跨镜一致锚点）。

- 已有参考图：直接用参考图锁定；
- 无图但标记 AI 出图：先出一张满意参考图，再锁定；
- 两者皆无：用角色名作伪 ID（退化为纯文生图）。
锁定结果回写数据库，保证「出图工坊 → 喂进视频」与逐镜出图都复用同一锚点。
"""
from __future__ import annotations

import logging
from pathlib import Path

from app.agents.base import Agent, AgentContext, MessageBus, PipelineState
from app import models
from app.common.constants import PROVIDER_LOCK_TYPE
from app.utils.files import asset_path, media_root

logger = logging.getLogger(__name__)


class CharacterDesignerAgent(Agent):
    role = "角色设计师"

    async def run(self, ctx: AgentContext, state: PipelineState, bus: MessageBus) -> None:
        bus.publish(self.role, "start", f"为 {len(state.characters)} 个角色产出并锁定参考图")
        root = ctx.media_root
        lock_type = PROVIDER_LOCK_TYPE.get(ctx.provider_name, models.CloudLockType.none)

        for spec in state.characters:
            char = ctx.db.get(models.Character, spec.id)
            if char is None:
                bus.publish(self.role, "warn", f"角色「{spec.name}」在数据库中不存在，跳过")
                continue

            if char.cloud_lock_id:
                # 已锁定：跨镜/跨集一致的关键，直接复用
                spec.cloud_lock_id = char.cloud_lock_id
                spec.cloud_lock_type = char.cloud_lock_type.value if char.cloud_lock_type else "none"
                bus.publish(self.role, "info", f"角色「{spec.name}」复用已有锁定（{spec.cloud_lock_id}）")
            elif spec.reference_images:
                refs = [Path(root / r) for r in spec.reference_images if r]
                spec.cloud_lock_id = await ctx.provider.lock_role(refs, spec.name)
                spec.cloud_lock_type = lock_type.value
                bus.publish(self.role, "info", f"角色「{spec.name}」用参考图锁定（{spec.cloud_lock_id}）")
            elif spec.need_ai_image:
                ref_out = asset_path(state.project_id, "images", f"ref_{spec.id}.png")
                res = await ctx.provider.generate_image(
                    prompt=spec.description or spec.name,
                    role_id=None,
                    resolution=ctx.resolution,
                    out_path=ref_out,
                )
                rel = str(Path(res.path).relative_to(root))
                spec.reference_images = [rel]
                spec.cloud_lock_id = await ctx.provider.lock_role([Path(res.path)], spec.name)
                spec.cloud_lock_type = lock_type.value
                bus.publish(self.role, "info", f"角色「{spec.name}」AI 出图并锁定（{spec.cloud_lock_id}）")
            else:
                spec.cloud_lock_id = f"NAME-{spec.name}"
                spec.cloud_lock_type = "none"
                bus.publish(self.role, "info", f"角色「{spec.name}」无参考图/未标记，用名字作伪 ID")

            # 回写数据库，保证后续逐镜出图复用同一锚点
            char.cloud_lock_id = spec.cloud_lock_id
            char.cloud_lock_type = models.CloudLockType(spec.cloud_lock_type)
            char.reference_images = list(spec.reference_images)
            ctx.db.commit()

        bus.publish(self.role, "done", "角色参考图与锁定完成")
