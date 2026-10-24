"""LLM 分镜服务：把小说/图文拆成结构化分镜 JSON。

支持的 provider：
- ``mock``      : 本地确定性输出，无需密钥即可跑通 MVP（单镜）。
- ``volc``      : 火山方舟 OpenAI 兼容端点（``/api/v3/chat/completions``），
                  DeepSeek / 豆包系模型走这里，复用 ``VOLC_API_KEY``。
- ``openai`` / ``deepseek`` : 其它 OpenAI 协议兼容服务（DeepSeek 官方、通义等）。

设计要点：
- Key / base_url 缺省时自动回退 mock，保证任何环境下都不阻塞流水线。
- 解析对模型输出格式做容错：`````json`` 围栏、裸数组、``{"shots":[...]}`` 都吃。
- 部分模型不接受 ``response_format``，遇到 400 自动去掉该字段重试一次。
"""
from __future__ import annotations

import json
import logging
import re
from typing import Any

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# 火山方舟 / 自建 OpenAI 兼容服务的“volc 家族”provider 名
_VOLC_FAMILY = {"volc", "ark", "volcengine", "jimeng"}


def resolve_llm() -> tuple[str, str, str]:
    """返回 (base_url, api_key, model)，并把 provider 归一化。"""
    provider = (settings.LLM_PROVIDER or "mock").lower()
    if provider in _VOLC_FAMILY:
        base = settings.VOLC_BASE_URL or "https://ark.cn-beijing.volces.com/api/v3"
        key = settings.LLM_API_KEY or settings.VOLC_API_KEY
        model = settings.LLM_MODEL or "deepseek-v4-1-flash-economy-261017"
    else:
        base = settings.LLM_BASE_URL or "https://api.deepseek.com/v1"
        key = settings.LLM_API_KEY
        model = settings.LLM_MODEL or "deepseek-chat"
    return base.rstrip("/"), key, model


async def split_storyboard(
    raw_text: str,
    characters: list[dict[str, Any]],
    *,
    target_duration: float = 15.0,
    style: str = "anime",
    provider: str | None = None,
) -> list[dict[str, Any]]:
    """拆分分镜。

    Args:
        raw_text: 原始小说/图文文本
        characters: 角色列表，每项含 id / name
        target_duration: 目标时长（秒）
        style: 风格预设
        provider: 覆盖默认 LLM provider

    Returns:
        分镜字典列表，字段对齐 Storyboard 表
    """
    provider = (provider or settings.LLM_PROVIDER or "mock").lower()
    _, key, _ = resolve_llm()
    if provider == "mock" or not key:
        if provider != "mock":
            logger.warning("LLM provider=%s 但未配置 Key，回退 mock 分镜", provider)
        return _mock_split(raw_text, characters, target_duration, style)
    return await _real_split(raw_text, characters, target_duration, style)


def _mock_split(
    raw_text: str, characters: list[dict], duration: float, style: str
) -> list[dict]:
    """确定性单镜分镜：把首段文本作为对白/旁白。"""
    first_line = (raw_text or "").strip().split("\n")[0].strip()
    dialogue = first_line[:120] if first_line else "（无对白）"
    char_ids = [c.get("id") for c in characters if c.get("id")]
    speaker = char_ids[0] if char_ids else None
    return [
        {
            "index": 1,
            "scene_description": (raw_text or "一个安静的场景")[:200],
            "shot_type": "medium",
            "camera_movement": "ken_burns",
            "character_ids": char_ids,
            "dialogue": dialogue,
            "speaker_character_id": speaker,
            "image_prompt": f"{style}风格，{first_line[:80]}，电影感，精致构图，角色居中",
            "duration": duration,
        }
    ]


# ---------------------------------------------------------------------------
# 真实 LLM 调用
# ---------------------------------------------------------------------------
_SYSTEM_TMPL = """你是资深的「动态漫」分镜师。把用户给的文本改编成 {n} 个连续分镜（总时长约 {dur} 秒）。

硬性要求：
1. 只输出 JSON，不要任何解释文字，不要 markdown 代码围栏。
2. 顶层结构为 {{"shots": [ ... ]}}，数组长度必须为 {n}。
3. 每个镜头对象包含且仅包含这些字段：
   - index: 整数，从 1 开始
   - scene_description: 本镜画面内容（中文，30~80 字，写清人物动作、环境、光线）
   - shot_type: "closeup" | "medium" | "wide"
   - camera_movement: "ken_burns" | "pan" | "parallax" | "none"
   - character_ids: 出现的角色 id 数组，只能从「可用角色」里选；没人则空数组
   - dialogue: 本镜台词（中文，无台词填空字符串 ""）
   - speaker_character_id: 说话角色的 id，旁白或无人说话填 null
   - image_prompt: 生图提示词（中文），包含角色外貌特征 + 镜头景别 + 光线氛围 + 画风
   - duration: 数字，本镜秒数，全部镜头之和约等于 {dur}
4. 一致性：同一角色在所有 image_prompt 里必须使用完全相同的外貌描述词，不得变化。
5. 画风统一为：{style}。

可用角色（id: 名字）：{chars}"""


async def _real_split(
    raw_text: str, characters: list[dict], duration: float, style: str
) -> list[dict]:
    """调用 OpenAI 兼容接口做分镜。"""
    base, key, model = resolve_llm()
    n = max(1, min(6, int(round(duration / 5.0)) or 1))  # 5 秒一镜
    char_desc = "；".join(f"{c.get('id')}: {c.get('name')}" for c in characters) or "无"
    system = _SYSTEM_TMPL.format(
        n=n, dur=int(duration), chars=char_desc, style=style
    )

    payload: dict[str, Any] = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": (raw_text or "")[:8000]},
        ],
        "temperature": 0.7,
    }

    content = await _chat(base, key, {**payload, "response_format": {"type": "json_object"}})
    if content is None:
        # 该模型不支持 response_format，去掉重试
        content = await _chat(base, key, payload)
    if not content:
        logger.warning("LLM 返回空内容，回退 mock 分镜")
        return _mock_split(raw_text, characters, duration, style)

    shots = _extract_shots(content)
    if not shots:
        logger.warning("LLM 输出无法解析为分镜，回退 mock。原始片段: %s", content[:300])
        return _mock_split(raw_text, characters, duration, style)
    return _normalize(shots, characters, duration)


async def _chat(base: str, key: str, payload: dict) -> str | None:
    """单次 chat 调用；不可重试类错误返回 None 表示让上层降级重试。"""
    try:
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                f"{base}/chat/completions",
                headers={
                    "Authorization": f"Bearer {key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
    except Exception as exc:  # noqa: BLE001
        logger.warning("LLM 请求异常: %s", exc)
        return None

    if resp.status_code >= 400:
        text = resp.text[:400]
        logger.warning("LLM 调用失败 %s: %s", resp.status_code, text)
        if "response_format" in payload and resp.status_code == 400:
            return None  # 交给调用方去掉 response_format 重试
        raise LLMError(f"LLM {resp.status_code}: {text}")

    data = resp.json()
    choices = (data or {}).get("choices") or []
    if not choices:
        raise LLMError(f"LLM 响应无 choices: {str(data)[:300]}")
    msg = choices[0].get("message") or {}
    return msg.get("content") or ""


class LLMError(RuntimeError):
    """LLM 调用失败（非可降级场景）。"""


def _extract_shots(text: str) -> list[dict]:
    """从模型输出里稳健地取出分镜数组。"""
    raw = (text or "").strip()
    # 去掉 ```json ... ``` 围栏
    fence = re.match(r"^```(?:json)?\s*([\s\S]*?)\s*```$", raw)
    if fence:
        raw = fence.group(1).strip()

    candidates: list[Any] = []
    for attempt in (raw, _first_json_blob(raw)):
        if not attempt:
            continue
        try:
            candidates.append(json.loads(attempt))
        except Exception:  # noqa: BLE001
            continue

    for data in candidates:
        if isinstance(data, list):
            items = data
        elif isinstance(data, dict):
            items = (
                data.get("shots")
                or data.get("storyboards")
                or data.get("scenes")
                or data.get("data")
                or []
            )
        else:
            items = []
        if isinstance(items, list) and items and isinstance(items[0], dict):
            return [i for i in items if isinstance(i, dict)]
    return []


def _first_json_blob(text: str) -> str | None:
    """截取第一个完整的 {...} 或 [...] 片段。"""
    for open_ch, close_ch in (("{", "}"), ("[", "]")):
        start = text.find(open_ch)
        end = text.rfind(close_ch)
        if start != -1 and end > start:
            return text[start : end + 1]
    return None


def _normalize(
    shots: list[dict], characters: list[dict], duration: float
) -> list[dict]:
    """补齐缺省字段、纠正非法取值，保证能落库。"""
    valid_ids = {c.get("id") for c in characters if c.get("id")}
    first_id = next(iter(valid_ids), None)
    out: list[dict] = []
    for i, s in enumerate(shots, start=1):
        ids = [cid for cid in (s.get("character_ids") or []) if cid in valid_ids]
        speaker = s.get("speaker_character_id")
        if speaker not in valid_ids:
            speaker = None
        shot_type = s.get("shot_type") if s.get("shot_type") in (
            "closeup", "medium", "wide"
        ) else "medium"
        raw_cam = (s.get("camera_movement") or "").lower()
        # 归一化：所有 pan 变体统一为 pan（与 DB 枚举一致）
        if raw_cam.startswith("pan") or raw_cam in ("left", "right"):
            cam = "pan"
        elif raw_cam in ("ken_burns", "parallax", "none"):
            cam = raw_cam
        else:
            cam = "ken_burns"
        try:
            dur = float(s.get("duration") or duration / len(shots))
        except Exception:  # noqa: BLE001
            dur = duration / len(shots)
        out.append(
            {
                "index": i,
                "scene_description": str(s.get("scene_description") or "")[:500],
                "shot_type": shot_type,
                "camera_movement": cam,
                "character_ids": ids,
                "dialogue": str(s.get("dialogue") or "")[:500],
                "speaker_character_id": speaker,
                "image_prompt": str(s.get("image_prompt") or s.get("scene_description") or "")[:1000],
                "duration": max(2.0, min(dur, 15.0)),
                "_fallback_char": first_id,
            }
        )
    # 若所有镜头都没绑角色但有可用角色，默认绑第一个（保证参考图一致性生效）
    if first_id and all(not s["character_ids"] for s in out):
        for s in out:
            s["character_ids"] = [first_id]
    for s in out:
        s.pop("_fallback_char", None)
    return out


# ---------------------------------------------------------------------------
# 编剧 Agent：剧情扩写 / 改编
# ---------------------------------------------------------------------------
_SCREENWRITER_TMPL = """你是资深「动态漫」编剧。把用户给的原始素材改编成一段可直接用于分镜的剧情脚本。

要求：
1. 输出纯文本（不要 JSON、不要 markdown 围栏、不要解释）。
2. 保持人物与世界观一致，补全必要的场景与动作描写，让画面可想象。
3. 控制篇幅，使之适配约 {dur} 秒的视频（中文约 {words} 字内）。
4. 画风基调：{style}。
5. 若原文已较完整，可在不破坏原意的前提下精简与润色。

只输出脚本正文。"""


async def expand_script(
    raw_text: str,
    *,
    target_duration: float = 15.0,
    style: str = "anime",
    provider: str | None = None,
) -> str:
    """编剧 Agent：把原始素材扩写/改编为更利于分镜的脚本。

    无 Key 或 mock 时直接返回原文（保证可运行）。
    """
    provider = (provider or settings.LLM_PROVIDER or "mock").lower()
    _, key, _ = resolve_llm()
    if provider == "mock" or not key:
        return raw_text or ""
    try:
        return await _real_expand(raw_text, target_duration, style)
    except Exception as exc:  # noqa: BLE001
        logger.warning("编剧扩写失败，回退原始文案: %s", exc)
        return raw_text or ""


async def _real_expand(raw_text: str, duration: float, style: str) -> str:
    base, key, model = resolve_llm()
    words = max(60, int(duration * 6))  # 中文约 6 字/秒
    system = _SCREENWRITER_TMPL.format(dur=int(duration), words=words, style=style)
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": (raw_text or "")[:8000]},
        ],
        "temperature": 0.8,
    }
    content = await _chat(base, key, payload)
    if not content:
        return raw_text or ""
    # 去掉可能的代码围栏残留
    content = content.strip()
    if content.startswith("```"):
        content = _first_json_blob(content) or content
    return content


# ---------------------------------------------------------------------------
# 视觉审校 Agent：可选调用视觉大模型打分（默认关闭）
# ---------------------------------------------------------------------------
async def vision_review(image_path: Path, prompt: str) -> dict:
    """调用视觉大模型对一帧图打分，返回 {pass:bool, score:float, reason:str}。

    未配置视觉模型时返回 pass=True（即不走真实视觉审校）。
    """
    base = (settings.VISION_BASE_URL or settings.LLM_BASE_URL or "").rstrip("/")
    key = settings.VISION_API_KEY or settings.LLM_API_KEY or settings.VOLC_API_KEY
    model = settings.VISION_MODEL
    if not (base and key and model):
        return {"pass": True, "score": 0.0, "reason": "vision disabled"}

    import base64

    suffix = image_path.suffix.lower()
    mime = "image/png" if suffix in (".png",) else "image/jpeg"
    b64 = base64.b64encode(image_path.read_bytes()).decode()
    data_uri = f"data:{mime};base64,{b64}"
    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": (
                            f"{prompt}\n只回复 JSON："
                            '{"pass": true/false, "score": 0-1, "reason": "..."}'
                        ),
                    },
                    {"type": "image_url", "image_url": {"url": data_uri}},
                ],
            }
        ],
        "temperature": 0.2,
    }
    try:
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                f"{base}/chat/completions",
                headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                json=payload,
            )
        if resp.status_code >= 400:
            return {"pass": True, "score": 0.0, "reason": f"vision http {resp.status_code}"}
        content = (resp.json().get("choices") or [{}])[0].get("message", {}).get("content", "")
        data = _extract_vision_json(content)
        return data
    except Exception as exc:  # noqa: BLE001
        logger.warning("视觉审校调用异常: %s", exc)
        return {"pass": True, "score": 0.0, "reason": f"vision error: {exc}"}


def _extract_vision_json(text: str) -> dict:
    raw = (text or "").strip()
    fence = re.match(r"^```(?:json)?\s*([\s\S]*?)\s*```$", raw)
    if fence:
        raw = fence.group(1).strip()
    blob = _first_json_blob(raw) or raw
    try:
        data = json.loads(blob)
    except Exception:  # noqa: BLE001
        return {"pass": True, "score": 0.0, "reason": "vision parse fail"}
    passed = bool(data.get("pass", True))
    try:
        score = float(data.get("score", 1.0))
    except Exception:  # noqa: BLE001
        score = 1.0
    return {"pass": passed, "score": score, "reason": str(data.get("reason", ""))[:200]}
