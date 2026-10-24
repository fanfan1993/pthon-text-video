import type {
  CameraMovement,
  ProjectStatus,
  TaskStage,
  TaskStatus,
} from "@/types";

// 流水线阶段（与设计稿 2 / 后端 TaskStage 对齐，并补 done/error 终态）
export const PIPELINE_STAGES: { key: TaskStage; label: string; hint: string }[] = [
  { key: "storyboard", label: "剧本分镜", hint: "LLM 拆解镜头与对白" },
  { key: "imagen", label: "角色出图", hint: "按角色锁定生成关键帧" },
  { key: "animation", label: "镜头运动", hint: "FFmpeg 推拉摇移 / 视差" },
  { key: "tts", label: "语音配音", hint: "旁白与对白合成" },
  { key: "composite", label: "合成成片", hint: "音画对齐并拼接" },
  { key: "done", label: "完成", hint: "输出最终视频" },
];

export const CAMERA_OPTIONS: { value: CameraMovement; label: string }[] = [
  { value: "ken_burns", label: "Ken Burns 缓动" },
  { value: "pan", label: "平移" },
  { value: "parallax", label: "分层视差" },
  { value: "none", label: "静态定格" },
];

export const PROVIDER_OPTIONS: { value: string; label: string }[] = [
  { value: "mock", label: "Mock（无需 Key）" },
  { value: "jimeng", label: "即梦 Seedance" },
  { value: "kling", label: "可灵" },
  { value: "volc", label: "火山 Seedance-mini" },
];

export const STATUS_META: Record<
  ProjectStatus,
  { label: string; className: string; dot: string }
> = {
  draft: {
    label: "草稿",
    className: "text-slate-300 bg-white/5 border-white/10",
    dot: "bg-slate-400",
  },
  generating: {
    label: "生成中",
    className: "text-accent-cyan bg-accent-cyan/10 border-accent-cyan/30",
    dot: "bg-accent-cyan animate-pulse-glow",
  },
  completed: {
    label: "已完成",
    className: "text-emerald-300 bg-emerald-400/10 border-emerald-400/30",
    dot: "bg-emerald-400",
  },
  failed: {
    label: "失败",
    className: "text-rose-300 bg-rose-500/10 border-rose-500/30",
    dot: "bg-rose-500",
  },
};

export const TASK_STATUS_LABEL: Record<TaskStatus, string> = {
  pending: "等待",
  running: "进行中",
  success: "成功",
  failed: "失败",
  manual_review: "待人工",
  cancelled: "已取消",
};

export const CAMERA_LABEL: Record<CameraMovement, string> = {
  ken_burns: "Ken Burns",
  pan: "平移",
  parallax: "视差",
  none: "静态",
};
