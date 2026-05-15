import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

/**
 * Dev proxy: browser calls same-origin `/api/*`, Vite forwards to FastAPI on :8000.
 * Set `VITE_API_BASE_URL=/api` in `frontend/.env` for local dev (see frontend/.env.example).
 */
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, "") || "/",
      },
    },
  },
});
