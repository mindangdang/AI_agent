import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
  ],
  server: {
    proxy: {
      // 프론트엔드에서 /api로 시작하는 요청을 보내면 
      // 8000번 포트에 떠 있는 파이썬 백엔드로 토스합니다.
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      }
    }
  }
})