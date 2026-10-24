import { create } from "zustand";
import type { ProgressMessage, TaskStage, TaskStatus } from "@/types";
import { PIPELINE_STAGES } from "@/lib/constants";

interface PipelineState {
  stageStatus: Partial<Record<TaskStage, TaskStatus>>;
  log: ProgressMessage[];
  finalOutput: string | null;
  connected: boolean;
  error: string | null;

  reset: () => void;
  setConnected: (v: boolean) => void;
  apply: (msg: ProgressMessage) => void;
}

const emptyStageStatus = (): Partial<Record<TaskStage, TaskStatus>> =>
  Object.fromEntries(PIPELINE_STAGES.map((s) => [s.key, "pending"])) as Record<
    TaskStage,
    TaskStatus
  >;

export const usePipelineStore = create<PipelineState>((set, get) => ({
  stageStatus: emptyStageStatus(),
  log: [],
  finalOutput: null,
  connected: false,
  error: null,

  reset: () =>
    set({
      stageStatus: emptyStageStatus(),
      log: [],
      finalOutput: null,
      connected: false,
      error: null,
    }),

  setConnected: (v) => set({ connected: v }),

  apply: (msg) => {
    const next = { ...get().stageStatus };
    next[msg.stage] = msg.status;
    const log = [...get().log, msg].slice(-40);
    let finalOutput = get().finalOutput;
    let error = get().error;
    if (msg.stage === "done" && msg.status === "success" && msg.output) {
      finalOutput = msg.output;
    }
    if (msg.stage === "error") {
      error = msg.message || "生成失败";
    }
    set({ stageStatus: next, log, finalOutput, error });
  },
}));
