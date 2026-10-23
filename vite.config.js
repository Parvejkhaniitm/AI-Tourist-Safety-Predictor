import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  server: {
    proxy: {
      // Dev me browser http://localhost:5173/api/... bulata hai,
      // Vite use Flask (127.0.0.1:5000) ko forward kar deta hai. Isse CORS error nahi aata.
      // Backend ka port alag ho to sirf yahan target badlo.
      '/api': {
        target: 'http://127.0.0.1:5000',
        changeOrigin: true,
      },
    },
  },
})