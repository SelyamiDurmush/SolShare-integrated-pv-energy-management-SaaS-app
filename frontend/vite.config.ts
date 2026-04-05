import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

// Look for a cloud URL, otherwise default to the local laptop URL
const backendUrl = process.env.BACKEND_URL || 'http://127.0.0.1:8000';

export default defineConfig({
    plugins: [sveltekit()],
    server: {
        proxy: {
            '/api': {
                target: backendUrl,
                changeOrigin: true
            },
            '/health': {
                target: backendUrl,
                changeOrigin: true
            }
        }
    }
});
