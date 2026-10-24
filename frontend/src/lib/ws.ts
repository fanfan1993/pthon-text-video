import { wsUrl } from "@/lib/api";
import type { ProgressMessage } from "@/types";

// 订阅项目实时进度。返回取消订阅函数。
export function subscribeProgress(
  projectId: string,
  onMessage: (msg: ProgressMessage) => void,
  onStatus?: (connected: boolean) => void,
): () => void {
  let ws: WebSocket | null = null;
  let closed = false;
  let retry: number | null = null;

  const connect = () => {
    if (closed) return;
    try {
      ws = new WebSocket(wsUrl(projectId));
    } catch {
      onStatus?.(false);
      return;
    }
    ws.onopen = () => onStatus?.(true);
    ws.onclose = () => {
      onStatus?.(false);
      // 自动重连（最多 5 次，间隔递增），保证刷新/瞬时断线不丢进度
      if (!closed && retry === null) {
        let attempt = 0;
        const tryReconnect = () => {
          if (closed || attempt >= 5) return;
          attempt += 1;
          connect();
        };
        retry = window.setTimeout(tryReconnect, 1500);
      }
    };
    ws.onerror = () => {
      /* onclose 会处理重连 */
    };
    ws.onmessage = (ev) => {
      try {
        const data = JSON.parse(ev.data) as ProgressMessage;
        onMessage(data);
      } catch {
        /* 忽略非 JSON 帧 */
      }
    };
  };

  connect();

  return () => {
    closed = true;
    if (retry !== null) window.clearTimeout(retry);
    ws?.close();
  };
}
