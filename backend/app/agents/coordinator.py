"""多 Agent 协作编排器（Coordinator）。

把原本写死的线性流水线，升级为「多个 LLM 角色 Agent 协作」：

    编剧 Agent  →  角色设计师 Agent  →  分镜师 Agent  →  导演 Agent（拍板每镜方案）
                                                          ↓
                    逐镜：出图 → 视觉审校 Agent（不达标打回重出）→ 导演方案执行 → 配音 → 合成
                                                          ↓
                                              拼接成片 → 完成

所有 Agent 通过 ``PipelineState``（黑板）共享状态、通过 ``MessageBus`` 互通消息；
Coordinator 负责驱动顺序、处理审校反馈闭环、并把结果落库（Task/Storyboard/Asset）
与推送进度（WebSocket），对外表现与旧流水线完全一致。
"""
from __future__ import annotations

import logging
from pathlib import Path

from sqlalchemy.orm import Session

from app import models
from app.common.realtime import publish
from app.config import get_settings
from app.database import SessionLocal
from app.schemas import ProgressMessage, TaskStage, TaskStatus
from app.services import ffmpeg_service as ffmpeg_svc
from app.services import tts_service as tts_svc
from app.services.providers import get_provider
from app.services.providers.mock import MockImageProvider
from app.services.task_progress import resolution_for, set_task
from app.utils.files import asset_path, media_root, project_dir

from app.agents.base import (
    AgentContext,
    CharacterSpec,
    MessageBus,
    PipelineState,
    ShotSpec,
)
from app.agents.character_designer import CharacterDesignerAgent
from app.agents.director import DirectorAgent
from app.agents.screenwriter import ScreenwriterAgent
from app.agents.storyboard import StoryboardAgent
from app.agents.visual_reviewer import VisualReviewerAgent

logger = logging.getLogger(__name__)
settings = get_settings()


async def run_multiagent_pipeline(
    project_id: str,
    *,
    provider: str | None = None,
    tts_engine: str | None = None,
    do_i2v: bool = False,
    camera: str = "ken_burns",
    db: Session | None = None,
) -> None:
    """多 Agent 协作执行一个项目的完整生成流水线。"""
    own_db = db is None
    db = db or SessionLocal()
    provider_inst = get_provider(provider)
    bus: MessageBus | None = None
    try:
        project = db.get(models.Project, project_id)
        if project is None:
            logger.error("项目不存在: %s", project_id)
            return
        project.status = models.ProjectStatus.generating
        db.commit()

        root = media_root()
        pdir = project_dir(project_id)
        resolution = resolution_for(project.aspect_ratio)

        ctx = AgentContext(
            db=db,
            provider=provider_inst,
            provider_name=getattr(provider_inst, "name", "mock"),
            resolution=resolution,
            media_root=root,
            project_dir=pdir,
            project=project,
            settings=settings,
            do_i2v=do_i2v,
            tts_engine=tts_engine,
            default_camera=camera,
        )
        bus = MessageBus(project_id, pdir)
        state = PipelineState(
            project_id=project_id,
            raw_input=project.raw_input or "",
            style=project.style_preset,
            aspect_ratio=project.aspect_ratio,
            target_duration=project.target_duration,
            resolution=resolution,
        )
        state.characters = [
            CharacterSpec(
                id=c.id,
                name=c.name,
                description=c.description or "",
                reference_images=list(c.reference_images or []),
                cloud_lock_id=c.cloud_lock_id,
                cloud_lock_type=(c.cloud_lock_type.value if c.cloud_lock_type else "none"),
                need_ai_image=c.need_ai_image,
            )
            for c in project.characters
        ]

        # 重置上一轮产物，避免重复
        db.query(models.Storyboard).filter_by(project_id=project_id).delete()
        db.query(models.Task).filter_by(project_id=project_id).delete()
        db.query(models.Asset).filter_by(project_id=project_id).delete()
        db.commit()

        # ---- 协作阶段 1：编剧 / 角色设计师 / 分镜师 / 导演 ----
        await ScreenwriterAgent().run(ctx, state, bus)

        await CharacterDesignerAgent().run(ctx, state, bus)

        await set_task(db, project_id, None, TaskStage.storyboard, TaskStatus.running)
        await StoryboardAgent().run(ctx, state, bus)
        await set_task(db, project_id, None, TaskStage.storyboard, TaskStatus.success)

        DirectorAgent().pre_plan(ctx, state, bus)

        # ---- 协作阶段 2：逐镜（出图 → 审校 → 导演方案 → 配音 → 合成） ----
        storyboards = (
            db.query(models.Storyboard)
            .filter_by(project_id=project_id)
            .order_by(models.Storyboard.index)
            .all()
        )
        reviewer = VisualReviewerAgent()
        clips: list[Path] = []

        for sb in storyboards:
            spec = next((s for s in state.shots if s.index == sb.index), None)
            if spec is None:
                spec = ShotSpec(index=sb.index)
                state.shots.append(spec)

            role_id = None
            if spec.character_ids:
                first = db.get(models.Character, spec.character_ids[0])
                role_id = first.cloud_lock_id if first else None

            # 出图 + 视觉审校反馈闭环
            await set_task(db, project_id, sb.id, TaskStage.imagen, TaskStatus.running)
            img_out = asset_path(project_id, "images", f"shot_{sb.index}.png")
            prompt = spec.image_prompt or sb.image_prompt or sb.scene_description
            ok = False
            last_res = None
            for attempt in range(settings.REVIEW_MAX_RETRIES + 1):
                try:
                    last_res = await provider_inst.generate_image(
                        prompt=prompt, role_id=role_id, resolution=resolution, out_path=img_out
                    )
                except Exception as exc:  # noqa: BLE001
                    logger.warning("云端出图失败，退化为 mock: %s", exc)
                    last_res = await MockImageProvider().generate_image(
                        prompt=prompt, role_id=role_id, resolution=resolution, out_path=img_out
                    )
                spec.keyframe_path = Path(last_res.path)
                verdict = await reviewer.review(ctx, state, spec, attempt)
                bus.publish(
                    "视觉审校", "review",
                    f"镜{sb.index} 第{attempt + 1}次：{'通过' if verdict.passed else '打回'}-{verdict.reason}",
                    shot_index=sb.index,
                )
                if verdict.passed:
                    ok = True
                    break
                # 不达标：把角色外貌约束补进提示词后重出
                if spec.character_ids:
                    appr = "; ".join(
                        c.description for c in state.characters
                        if c.id in spec.character_ids and c.description
                    )[:200]
                    if appr:
                        prompt = f"{prompt}，务必保持角色外貌一致：{appr}"
            if not ok:
                logger.warning("镜%s 审校未达满分，但接受当前结果以保证流水线完成", sb.index)

            img_rel = str(Path(last_res.path).relative_to(root))
            img_asset = models.Asset(
                project_id=project_id, shot_id=sb.id, type=models.AssetType.image,
                path=img_rel, source=models.AssetSource.generated,
            )
            db.add(img_asset)
            db.commit()
            sb.keyframe_asset_id = img_asset.id
            await set_task(db, project_id, sb.id, TaskStage.imagen, TaskStatus.success)

            # 镜头运动 / 图生视频（导演已拍板 spec.use_i2v）
            await set_task(db, project_id, sb.id, TaskStage.animation, TaskStatus.running)
            video_out = asset_path(project_id, "video", f"shot_{sb.index}.mp4")
            try:
                if spec.use_i2v and hasattr(provider_inst, "generate_video") and do_i2v:
                    await provider_inst.generate_video(
                        prompt=spec.image_prompt or sb.image_prompt,
                        first_frame=Path(last_res.path),
                        duration=int(sb.duration),
                        out_path=video_out,
                    )
                else:
                    await ffmpeg_svc.camera_movement(
                        Path(last_res.path), video_out,
                        movement=spec.camera_movement or camera, duration=sb.duration,
                    )
            except Exception as exc:  # noqa: BLE001
                logger.warning("视频生成失败，回退 FFmpeg 运镜: %s", exc)
                await ffmpeg_svc.camera_movement(
                    Path(last_res.path), video_out,
                    movement=spec.camera_movement or camera, duration=sb.duration,
                )
            spec.video_path = video_out
            vid_rel = str(video_out.relative_to(root))
            vid_asset = models.Asset(
                project_id=project_id, shot_id=sb.id, type=models.AssetType.video,
                path=vid_rel, source=models.AssetSource.generated,
            )
            db.add(vid_asset)
            db.commit()
            sb.video_asset_id = vid_asset.id
            await set_task(db, project_id, sb.id, TaskStage.animation, TaskStatus.success)

            # 配音
            await set_task(db, project_id, sb.id, TaskStage.tts, TaskStatus.running)
            audio_out = asset_path(project_id, "audio", f"shot_{sb.index}.mp3")
            is_narrator = sb.speaker_character_id is None
            audio_path = await tts_svc.synthesize(
                sb.dialogue, audio_out, engine=tts_engine, is_narrator=is_narrator
            )
            spec.audio_path = Path(audio_path)
            aud_rel = str(Path(audio_path).relative_to(root))
            aud_asset = models.Asset(
                project_id=project_id, shot_id=sb.id, type=models.AssetType.audio,
                path=aud_rel, source=models.AssetSource.generated,
            )
            db.add(aud_asset)
            db.commit()
            sb.audio_asset_id = aud_asset.id
            await set_task(db, project_id, sb.id, TaskStage.tts, TaskStatus.success)

            # 逐镜合成（动态漫视频 + 配音 → 该镜成片）
            shot_final = pdir / f"clip_{sb.index}.mp4"
            await ffmpeg_svc.composite(video_out, Path(audio_path), shot_final)
            clips.append(shot_final)
            sb.status = models.ShotStatus.done
            db.commit()

        # ---- 协作阶段 3：拼接成片 ----
        await set_task(db, project_id, None, TaskStage.composite, TaskStatus.running)
        final_out = pdir / f"final_{project_id}.mp4"
        await ffmpeg_svc.concat(clips, final_out)
        final_rel = str(final_out.relative_to(root))
        final_asset = models.Asset(
            project_id=project_id, shot_id=None, type=models.AssetType.video,
            path=final_rel, source=models.AssetSource.generated,
        )
        db.add(final_asset)
        db.commit()
        await set_task(
            db, project_id, None, TaskStage.composite, TaskStatus.success,
            msg=f"成片: {final_out}",
        )
        project.status = models.ProjectStatus.completed
        db.commit()
        if bus:
            bus.save()
        await publish(
            project_id,
            ProgressMessage(stage="done", status="success", progress=1.0, output=final_rel),
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("多 Agent 流水线失败: %s", exc)
        project = db.get(models.Project, project_id)
        if project:
            project.status = models.ProjectStatus.failed
            db.commit()
        if bus:
            bus.save()
        await publish(
            project_id,
            ProgressMessage(stage="error", status="failed", progress=1.0, message=str(exc)[:300]),
        )
    finally:
        if own_db:
            db.close()
