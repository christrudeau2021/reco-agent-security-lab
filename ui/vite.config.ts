import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  // Single source of truth for secrets: read the repo's root .env instead
  // of requiring a second, duplicate ui/.env.
  envDir: '../',
  server: {
    port: 5173,
    strictPort: true,
  },
})
