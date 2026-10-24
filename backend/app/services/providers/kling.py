"""可灵（Kling）Provider：备选方案（质感好但偏贵）。

文档：https://klingai.com/cn/dev  /  https://docs.klingai.com
"""
from __future__ import annotations

import logging
from pathlib import Path

from app.config import get_settings
from app.services.providers.ark import parse_role_token, ref_data_uris
from app.services.providers.base import HttpImageProvider, ImageResult, ProviderError

logger = logging.getLogger(__name__)
settings = get_settings()


class KlingProvider(HttpImageProvider):
    name = "kling"
    model_image = "kling-v1"
    model_video = "kling-v1"

    def __init__(self) -> None:
        super().__init__(settings.KLING_BASE_URL, settings.KLING_API_KEY)

    # ---------- 主体库（可选钩子） ----------
    def _create_cloud_role(self, ref_images: list[Path], name: str) -> str | None:
        """上传参考图创建「主体」，返回 subject_id；失败自动退化为参考图方式。"""
        try:
            uris = ref_data_uris([str(p) for p in ref_images])
            if not uris:
                return None
            data = self._sync_post("/v1/subjects", {"name": name, "images": uris})
            return (data or {}).get("data", {}).get("subject_id")
        except Exception as exc:  # noqa: BLE001
            logger.info("可灵主体创建失败，退化为参考图: %s", exc)
            return None

    def _sync_post(self, path: str, body: dict) -> dict:
        """同步 POST（仅供 lock_role 这类非 async 钩子使用）。"""
        import httpx

        with httpx.Client(timeout=60) as client:
            resp = client.post(
                f"{self.base_url}{path}", json=body, headers=self._headers()
            )
        if resp.status_code >= 400:
            raise ProviderError(f"kling POST {path}: {resp.status_code} {resp.text[:300]}")
        return resp.json()

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
        refs = ref_data_uris(tok.get("refs") or [])
        body: dict = {
            "model": self.model_image,
            "prompt": prompt,
            "n": 1,
            "size": resolution,
        }
        if tok.get("cid"):
            body["subject_id"] = tok["cid"]
        elif refs:
            body["image"] = refs[0]

        data = await self._post("/v1/images/generations", body)
        task_id = (data or {}).get("data", {}).get("task_id")
        if not task_id:
            raise ProviderError(f"kling 出图任务创建失败: {str(data)[:300]}")

        final = await self._poll_until(lambda: self._image_status(task_id))
        url = self._parse_image(final)
        await self._download(url, out_path)
        return ImageResult(
            path=str(out_path),
            meta={"provider": "kling", "model": self.model_image, "resolution": resolution},
        )

    async def _image_status(self, task_id: str):
        data = await self._get(f"/v1/images/generation/{task_id}")
        return (data or {}).get("data", {}).get("task_status"), data

    @staticmethod
    def _parse_image(data: dict) -> str:
        works = (data or {}).get("data", {}).get("works") or []
        if not works:
            raise ProviderError(f"kling 出图无结果: {str(data)[:300]}")
        return works[0].get("image") or works[0].get("url")

    # ---------- 出视频（I2V） ----------
    async def generate_video(
        self,
        *,
        prompt: str,
        first_frame: Path,
        duration: int = 5,
        out_path: Path,
    ) -> str:
        uri = ref_data_uris([str(first_frame)])[0]
        body = {
            "model": self.model_video,
            "image": uri,
            "prompt": prompt,
            "duration": str(duration),
            "mode": "std",
        }
        data = await self._post("/v1/videos/generations", body)
        task_id = (data or {}).get("data", {}).get("task_id")
        if not task_id:
            raise ProviderError(f"kling 视频任务创建失败: {str(data)[:300]}")
        final = await self._poll_until(lambda: self._video_status(task_id))
        url = self._parse_video(final)
        await self._download(url, out_path)
        return str(out_path)

    async def _video_status(self, task_id: str):
        data = await self._get(f"/v1/videos/generation/{task_id}")
        return (data or {}).get("data", {}).get("task_status"), data

    @staticmethod
    def _parse_video(data: dict) -> str:
        works = (data or {}).get("data", {}).get("works") or []
        if not works:
            raise ProviderError(f"kling 视频无结果: {str(data)[:300]}")
        w = works[0]
        return w.get("video") or w.get("resource_url") or w.get("url")
