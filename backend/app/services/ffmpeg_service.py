"""FFmpeg 服务：镜头运动（动态漫核心）与成片合成。

动态漫「严格版」默认不走图生视频，而是对静态关键帧做镜头运动（Ken Burns / 平移），
零视频生成额度消耗（设计稿 2 阶段 3）。所有调用均经 asyncio 子进程，避免阻塞事件循环。
"""
from __future__ import annotations

import asyncio
import logging
import os
import shutil
from pathlib import Path

logger = logging.getLogger(__name__)


def _resolve_ffmpeg() -> str:
    """定位 ffmpeg 可执行文件：优先环境变量/系统 PATH，其次用项目内置二进制。"""
    env_bin = os.environ.get("FFMPEG_BIN")
    if env_bin and shutil.which(env_bin):
        return env_bin
    sys_bin = shutil.which("ffmpeg")
    if sys_bin:
        return sys_bin
    # 项目内置：backend/.bin/ffmpeg（通过 imageio-ffmpeg 安装，避免依赖 brew）
    bundled = Path(__file__).resolve().parents[2] / ".bin" / "ffmpeg"
    if bundled.exists():
        return str(bundled)
    return "ffmpeg"  # 兜底，交由调用方报错


_FFMPEG = _resolve_ffmpeg()


def ffmpeg_available() -> bool:
    """检查 ffmpeg 是否可用（系统或内置）。"""
    return not _FFMPEG.endswith("ffmpeg") or shutil.which("ffmpeg") is not None or (
        Path(__file__).resolve().parents[2] / ".bin" / "ffmpeg"
    ).exists()


async def camera_movement(
    in_path: Path,
    out_path: Path,
    *,
    movement: str = "ken_burns",
    duration: float = 15.0,
    zoom: float = 1.12,
    width: int = 1920,
    height: int = 1080,
) -> str:
    """对静态关键帧做镜头运动，输出一段「会动」的视频。

    Args:
        in_path: 静态关键帧图路径
        out_path: 输出视频路径
        movement: ken_burns(缓慢推拉) | pan/parallax(缓慢平移) | none(固定)
        duration: 镜头时长（秒）
        zoom: Ken Burns 最大放大倍数

    Returns:
        输出视频路径
    """
    if not ffmpeg_available():
        raise RuntimeError("未检测到 ffmpeg，请先安装（mac: brew install ffmpeg / ubuntu: apt install ffmpeg）")

    frames = max(1, int(25 * duration))
    if movement == "ken_burns":
        vf = (
            f"scale={width}:{height}:force_original_aspect_ratio=increase,"
            f"crop={width}:{height},"
            f"zoompan=z='min(1.0+0.0006*on,{zoom})':d={frames}:s={width}x{height}:fps=25"
        )
    elif movement in ("pan", "parallax"):
        # 用 crop 做平移（translate 滤镜在部分 ffmpeg 构建中缺失，改用 crop 更通用）
        vf = (
            f"scale={width}:{height}:force_original_aspect_ratio=increase,"
            f"crop={width}:{height}:x='((iw-{width})/2)+150*sin(t/4)':y=0"
        )
    else:  # none
        vf = f"scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height}"

    cmd = [
        _FFMPEG, "-y", "-loop", "1", "-i", str(in_path),
        "-vf", vf, "-t", str(duration), "-r", "25",
        "-pix_fmt", "yuv420p", str(out_path),
    ]
    await _run(cmd)
    return str(out_path)


async def composite(
    video_path: Path,
    audio_path: Path,
    out_path: Path,
    *,
    subtitle_path: Path | None = None,
) -> str:
    """合成：视频 + 配音（+ 可选字幕）→ 成片。"""
    if not ffmpeg_available():
        raise RuntimeError("未检测到 ffmpeg")
    cmd = [_FFMPEG, "-y", "-i", str(video_path), "-i", str(audio_path)]
    if subtitle_path:
        cmd += ["-vf", f"subtitles='{subtitle_path}'"]
    cmd += ["-c:v", "libx264", "-c:a", "aac", "-shortest", "-movflags", "+faststart", str(out_path)]
    await _run(cmd)
    return str(out_path)


async def concat(videos: list[Path], out_path: Path) -> str:
    """多镜拼接（后期 1 分钟成片用）。"""
    if not ffmpeg_available():
        raise RuntimeError("未检测到 ffmpeg")
    list_file = out_path.with_suffix(".txt")
    list_file.write_text("\n".join(f"file '{v.resolve()}'" for v in videos), encoding="utf-8")
    cmd = [
        _FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", str(list_file),
        "-c", "copy", str(out_path),
    ]
    await _run(cmd)
    return str(out_path)


async def _run(cmd: list[str]) -> None:
    logger.info("执行 ffmpeg: %s", " ".join(cmd[:6]) + " ...")
    proc = await asyncio.create_subprocess_exec(
        *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    _out, err = await proc.communicate()
    if proc.returncode != 0:
        err_text = err.decode(errors="ignore")
        # 真实错误通常在 stderr 末尾，取最后 1500 字符
        tail = err_text[-1500:]
        raise RuntimeError(
            f"ffmpeg 失败({proc.returncode}): cmd={' '.join(map(str, cmd))}\n{tail}"
        )
