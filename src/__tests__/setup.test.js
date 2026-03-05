/**
 * 测试环境配置验证测试
 * 用于验证 Vitest、Vue Test Utils、Element Plus 和 Pinia 的配置是否正确
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia, defineStore } from 'pinia'
import { defineComponent, ref, computed } from 'vue'
import { 
  createMountOptions, 
  mockMessage, 
  mockMessageBox,
  mockRouter,
  resetAllMocks 
} from './setup.js'

// ============================================
// 测试环境基础配置验证
// ============================================

describe('测试环境配置验证', () => {
  beforeEach(() => {
    resetAllMocks()
  })

  it('Vitest 全局 API 应该可用', () => {
    expect(describe).toBeDefined()
    expect(it).toBeDefined()
    expect(expect).toBeDefined()
    expect(vi).toBeDefined()
    expect(beforeEach).toBeDefined()
  })

  it('Vue Test Utils 应该可用', () => {
    expect(mount).toBeDefined()
  })

  it('Pinia 应该可用', () => {
    expect(createPinia).toBeDefined()
    expect(setActivePinia).toBeDefined()
  })
})

// ============================================
// Element Plus 组件模拟测试
// ============================================

describe('Element Plus 组件模拟测试', () => {
  it('ElButton 组件应该被正确模拟', () => {
    const wrapper = mount({
      template: '<el-button>测试按钮</el-button>'
    })
    
    expect(wrapper.find('.mock-elbutton').exists()).toBe(true)
    expect(wrapper.text()).toContain('测试按钮')
  })

  it('ElInput 组件应该被正确模拟', () => {
    const wrapper = mount({
      template: '<el-input v-model="value" />',
      setup() {
        const value = ref('')
        return { value }
      }
    })
    
    expect(wrapper.find('.mock-elinput').exists()).toBe(true)
  })

  it('ElTable 组件应该被正确模拟', () => {
    const wrapper = mount({
      template: `
        <el-table :data="[]">
          <el-table-column prop="name" label="名称" />
        </el-table>
      `
    })
    
    expect(wrapper.find('.mock-eltable').exists()).toBe(true)
  })
})

// ============================================
// Element Plus 服务模拟测试
// ============================================

describe('Element Plus 服务模拟测试', () => {
  beforeEach(() => {
    resetAllMocks()
  })

  it('ElMessage.success 应该被正确模拟', () => {
    mockMessage.success('操作成功')
    
    expect(mockMessage.success).toHaveBeenCalled()
    expect(mockMessage.success).toHaveBeenCalledWith('操作成功')
  })

  it('ElMessage.error 应该被正确模拟', () => {
    mockMessage.error('操作失败')
    
    expect(mockMessage.error).toHaveBeenCalled()
    expect(mockMessage.error).toHaveBeenCalledWith('操作失败')
  })

  it('ElMessageBox.confirm 应该被正确模拟', async () => {
    const result = await mockMessageBox.confirm('确认删除？', '提示')
    
    expect(mockMessageBox.confirm).toHaveBeenCalled()
    expect(result).toBe('confirm')
  })
})

// ============================================
// Pinia 状态管理测试
// ============================================

describe('Pinia 状态管理测试', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('应该能够创建和使用 Pinia store', () => {
    // 定义一个简单的 store
    const useTestStore = defineStore('test', () => {
      const count = ref(0)
      const doubleCount = computed(() => count.value * 2)
      
      function increment() {
        count.value++
      }
      
      return { count, doubleCount, increment }
    })
    
    const store = useTestStore()
    
    expect(store.count).toBe(0)
    expect(store.doubleCount).toBe(0)
    
    store.increment()
    
    expect(store.count).toBe(1)
    expect(store.doubleCount).toBe(2)
  })
})

// ============================================
// Vue Router 模拟测试
// ============================================

describe('Vue Router 模拟测试', () => {
  beforeEach(() => {
    resetAllMocks()
  })

  it('router.push 应该被正确模拟', () => {
    mockRouter.push('/houses')
    
    expect(mockRouter.push).toHaveBeenCalled()
    expect(mockRouter.push).toHaveBeenCalledWith('/houses')
  })

  it('router.replace 应该被正确模拟', () => {
    mockRouter.replace({ name: 'login' })
    
    expect(mockRouter.replace).toHaveBeenCalled()
    expect(mockRouter.replace).toHaveBeenCalledWith({ name: 'login' })
  })

  it('router.currentRoute 应该可用', () => {
    expect(mockRouter.currentRoute.value.path).toBe('/')
  })
})

// ============================================
// 测试工具函数验证
// ============================================

describe('测试工具函数验证', () => {
  it('createMountOptions 应该返回正确的挂载选项', () => {
    const options = createMountOptions()
    
    expect(options.global).toBeDefined()
    expect(options.global.plugins).toBeDefined()
    expect(options.global.mocks).toBeDefined()
    expect(options.global.mocks.$router).toBeDefined()
    expect(options.global.mocks.$route).toBeDefined()
    expect(options.global.mocks.$message).toBeDefined()
  })

  it('createMountOptions 应该支持自定义选项', () => {
    const customMocks = { $custom: 'value' }
    const options = createMountOptions({ mocks: customMocks })
    
    expect(options.global.mocks.$custom).toBe('value')
  })

  it('resetAllMocks 应该清除所有模拟调用', () => {
    mockMessage.success('test')
    mockRouter.push('/test')
    
    resetAllMocks()
    
    expect(mockMessage.success).not.toHaveBeenCalled()
    expect(mockRouter.push).not.toHaveBeenCalled()
  })
})
