// vite.config.js

import path from "path";
import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [vue()],
  strict: false,
  optimizeDeps: {
    strict: false,
  },
  server: {
    port: 8080,
    strictPort: true,

    allowedHosts: ["localhost", "webserver"],

    proxy: {
      "/api/assistants": {
        target: "http://ia:6001/",
        changeOrigin: true,
        secure: false,
        rewrite: (path) => path.replace(/^\/api\/assistants/, ""),
      },
      "/api": {
        target: "http://webserver:5001/api/",
        changeOrigin: true,
        secure: false,
        rewrite: (path) => path.replace(/^\/api/, ""),
      },
      "/socket.io": {
        target: "http://webserver:5001/socket.io",
        changeOrigin: false,
        secure: false,
        ws: true,
        rewrite: (path) => path.replace(/^\/socket.io/, ""),
      },
    },
  },

  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
    extensions: [".mjs", ".js", ".ts", ".jsx", ".tsx", ".json", ".vue"],
  },
});
