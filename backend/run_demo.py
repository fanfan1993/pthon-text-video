"""一键端到端演示：创建一个项目 + 一个角色，跑通整条流水线，产出成片。

仅用于本地验证（无需任何 API Key，使用 mock provider + Edge-TTS）。
运行：
    cd backend
    PYTHONPATH=. python run_demo.py
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

# 确保 backend 目录在 path 中
BACKEND = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND))

from app.database import SessionLocal, init_db  # noqa: E402
from app import models  # noqa: E402
from app.services.project_service import run_pipeline  # noqa: E402
from app.config import get_settings  # noqa: E402
from app.utils.files import media_root  # noqa: E402


def main() -> None:
    settings = get_settings()
    media_root().mkdir(parents=True, exist_ok=True)
    init_db()

    db = SessionLocal()
    try:
        # 1) 创建项目
        project = models.Project(
            title="演示：雨夜少女",
            source_type=models.SourceType.novel,
            raw_input=(
                "雨夜，少女撑伞立在霓虹灯下，轻声说：今天的天，好像也累了。"
            ),
            style_preset="anime",
            aspect_ratio="16:9",
            target_duration=15.0,
        )
        db.add(project)
        db.commit()
        db.refresh(project)
        print(f"[1] 创建项目 id={project.id}")

        # 2) 角色：无参考图，由流水线 AI 出图并锁角色（mock 下为占位图）
        char = models.Character(
            project_id=project.id,
            name="少女",
            description="黑发少女，蓝色雨衣，霓虹都市背景",
            need_ai_image=True,
        )
        db.add(char)
        db.commit()
        db.refresh(char)
        print(f"[2] 创建角色 id={char.id} (need_ai_image=True)")

        project_id = project.id
    finally:
        db.close()

    # 3) 跑流水线。配置了方舟 Key 则真实出图（volc），否则回退 mock 占位图。
    provider = "volc" if settings.VOLC_API_KEY else "mock"
    print(f"[3] 启动流水线（provider={provider} 出图 + TTS + FFmpeg 合成）...")
    asyncio.run(
        run_pipeline(
            project_id,
            provider=provider,
            tts_engine="edge",
            do_i2v=False,
            camera="ken_burns",
        )
    )

    # 4) 报告成片
    final = media_root() / project_id / f"final_{project_id}.mp4"
    if final.exists():
        size = final.stat().st_size
        print(f"\n✅ 成片已生成: {final}")
        print(f"   大小: {size/1024:.1f} KB")
        # 用 ffprobe 取时长（如有）
        import shutil
        import subprocess

        if shutil.which("ffprobe"):
            out = subprocess.run(
                ["ffprobe", "-v", "error", "-show_entries", "format=duration",
                 "-of", "default=noprint_wrappers=1:nokey=1", str(final)],
                capture_output=True, text=True,
            )
            if out.stdout.strip():
                print(f"   时长: {float(out.stdout.strip()):.1f}s")
    else:
        print(f"\n❌ 未找到成片: {final}")
        print("   请确认 ffmpeg 已安装（brew install ffmpeg）")


if __name__ == "__main__":
    main()
