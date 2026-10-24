import { useEffect, useState } from "react";
import { Bot, Loader2, MessageSquareDashed, RefreshCw } from "lucide-react";
import { api } from "@/lib/api";
import type { AgentLogMessage } from "@/types";

// 每个 Agent 的身份配色（与影院深色主题一致）
const AGENT_META: Record<string, { dot: string; badge: string; text: string }> = {
  编剧: { dot: "bg-fuchsia-400", badge: "bg-fuchsia-500/15 text-fuchsia-300 border-fuchsia-500/30", text: "text-fuchsia-300" },
  角色设计师: { dot: "bg-rose-400", badge: "bg-rose-500/15 text-rose-300 border-rose-500/30", text: "text-rose-300" },
  分镜师: { dot: "bg-cyan-400", badge: "bg-cyan-500/15 text-cyan-300 border-cyan-500/30", text: "text-cyan-300" },
  导演: { dot: "bg-amber-400", badge: "bg-amber-500/15 text-amber-300 border-amber-500/30", text: "text-amber-300" },
  视觉审校: { dot: "bg-emerald-400", badge: "bg-emerald-500/15 text-emerald-300 border-emerald-500/30", text: "text-emerald-300" },
};

const DEFAULT_AGENT = { dot: "bg-slate-400", badge: "bg-slate-500/15 text-slate-300 border-slate-500/30", text: "text-slate-300" };

// 消息类型的标签配色
const KIND_META: Record<string, string> = {
  done: "bg-emerald-500/15 text-emerald-300 border-emerald-500/30",
  info: "bg-sky-500/15 text-sky-300 border-sky-500/30",
  plan: "bg-amber-500/15 text-amber-300 border-amber-500/30",
  review: "bg-violet-500/15 text-violet-300 border-violet-500/30",
  warn: "bg-orange-500/15 text-orange-300 border-orange-500/30",
  retry: "bg-orange-500/15 text-orange-300 border-orange-500/30",
  error: "bg-rose-500/15 text-rose-300 border-rose-500/30",
};

function fmtTime(ts: string): string {
  try {
    const d = new Date(ts);
    if (Number.isNaN(d.getTime())) return ts;
    return d.toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit", second: "2-digit" });
  } catch {
    return ts;
  }
}

function agentMeta(sender: string) {
  return AGENT_META[sender] ?? DEFAULT_AGENT;
}

export function AgentLogPanel({
  projectId,
  refreshToken,
}: {
  projectId: string;
  refreshToken?: string | number | null;
}) {
  const [logs, setLogs] = useState<AgentLogMessage[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;
    (async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await api.getAgentLog(projectId);
        if (!alive) return;
        setLogs(data ?? []);
      } catch (e) {
        if (!alive) return;
        // 后端在「没有记录」时返回 404
        setLogs([]);
        setError(e instanceof Error ? e.message : "加载失败");
      } finally {
        if (alive) setLoading(false);
      }
    })();
    return () => {
      alive = false;
    };
  }, [projectId, refreshToken]);

  if (loading) {
    return (
      <div className="grid place-items-center rounded-2xl glass py-16 text-slate-400">
        <Loader2 className="animate-spin" />
        <span className="mt-2 text-sm">正在读取 Agent 协作记录…</span>
      </div>
    );
  }

  if (logs.length === 0) {
    return (
      <div className="grid place-items-center rounded-2xl glass px-6 py-16 text-center text-slate-400">
        <MessageSquareDashed className="mb-3 opacity-60" size={28} />
        <p className="text-sm">{error ? `暂无记录：${error}` : "暂无 Agent 协作记录，请先运行一次生成"}</p>
        <p className="mt-1 text-xs text-slate-500">
          生成时，编剧 / 角色设计师 / 分镜师 / 导演 / 视觉审校 会通过消息总线协作，过程会记录在这里。
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-xs text-slate-500">参与 Agent：</span>
        {Object.entries(AGENT_META).map(([name, m]) => (
          <span key={name} className={`inline-flex items-center gap-1.5 rounded-md border px-2 py-0.5 text-xs ${m.badge}`}>
            <span className={`h-1.5 w-1.5 rounded-full ${m.dot}`} />
            {name}
          </span>
        ))}
      </div>

      <div className="rounded-2xl glass p-4">
        <ol className="relative space-y-4 before:absolute before:left-[7px] before:top-1 before:h-[calc(100%-0.5rem)] before:w-px before:bg-white/10">
          {logs.map((m, i) => {
            const meta = agentMeta(m.sender);
            const kindCls = KIND_META[m.kind] ?? "bg-slate-500/15 text-slate-300 border-slate-500/30";
            return (
              <li key={i} className="relative flex gap-3 pl-1">
                <span className={`relative z-10 mt-1.5 h-3.5 w-3.5 shrink-0 rounded-full border-2 border-[#0b0f1a] ${meta.dot}`} />
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className={`inline-flex items-center gap-1 rounded-md border px-2 py-0.5 text-xs font-medium ${meta.badge}`}>
                      <Bot size={12} /> {m.sender}
                    </span>
                    <span className={`rounded border px-1.5 py-0.5 text-[10px] uppercase tracking-wide ${kindCls}`}>
                      {m.kind}
                    </span>
                    {m.shot_index != null && (
                      <span className="rounded bg-white/5 px-1.5 py-0.5 text-[10px] text-slate-400">
                        镜 {m.shot_index}
                      </span>
                    )}
                    <span className="ml-auto text-[10px] tabular-nums text-slate-500">{fmtTime(m.ts)}</span>
                  </div>
                  <p className="mt-1 break-words text-sm leading-relaxed text-slate-300">{m.content}</p>
                </div>
              </li>
            );
          })}
        </ol>
      </div>

      <div className="flex items-center justify-between text-xs text-slate-500">
        <span>共 {logs.length} 条协作消息</span>
        <button
          className="inline-flex items-center gap-1 rounded-md border border-white/10 px-2 py-1 text-slate-300 transition hover:border-white/20 hover:text-white"
          onClick={() => {
            setLoading(true);
            api
              .getAgentLog(projectId)
              .then((d) => setLogs(d ?? []))
              .catch(() => setLogs([]))
              .finally(() => setLoading(false));
          }}
        >
          <RefreshCw size={12} /> 刷新
        </button>
      </div>
    </div>
  );
}
