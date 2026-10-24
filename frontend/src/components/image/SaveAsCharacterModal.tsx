import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { CheckCircle2, Film, UserPlus } from "lucide-react";
import { api, mediaUrl } from "@/lib/api";
import type { Project, SaveAsCharacterResult } from "@/types";
import { Button } from "@/components/ui/Button";
import { Modal } from "@/components/ui/Modal";
import { Field, Input, Select, Textarea } from "@/components/ui/Input";

interface Props {
  open: boolean;
  onClose: () => void;
  jobId: string | null;
  /** 使用任务里的第几张（0-based） */
  imageIndex: number;
  /** 预览用图片相对路径 */
  imagePath: string;
  /** 默认提示词，用于预填角色设定 */
  defaultPrompt?: string;
  /** character=只存角色；video=存完立即生成视频 */
  mode?: "character" | "video";
}

/**
 * 把出图结果沉淀为角色设定。
 * - 可存进现有项目，也可顺手新建一个项目；
 * - 「生成视频」模式下会同时触发流水线，图片直接作为角色参考图参与分镜出图。
 */
export function SaveAsCharacterModal({
  open,
  onClose,
  jobId,
  imageIndex,
  imagePath,
  defaultPrompt = "",
  mode = "character",
}: Props) {
  const navigate = useNavigate();
  const [projects, setProjects] = useState<Project[]>([]);
  const [projectId, setProjectId] = useState<string>("__new__");
  const [projectTitle, setProjectTitle] = useState("");
  const [projectInput, setProjectInput] = useState("");
  const [name, setName] = useState("角色");
  const [description, setDescription] = useState(defaultPrompt);
  const [startPipeline, setStartPipeline] = useState(mode === "video");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState<SaveAsCharacterResult | null>(null);

  // 每次打开重置表单（保留默认值），并拉取项目列表
  useEffect(() => {
    if (!open) return;
    setProjectId("__new__");
    setProjectTitle("");
    setProjectInput("");
    setName("角色");
    setDescription(defaultPrompt);
    setStartPipeline(mode === "video");
    setError("");
    setResult(null);
    api
      .getProjects()
      .then((list) => {
        setProjects(list);
        // 有草稿项目时默认选最近一个，减少「新建」误触
        const draft = list.find((p) => p.status === "draft");
        if (draft && mode === "character") setProjectId(draft.id);
      })
      .catch(() => setProjects([]));
  }, [open, defaultPrompt, mode]);

  const isNewProject = projectId === "__new__";
  const selectedProject = useMemo(
    () => projects.find((p) => p.id === projectId) ?? null,
    [projects, projectId],
  );

  const canSubmit =
    !submitting &&
    !!jobId &&
    (!startPipeline || isNewProject || Boolean(selectedProject?.id));

  const onSubmit = async () => {
    if (!jobId) return;
    if (startPipeline && isNewProject && !projectInput.trim()) {
      setError("生成视频需要一段文案（用于分镜），请填写或改用已有项目");
      return;
    }
    setError("");
    setSubmitting(true);
    try {
      const res = await api.saveImageAsCharacter(jobId, {
        image_index: imageIndex,
        project_id: isNewProject ? null : projectId,
        project_title: isNewProject ? projectTitle || undefined : undefined,
        project_input: isNewProject ? projectInput : undefined,
        name: name.trim() || "角色",
        description: description.trim(),
        lock_role: true,
        start_pipeline: startPipeline,
      });
      setResult(res);
    } catch (e) {
      setError((e as Error).message || "保存失败");
    } finally {
      setSubmitting(false);
    }
  };

  const title = startPipeline ? "存为角色并生成视频" : "存为角色设定";

  return (
    <Modal
      open={open}
      onClose={onClose}
      title={title}
      footer={
        result ? (
          <>
            <Button variant="ghost" onClick={onClose}>
              继续出图
            </Button>
            <Button
              icon={<Film size={16} />}
              onClick={() => navigate(`/projects/${result.project_id}`)}
            >
              打开项目
            </Button>
          </>
        ) : (
          <>
            <Button variant="ghost" onClick={onClose}>
              取消
            </Button>
            <Button
              loading={submitting}
              disabled={!canSubmit}
              icon={startPipeline ? <Film size={16} /> : <UserPlus size={16} />}
              onClick={onSubmit}
            >
              {startPipeline ? "保存并生成" : "存为角色"}
            </Button>
          </>
        )
      }
    >
      {result ? (
        <div className="space-y-4">
          <div className="flex items-center gap-2 rounded-xl border border-emerald-400/30 bg-emerald-400/10 px-4 py-3 text-emerald-300">
            <CheckCircle2 size={18} />
            <span className="text-sm">已存为角色「{result.character.name}」</span>
          </div>
          <ul className="space-y-2 text-sm text-slate-300">
            <li>
              目标项目：<span className="text-white">{result.project_title}</span>
              {result.created_project && (
                <span className="ml-2 rounded-full bg-white/10 px-2 py-0.5 text-[11px] text-slate-300">
                  新建
                </span>
              )}
            </li>
            <li>
              参考图已写入项目：
              <span className="ml-1 break-all text-slate-400">{result.image_path}</span>
            </li>
            <li>
              云角色锁定：
              {result.locked ? (
                <span className="text-emerald-300">已锁定（跨镜一致）</span>
              ) : (
                <span className="text-amber-300">未锁定，流水线执行时会自动重试</span>
              )}
            </li>
            {result.pipeline_queued && (
              <li className="text-accent-cyan">视频流水线已提交，可在项目页查看进度</li>
            )}
          </ul>
        </div>
      ) : (
        <div className="space-y-4">
          <div className="flex gap-4">
            <div className="h-24 w-24 shrink-0 overflow-hidden rounded-xl border border-white/10 bg-white/5">
              {imagePath && (
                <img src={mediaUrl(imagePath)} alt="选中的图" className="h-full w-full object-cover" />
              )}
            </div>
            <div className="min-w-0 flex-1 space-y-3">
              <Field label="角色名">
                <Input value={name} onChange={(e) => setName(e.target.value)} placeholder="例如：雨夜少女" />
              </Field>
            </div>
          </div>

          <Field label="角色设定（会作为出图提示词的一部分，保持人物一致）">
            <Textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="min-h-[80px]"
              placeholder="黑长直发，米白色风衣，手持透明雨伞……"
            />
          </Field>

          <Field label="目标项目" hint="选「新建项目」可直接把这张图变成一个视频项目">
            <Select value={projectId} onChange={(e) => setProjectId(e.target.value)}>
              <option value="__new__">＋ 新建项目</option>
              {projects.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.title}（{p.status}）
                </option>
              ))}
            </Select>
          </Field>

          {isNewProject && (
            <>
              <Field label="项目名称">
                <Input
                  value={projectTitle}
                  onChange={(e) => setProjectTitle(e.target.value)}
                  placeholder="留空则自动命名"
                />
              </Field>
              <Field
                label={startPipeline ? "视频文案（必填）" : "视频文案（可选）"}
                hint="一段小说或剧情文本，流水线会据此拆解分镜"
              >
                <Textarea
                  value={projectInput}
                  onChange={(e) => setProjectInput(e.target.value)}
                  placeholder="雨夜，少女撑着透明雨伞走过霓虹街头，抬头看见旧书店的灯……"
                />
              </Field>
            </>
          )}

          <label className="flex cursor-pointer items-start gap-3 rounded-xl border border-white/10 bg-white/[0.02] p-3">
            <input
              type="checkbox"
              checked={startPipeline}
              onChange={(e) => setStartPipeline(e.target.checked)}
              className="mt-0.5 h-4 w-4 accent-accent"
            />
            <span className="text-sm text-slate-300">
              存完立即生成视频
              <span className="block text-xs text-slate-500">
                会用这张图作为角色锚点，跑分镜 → 出图 → 运镜 → 配音 → 合成
              </span>
            </span>
          </label>

          {error && <p className="text-xs text-rose-400">{error}</p>}
        </div>
      )}
    </Modal>
  );
}
