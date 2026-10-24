"""多 Agent 协作的共享基础：黑板状态、消息总线、Agent 上下文与基类。

设计要点：
- ``PipelineState``（黑板）：所有 Agent 共享的可读写状态，是 Agent 间"协作"的载体。
- ``MessageBus``：Agent 之间用消息互通（发布/订阅式 transcript），同时可持久化为
  ``agent_transcript.json`` 供前端回看"五个 Agent 是怎么一起把视频做出来的"。
- ``AgentContext``：一次流水线运行所需的外部依赖（DB、Provider、配置、路径等）。
- ``Agent``：所有角色 Agent 的基类，只有一个 ``run`` 协程，签名统一为
  ``run(ctx, state, bus)``，便于 Coordinator 统一调度。
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class CharacterSpec:
    """角色在协作期的轻量表示（非 ORM，便于 Agent 间传递）。"""

    id: str
    name: str
    description: str = ""
    reference_images: list[str] = field(default_factory=list)  # 相对 MEDIA_ROOT 的路径
    cloud_lock_id: str | None = None
    cloud_lock_type: str = "none"
    need_ai_image: bool = False


@dataclass
class ShotSpec:
    """单镜在协作期的轻量表示。"""

    index: int
    scene_description: str = ""
    shot_type: str = "medium"
    camera_movement: str = "ken_burns"
    character_ids: list[str] = field(default_factory=list)
    dialogue: str = ""
    speaker_character_id: str | None = None
    image_prompt: str = ""
    duration: float = 5.0
    use_i2v: bool = False  # 由导演 Agent 决定
    status: str = "pending"
    keyframe_path: Path | None = None
    video_path: Path | None = None
    audio_path: Path | None = None
    review_notes: list[str] = field(default_factory=list)


@dataclass
class AgentMessage:
    """Agent 之间的一条消息（写入 transcript）。"""

    sender: str
    kind: str
    content: str
    shot_index: int | None = None
    ts: str = ""

    def __post_init__(self) -> None:
        if not self.ts:
            self.ts = datetime.now(timezone.utc).isoformat(timespec="seconds")


class MessageBus:
    """Agent 消息总线：顺序流水线里主要靠"共享状态 + 消息 transcript"协作。

    发布即追加到内存 transcript，并可选持久化到项目目录，方便回看。
    """

    def __init__(self, project_id: str, project_dir: Path) -> None:
        self.project_id = project_id
        self.project_dir = project_dir
        self._log: list[AgentMessage] = []

    def publish(
        self, sender: str, kind: str, content: str, *, shot_index: int | None = None
    ) -> AgentMessage:
        msg = AgentMessage(sender=sender, kind=kind, content=content, shot_index=shot_index)
        self._log.append(msg)
        return msg

    def transcript(self) -> list[dict]:
        return [vars(m) for m in self._log]

    def save(self) -> Path:
        path = self.project_dir / "agent_transcript.json"
        path.write_text(
            json.dumps(self.transcript(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return path


class PipelineState:
    """黑板（Blackboard）：所有 Agent 共享的流水线状态。"""

    def __init__(
        self,
        project_id: str,
        raw_input: str,
        style: str,
        aspect_ratio: str,
        target_duration: float,
        resolution: str,
    ) -> None:
        self.project_id = project_id
        self.raw_input = raw_input
        self.script = raw_input  # 编剧 Agent 会改写为扩写后的剧情
        self.style = style
        self.aspect_ratio = aspect_ratio
        self.target_duration = target_duration
        self.resolution = resolution
        self.characters: list[CharacterSpec] = []
        self.shots: list[ShotSpec] = []
        self.reviews: list[dict] = []


@dataclass
class AgentContext:
    """一次流水线运行所需的外部依赖（注入给每个 Agent）。"""

    db: Any
    provider: Any
    provider_name: str
    resolution: str
    media_root: Path
    project_dir: Path
    project: Any
    settings: Any
    do_i2v: bool
    tts_engine: str | None
    default_camera: str


class Agent:
    """所有角色 Agent 的基类。"""

    role: str = "agent"

    async def run(self, ctx: AgentContext, state: PipelineState, bus: MessageBus) -> None:
        raise NotImplementedError
