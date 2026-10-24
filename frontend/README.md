# TextToVideo Studio · 前端

图文 / 小说转视频 Agent 的 Web 工作台。React 19 + TypeScript + Zustand + Tailwind CSS + Vite。

## 技术栈
- **React 19** + **TypeScript**（严格模式）
- **Zustand** 状态管理（项目列表 / 项目详情 / 实时流水线三仓）
- **React Router** 路由（工作台 + 项目详情）
- **Tailwind CSS** 影院风深色主题（玻璃拟态 + 双色辉光）
- **Framer Motion** 过渡动效
- **React Hook Form + Zod** 表单校验（保留输入、内联错误）
- 原生 **WebSocket** 订阅生成进度

## 目录结构
```
src/
  lib/         api.ts(类型+请求) · ws.ts(进度订阅) · cn.ts · constants.ts · format.ts
  types/       与后端 Pydantic Schema 对齐的领域类型
  store/       useProjectsStore · useProjectStore · usePipelineStore
  components/
    ui/        Button/Card/Input/Modal/Badge/Spinner
    layout/    AppShell · Sidebar
    pipeline/  PipelineRail（实时进度轨道，核心视觉记忆点）
    project/   ProjectCard · NewProjectModal
    character/ CharacterManager
    storyboard/StoryboardGrid
    common/    VideoPlayer · GenerateDialog
  pages/       Dashboard · ProjectDetail
```

## 运行
```bash
npm install
cp .env .env.local   # 默认走 Vite 代理（/api /media /ws -> :8000）
npm run dev          # http://localhost:5173
```
开发模式下前端请求经 Vite 代理转发到本地 FastAPI 后端（:8000），无需处理跨域；
媒体文件通过 `/media/...` 静态路径加载，进度经 `/ws/...` 推送。

直连后端时设置 `VITE_API_BASE=http://localhost:8000/api/v1`（媒体/WS 基址自动推导）。

## 构建
```bash
npm run build      # tsc --noEmit + vite build
npm run preview
```

## 与后端契约
- `GET  /api/v1/projects` 项目列表
- `POST /api/v1/projects` 新建项目
- `GET  /api/v1/projects/{id}` 项目详情
- `GET/POST /api/v1/projects/{id}/characters` 角色（POST 为 multipart：name/description/need_ai_image/file）
- `GET  /api/v1/projects/{id}/storyboards` 分镜
- `GET  /api/v1/projects/{id}/assets` 资产（图片/视频/音频路径）
- `POST /api/v1/projects/{id}/generate` 触发生成（JSON：provider/tts_engine/do_i2v/camera）
- `GET  /api/v1/tasks/{id}` 任务
- `WS   /api/v1/ws/projects/{id}/progress` 实时进度

> 默认 `mock` provider 无需任何 API Key 即可跑通整条流水线（占位出图 + Edge/静音配音）。
