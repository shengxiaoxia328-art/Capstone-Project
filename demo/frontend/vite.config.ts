import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:5000',
        changeOrigin: true,
        // 流式接口（analyze/stream、answer/stream、generate_story/stream）会长时间保持连接，避免代理超时关闭
        timeout: 300000, // 5 分钟
        proxyTimeout: 300000,
      },
    },
  },
})
