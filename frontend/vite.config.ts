import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 13002,
    host: '0.0.0.0',
    strictPort: true,
    cors: true,
    allowedHosts: true,
    proxy: {
      '/api': {
        target: 'http://localhost:18000',
        changeOrigin: true
      }
    }
  }
})