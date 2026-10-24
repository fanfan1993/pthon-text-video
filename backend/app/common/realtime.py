"""实时进度通道（进程内 pub/sub）。

编排层 ``publish``，WebSocket 路由 ``subscribe``。
MVP 单进程足够；多 worker 场景应换 Redis pub/sub（见 README 备注）。
"""
from __future__ import annotations

import asyncio
from collections import defaultdict
from collections.abc import AsyncIterator
from typing import Any

_subscribers: dict[str, set[asyncio.Queue]] = defaultdict(set)


async def subscribe(project_id: str) -> AsyncIterator[Any]:
    """返回异步生成器，逐个产出该项目的进度消息。"""
    queue: asyncio.Queue = asyncio.Queue()
    _subscribers[project_id].add(queue)
    try:
        while True:
            yield await queue.get()
    finally:
        _subscribers[project_id].discard(queue)


async def publish(project_id: str, message: Any) -> None:
    """向该项目的所有订阅者推送一条进度（message 为可 model_dump 的对象）。"""
    for queue in list(_subscribers.get(project_id, set())):
        await queue.put(message)
