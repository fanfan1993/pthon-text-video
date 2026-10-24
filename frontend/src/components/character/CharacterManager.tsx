import { useState } from "react";
import { UserPlus, Sparkles, Lock, ImageOff } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { useProjectStore } from "@/store/useProjectStore";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Field, Input, Textarea } from "@/components/ui/Input";
import { Tag } from "@/components/ui/Badge";
import { mediaUrl } from "@/lib/api";
import type { Character } from "@/types";

function CharAvatar({ char }: { char: Character }) {
  const ref = char.reference_images?.[0];
  if (ref) {
    return (
      <img
        src={mediaUrl(ref)}
        alt={char.name}
        className="h-14 w-14 rounded-xl object-cover ring-1 ring-white/10"
      />
    );
  }
  return (
    <div className="grid h-14 w-14 place-items-center rounded-xl bg-white/5 text-lg font-semibold text-slate-300 ring-1 ring-white/10">
      {char.name.slice(0, 1).toUpperCase()}
    </div>
  );
}

export function CharacterManager({ projectId }: { projectId: string }) {
  const { characters, addCharacter } = useProjectStore();
  const [open, setOpen] = useState(false);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [needAi, setNeedAi] = useState(true);
  const [file, setFile] = useState<File | null>(null);
  const [busy, setBusy] = useState(false);

  const submit = async () => {
    if (!name.trim()) return;
    setBusy(true);
    try {
      await addCharacter(projectId, {
        name: name.trim(),
        description: description.trim(),
        need_ai_image: needAi && !file,
        file,
      });
      setName("");
      setDescription("");
      setNeedAi(true);
      setFile(null);
      setOpen(false);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="font-display text-sm font-semibold text-white">
          角色素材 <span className="text-slate-500">（{characters.length}）</span>
        </h3>
        <Button size="sm" variant="outline" icon={<UserPlus size={15} />} onClick={() => setOpen((v) => !v)}>
          添加角色
        </Button>
      </div>

      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="overflow-hidden"
          >
            <Card className="space-y-3 p-4">
              <Field label="角色名">
                <Input value={name} onChange={(e) => setName(e.target.value)} placeholder="例如：林晚" />
              </Field>
              <Field label="人设 / 形象提示词" hint="描述外貌、服饰、气质，用于出图与锁角色">
                <Textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="黑长直发、淡蓝色和服、清冷气质……"
                />
              </Field>
              <div className="flex flex-wrap items-center gap-3">
                <label className="flex cursor-pointer items-center gap-2 text-sm text-slate-300">
                  <input
                    type="checkbox"
                    checked={needAi}
                    onChange={(e) => setNeedAi(e.target.checked)}
                    className="h-4 w-4 accent-accent"
                  />
                  无参考图，AI 出一张满意图再锁角色
                </label>
                <label className="flex cursor-pointer items-center gap-2 rounded-lg border border-white/10 px-3 py-1.5 text-sm text-slate-300 hover:bg-white/5">
                  <ImageOff size={14} />
                  <span>上传参考图</span>
                  <input
                    type="file"
                    accept="image/*"
                    className="hidden"
                    onChange={(e) => setFile(e.target.files?.[0] ?? null)}
                  />
                </label>
                {file && <Tag>{file.name.slice(0, 16)}</Tag>}
              </div>
              <div className="flex justify-end gap-2">
                <Button variant="ghost" size="sm" onClick={() => setOpen(false)}>
                  取消
                </Button>
                <Button size="sm" loading={busy} onClick={submit}>
                  添加
                </Button>
              </div>
            </Card>
          </motion.div>
        )}
      </AnimatePresence>

      {characters.length === 0 ? (
        <Card className="flex flex-col items-center gap-2 p-8 text-center text-sm text-slate-500">
          <Sparkles size={22} className="text-accent-cyan" />
          暂无角色。添加后流水线会在生成时自动锁定角色一致性。
        </Card>
      ) : (
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          {characters.map((c) => (
            <Card key={c.id} className="flex items-center gap-3 p-3">
              <CharAvatar char={c} />
              <div className="min-w-0 flex-1">
                <p className="truncate font-medium text-slate-100">{c.name}</p>
                <p className="truncate text-xs text-slate-500">{c.description || "（无描述）"}</p>
                <div className="mt-1 flex flex-wrap gap-1.5">
                  {c.cloud_lock_id && (
                    <Tag className="text-accent-cyan">
                      <Lock size={10} /> {c.cloud_lock_id}
                    </Tag>
                  )}
                  {c.need_ai_image && !c.reference_images.length && (
                    <Tag>AI 出图锁定</Tag>
                  )}
                  {c.reference_images.length > 0 && <Tag>自有参考图</Tag>}
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
