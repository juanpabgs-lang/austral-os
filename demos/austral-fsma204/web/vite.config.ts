import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { VitePWA } from "vite-plugin-pwa";

export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: "autoUpdate",
      manifest: { name: "Norfront Fresh · FSMA 204", short_name: "FSMA204", start_url: "/empaque", display: "standalone", background_color: "#F1F1F1", theme_color: "#111111" },
    }),
  ],
  server: {
    port: 5177,
    host: "0.0.0.0",
    allowedHosts: true,
    proxy: { "/api": "http://127.0.0.1:8017", "/health": "http://127.0.0.1:8017" },
  },
});
