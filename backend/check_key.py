"""一键验 Key：检查方舟 Ark API Key + 三个模型是否可用。

用法：
    python check_key.py             # 测 LLM + 出图
    python check_key.py --video     # 再多测一个 图生视频 任务
    python check_key.py --models    # 只列出本账号可用的出图/视频模型 ID（不消耗额度）

错误码含义（关键）：
    401/403                       → Key 错误或未启用
    InvalidEndpointOrModel.NotFound → Model ID 写错/已下线（去 --models 查真实 ID）
    ModelNotOpen                  → ID 正确，但账号没开通（去「开通管理」点开通服务）
    SetLimitExceeded              → 触发用量上限（在开通管理里改上限）
退出码非 0 表示有失败项。
"""
from __future__ import annotations

import asyncio
import sys

import httpx

from app.config import get_settings
from app.services.llm_service import resolve_llm

settings = get_settings()
PASS = "✅"
FAIL = "❌"


def _h() -> dict:
    return {
        "Authorization": f"Bearer {settings.VOLC_API_KEY}",
        "Content-Type": "application/json",
    }


def _diagnose(text: str) -> str:
    if "ModelNotOpen" in text:
        return "模型 ID 正确但未开通 → 去控制台「开通管理」点该模型右侧的「开通服务」"
    if "InvalidEndpointOrModel" in text:
        return "Model ID 不存在或已下线 → 跑 python check_key.py --models 查当前有效 ID，填进 .env"
    if "SetLimitExceeded" in text:
        return "用量上限已触发 → 去「开通管理」把该模型的模型用量上限改大或移除"
    if "401" in text or "403" in text:
        return "Key 无效或无权限 → 检查「API Key 管理」里 Key 是否启用"
    return "见上方原始报错"


async def list_models() -> int:
    """列出本账号可见的出图/视频模型（有效 ID + 状态）。"""
    if not settings.VOLC_API_KEY:
        print(f"{FAIL} VOLC_API_KEY 为空")
        return 1
    url = f"{settings.VOLC_BASE_URL.rstrip('/')}/models"
    async with httpx.AsyncClient(timeout=30) as c:
        r = await c.get(url, headers=_h())
    if r.status_code >= 400:
        print(f"{FAIL} 拉取模型列表失败 HTTP {r.status_code}: {r.text[:300]}")
        return 1
    data = r.json().get("data", [])
    for kw, label in (("seedream", "出图 Seedream"), ("seedance", "视频 Seedance")):
        hits = [m for m in data if kw in m["id"].lower()]
        print(f"\n=== {label} ===")
        for m in sorted(hits, key=lambda x: x["id"]):
            st = m.get("status")
            mark = "可用" if st is None else st
            print(f"  {m['id']:44s} {mark}")
    print("\n提示：status=None 表示在售；Retiring/Shutdown 会 404，别用。")
    print(f"当前 .env：IMAGE_MODEL={settings.IMAGE_MODEL}  VIDEO_MODEL={settings.VIDEO_MODEL}")
    return 0


async def test_llm() -> tuple[bool, str]:
    base, key, model = resolve_llm()
    if not key:
        return False, "未配置 Key（VOLC_API_KEY / LLM_API_KEY 为空）"
    try:
        async with httpx.AsyncClient(timeout=60) as c:
            r = await c.post(
                f"{base}/chat/completions",
                headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": "用一句话介绍你自己"}],
                    "max_tokens": 64,
                },
            )
    except Exception as e:  # noqa: BLE001
        return False, f"请求异常: {e}"
    if r.status_code >= 400:
        return False, f"HTTP {r.status_code}: {r.text[:200]} → {_diagnose(r.text)}"
    content = (r.json().get("choices") or [{}])[0].get("message", {}).get("content", "")
    return True, f"模型 {model} 已通，回复: {content[:60]!r}"


async def test_image(real: bool = False) -> tuple[bool, str]:
    """real=False 时用最小请求探活（不追求出图效果）。"""
    if not settings.VOLC_API_KEY:
        return False, "VOLC_API_KEY 为空"
    url = f"{settings.VOLC_BASE_URL.rstrip('/')}/images/generations"
    body = {
        "model": settings.IMAGE_MODEL,
        "prompt": "一只戴草帽的橘猫，海边日落，简洁线条",
        "size": "2048x1152",   # Seedream 5.0：总像素 2359296，落在 [921600,4624220] 内
        "response_format": "url",
        "watermark": False,
    }
    try:
        async with httpx.AsyncClient(timeout=120) as c:
            r = await c.post(url, headers=_h(), json=body)
    except Exception as e:  # noqa: BLE001
        return False, f"请求异常: {e}"
    if r.status_code >= 400:
        return False, f"HTTP {r.status_code}: {r.text[:200]} → {_diagnose(r.text)}"
    items = r.json().get("data") or []
    if not items:
        return False, f"返回结构异常: {str(r.json())[:300]}"
    it = items[0]
    if it.get("url"):
        return True, f"出图 OK（{settings.IMAGE_MODEL}）: {it['url'][:56]}…"
    if it.get("b64_json"):
        return True, f"出图 OK（{settings.IMAGE_MODEL}）: 返回 b64，长度 {len(it['b64_json'])}"
    return False, f"返回无 url/b64: {str(it)[:200]}"


async def test_video() -> tuple[bool, str]:
    """创建任务即返回（不等生成完成），验证鉴权 + 模型开通。"""
    if not settings.VOLC_API_KEY:
        return False, "VOLC_API_KEY 为空"
    url = f"{settings.VOLC_BASE_URL.rstrip('/')}/contents/generations/tasks"
    # 1x1 占位 PNG 作首帧，仅验证接口与调度，不追求可看效果
    tiny = ("data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0l"
            "EQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==")
    legacy = "seedance-1-0" in (settings.VIDEO_MODEL or "")
    if legacy:
        content = [
            {"type": "text", "text": "一只猫在走路 --resolution 720p --duration 5"},
            {"type": "image_url", "image_url": {"url": tiny}, "role": "first_frame"},
        ]
        body = {"model": settings.VIDEO_MODEL, "content": content}
    else:
        body = {
            "model": settings.VIDEO_MODEL,
            "content": [
                {"type": "text", "text": "一只猫在走路"},
                {"type": "image_url", "image_url": {"url": tiny}},
            ],
            "resolution": "720p",
            "duration": 5,
            "ratio": "adaptive",
            "watermark": False,
            "generate_audio": False,
        }
    try:
        async with httpx.AsyncClient(timeout=90) as c:
            r = await c.post(url, headers=_h(), json=body)
    except Exception as e:  # noqa: BLE001
        return False, f"请求异常: {e}"
    if r.status_code >= 400:
        return False, f"HTTP {r.status_code}: {r.text[:200]} → {_diagnose(r.text)}"
    tid = r.json().get("id") or "?"
    return True, f"视频任务已创建（{settings.VIDEO_MODEL}），id={tid}"


async def main() -> int:
    if "--models" in sys.argv:
        return await list_models()

    print("=" * 62)
    print("方舟 Ark Key 自检")
    print("Key  :", (settings.VOLC_API_KEY[:8] + "…" + settings.VOLC_API_KEY[-4:])
          if settings.VOLC_API_KEY else "(空)")
    print("出图 :", settings.IMAGE_MODEL)
    print("视频 :", settings.VIDEO_MODEL)
    print("=" * 62)

    results = []
    for title, coro in [
        ("[1] LLM 分镜模型", test_llm()),
        ("[2] Seedream 出图", test_image()),
    ]:
        ok, msg = await coro
        results.append(ok)
        print(f"{PASS if ok else FAIL} {title}: {msg}")

    if "--video" in sys.argv:
        ok, msg = await test_video()
        results.append(ok)
        print(f"{PASS if ok else FAIL} [3] Seedance 视频: {msg}")

    print("-" * 62)
    if all(results):
        print("全部通过 ✅  可以直接跑真实 AI 视频了。")
        return 0
    print("存在失败项 ❌ 排查：")
    print("  • python check_key.py --models   查当前有效且未下线的 Model ID")
    print("  • 控制台「开通管理」→ 点模型右侧「开通服务」→ 状态变「已开通」")
    print("  • 改完 .env 需重启后端（uvicorn）才生效")
    return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
