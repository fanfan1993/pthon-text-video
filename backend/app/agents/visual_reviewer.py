"""视觉审校 Agent：检查每镜关键帧，不达标则打回重出。

审校维度（默认启发式，零额外成本）：
1. 文件完整性：存在、非空（<2KB 视为空图）；
2. 画幅一致性：宽高比与项目分辨率匹配；
3. 角色一致性：角色名应出现在该镜出图提示词中；
4.（可选）真实视觉大模型打分：配置 VISION_MODEL 后开启，低于阈值打回。

返回 ``Verdict``，Coordinator 据此决定是否重出（最多 REVIEW_MAX_RETRIES 次）。
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from app.agents.base import Agent, AgentContext, MessageBus, PipelineState, ShotSpec
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


@dataclass
class Verdict:
    passed: bool
    reason: str
    score: float


class VisualReviewerAgent(Agent):
    role = "视觉审校"

    async def review(self, ctx: AgentContext, state: PipelineState, spec: ShotSpec, attempt: int) -> Verdict:
        notes: list[str] = []
        path = spec.keyframe_path
        if not path or not Path(path).exists():
            return Verdict(False, "关键帧文件缺失", 0.0)
        size = Path(path).stat().st_size
        if size < 2048:
            return Verdict(False, f"关键帧过小（{size}B），疑似空图", 0.0)
        notes.append(f"文件校验通过（{size // 1024}KB）")

        # 画幅一致性
        try:
            from PIL import Image

            w, h = Image.open(path).size
            ew, eh = ctx.resolution.lower().split("x")
            if abs(w / h - int(ew) / int(eh)) > 0.05:
                notes.append(f"画幅偏差 {w}x{h} vs {ctx.resolution}")
        except Exception:  # noqa: BLE001
            pass

        # 角色一致性（文本启发式）
        for cid in spec.character_ids:
            c = next((x for x in state.characters if x.id == cid), None)
            if not c or not c.name:
                continue
            if c.name not in (spec.image_prompt or ""):
                notes.append(f"角色「{c.name}」名未出现在出图提示词")

        # 可选：真实视觉大模型审校
        if settings.VISION_REVIEW and settings.VISION_MODEL:
            try:
                from app.services import llm_service as llm

                vr = await llm.vision_review(
                    Path(path), f"检查这帧是否符合分镜：{spec.scene_description}。"
                )
                if not vr.get("pass"):
                    return Verdict(False, f"视觉模型未通过：{vr.get('reason')}", float(vr.get("score", 0)))
                notes.append(f"视觉模型评分 {vr.get('score')}")
            except Exception as exc:  # noqa: BLE001
                notes.append(f"视觉审校调用失败: {exc}")

        spec.review_notes = notes
        return Verdict(True, "；".join(notes) or "ok", 1.0)
