"""WebSocket 实时进度。"""
from __future__ import annotations

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.common.realtime import subscribe

router = APIRouter()


@router.websocket("/ws/projects/{project_id}/progress")
async def ws_progress(websocket: WebSocket, project_id: str) -> None:
    """订阅项目进度，实时推送阶段状态与成片路径。"""
    await websocket.accept()
    try:
        async for message in subscribe(project_id):
            await websocket.send_json(message.model_dump())
    except WebSocketDisconnect:
        pass
