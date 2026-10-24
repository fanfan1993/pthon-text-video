import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Plus, Sparkles, Loader2 } from "lucide-react";
import { useProjectsStore } from "@/store/useProjectsStore";
import { ProjectCard } from "@/components/project/ProjectCard";
import { NewProjectModal } from "@/components/project/NewProjectModal";
import { Button } from "@/components/ui/Button";

export function Dashboard() {
  const { projects, loading, fetch } = useProjectsStore();
  const [modalOpen, setModalOpen] = useState(false);

  useEffect(() => {
    fetch();
  }, [fetch]);

  return (
    <div className="space-y-8">
      {/* 英雄区 */}
      <section className="relative overflow-hidden rounded-3xl border border-white/10 bg-gradient-to-br from-accent/15 via-ink-800/40 to-transparent p-8 md:p-10">
        <div className="absolute -right-16 -top-16 h-56 w-56 rounded-full bg-accent-cyan/20 blur-3xl" />
        <div className="relative max-w-2xl space-y-4">
          <span className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs text-accent-cyan">
            <Sparkles size={13} /> 图文 / 小说 → 动态漫 / 短剧视频
          </span>
          <h1 className="font-display text-3xl font-bold leading-tight text-white md:text-4xl">
            把文字，<span className="text-gradient">变成会动的画面</span>
          </h1>
          <p className="max-w-xl text-[15px] leading-relaxed text-slate-400">
            粘贴一段小说或图文，平台自动分镜、锁定角色一致性、生成关键帧与镜头运动、配音合成，
            输出成片。先做 15 秒单镜，再扩到 1 分钟。
          </p>
          <Button size="lg" icon={<Plus size={18} />} onClick={() => setModalOpen(true)}>
            新建项目
          </Button>
        </div>
      </section>

      {/* 项目列表 */}
      <section className="space-y-4">
        <div className="flex items-end justify-between">
          <h2 className="font-display text-xl font-semibold text-white">我的项目</h2>
          <span className="text-sm text-slate-500">{projects.length} 个</span>
        </div>

        {loading ? (
          <div className="grid place-items-center py-20 text-slate-500">
            <Loader2 className="animate-spin" />
          </div>
        ) : projects.length === 0 ? (
          <div className="rounded-2xl border border-dashed border-white/10 py-20 text-center text-slate-500">
            还没有项目，点击右上角「新建项目」开始。
          </div>
        ) : (
          <motion.div
            initial="hidden"
            animate="show"
            variants={{ show: { transition: { staggerChildren: 0.05 } } }}
            className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3"
          >
            {projects.map((p) => (
              <motion.div
                key={p.id}
                variants={{ hidden: { opacity: 0, y: 12 }, show: { opacity: 1, y: 0 } }}
              >
                <ProjectCard project={p} />
              </motion.div>
            ))}
          </motion.div>
        )}
      </section>

      <NewProjectModal open={modalOpen} onClose={() => setModalOpen(false)} />
    </div>
  );
}
