import { defineConfig } from 'vite'
import { svelte } from '@sveltejs/vite-plugin-svelte'

export default defineConfig({
  plugins: [svelte()],
  build: {
    // El manifest explícito fuerza la ruta outDir/manifest.json en Vite 5+
    manifest: 'manifest.json',
    // Relativo a la ubicación de vite.config.js (frontend/)
    outDir: '../clientes/static/clientes/dist',
    emptyOutDir: true,
    rollupOptions: {
      input: 'src/main.js',
    },
  },
  server: {
    // Permite que Django (localhost:8000) cargue módulos desde el dev server
    cors: true,
    port: 5173,
  },
})
