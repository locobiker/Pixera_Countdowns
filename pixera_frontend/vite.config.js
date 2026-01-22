import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    host: true, // Enables Docker mapping
    proxy: {
      // 1. Match behavior of Nginx "location /api/"
      "/api": {
        target: "http://backend-dev:8000", // Ensure this matches your Docker Compose service name for Dev
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '') // Strips /api
      },
      // 2. Match behavior of Nginx "location /ws"
      "/ws": {
        target: "ws://backend-dev:8000", // Ensure this matches your Docker Compose service name for Dev
        ws: true,
        changeOrigin: true,
        // No rewrite needed, path is passed as /ws
      },
    },
  },
});