import { useEffect, useState } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import {
  ArrowLeft,
  Play,
  RefreshCw,
  FileText,
  Settings2,
  Loader2,
  Bot,
  Clapperboard,
} from "lucide-react";
import { useProjectStore } from "@/store/useProjectStore";
import { usePipelineStore } from "@/store/usePipelineStore";
import { subscribeProgress } from "@/lib/ws";
import { PIPELINE_STAGES } from "@/lib/constants";
import { formatDate, formatDuration, truncate } from "@/lib/format";
import type { GenerateRequest, TaskStage, TaskStatus } from "@/types";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { StatusBadge, Tag } from "@/components/ui/Badge";
import { PipelineRail } from "@/components/pipeline/PipelineRail";
import { CharacterManager } from "@/components/character/CharacterManager";
import { StoryboardGrid } from "@/components/storyboard/StoryboardGrid";
import { VideoPlayer } from "@/components/common/VideoPlayer";
import { GenerateDialog } from "@/components/common/GenerateDialog";
import { AgentLogPanel } from "@/components/project/AgentLogPanel";

const allSuccess = (): Partial<Record<TaskStage, TaskStatus>> =>
  Object.fromEntries(PIPELINE_STAGES.map((s) => [s.key, "success"])) as Partial<
    Record<TaskStage, TaskStatus>
  >;

export function ProjectDetail() {
  const { projectId = "" } = useParams();
  const navigate = useNavigate();
  const { project, characters, storyboards, assets, loadAll, generate } =
    useProjectStore();
  const { reset, apply, setConnected, finalOutput, log } = usePipelineStore();
  const [genOpen, setGenOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const [mainTab, setMainTab] = useState<"storyboard" | "agents">("storyboard");

  // 载入详情 + 重置流水线状态
  useEffect(() => {
    let alive = true;
    (async () => {
      reset();
      await loadAll(projectId);
    })();
    return () => {
      alive = false;
    };
  }, [projectId, loadAll, reset]);

  // 已完成项目：直接把流水线标记为全成功并定位成片
  useEffect(() => {
    if (project?.status === "completed" && !log.length) {
      const final = assets.find((a) => a.shot_id === null && a.type === "video");
      usePipelineStore.setState({
        stageStatus: allSuccess(),
        finalOutput: final?.path ?? null,
      });
    }
  }, [project?.status, assets, log.length]);

  // 订阅实时进度（WebSocket）
  useEffect(() => {
    const unsub = subscribeProgress(
      projectId,
      (msg) => {
        apply(msg);
        if (msg.stage === "done" && msg.status === "success") {
          loadAll(projectId);
        } else if (msg.stage === "error") {
          loadAll(projectId);
        }
      },
      (connected) => setConnected(connected),
    );
    return unsub;
  }, [projectId, apply, setConnected, loadAll]);

  const onGenerate = async (opts: GenerateRequest) => {
    reset();
    setBusy(true);
    try {
      await generate(projectId, opts);
    } finally {
      setBusy(false);
    }
  };

  if (!project && storyboards.length === 0 && assets.length === 0) {
    // 首次加载占位
    return (
      <div className="grid place-items-center py-32 text-slate-500">
        <Loader2 className="animate-spin" />
      </div>
    );
  }

  const isGenerating = project?.status === "generating";
  const finalVideo =
    finalOutput || assets.find((a) => a.shot_id === null && a.type === "video")?.path;
  const showRail = isGenerating || Boolean(finalOutput) || log.length > 0;

  return (
    <div className="space-y-6">
      <Link
        to="/"
        className="inline-flex items-center gap-1.5 text-sm text-slate-400 hover:text-slate-200 focus-ring rounded"
      >
        <ArrowLeft size={15} /> 返回工作台
      </Link>

      {/* 头部 */}
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="space-y-2">
          <div className="flex items-center gap-3">
            <h1 className="font-display text-2xl font-bold text-white">
              {project?.title ?? "加载中…"}
            </h1>
            {project && <StatusBadge status={project.status} />}
          </div>
          <div className="flex flex-wrap gap-2 text-xs text-slate-400">
            <Tag>{project?.style_preset}</Tag>
            <Tag>{project?.aspect_ratio}</Tag>
            {project && <Tag>{formatDuration(project.target_duration)}</Tag>}
            {project && <span className="text-slate-500">{formatDate(project.created_at)}</span>}
          </div>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            icon={<RefreshCw size={15} />}
            onClick={() => loadAll(projectId)}
          >
            刷新
          </Button>
          <Button
            icon={<Play size={15} />}
            loading={busy}
            disabled={isGenerating}
            onClick={() => setGenOpen(true)}
          >
            {isGenerating ? "生成中…" : "生成视频"}
          </Button>
        </div>
      </div>

      {showRail && <PipelineRail />}

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* 主区 */}
        <div className="space-y-6 lg:col-span-2">
          {finalVideo && (
            <Card className="overflow-hidden">
              <div className="flex items-center justify-between border-b border-white/10 px-4 py-3">
                <span className="font-display text-sm font-semibold text-white">成片</span>
                <Tag className="text-emerald-300">输出完成</Tag>
              </div>
              <VideoPlayer src={finalVideo} className="aspect-video w-full bg-black" />
            </Card>
          )}

          {project?.raw_input && (
            <Card className="p-4">
              <div className="mb-2 flex items-center gap-2 text-sm font-medium text-slate-300">
                <FileText size={15} className="text-accent-cyan" /> 素材原文
              </div>
              <p className="whitespace-pre-wrap text-sm leading-relaxed text-slate-400">
                {project.raw_input}
              </p>
            </Card>
          )}

          <section className="space-y-3">
            {/* 主区标签：分镜视图 / 多 Agent 协作记录 */}
            <div className="flex items-center gap-1 rounded-xl border border-white/10 bg-white/5 p-1">
              <button
                type="button"
                onClick={() => setMainTab("storyboard")}
                className={`inline-flex flex-1 items-center justify-center gap-1.5 rounded-lg px-3 py-1.5 text-sm font-medium transition ${
                  mainTab === "storyboard"
                    ? "bg-white/10 text-white shadow-sm"
                    : "text-slate-400 hover:text-slate-200"
                }`}
              >
                <Clapperboard size={15} /> 分镜（{storyboards.length}）
              </button>
              <button
                type="button"
                onClick={() => setMainTab("agents")}
                className={`inline-flex flex-1 items-center justify-center gap-1.5 rounded-lg px-3 py-1.5 text-sm font-medium transition ${
                  mainTab === "agents"
                    ? "bg-white/10 text-white shadow-sm"
                    : "text-slate-400 hover:text-slate-200"
                }`}
              >
                <Bot size={15} /> Agent 协作记录
              </button>
            </div>

            {mainTab === "storyboard" ? (
              storyboards.length > 0 ? (
                <StoryboardGrid storyboards={storyboards} assets={assets} />
              ) : (
                <div className="grid place-items-center rounded-2xl glass px-6 py-16 text-center text-sm text-slate-400">
                  还没有分镜，点击右上角「生成视频」开始。
                </div>
              )
            ) : (
              <AgentLogPanel
                projectId={projectId}
                refreshToken={`${project?.status ?? ""}:${finalOutput ?? ""}`}
              />
            )}
          </section>
        </div>

        {/* 侧栏 */}
        <div className="space-y-6">
          <Card className="space-y-3 p-4">
            <div className="flex items-center gap-2 text-sm font-medium text-slate-300">
              <Settings2 size={15} className="text-accent-cyan" /> 项目信息
            </div>
            <dl className="space-y-2 text-sm">
              <div className="flex justify-between">
                <dt className="text-slate-500">项目 ID</dt>
                <dd className="font-mono text-xs text-slate-300">{truncate(project?.id ?? "", 18)}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-slate-500">风格</dt>
                <dd className="text-slate-300">{project?.style_preset}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-slate-500">画幅</dt>
                <dd className="text-slate-300">{project?.aspect_ratio}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-slate-500">时长</dt>
                <dd className="text-slate-300">
                  {project ? formatDuration(project.target_duration) : "—"}
                </dd>
              </div>
            </dl>
          </Card>

          <Card className="p-4">
            <CharacterManager projectId={projectId} />
          </Card>
        </div>
      </div>

      <GenerateDialog
        open={genOpen}
        onClose={() => setGenOpen(false)}
        onConfirm={onGenerate}
        busy={busy}
      />
    </div>
  );
}
