"""服务层：按领域拆分的业务实现。

- ``providers/``：出图 / 出视频 Provider 抽象与各厂商实现；
- ``project_service``：视频流水线编排（分镜 → 出图 → 运镜 → 配音 → 合成）；
- ``image_service``：独立出图任务执行；
- ``character_service``：角色创建与「出图 → 角色」沉淀；
- ``llm_service`` / ``tts_service`` / ``ffmpeg_service``：单项能力封装。

约定：service 只依赖 models / schemas / utils，不依赖 FastAPI 的请求对象。
"""
