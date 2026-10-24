import { create } from "zustand";
import { api } from "@/lib/api";
import type {
  Asset,
  Character,
  GenerateRequest,
  Project,
  Storyboard,
} from "@/types";

interface ProjectState {
  project: Project | null;
  characters: Character[];
  storyboards: Storyboard[];
  assets: Asset[];
  loading: boolean;
  error: string | null;

  loadAll: (projectId: string) => Promise<void>;
  refreshProject: (projectId: string) => Promise<void>;
  addCharacter: (
    projectId: string,
    data: { name: string; description?: string; need_ai_image?: boolean; file?: File | null },
  ) => Promise<void>;
  generate: (projectId: string, opts: GenerateRequest) => Promise<void>;
}

async function loadDetail(projectId: string) {
  const [project, characters, storyboards, assets] = await Promise.all([
    api.getProject(projectId),
    api.getCharacters(projectId),
    api.getStoryboards(projectId),
    api.getAssets(projectId),
  ]);
  return { project, characters, storyboards, assets };
}

export const useProjectStore = create<ProjectState>((set, get) => ({
  project: null,
  characters: [],
  storyboards: [],
  assets: [],
  loading: false,
  error: null,

  loadAll: async (projectId) => {
    set({ loading: true, error: null });
    try {
      const data = await loadDetail(projectId);
      set({ ...data, loading: false });
    } catch (e) {
      set({ error: (e as Error).message, loading: false });
    }
  },

  refreshProject: async (projectId) => {
    const project = await api.getProject(projectId);
    set({ project });
  },

  addCharacter: async (projectId, data) => {
    const char = await api.createCharacter(projectId, data);
    set({ characters: [...get().characters, char] });
  },

  generate: async (projectId, opts) => {
    await api.generate(projectId, opts);
    // 触发后由组件订阅 WS 推进；这里把状态切到 generating
    const cur = get().project;
    if (cur) set({ project: { ...cur, status: "generating" } });
  },
}));
