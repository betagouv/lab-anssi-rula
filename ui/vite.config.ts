import { defineConfig } from 'vite';
import { svelte } from '@sveltejs/vite-plugin-svelte';

export default defineConfig({
  plugins: [svelte()],
  server: {
    host: true,
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://backend:3001',
        changeOrigin: true,
      },
    },
  },
});
