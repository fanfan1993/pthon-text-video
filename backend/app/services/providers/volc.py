"""火山方舟 Provider：Seedream 出图 + Seedance 出视频（个人验证首选，有免费额度）。

文档：https://www.volcengine.com/docs/82379
费用参考（2026-10）：Seedream 按张计费约 0.2 元/张；Seedance 5s 720P ≈ 2.2 万 token。

⚠️ 响应字段可能随版本调整，解析集中在 ``_parse_image_url`` / ``_video_status``，只需改一处。
"""
from __future__ import annotations

import logging
from pathlib import Path

from app.config import get_settings
from app.services.providers.ark import ark_size, parse_role_token, ref_data_uris
from app.services.providers.base import HttpImageProvider, ImageResult, ProviderError

logger = logging.getLogger(__name__)
settings = get_settings()


class VolcProvider(HttpImageProvider):
    """方舟：Seedream 5.0 出图 / Seedance 2.x 图生视频。"""

    name = "volc"
    # 模型 ID 从方舟控制台「开通管理」复制；也可用 .env 的 IMAGE_MODEL / VIDEO_MODEL 覆盖
    model_image = "doubao-seedream-5-0-flash-260915"
    model_video = "doubao-seedance-2-0-mini-260615"

    def __init__(self) -> None:
        super().__init__(settings.VOLC_BASE_URL, settings.VOLC_API_KEY)
        self.model_image = settings.IMAGE_MODEL or self.model_image
        self.model_video = settings.VIDEO_MODEL or self.model_video

    # ---------- 出图 ----------
    async def generate_image(
        self,
        *,
        prompt: str,
        role_id: str | None,
        resolution: str,
        out_path: Path,
    ) -> ImageResult:
        tok = parse_role_token(role_id)
        body: dict = {
            "model": self.model_image,
            "prompt": prompt,
            "size": ark_size(resolution),
            "response_format": "url",
            "watermark": False,
            "seed": -1,
        }
        refs = ref_data_uris(tok.get("refs") or [])
        if refs:
            # Seedream 参考生图字段名是 image（string | string[]），
            # 传 data URI 数组即「多参考图生图」，这是跨镜角色一致的关键。
            body["image"] = refs if len(refs) > 1 else refs[0]
        elif tok.get("cid"):
            logger.info("volc 暂无云端角色库能力，cid 忽略，退化为纯文生图")

        data = await self._post("/images/generations", body)
        url = self._parse_image_url(data)
        await self._download(url, out_path)
        return ImageResult(
            path=str(out_path),
            meta={
                "provider": self.name,
                "model": self.model_image,
                "resolution": resolution,
                "size": body["size"],
                "refs": len(refs),
            },
        )

    @staticmethod
    def _parse_image_url(data: dict) -> str:
        items = (data or {}).get("data") or []
        if not items:
            raise ProviderError(f"volc 出图返回无数据: {str(data)[:300]}")
        item = items[0]
        if item.get("url"):
            return item["url"]
        if item.get("b64_json"):
            raise ProviderError("volc 返回 b64_json，需改 response_format 或本地解码（见 _parse_image_url）")
        raise ProviderError(f"volc 出图返回结构未知: {str(data)[:300]}")

    # ---------- 出视频（I2V） ----------
    async def generate_video(
        self,
        *,
        prompt: str,
        first_frame: Path,
        duration: int = 5,
        out_path: Path,
    ) -> str:
        """Seedance 图生视频：创建异步任务 → 轮询 → 下载 mp4。

        两代接口参数位置不同（本方法自动适配）：
        - Seedance 2.x（2026-10 在售）：resolution/duration/ratio 放在 body 顶层；
        - Seedance 1.0（旧）：参数写在 text 后缀 --resolution/--duration，图片需 role=first_frame。
        """
        first_uri = ref_data_uris([str(first_frame)])[0]
        legacy = "seedance-1-0" in (self.model_video or "")

        if legacy:
            text = f"{prompt} --resolution 720p --duration {int(duration)}"
            img_part = {
                "type": "image_url",
                "image_url": {"url": first_uri},
                "role": "first_frame",
            }
            body = {
                "model": self.model_video,
                "content": [{"type": "text", "text": text}, img_part],
            }
        else:
            body = {
                "model": self.model_video,
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": first_uri}},
                ],
                "resolution": "720p",
                "duration": int(duration),
                "ratio": "adaptive",  # 跟随首帧画幅，避免变形成片
                "watermark": False,
                "generate_audio": False,  # 配音由本地 TTS 负责，省 token
            }

        data = await self._post("/contents/generations/tasks", body)
        task_id = (data or {}).get("id") or (data or {}).get("data", {}).get("task_id")
        if not task_id:
            raise ProviderError(f"volc 视频任务创建失败: {str(data)[:300]}")
        logger.info("volc 视频任务已提交: %s（模型 %s）", task_id, self.model_video)

        final = await self._poll_until(
            lambda: self._video_status(task_id), interval=5.0, timeout=600.0
        )
        url = (
            (final.get("content") or {}).get("video_url")
            or final.get("video_url")
            or final.get("data", {}).get("video_url")
        )
        if not url:
            raise ProviderError(f"volc 视频返回无 url: {str(final)[:400]}")
        await self._download(url, out_path)
        return str(out_path)

    async def _video_status(self, task_id: str):
        data = await self._get(f"/contents/generations/tasks/{task_id}")
        status = (data or {}).get("status") or (data or {}).get("data", {}).get("status")
        # 方舟状态枚举：queued / running / succeeded / failed / cancelled
        mapped = {
            "succeeded": "succeed",
            "cancelled": "failed",
            "canceled": "failed",
        }.get(status, status)
        if mapped == "failed":
            logger.error("volc 视频任务失败详情: %s", str(data)[:400])
        return mapped, data


class JimengProvider(VolcProvider):
    """即梦：开发者能力已并入火山方舟，复用同一后端；如有独立网关覆盖 base_url 即可。"""

    name = "jimeng"

    def __init__(self) -> None:
        super().__init__()
        self.base_url = (settings.JIMENG_BASE_URL or settings.VOLC_BASE_URL).rstrip("/")
        self.api_key = settings.JIMENG_API_KEY or settings.VOLC_API_KEY
