import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// 开发期把前端请求代理到本地 FastAPI 后端（:8000），
// 免去 CORS 配置，且媒体/WS 同域，前端只用相对路径即可。
const srcDir = import.meta.dirname + "/src";

export default defineConfig({
  plugins: [react()],
  // 把 Vite 缓存放到 node_modules 之外，规避某些沙箱对 node_modules 下批量删除的安全拦截。
  cacheDir: ".vite-cache",
  resolve: {
    alias: {
      "@": srcDir,
    },
  },
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },
      "/media": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },
      "/ws": {
        target: "ws://127.0.0.1:8000",
        ws: true,
      },
    },
  },
});
