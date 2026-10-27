import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// During `npm run dev`, API calls go to a builder running locally on :8000
export default defineConfig({
  plugins: [react()],
  server: { proxy: { "/api": "http://localhost:8000" } },
});
