/// <reference types="vitest" />
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'happy-dom',
    setupFiles: './src/setupTests.js',
  },
  server: {
    port: 5173,
    proxy: {
      '/auth': 'http://127.0.0.1:8000',
      '/me': 'http://127.0.0.1:8000',
      '/users': 'http://127.0.0.1:8000',
      '/tasks': 'http://127.0.0.1:8000',
      '/categories': 'http://127.0.0.1:8000',
      '/templates': 'http://127.0.0.1:8000',
      '/fixed-blocks': 'http://127.0.0.1:8000',
      '/integrations': 'http://127.0.0.1:8000',
      '/ai': 'http://127.0.0.1:8000',
    },
  },
});
