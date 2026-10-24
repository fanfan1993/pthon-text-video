import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { Clock, Film, ArrowUpRight } from "lucide-react";
import type { Project } from "@/types";
import { Card } from "@/components/ui/Card";
import { StatusBadge, Tag } from "@/components/ui/Badge";
import { formatDate, formatDuration } from "@/lib/format";

export function ProjectCard({ project }: { project: Project }) {
  const navigate = useNavigate();
  const tone =
    project.status === "completed"
      ? "from-emerald-500/20 to-accent-cyan/10"
      : project.status === "generating"
        ? "from-accent/25 to-accent-cyan/10"
        : "from-white/5 to-white/[0.02]";

  return (
    <motion.div
      whileHover={{ y: -4 }}
      transition={{ type: "spring", stiffness: 300, damping: 24 }}
    >
      <Card
        hover
        onClick={() => navigate(`/projects/${project.id}`)}
        className="cursor-pointer overflow-hidden"
      >
        <div className={`relative h-28 bg-gradient-to-br ${tone}`}>
          <div className="absolute inset-0 opacity-20 [background:radial-gradient(circle_at_30%_20%,#fff,transparent_40%)]" />
          <div className="absolute left-4 top-4">
            <StatusBadge status={project.status} />
          </div>
          <ArrowUpRight
            size={18}
            className="absolute right-4 top-4 text-slate-300/60 transition group-hover:text-white"
          />
          <Film size={26} className="absolute bottom-4 right-5 text-white/30" />
        </div>

        <div className="space-y-3 p-4">
          <h3 className="truncate font-display text-base font-semibold text-white">
            {project.title}
          </h3>
          <p className="line-clamp-2 min-h-[2.5rem] text-sm text-slate-400">
            {project.raw_input || "（暂无素材文本）"}
          </p>
          <div className="flex flex-wrap items-center gap-2 text-xs text-slate-400">
            <Tag>{project.style_preset}</Tag>
            <Tag>{project.aspect_ratio}</Tag>
            <span className="inline-flex items-center gap-1">
              <Clock size={12} />
              {formatDuration(project.target_duration)}
            </span>
            <span className="ml-auto text-slate-500">{formatDate(project.created_at)}</span>
          </div>
        </div>
      </Card>
    </motion.div>
  );
}
