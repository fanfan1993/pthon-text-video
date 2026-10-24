// 与后端 Pydantic Schema 对齐的领域模型类型。
// 字段命名与序列化值保持一致（枚举用字符串字面量）。

export type ProjectStatus = "draft" | "generating" | "completed" | "failed";
export type SourceType = "novel" | "image_text";
export type CloudLockType = "jimeng_role_id" | "kling_subject" | "none";
export type CameraMovement = "ken_burns" | "pan" | "parallax" | "none";
export type ShotStatus = "pending" | "done" | "failed";
export type AssetType = "image" | "video" | "audio";
export type AssetSource = "generated" | "uploaded";

export type TaskStage =
  | "storyboard"
  | "imagen"
  | "animation"
  | "tts"
  | "composite"
  | "done"
  | "error";

export type TaskStatus =
  | "pending"
  | "running"
  | "success"
  | "failed"
  | "manual_review"
  | "cancelled";

export interface Project {
  id: string;
  title: string;
  source_type: SourceType;
  raw_input: string;
  status: ProjectStatus;
  target_duration: number;
  aspect_ratio: string;
  style_preset: string;
  created_at: string;
}

export interface Character {
  id: string;
  project_id: string;
  name: string;
  description: string;
  reference_images: string[];
  cloud_lock_type: CloudLockType;
  cloud_lock_id: string | null;
  need_ai_image: boolean;
}

export interface Storyboard {
  id: string;
  project_id: string;
  index: number;
  scene_description: string;
  shot_type: string;
  camera_movement: CameraMovement;
  character_ids: string[];
  dialogue: string;
  speaker_character_id: string | null;
  image_prompt: string;
  duration: number;
  status: ShotStatus;
  keyframe_asset_id: string | null;
  video_asset_id: string | null;
  audio_asset_id: string | null;
}

export interface Asset {
  id: string;
  project_id: string;
  shot_id: string | null;
  type: AssetType;
  path: string;
  source: AssetSource;
  meta_json: Record<string, unknown>;
}

export interface Task {
  id: string;
  project_id: string;
  shot_id: string | null;
  stage: TaskStage;
  status: TaskStatus;
  external_job_id: string | null;
  retry_count: number;
  error_msg: string | null;
  updated_at: string;
}

export interface GenerateRequest {
  provider?: string | null;
  tts_engine?: string | null;
  do_i2v?: boolean;
  camera?: CameraMovement | "ken_burns";
}

export type ImageJobStatus = "pending" | "running" | "completed" | "failed";

export interface ImageJob {
  id: string;
  prompt: string;
  negative_prompt: string;
  resolution: string;
  count: number;
  provider: string;
  status: ImageJobStatus;
  result_paths: string[];
  ref_paths: string[];
  error_msg: string | null;
  created_at: string;
}

export interface SaveAsCharacterPayload {
  /** 用出图任务里的第几张（0-based） */
  image_index?: number;
  /** 目标项目：传 project_id 复用；都不传则用 project_title 新建 */
  project_id?: string | null;
  project_title?: string | null;
  project_input?: string | null;
  name?: string;
  description?: string;
  lock_role?: boolean;
  start_pipeline?: boolean;
  provider?: string | null;
  camera?: CameraMovement;
  do_i2v?: boolean;
}

export interface SaveAsCharacterResult {
  project_id: string;
  project_title: string;
  character: Character;
  image_path: string;
  locked: boolean;
  pipeline_queued: boolean;
  created_project: boolean;
}

export interface ProgressMessage {
  stage: TaskStage;
  shot_index?: number | null;
  status: TaskStatus;
  progress: number;
  message?: string;
  output?: string | null;
}

/** 多 Agent 协作记录中的一条消息（对应后端 agent_transcript.json）。 */
export interface AgentLogMessage {
  /** 发送方 Agent 名称，如 编剧 / 角色设计师 / 分镜师 / 导演 / 视觉审校 */
  sender: string;
  /** 消息类型，如 done / info / plan / review / warn / error */
  kind: string;
  /** 消息正文 */
  content: string;
  /** 关联镜头序号（审校/导演逐镜决策时有值） */
  shot_index: number | null;
  /** ISO 时间戳（UTC，秒级） */
  ts: string;
}
