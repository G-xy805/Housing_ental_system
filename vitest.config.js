import { defineConfig } from 'vitest/config'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig({
  plugins: [vue()],
  test: {
    // 使用 happy-dom 作为测试环境
    environment: 'happy-dom',
    
    // 全局测试设置文件
    setupFiles: ['./src/__tests__/setup.js'],
    
    // 全局 API，不需要显式导入
    globals: true,
    
    // 测试覆盖率配置
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      reportsDirectory: './coverage',
      // 需要统计覆盖率的文件
      include: [
        'src/components/**/*.{js,vue}',
        'src/views/**/*.{js,vue}',
        'src/utils/**/*.js',
        'src/store/**/*.js',
        'src/api/**/*.js'
      ],
      // 排除的文件
      exclude: [
        'src/__tests__/**',
        'src/**/*.spec.js',
        'src/**/*.test.js',
        'node_modules/**'
      ]
    },
    
    // 测试文件匹配模式
    include: [
      'src/**/*.{test,spec}.{js,ts}',
      'src/__tests__/**/*.test.{js,ts}'
    ],
    
    // 排除的文件
    exclude: [
      'node_modules/**',
      'dist/**',
      'src/__tests__/setup.js'
    ],
    
    // 测试超时时间（毫秒）
    testTimeout: 10000,
    
    // 钩子函数超时时间
    hookTimeout: 10000
  },
  
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src')
    }
  },
  
  css: {
    preprocessorOptions: {
      scss: {
        additionalData: `@use "@/styles/variables.scss" as *;`
      }
    }
  }
})
