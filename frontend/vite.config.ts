import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'
import AutoImport from 'unplugin-auto-import/vite'
import Components from 'unplugin-vue-components/vite'
import { ElementPlusResolver } from 'unplugin-vue-components/resolvers'

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  // 加载环境变量
  const env = loadEnv(mode, process.cwd(), '')
  const apiTarget = env.VITE_API_TARGET || 'http://localhost:8000'
  const port = env.VITE_PORT ? parseInt(env.VITE_PORT, 10) : 3000

  console.log('🔧 Vite配置加载:')
  console.log(`   - 前端端口: ${port}`)
  console.log(`   - 后端代理: ${apiTarget}`)
  console.log(`   - 运行模式: ${mode}`)

  return {
  plugins: [
    vue(),
    AutoImport({
      resolvers: [ElementPlusResolver()],
      imports: [
        'vue',
        'vue-router',
        'pinia',
        '@vueuse/core'
      ],
      dts: true,
      eslintrc: {
        enabled: true
      }
    }),
    // 自动按需组件导入
    Components({
      resolvers: [ElementPlusResolver()],
      dts: true
    })
  ],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
      '@components': resolve(__dirname, 'src/components'),
      '@views': resolve(__dirname, 'src/views'),
      '@stores': resolve(__dirname, 'src/stores'),
      '@utils': resolve(__dirname, 'src/utils'),
      '@types': resolve(__dirname, 'src/types'),
      '@api': resolve(__dirname, 'src/api')
    }
  },
  server: {
    host: '0.0.0.0',
    port: port,
    hmr: {
      overlay: false
    },
    // 允许从项目根目录之外（例如 /docs）导入原始文件
    fs: {
      allow: [resolve(__dirname, '..')]
    },
    proxy: {
      '/api': {
        target: apiTarget,
        changeOrigin: true,
        secure: false,
        ws: true,  // 🔥 启用 WebSocket 代理支持
        configure: (proxy, _options) => {
          proxy.on('error', (err, _req, _res) => {
            console.log('🔴 代理错误:', err.message)
          })
          proxy.on('proxyReq', (proxyReq, req, _res) => {
            console.log(`🚀 代理请求: ${req.method} ${req.url} -> ${apiTarget}${req.url}`)
          })
          proxy.on('proxyRes', (proxyRes, req, _res) => {
            console.log(`✅代理响应: ${req.url} - ${proxyRes.statusCode}`)
          })
        }
      }
    }
  },
  build: {
    target: 'es2020',  // 支持 nullish coalescing operator (??) 和 optional chaining (?.)
    outDir: 'dist',
    assetsDir: 'assets',
    sourcemap: false,
    rollupOptions: {
      output: {
        chunkFileNames: 'js/[name]-[hash].js',
        entryFileNames: 'js/[name]-[hash].js',
        assetFileNames: '[ext]/[name]-[hash].[ext]'
      }
    }
  },
  css: {
    preprocessorOptions: {
      scss: {
        additionalData: `@use "@/styles/variables.scss" as *;`
      }
    }
  }
}})
