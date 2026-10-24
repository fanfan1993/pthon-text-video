import { mediaUrl } from "@/lib/api";

export function VideoPlayer({ src, className }: { src: string; className?: string }) {
  if (!src) return null;
  return (
    <video
      className={className}
      controls
      playsInline
      preload="metadata"
      src={mediaUrl(src)}
    >
      你的浏览器不支持视频播放。
    </video>
  );
}
