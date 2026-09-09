import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'
import viteCompression from 'vite-plugin-compression'

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  const isProduction = mode === 'production'

  return {
    plugins: [
      vue(),
      // 生产环境启用 gzip 压缩
      isProduction && viteCompression({
        algorithm: 'gzip',
        ext: '.gz',
        threshold: 10240, // 大于 10KB 的文件才压缩
        deleteOriginFile: false, // 保留原文件
        compressionOptions: {
          level: 9 // 最高压缩级别
        }
      })
    ].filter(Boolean),
    resolve: {
      alias: {
        '@': resolve(__dirname, 'src')
      }
    },
    server: {
      port: 5173,
      host: true,
      proxy: {
        '/api': {
          target: 'http://localhost:5000',
          changeOrigin: true,
          secure: false
        },
        '/uploads': {
          target: 'http://localhost:5000',
          changeOrigin: true,
          secure: false
        }
      }
    },
    build: {
      outDir: 'dist',
      assetsDir: 'static',
      sourcemap: false,
      // 生产构建优化
      minify: 'terser',
      terserOptions: {
        compress: {
          drop_console: true, // 移除 console
          drop_debugger: true, // 移除 debugger
          pure_funcs: ['console.log'] // 移除 console.log
        },
        format: {
          comments: false // 移除注释
        }
      },
      // chunk 大小警告阈值
      chunkSizeWarningLimit: 1000,
      rollupOptions: {
        output: {
          // 更细粒度的代码分割策略
          manualChunks: (id) => {
            // Vue 核心生态
            if (id.includes('node_modules/vue/') ||
                id.includes('node_modules/@vue/') ||
                id.includes('node_modules/vue-router/') ||
                id.includes('node_modules/pinia/')) {
              return 'vendor-vue'
            }
            // Element Plus UI 库
            if (id.includes('node_modules/element-plus/')) {
              return 'vendor-element'
            }
            // ECharts 图表库
            if (id.includes('node_modules/echarts/') ||
                id.includes('node_modules/zrender/')) {
              return 'vendor-echarts'
            }
            // 工具库
            if (id.includes('node_modules/lodash-es/') ||
                id.includes('node_modules/dayjs/') ||
                id.includes('node_modules/axios/')) {
              return 'vendor-utils'
            }
            // 其他 node_modules
            if (id.includes('node_modules/')) {
              return 'vendor-other'
            }
          },
          // 入口文件命名
          entryFileNames: 'js/[name]-[hash].js',
          // chunk 文件命名
          chunkFileNames: 'js/[name]-[hash].js',
          // 静态资源命名
          assetFileNames: (assetInfo) => {
            const info = assetInfo.name.split('.')
            const ext = info[info.length - 1]
            if (/\.(png|jpe?g|gif|svg|webp|ico)$/i.test(assetInfo.name)) {
              return 'images/[name]-[hash].[ext]'
            } else if (/\.(woff2?|eot|ttf|otf)$/i.test(assetInfo.name)) {
              return 'fonts/[name]-[hash].[ext]'
            } else if (/\.css$/i.test(assetInfo.name)) {
              return 'css/[name]-[hash].[ext]'
            }
            return 'assets/[name]-[hash].[ext]'
          },
          // 用于拆分模块的 ID 生成算法
          compact: true
        }
      },
      // CSS 代码分割
      cssCodeSplit: true,
      // 启用 CSS 压缩
      cssMinify: true
    },
    css: {
      preprocessorOptions: {
        scss: {
          additionalData: `@use "@/styles/variables.scss" as *;`
        }
      }
    },
    // 优化依赖预构建
    optimizeDeps: {
      include: [
        'vue',
        'vue-router',
        'pinia',
        'element-plus',
        'axios',
        'dayjs',
        'lodash-es',
        'echarts'
      ],
      exclude: ['@iconify/json']
    }
  }
})
