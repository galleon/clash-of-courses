import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
    plugins: [react()],
    server: {
        port: 5173,
        host: '0.0.0.0', // Allow connections from outside container

        // CORS Proxy Configuration
        // This forwards all /api requests to the backend container
        // Example: http://localhost:5173/api/v1/auth/login -> http://backend:8000/api/v1/auth/login
        proxy: {
            '/api': {
                target: 'http://backend:8000',  // Backend container address in Docker network
                changeOrigin: true,             // Changes the origin header to match target
                secure: false,                  // Allow non-HTTPS targets
            }
        }
    },
});
