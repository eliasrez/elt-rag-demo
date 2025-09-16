import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      // Proxy all requests starting with '/config' to your Flask server
      '/config': 'http://127.0.0.1:5000',
      '/api': 'http://127.0.0.1:5000',
    },
  },
});