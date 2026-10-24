"""出图 / 出视频 Provider 抽象层。

- ``ImageProvider``：编排层唯一依赖的接口；
- ``HttpImageProvider``：基于 httpx 的云端实现基类（重试、轮询、下载、角色锁定）；
- ``ProviderError``：统一的调用失败异常，编排层捕获后降级或转人工审核。
"""
from __future__ import annotations

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


class ProviderError(RuntimeError):
    """出图 / 出视频 Provider 调用失败。"""


@dataclass
class ImageResult:
    """一次出图的结果。"""

    path: str  # 保存后的文件完整路径
    meta: dict  # 模型/分辨率/角色ID 等元信息


class ImageProvider(ABC):
    """出图 Provider 接口。"""

    name: str

    @abstractmethod
    async def lock_role(self, ref_images: list[Path], name: str) -> str:
        """锁定角色，返回可复用的角色 ID（即梦 RM-XXXXXX / 可灵主体 ID / mock 伪 ID）。"""

    @abstractmethod
    async def generate_image(
        self,
        *,
        prompt: str,
        role_id: str | None,
        resolution: str,
        out_path: Path,
    ) -> ImageResult:
        """生成关键帧图并写入 out_path。"""


class HttpImageProvider(ImageProvider):
    """基于 httpx 的云端 Provider 基类（含请求、轮询与下载）。"""

    # 子类覆盖
    name = "http"
    model_image: str = ""
    model_video: str = ""

    def __init__(self, base_url: str, api_key: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key

    # ---------- HTTP ----------
    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def _post(self, path: str, body: dict, *, timeout: float = 120) -> dict:
        import httpx

        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(
                f"{self.base_url}{path}", json=body, headers=self._headers()
            )
        if resp.status_code >= 400:
            raise ProviderError(
                f"{self.name} POST {path} 失败: {resp.status_code} {resp.text[:400]}"
            )
        return resp.json()

    async def _get(self, path: str, *, timeout: float = 30) -> dict:
        import httpx

        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.get(f"{self.base_url}{path}", headers=self._headers())
        if resp.status_code >= 400:
            raise ProviderError(
                f"{self.name} GET {path} 失败: {resp.status_code} {resp.text[:400]}"
            )
        return resp.json()

    async def _download(self, url: str, out_path: Path) -> None:
        import httpx

        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_bytes(resp.content)

    async def _poll_until(
        self,
        get_status,
        *,
        interval: float = 3.0,
        timeout: float = 300.0,
        done_states=("succeed", "success", "completed"),
        fail_states=("failed", "error"),
    ) -> dict:
        """通用轮询：``get_status`` 返回 ``(state, payload)``。"""
        start = time.monotonic()
        while True:
            state, data = await get_status()
            if state in done_states:
                return data
            if state in fail_states:
                raise ProviderError(f"{self.name} 任务失败: {data}")
            if time.monotonic() - start > timeout:
                raise ProviderError(f"{self.name} 轮询超时（{timeout}s）")
            await asyncio.sleep(interval)

    # ---------- 角色锁定 ----------
    def _create_cloud_role(self, ref_images: list[Path], name: str) -> str | None:
        """可选钩子：创建云端持久角色/主体。默认返回 None（退化为参考图方式）。"""
        return None

    async def lock_role(self, ref_images: list[Path], name: str) -> str:
        from app.services.providers.ark import build_role_token

        refs = [str(p) for p in ref_images]
        cid = None
        try:
            cid = self._create_cloud_role(ref_images, name)
        except Exception as exc:  # noqa: BLE001
            logger.info("%s 云端角色创建跳过（退化为参考图）: %s", self.name, exc)
        return build_role_token(self.name, refs, cid)

    # ---------- 子类实现 ----------
    async def generate_image(
        self,
        *,
        prompt: str,
        role_id: str | None,
        resolution: str,
        out_path: Path,
    ) -> ImageResult:
        raise NotImplementedError

    async def generate_video(
        self,
        *,
        prompt: str,
        first_frame: Path,
        duration: int = 5,
        out_path: Path,
    ) -> str:
        raise NotImplementedError(f"{self.name} 未实现 generate_video")
