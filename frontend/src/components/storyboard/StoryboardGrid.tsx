import { ImageIcon, Mic, Film, MessageSquare } from "lucide-react";
import { Card } from "@/components/ui/Card";
import { Tag } from "@/components/ui/Badge";
import { mediaUrl } from "@/lib/api";
import { CAMERA_LABEL } from "@/lib/constants";
import { truncate } from "@/lib/format";
import type { Asset, Storyboard } from "@/types";

function assetByShot(assets: Asset[], shotId: string, type: Asset["type"]) {
  return assets.find((a) => a.shot_id === shotId && a.type === type);
}

export function StoryboardGrid({
  storyboards,
  assets,
}: {
  storyboards: Storyboard[];
  assets: Asset[];
}) {
  if (storyboards.length === 0) return null;

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {storyboards.map((sb) => {
        const img = assetByShot(assets, sb.id, "image");
        const vid = assetByShot(assets, sb.id, "video");
        const aud = assetByShot(assets, sb.id, "audio");
        const poster = vid ?? img;
        return (
          <Card key={sb.id} className="overflow-hidden">
            <div className="relative aspect-video bg-ink-800">
              {img ? (
                <img
                  src={mediaUrl(img.path)}
                  alt={`分镜 ${sb.index + 1}`}
                  className="h-full w-full object-cover"
                />
              ) : (
                <div className="grid h-full place-items-center text-slate-600">
                  <ImageIcon size={28} />
                </div>
              )}
              <span className="absolute left-2 top-2 rounded-md bg-black/60 px-2 py-0.5 text-xs font-medium text-white backdrop-blur">
                镜 {sb.index + 1}
              </span>
              {poster && (
                <span className="absolute right-2 top-2 inline-flex items-center gap-1 rounded-md bg-black/60 px-2 py-0.5 text-xs text-white backdrop-blur">
                  <Film size={11} /> {sb.duration}s
                </span>
              )}
            </div>
            <div className="space-y-2 p-3">
              <p className="text-sm leading-snug text-slate-200">
                {truncate(sb.scene_description || sb.image_prompt, 80)}
              </p>
              <div className="flex items-start gap-1.5 text-xs text-slate-400">
                <MessageSquare size={13} className="mt-0.5 shrink-0 text-accent-cyan" />
                <span className="line-clamp-2">{sb.dialogue || "（旁白）"}</span>
              </div>
              <div className="flex flex-wrap gap-1.5">
                <Tag>{CAMERA_LABEL[sb.camera_movement]}</Tag>
                <Tag>{sb.shot_type}</Tag>
                {aud && (
                  <Tag className="text-emerald-300">
                    <Mic size={10} /> 已配音
                  </Tag>
                )}
              </div>
            </div>
          </Card>
        );
      })}
    </div>
  );
}
