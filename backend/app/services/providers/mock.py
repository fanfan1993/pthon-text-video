"""Mock 出图 Provider：无需任何密钥即可跑通整条流水线。

用 Pillow 画一张带角色 ID / 提示词的占位图，便于本地调试与单元测试。
"""
from __future__ import annotations

import hashlib
import logging
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from app.services.providers.base import ImageProvider, ImageResult

logger = logging.getLogger(__name__)


class MockImageProvider(ImageProvider):
    name = "mock"

    async def lock_role(self, ref_images: list[Path], name: str) -> str:
        # 伪 ID：保证同一角色名在会话内稳定
        digest = hashlib.md5(name.encode()).hexdigest()[:8]
        return f"MOCK-{digest}"

    async def generate_image(
        self,
        *,
        prompt: str,
        role_id: str | None,
        resolution: str,
        out_path: Path,
    ) -> ImageResult:
        w, h = _parse_resolution(resolution)
        img = Image.new("RGB", (w, h), _color_from(role_id or "x"))
        draw = ImageDraw.Draw(img)

        # 顶部角色 ID 条
        draw.rectangle([0, 0, w, 60], fill=(20, 20, 30))
        _text(draw, f"role={role_id}", (10, 18), 28, (220, 220, 220))

        # 居中提示词（自动换行）
        _wrap_text(draw, prompt, (40, 100), w - 80, 36, (235, 235, 235))

        out_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(out_path)
        logger.info("mock 出图已写入 %s", out_path)
        return ImageResult(
            path=str(out_path),
            meta={"provider": "mock", "resolution": resolution, "role_id": role_id},
        )


def _parse_resolution(res: str) -> tuple[int, int]:
    try:
        w, h = res.lower().split("x")
        return int(w), int(h)
    except Exception:  # noqa: BLE001
        return 1920, 1080


def _color_from(seed: str) -> tuple[int, int, int]:
    h = int(hashlib.md5(seed.encode()).hexdigest()[:6], 16)
    return (h >> 16) & 255, (h >> 8) & 255, h & 255


def _font(size: int):
    try:
        return ImageFont.truetype("DejaVuSans.ttf", size)
    except Exception:  # noqa: BLE001
        return ImageFont.load_default()


def _text(draw, text, xy, size, fill) -> None:
    draw.text(xy, text, fill=fill, font=_font(size))


def _wrap_text(draw, text, xy, max_w, size, fill) -> None:
    font = _font(size)
    lines, cur = [], ""
    for word in text.split():
        test = f"{cur} {word}".strip()
        if draw.textlength(test, font=font) > max_w and cur:
            lines.append(cur)
            cur = word
        else:
            cur = test
    if cur:
        lines.append(cur)
    y = xy[1]
    for line in lines[:12]:
        draw.text((xy[0], y), line, fill=fill, font=font)
        y += size + 8
