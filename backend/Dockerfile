# 后端镜像：同时用于 web(UVicorn) 与 worker(Celery)
FROM python:3.12-slim

WORKDIR /app

# 安装 ffmpeg（动态漫镜头运动 + 合成必需）
RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
