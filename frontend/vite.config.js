import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],

  build: {
    // Increase chunk warning threshold
    chunkSizeWarningLimit: 1000,

    // Enable minification
    minify: 'esbuild',

    // Code splitting - split vendor chunks
    rollupOptions: {
      output: {
        manualChunks: {
          // Core React - loaded first
          'vendor-react': ['react', 'react-dom', 'react-router-dom'],

          // Animation library - separate chunk
          'vendor-motion': ['framer-motion'],

          // Icons - separate chunk (large library)
          'vendor-icons': ['lucide-react'],

          // Charts - only loaded when needed
          'vendor-charts': ['recharts'],
        },
      },
    },

    // Generate source maps only in development
    sourcemap: false,

    // Optimize CSS
    cssCodeSplit: true,

    // Target modern browsers (smaller bundle)
    target: 'es2020',
  },

  // Development server optimization
  server: {
    port: 3000,
    strictPort: true,
    hmr: { overlay: true },
  },

  // Preview server (for production build testing)
  preview: {
    port: 3000,
  },

  optimizeDeps: {
    include: [
      'react',
      'react-dom',
      'react-router-dom',
      'framer-motion',
      'lucide-react',
    ],
  },

  esbuild: {
    drop: ['console', 'debugger'],
    pure: ['console.log', 'console.info', 'console.debug'],
  },

  // Resolve aliases for cleaner imports
  resolve: {
    alias: {
      '@': '/src',
      '@components': '/src/components',
      '@pages': '/src/pages',
      '@services': '/src/services',
      '@utils': '/src/utils',
    },
  },
})
