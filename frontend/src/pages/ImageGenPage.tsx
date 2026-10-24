import { useEffect, useRef, useState } from "react";
import { motion } from "framer-motion";
import {
  Film,
  ImagePlus,
  Loader2,
  Sparkles,
  Trash2,
  UserPlus,
  Wand2,
  AlertTriangle,
} from "lucide-react";
import { api, mediaUrl } from "@/lib/api";
import type { ImageJob } from "@/types";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Field, Select, Textarea } from "@/components/ui/Input";
import { SaveAsCharacterModal } from "@/components/image/SaveAsCharacterModal";
import { cn } from "@/lib/cn";

const RESOLUTION_OPTIONS = [
  { value: "1K", label: "1K（最快）" },
  { value: "1.5K", label: "1.5K（均衡）" },
  { value: "2K", label: "2K（最清晰）" },
];
const COUNT_OPTIONS = [1, 2, 3, 4];

export function ImageGenPage() {
  const [prompt, setPrompt] = useState("");
  const [resolution, setResolution] = useState("2K");
  const [count, setCount] = useState(1);
  const [refs, setRefs] = useState<File[]>([]);
  const [current, setCurrent] = useState<ImageJob | null>(null);
  const [history, setHistory] = useState<ImageJob[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  // 「存为角色 / 喂进视频项目」弹窗：记录选中的图与默认模式
  const [link, setLink] = useState<{ index: number; path: string; mode: "character" | "video" } | null>(
    null,
  );
  const timer = useRef<number | undefined>(undefined);

  const loadHistory = async () => {
    try {
      setHistory(await api.listImageJobs());
    } catch {
      /* 忽略历史加载失败 */
    }
  };

  useEffect(() => {
    loadHistory();
    return () => window.clearInterval(timer.current);
  }, []);

  const poll = (id: string) => {
    window.clearInterval(timer.current);
    timer.current = window.setInterval(async () => {
      try {
        const j = await api.getImageJob(id);
        setCurrent(j);
        if (j.status === "completed" || j.status === "failed") {
          window.clearInterval(timer.current);
          loadHistory();
        }
      } catch {
        /* 轮询容错 */
      }
    }, 2000);
  };

  const onSubmit = async () => {
    if (!prompt.trim()) {
      setError("请输入出图提示词");
      return;
    }
    setError("");
    setLoading(true);
    try {
      const job = await api.createImageJob({ prompt, resolution, count, refImages: refs });
      setCurrent(job);
      setRefs([]);
      poll(job.id);
    } catch (e) {
      setError((e as Error).message || "出图请求失败");
    } finally {
      setLoading(false);
    }
  };

  const onPickRefs = (files: FileList | null) => {
    if (!files) return;
    setRefs((prev) => [...prev, ...Array.from(files)]);
  };

  const removeRef = (i: number) => setRefs((prev) => prev.filter((_, idx) => idx !== i));

  const running = current?.status === "pending" || current?.status === "running";

  return (
    <div className="space-y-8">
      {/* 头部 */}
      <section className="relative overflow-hidden rounded-3xl border border-white/10 bg-gradient-to-br from-accent/15 via-ink-800/40 to-transparent p-8">
        <div className="absolute -right-16 -top-16 h-56 w-56 rounded-full bg-accent-cyan/20 blur-3xl" />
        <div className="relative max-w-2xl space-y-3">
          <span className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs text-accent-cyan">
            <ImagePlus size={13} /> 独立出图 · 不走视频流水线
          </span>
          <h1 className="font-display text-3xl font-bold leading-tight text-white">
            出图工坊
          </h1>
          <p className="text-[15px] leading-relaxed text-slate-400">
            把一句话、一段角色设定或参考图，直接生成关键帧图。可一次出多张，
            传参考图后多张会共享同一参考，保证角色一致。
            <br />
            满意的图可一键<span className="text-slate-200">存为角色设定</span>或
            <span className="text-slate-200">直接喂进视频项目</span>——图片会作为角色锚点参与整条流水线。
          </p>
        </div>
      </section>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-[380px_1fr]">
        {/* 左侧配置 */}
        <div className="space-y-4">
          <Card strong className="p-5">
            <div className="space-y-4">
              <Field label="出图提示词">
                <Textarea
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                  placeholder="例如：黑长直发少女，米白色风衣，霓虹都市雨夜，宫崎骏动画风，全身像"
                  className="min-h-[120px]"
                />
              </Field>

              <div className="grid grid-cols-2 gap-3">
                <Field label="分辨率档位">
                  <Select value={resolution} onChange={(e) => setResolution(e.target.value)}>
                    {RESOLUTION_OPTIONS.map((o) => (
                      <option key={o.value} value={o.value}>
                        {o.label}
                      </option>
                    ))}
                  </Select>
                </Field>
                <Field label="出图张数">
                  <Select value={count} onChange={(e) => setCount(Number(e.target.value))}>
                    {COUNT_OPTIONS.map((c) => (
                      <option key={c} value={c}>
                        {c} 张
                      </option>
                    ))}
                  </Select>
                </Field>
              </div>

              <Field label="参考图（可选）" hint="上传角色设定图，生成图会与之保持一致">
                <label className="flex cursor-pointer flex-col items-center justify-center gap-2 rounded-xl border border-dashed border-white/15 bg-white/[0.02] px-4 py-6 text-center text-sm text-slate-400 transition hover:border-accent-cyan/40 hover:text-slate-200">
                  <ImagePlus size={20} />
                  点击或拖拽上传（可多张）
                  <input
                    type="file"
                    accept="image/*"
                    multiple
                    className="hidden"
                    onChange={(e) => onPickRefs(e.target.files)}
                  />
                </label>
              </Field>

              {refs.length > 0 && (
                <div className="flex flex-wrap gap-2">
                  {refs.map((f, i) => (
                    <div
                      key={`${f.name}-${i}`}
                      className="group relative h-16 w-16 overflow-hidden rounded-lg border border-white/10"
                    >
                      <img
                        src={URL.createObjectURL(f)}
                        alt={f.name}
                        className="h-full w-full object-cover"
                      />
                      <button
                        type="button"
                        onClick={() => removeRef(i)}
                        className="absolute right-0.5 top-0.5 grid h-5 w-5 place-items-center rounded-full bg-black/60 text-white opacity-0 transition group-hover:opacity-100"
                      >
                        <Trash2 size={11} />
                      </button>
                    </div>
                  ))}
                </div>
              )}

              {error && <p className="text-xs text-rose-400">{error}</p>}

              <Button
                size="lg"
                className="w-full"
                loading={loading}
                icon={<Wand2 size={18} />}
                onClick={onSubmit}
              >
                {loading ? "提交中…" : "开始出图"}
              </Button>
              <p className="text-center text-xs text-slate-500">
                当前引擎：火山 Seedream（默认 provider，自动回退 Mock）
              </p>
            </div>
          </Card>
        </div>

        {/* 右侧结果 */}
        <div className="space-y-6">
          <Card className="p-5">
            <div className="mb-4 flex items-center gap-2">
              <Sparkles size={16} className="text-accent-cyan" />
              <h2 className="font-display text-lg font-semibold text-white">出图结果</h2>
            </div>

            {!current && (
              <div className="grid place-items-center rounded-2xl border border-dashed border-white/10 py-20 text-center text-slate-500">
                还没有生成任务，左侧输入提示词后点击「开始出图」
              </div>
            )}

            {current && running && (
              <div className="grid place-items-center py-20 text-slate-400">
                <Loader2 className="mb-3 animate-spin text-accent-cyan" size={28} />
                <p>生成中…（{current.status === "pending" ? "排队中" : "出图中"}）</p>
              </div>
            )}

            {current && current.status === "failed" && (
              <div className="flex items-start gap-3 rounded-2xl border border-rose-500/30 bg-rose-500/10 p-4 text-rose-200">
                <AlertTriangle size={18} className="mt-0.5 shrink-0" />
                <p className="text-sm">
                  出图失败：{current.error_msg || "未知错误"}
                  <br />
                  常见原因：模型未开通 / API Key 失效 / 参考图过大。
                </p>
              </div>
            )}

            {current && current.status === "completed" && (
              <motion.div
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                className="grid grid-cols-2 gap-3 sm:grid-cols-3"
              >
                {current.result_paths.map((p, i) => (
                  <div
                    key={p}
                    className="group relative aspect-square overflow-hidden rounded-xl border border-white/10"
                  >
                    <a href={mediaUrl(p)} target="_blank" rel="noreferrer">
                      <img
                        src={mediaUrl(p)}
                        alt={`生成结果 ${i + 1}`}
                        className="h-full w-full object-cover transition group-hover:scale-105"
                      />
                    </a>
                    {/* 悬浮操作：把这张图变成角色 / 直接喂进视频项目 */}
                    <div className="absolute inset-x-0 bottom-0 flex gap-1.5 bg-gradient-to-t from-black/85 via-black/55 to-transparent p-2 opacity-0 transition group-hover:opacity-100">
                      <button
                        type="button"
                        onClick={() => setLink({ index: i, path: p, mode: "character" })}
                        className="inline-flex flex-1 items-center justify-center gap-1 rounded-lg bg-white/15 px-2 py-1.5 text-[12px] text-white backdrop-blur transition hover:bg-white/25"
                      >
                        <UserPlus size={13} /> 存为角色
                      </button>
                      <button
                        type="button"
                        onClick={() => setLink({ index: i, path: p, mode: "video" })}
                        className="inline-flex flex-1 items-center justify-center gap-1 rounded-lg bg-accent-gradient px-2 py-1.5 text-[12px] text-white shadow-glow transition hover:brightness-110"
                      >
                        <Film size={13} /> 生成视频
                      </button>
                    </div>
                  </div>
                ))}
              </motion.div>
            )}
          </Card>

          {/* 历史 */}
          <Card className="p-5">
            <h2 className="mb-4 font-display text-lg font-semibold text-white">历史记录</h2>
            {history.length === 0 ? (
              <p className="py-8 text-center text-sm text-slate-500">暂无出图记录</p>
            ) : (
              <div className="space-y-2">
                {history.map((job) => {
                  const cover = job.result_paths[0];
                  const active = current?.id === job.id;
                  return (
                    <button
                      key={job.id}
                      onClick={() => setCurrent(job)}
                      className={cn(
                        "flex w-full items-center gap-3 rounded-xl border p-2.5 text-left transition",
                        active
                          ? "border-accent-cyan/40 bg-accent-cyan/5"
                          : "border-white/10 hover:bg-white/5",
                      )}
                    >
                      <div className="h-12 w-12 shrink-0 overflow-hidden rounded-lg bg-white/5">
                        {cover ? (
                          <img src={mediaUrl(cover)} alt="" className="h-full w-full object-cover" />
                        ) : (
                          <div className="grid h-full place-items-center text-slate-600">—</div>
                        )}
                      </div>
                      <div className="min-w-0 flex-1">
                        <p className="truncate text-sm text-slate-200">
                          {job.prompt || "（空提示词）"}
                        </p>
                        <p className="text-xs text-slate-500">
                          {job.resolution} · {job.count} 张 · {job.result_paths.length} 完成
                        </p>
                      </div>
                      <span
                        className={cn(
                          "rounded-full px-2 py-0.5 text-[11px]",
                          job.status === "completed" && "bg-emerald-400/10 text-emerald-300",
                          job.status === "failed" && "bg-rose-500/10 text-rose-300",
                          (job.status === "pending" || job.status === "running") &&
                            "bg-accent-cyan/10 text-accent-cyan",
                        )}
                      >
                        {job.status}
                      </span>
                    </button>
                  );
                })}
              </div>
            )}
          </Card>
        </div>
      </div>

      <SaveAsCharacterModal
        open={!!link}
        onClose={() => setLink(null)}
        jobId={current?.id ?? null}
        imageIndex={link?.index ?? 0}
        imagePath={link?.path ?? ""}
        defaultPrompt={current?.prompt ?? ""}
        mode={link?.mode ?? "character"}
      />
    </div>
  );
}
