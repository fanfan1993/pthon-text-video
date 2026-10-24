import { useState, type ReactNode } from "react";
import { Menu, X } from "lucide-react";
import { AnimatePresence, motion } from "framer-motion";
import { Sidebar } from "./Sidebar";

export function AppShell({ children }: { children: ReactNode }) {
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <div className="relative z-10 flex min-h-screen">
      {/* 桌面侧边栏 */}
      <div className="hidden md:block">
        <Sidebar />
      </div>

      {/* 移动端抽屉 */}
      <AnimatePresence>
        {mobileOpen && (
          <>
            <motion.div
              className="fixed inset-0 z-40 bg-black/60 md:hidden"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setMobileOpen(false)}
            />
            <motion.div
              className="fixed inset-y-0 left-0 z-50 md:hidden"
              initial={{ x: "-100%" }}
              animate={{ x: 0 }}
              exit={{ x: "-100%" }}
              transition={{ type: "spring", stiffness: 320, damping: 32 }}
            >
              <Sidebar onNavigate={() => setMobileOpen(false)} />
            </motion.div>
          </>
        )}
      </AnimatePresence>

      <div className="flex min-w-0 flex-1 flex-col">
        {/* 顶部栏（移动端含菜单按钮） */}
        <header className="sticky top-0 z-30 flex h-16 items-center gap-3 border-b border-white/10 bg-ink-900/70 px-4 backdrop-blur-xl md:px-8">
          <button
            className="grid h-10 w-10 place-items-center rounded-lg text-slate-300 hover:bg-white/10 md:hidden focus-ring"
            onClick={() => setMobileOpen(true)}
            aria-label="打开菜单"
          >
            {mobileOpen ? <X size={20} /> : <Menu size={20} />}
          </button>
          <div className="flex items-center gap-2">
            <span className="font-display text-sm font-semibold tracking-wide text-slate-200">
              TextToVideo <span className="text-gradient">Studio</span>
            </span>
          </div>
          <div className="ml-auto flex items-center gap-2 text-xs text-slate-400">
            <span className="hidden sm:inline">本地 Docker · FastAPI</span>
            <span className="h-2 w-2 rounded-full bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.8)]" />
          </div>
        </header>

        <main className="flex-1 px-4 py-6 md:px-8 md:py-8">
          <div className="mx-auto w-full max-w-6xl">{children}</div>
        </main>
      </div>
    </div>
  );
}
