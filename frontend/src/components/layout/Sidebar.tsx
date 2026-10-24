import { NavLink } from "react-router-dom";
import { Clapperboard, Image as ImageIcon, LayoutDashboard, Sparkles } from "lucide-react";
import { cn } from "@/lib/cn";

const NAV = [
  { to: "/", label: "工作台", icon: LayoutDashboard, end: true },
  { to: "/image-gen", label: "出图工坊", icon: ImageIcon, end: false },
];

export function Sidebar({ onNavigate }: { onNavigate?: () => void }) {
  return (
    <aside className="flex h-full w-64 flex-col gap-2 border-r border-white/10 bg-ink-800/60 px-4 py-6 backdrop-blur-xl">
      <div className="flex items-center gap-3 px-2">
        <div className="grid h-10 w-10 place-items-center rounded-xl bg-accent-gradient shadow-glow">
          <Clapperboard size={20} className="text-white" />
        </div>
        <div className="leading-tight">
          <p className="font-display text-[15px] font-semibold text-white">TextToVideo</p>
          <p className="text-[11px] text-slate-400">Studio · 图文转视频</p>
        </div>
      </div>

      <nav className="mt-6 flex flex-col gap-1">
        {NAV.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.end}
            onClick={onNavigate}
            className={({ isActive }) =>
              cn(
                "group flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition focus-ring",
                isActive
                  ? "bg-white/[0.07] text-white shadow-[inset_0_0_0_1px_rgba(124,92,255,0.4)]"
                  : "text-slate-400 hover:bg-white/5 hover:text-slate-100",
              )
            }
          >
            <item.icon size={18} className="shrink-0" />
            {item.label}
          </NavLink>
        ))}
      </nav>

      <div className="mt-auto rounded-xl border border-white/10 bg-white/[0.03] p-3 text-xs text-slate-400">
        <div className="flex items-center gap-2 text-slate-300">
          <Sparkles size={14} className="text-accent-cyan" />
          动态漫优先 · 跨集一致
        </div>
        <p className="mt-1.5 leading-relaxed">
          角色锁定 + FFmpeg 镜头运动，零边际成本产出 15s 单镜。
        </p>
      </div>
    </aside>
  );
}
