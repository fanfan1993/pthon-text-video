"""后端冒烟测试：导入应用、健康检查、创建项目。

运行：在 backend/ 目录下 ``pytest``（需先 ``pip install -r requirements.txt``）。
"""
from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def test_health() -> None:
    with TestClient(app) as client:
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"


def test_create_project() -> None:
    with TestClient(app) as client:
        resp = client.post(
            "/api/v1/projects",
            json={"title": "测试项目", "raw_input": "夜色中，少女撑伞而立。", "target_duration": 15},
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["id"]
        assert body["status"] == "draft"
