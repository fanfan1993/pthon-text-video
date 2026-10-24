"""火山方舟（Ark）通用工具：角色 token、参考图编码、尺寸映射。

Seedream（出图）与 Seedance（出视频）共用同一套鉴权与参考图嵌入方式，
把通用部分独立于此，volc / jimeng 两个 Provider 直接复用。
"""
from __future__ import annotations

import base64
import io
import json
import logging

from PIL import Image

from app.common.constants import (
    PSEUDO_ROLE_PREFIXES,
    REF_MAX_EDGE,
    SEEDREAM_SIZE_MAP,
    SEEDREAM_TIERS,
)

logger = logging.getLogger(__name__)


def build_role_token(provider: str, refs: list[str], cid: str | None) -> str:
    """构造角色 token（序列化进 ``character.cloud_lock_id``）。

    结构：``{"p": provider名, "refs": [参考图绝对路径], "cid": 云端角色ID 或 null}``
    """
    return json.dumps({"p": provider, "refs": refs, "cid": cid}, ensure_ascii=False)


def parse_role_token(role_id: str | None) -> dict:
    """解析角色 token；mock/NAME 伪 ID 或非法值安全退化为「无参考」。"""
    if not role_id:
        return {"p": "", "refs": [], "cid": None}
    if role_id.startswith(PSEUDO_ROLE_PREFIXES):
        return {"p": "", "refs": [], "cid": None}
    try:
        data = json.loads(role_id)
        if isinstance(data, dict) and "refs" in data:
            return data
    except Exception:  # noqa: BLE001
        pass
    return {"p": "", "refs": [], "cid": None}


def ref_data_uris(ref_paths: list[str], max_edge: int = REF_MAX_EDGE) -> list[str]:
    """把本地参考图降采样并编码为 data URI，供请求体嵌入。"""
    uris: list[str] = []
    for p in ref_paths:
        try:
            im = Image.open(p).convert("RGB")
            im.thumbnail((max_edge, max_edge))
            buf = io.BytesIO()
            im.save(buf, "PNG")
            b64 = base64.b64encode(buf.getvalue()).decode("ascii")
            uris.append(f"data:image/png;base64,{b64}")
        except Exception as exc:  # noqa: BLE001
            logger.warning("参考图编码失败 %s: %s", p, exc)
    return uris


def ark_size(resolution: str) -> str:
    """把项目内分辨率映射成方舟 Seedream 可接受的 size 值。

    Seedream 5.0 支持档位字符串 "1K"/"1.5K"/"2K" 与像素值（总像素在合法区间内）。
    """
    res = (resolution or "").strip().upper()
    if res in SEEDREAM_TIERS:
        return res
    return SEEDREAM_SIZE_MAP.get(res.lower(), "2K")
