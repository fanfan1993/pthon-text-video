import type {
  AgentLogMessage,
  Asset,
  Character,
  GenerateRequest,
  ImageJob,
  Project,
  ProjectStatus,
  SaveAsCharacterPayload,
  SaveAsCharacterResult,
  Storyboard,
  Task,
} from "@/types";

const API_BASE = import.meta.env.VITE_API_BASE || "/api/v1";

// 媒体基址：若 API_BASE 为绝对地址（直连后端），则剥离 /api/v1 得到 host；
// 否则走同源（Vite 代理），基址为空串。
const MEDIA_BASE = API_BASE.startsWith("http")
  ? API_BASE.replace(/\/api\/v1\/?$/, "")
  : "";

function url(path: string): string {
  return `${API_BASE}${path}`;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url(path), {
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
    ...init,
  });
  if (!res.ok) {
    let detail = "";
    try {
      detail = (await res.json())?.detail ?? "";
    } catch {
      /* ignore */
    }
    throw new Error(detail || `请求失败 (${res.status})`);
  }
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

// 把后端资产相对路径拼成可访问的 URL
export function mediaUrl(path: string): string {
  if (!path) return "";
  if (path.startsWith("http")) return path;
  return `${MEDIA_BASE}/media/${path.replace(/^\/?media\//, "")}`;
}

// WebSocket 进度地址
export function wsUrl(projectId: string): string {
  const proto = window.location.protocol === "https:" ? "wss" : "ws";
  if (API_BASE.startsWith("http")) {
    const host = API_BASE.replace(/^https?:\/\//, "").replace(/\/api\/v1\/?$/, "");
    return `${proto}://${host}/api/v1/ws/projects/${projectId}/progress`;
  }
  // 同源：走 Vite 代理 /ws
  return `${proto}://${window.location.host}/api/v1/ws/projects/${projectId}/progress`;
}

// ---------- 项目 ----------
export interface ProjectCreatePayload {
  title?: string;
  source_type?: string;
  raw_input?: string;
  style_preset?: string;
  aspect_ratio?: string;
  target_duration?: number;
}

export const api = {
  getProjects: () => request<Project[]>("/projects"),
  createProject: (data: ProjectCreatePayload) =>
    request<Project>("/projects", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  getProject: (id: string) => request<Project>(`/projects/${id}`),
  generate: (id: string, opts: GenerateRequest) =>
    request<{ project_id: string; status: string; opts: GenerateRequest }>(
      `/projects/${id}/generate`,
      { method: "POST", body: JSON.stringify(opts) },
    ),

  // ---------- 角色 ----------
  getCharacters: (id: string) =>
    request<Character[]>(`/projects/${id}/characters`),
  createCharacter: async (
    projectId: string,
    data: { name: string; description?: string; need_ai_image?: boolean; file?: File | null },
  ): Promise<Character> => {
    const form = new FormData();
    form.append("name", data.name);
    form.append("description", data.description ?? "");
    form.append("need_ai_image", String(Boolean(data.need_ai_image)));
    if (data.file) form.append("file", data.file);
    const res = await fetch(url(`/projects/${projectId}/characters`), {
      method: "POST",
      body: form,
    });
    if (!res.ok) {
      const detail = (await res.json().catch(() => ({})))?.detail ?? "角色创建失败";
      throw new Error(detail);
    }
    return (await res.json()) as Character;
  },

  // ---------- 分镜 / 资产 / 任务 ----------
  getStoryboards: (id: string) =>
    request<Storyboard[]>(`/projects/${id}/storyboards`),
  getAssets: (id: string) => request<Asset[]>(`/projects/${id}/assets`),
  getTask: (id: string) => request<Task>(`/tasks/${id}`),

  /** 回看某次生成里「多 Agent 协作」的消息记录（无记录时抛 404）。 */
  getAgentLog: (id: string) =>
    request<AgentLogMessage[]>(`/projects/${id}/agent-log`),

  // ---------- 独立出图 ----------
  listImageJobs: () => request<ImageJob[]>("/image-gen"),
  getImageJob: (id: string) => request<ImageJob>(`/image-gen/${id}`),
  createImageJob: async (data: {
    prompt: string;
    resolution?: string;
    count?: number;
    provider?: string | null;
    refImages?: File[];
  }): Promise<ImageJob> => {
    const form = new FormData();
    form.append("prompt", data.prompt);
    form.append("resolution", data.resolution ?? "2K");
    form.append("count", String(data.count ?? 1));
    if (data.provider) form.append("provider", data.provider);
    (data.refImages ?? []).forEach((f) => form.append("ref_images", f));
    const res = await fetch(url("/image-gen"), { method: "POST", body: form });
    if (!res.ok) {
      const detail = (await res.json().catch(() => ({})))?.detail ?? "出图失败";
      throw new Error(detail);
    }
    return (await res.json()) as ImageJob;
  },

  /** 把出图结果存为角色设定（可选同时喂进视频流水线）。 */
  saveImageAsCharacter: (jobId: string, data: SaveAsCharacterPayload) =>
    request<SaveAsCharacterResult>(`/image-gen/${jobId}/to-character`, {
      method: "POST",
      body: JSON.stringify(data),
    }),
};

export type {
  Project,
  ProjectStatus,
  Storyboard,
  Character,
  Asset,
  Task,
  ImageJob,
  SaveAsCharacterPayload,
  SaveAsCharacterResult,
  AgentLogMessage,
};
