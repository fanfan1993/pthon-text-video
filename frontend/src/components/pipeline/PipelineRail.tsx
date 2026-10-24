import {
  FileText,
  Image as ImageIcon,
  Film,
  Mic,
  Wand2,
  CheckCircle2,
  Loader2,
  AlertTriangle,
  Wifi,
  WifiOff,
} from "lucide-react";
import { motion } from "framer-motion";
import { cn } from "@/lib/cn";
import { PIPELINE_STAGES } from "@/lib/constants";
import { usePipelineStore } from "@/store/usePipelineStore";
import type { TaskStage, TaskStatus } from "@/types";

const ICONS: Record<TaskStage, typeof FileText> = {
  storyboard: FileText,
  imagen: ImageIcon,
  animation: Film,
  tts: Mic,
  composite: Wand2,
  done: CheckCircle2,
  error: AlertTriangle,
};

function StageNode({
  stage,
  status,
  active,
}: {
  stage: TaskStage;
  status?: TaskStatus;
  active: boolean;
}) {
  const Icon = ICONS[stage] ?? CheckCircle2;
  const done = status === "success";
  const failed = status === "failed";
  const running = status === "running" || active;

  return (
    <div className="flex flex-1 flex-col items-center gap-2">
      <motion.div
        initial={false}
        animate={
          running
            ? { scale: [1, 1.08, 1], boxShadow: "0 0 24px rgba(124,92,255,0.6)" }
            : { scale: 1 }
        }
        transition={{ duration: 1.4, repeat: running ? Infinity : 0 }}
        className={cn(
          "grid h-12 w-12 place-items-center rounded-2xl border transition-colors",
          done && "border-emerald-400/40 bg-emerald-400/15 text-emerald-300",
          failed && "border-rose-500/40 bg-rose-500/15 text-rose-300",
          running && !done && "border-accent/60 bg-accent/15 text-accent-soft",
          !done && !failed && !running && "border-white/10 bg-white/5 text-slate-500",
        )}
      >
        {running && !done ? (
          <Loader2 size={20} className="animate-spin" />
        ) : (
          <Icon size={20} />
        )}
      </motion.div>
    </div>
  );
}

export function PipelineRail() {
  const { stageStatus, log, connected, error, finalOutput } = usePipelineStore();

  const stages = PIPELINE_STAGES;
  const total = stages.length;
  const completed = stages.filter((s) => stageStatus[s.key] === "success").length;
  const hasError = Boolean(error) || stageStatus.error === "failed";
  const overall = hasError ? 1 : Math.max(completed / (total - 1), finalOutput ? 1 : 0);

  return (
    <div className="glass rounded-2xl p-5 shadow-card">
      <div className="mb-4 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="font-display text-sm font-semibold text-white">生成流水线</span>
          <span className="text-xs text-slate-400">
            {completed}/{total - 1} 阶段完成
          </span>
        </div>
        <span
          className={cn(
            "inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs",
            connected
              ? "bg-emerald-400/10 text-emerald-300"
              : "bg-rose-500/10 text-rose-300",
          )}
        >
          {connected ? <Wifi size={13} /> : <WifiOff size={13} />}
          {connected ? "实时连接" : "未连接"}
        </span>
      </div>

      {/* 阶段节点 + 连接线 */}
      <div className="flex items-start">
        {stages.map((s, i) => {
          const status = stageStatus[s.key];
          const active = status === "running";
          const isLast = i === stages.length - 1;
          const prevDone = i > 0 && stageStatus[stages[i - 1].key] === "success";
          return (
            <div key={s.key} className="flex flex-1 flex-col items-center">
              <StageNode stage={s.key} status={status} active={active} />
              <span className="mt-2 text-center text-xs font-medium text-slate-300">
                {s.label}
              </span>
              {!isLast && (
                <div className="-mt-[52px] ml-[60%] h-[3px] w-full rounded-full bg-white/10">
                  <div
                    className={cn(
                      "h-full rounded-full transition-all duration-500",
                      prevDone ? "bg-emerald-400/70 w-full" : "w-0",
                    )}
                  />
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* 总进度 */}
      <div className="mt-5 h-1.5 w-full overflow-hidden rounded-full bg-white/10">
        <div
          className={cn(
            "h-full rounded-full transition-[width] duration-500",
            hasError ? "bg-rose-500" : "bg-accent-gradient",
          )}
          style={{ width: `${Math.round(overall * 100)}%` }}
        />
      </div>

      {/* 实时日志 */}
      <div className="mt-4 max-h-40 space-y-1 overflow-y-auto font-mono text-xs">
        {log.length === 0 && (
          <p className="text-slate-500">等待进度消息…</p>
        )}
        {log
          .slice()
          .reverse()
          .map((m, idx) => (
            <p key={idx} className="flex gap-2 text-slate-400">
              <span className="text-slate-600">›</span>
              <span className="text-slate-300">{m.stage}</span>
              <span className="text-slate-500">[{m.status}]</span>
              {m.message && <span className="truncate text-slate-400">{m.message}</span>}
            </p>
          ))}
      </div>

      {error && (
        <p className="mt-3 rounded-lg border border-rose-500/30 bg-rose-500/10 px-3 py-2 text-sm text-rose-300">
          {error}
        </p>
      )}
    </div>
  );
}
