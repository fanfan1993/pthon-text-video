"""配音服务：Edge-TTS（真实、免费） + 静音兜底。

- 默认 ``edge``：调用微软 Edge 在线 TTS，中文音色好、零费用。
- 失败（无网络/被墙）自动回退静音 wav，保证流水线不中断。
- 每个角色可锁定一个音色（voice 参数），旁白用固定男声。
"""
from __future__ import annotations

import logging
import math
import wave
from pathlib import Path

import edge_tts

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

DEFAULT_VOICE = "zh-CN-XiaoxiaoNeural"  # 角色女声
NARRATOR_VOICE = "zh-CN-YunxiNeural"  # 旁白男声
SAMPLE_RATE = 24000
CHARS_PER_SEC = 4.5  # 中文朗读速度估算


async def synthesize(
    text: str,
    out_path: Path,
    *,
    engine: str | None = None,
    voice: str | None = None,
    is_narrator: bool = False,
) -> str:
    """把文本合成为音频文件，返回路径。

    Args:
        text: 要朗读的文本
        out_path: 输出文件路径（.mp3 或 .wav）
        engine: 覆盖默认引擎（edge | silent）
        voice: 指定音色；None 时按旁白/角色自动选
        is_narrator: 是否为旁白（影响默认音色）

    Returns:
        实际写出的文件路径字符串
    """
    engine = engine or settings.DEFAULT_TTS
    voice = voice or (NARRATOR_VOICE if is_narrator else DEFAULT_VOICE)

    if engine == "edge":
        try:
            await _edge_tts(text or " ", out_path, voice)
            # 偶发「成功但写出空文件」（网络被拦截时常见），需校验后再信任
            if out_path.exists() and out_path.stat().st_size > 200:
                logger.info("Edge-TTS 合成成功: %s", out_path)
                return str(out_path)
            logger.warning("Edge-TTS 产出异常（空文件），回退静音音频")
        except Exception as exc:  # 网络/被墙/限流
            logger.warning("Edge-TTS 失败，回退静音音频: %s", exc)

    await _silent_wav(text, out_path.with_suffix(".wav"))
    return str(out_path.with_suffix(".wav"))


async def _edge_tts(text: str, out_path: Path, voice: str) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(str(out_path))


async def _silent_wav(text: str, out_path: Path) -> None:
    """生成与文本长度匹配的静音 wav（兜底，保证音画时长对齐）。"""
    duration = max(1.5, len(text) / CHARS_PER_SEC)
    n_frames = int(SAMPLE_RATE * duration)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(out_path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(SAMPLE_RATE)
        wav.writeframes(b"\x00\x00" * n_frames)
    logger.info("静音兜底音频已生成: %s (%.1fs)", out_path, duration)
