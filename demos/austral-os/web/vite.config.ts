import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { VitePWA } from "vite-plugin-pwa";

export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: "autoUpdate",
      manifest: {
        name: "Norfront Fresh · Austral",
        short_name: "Norfront",
        start_url: "/captura",
        display: "standalone",
        background_color: "#F1F1F1",
        theme_color: "#111111",
      },
    }),
  ],
  server: {
    port: 5176,
    host: "0.0.0.0",
    proxy: {
      "/api": "http://127.0.0.1:8016",
      "/health": "http://127.0.0.1:8016",
    },
  },
});
