import { create } from "zustand";
import { api, type ProjectCreatePayload } from "@/lib/api";
import type { Project } from "@/types";

interface ProjectsState {
  projects: Project[];
  loading: boolean;
  error: string | null;
  fetch: () => Promise<void>;
  create: (data: ProjectCreatePayload) => Promise<Project>;
  removeFromCache: (id: string) => void;
}

export const useProjectsStore = create<ProjectsState>((set, get) => ({
  projects: [],
  loading: false,
  error: null,
  fetch: async () => {
    set({ loading: true, error: null });
    try {
      const projects = await api.getProjects();
      set({ projects, loading: false });
    } catch (e) {
      set({ error: (e as Error).message, loading: false });
    }
  },
  create: async (data) => {
    const project = await api.createProject(data);
    set({ projects: [project, ...get().projects] });
    return project;
  },
  removeFromCache: (id) =>
    set({ projects: get().projects.filter((p) => p.id !== id) }),
}));
