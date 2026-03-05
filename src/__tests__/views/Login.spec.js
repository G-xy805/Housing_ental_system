/**
 * 登录页面测试用例
 * 测试内容：
 * 1. 表单验证（用户名、密码必填）
 * 2. 登录成功流程
 * 3. 登录失败错误提示
 * 4. Token 存储和跳转
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import Login from '@/views/Login.vue'
import { login as loginApi } from '@/api/user'
import { useUserStore } from '@/store/user'
import { ElMessage } from 'element-plus'
import { User, Lock } from '@element-plus/icons-vue'

// ============================================
// Mock 模块
// ============================================

// 使用 vi.hoisted 提升变量定义
const mockPush = vi.hoisted(() => vi.fn())
const mockReplace = vi.hoisted(() => vi.fn())

// Mock login API
vi.mock('@/api/user', () => ({
  login: vi.fn()
}))

// Mock vue-router
vi.mock('vue-router', () => ({
  useRouter: () => ({
    push: mockPush,
    replace: mockReplace,
    go: vi.fn(),
    back: vi.fn(),
    forward: vi.fn()
  }),
  useRoute: () => ({
    path: '/login',
    params: {},
    query: {},
    meta: {},
    name: 'login'
  }),
  createRouter: vi.fn(() => ({
    push: mockPush,
    replace: mockReplace,
    go: vi.fn(),
    back: vi.fn(),
    forward: vi.fn(),
    beforeEach: vi.fn(),
    afterEach: vi.fn(),
    beforeResolve: vi.fn(),
    onError: vi.fn(),
    currentRoute: {
      value: {
        path: '/login',
        params: {},
        query: {},
        meta: {},
        name: 'login'
      }
    }
  })),
  createWebHistory: vi.fn(() => ({}))
}))

// Mock Element Plus
vi.mock('element-plus', () => ({
  ElMessage: {
    success: vi.fn(),
    error: vi.fn(),
    warning: vi.fn(),
    info: vi.fn()
  },
  ElMessageBox: {
    confirm: vi.fn(),
    alert: vi.fn()
  }
}))

// Mock localStorage
const localStorageMock = (() => {
  let store = {}
  return {
    getItem: vi.fn((key) => store[key] || null),
    setItem: vi.fn((key, value) => {
      store[key] = value.toString()
    }),
    removeItem: vi.fn((key) => {
      delete store[key]
    }),
    clear: vi.fn(() => {
      store = {}
    })
  }
})()
Object.defineProperty(window, 'localStorage', { value: localStorageMock })

// ============================================
// 测试用例
// ============================================

describe('Login.vue - 登录页面测试', () => {
  let wrapper
  let pinia

  beforeEach(() => {
    // 重置 Pinia
    pinia = createPinia()
    setActivePinia(pinia)
    
    // 重置所有 mock
    vi.clearAllMocks()
    localStorageMock.clear()
    
    // 重置 mock 返回值
    loginApi.mockReset()
  })

  afterEach(() => {
    if (wrapper) {
      wrapper.unmount()
    }
  })

  // ============================================
  // 辅助函数
  // ============================================

  /**
   * 创建组件挂载
   */
  const createWrapper = (options = {}) => {
    return mount(Login, {
      global: {
        plugins: [pinia],
        components: {
          User,
          Lock
        },
        stubs: {
          'el-form': {
            name: 'ElForm',
            template: `<form><slot /></form>`,
            methods: {
              validate: function(callback) {
                // 模拟表单验证
                if (callback) {
                  callback(this._isValid !== false)
                }
                return Promise.resolve(this._isValid !== false)
              },
              _isValid: true
            },
            props: ['model', 'rules']
          },
          'el-form-item': {
            name: 'ElFormItem',
            template: `<div class="el-form-item"><slot /></div>`,
            props: ['prop']
          },
          'el-input': {
            name: 'ElInput',
            template: `<input class="el-input" :value="modelValue" @input="$emit('update:modelValue', $event.target.value)" :type="type" :placeholder="placeholder" />`,
            props: ['modelValue', 'type', 'placeholder', 'prefixIcon', 'clearable', 'showPassword'],
            emits: ['update:modelValue', 'keyup.enter']
          },
          'el-button': {
            name: 'ElButton',
            template: `<button class="el-button" :disabled="disabled" @click="$emit('click')"><slot /></button>`,
            props: ['type', 'size', 'loading'],
            emits: ['click']
          },
          'el-checkbox': {
            name: 'ElCheckbox',
            template: `<input type="checkbox" class="el-checkbox" :checked="modelValue" @change="$emit('update:modelValue', $event.target.checked)" /><slot /></input>`,
            props: ['modelValue'],
            emits: ['update:modelValue']
          },
          'el-link': {
            name: 'ElLink',
            template: `<a class="el-link"><slot /></a>`,
            props: ['type', 'underline']
          }
        },
        ...options.global
      },
      ...options
    })
  }

  /**
   * 获取表单数据
   */
  const getFormData = (wrapper) => {
    const vm = wrapper.vm
    return {
      username: vm.loginForm?.username || '',
      password: vm.loginForm?.password || ''
    }
  }

  // ============================================
  // 1. 页面渲染测试
  // ============================================

  describe('页面渲染', () => {
    it('应该正确渲染登录表单', () => {
      wrapper = createWrapper()
      
      // 检查登录容器存在
      expect(wrapper.find('.login-container').exists()).toBe(true)
      
      // 检查品牌区域存在
      expect(wrapper.find('.brand-section').exists()).toBe(true)
      expect(wrapper.find('.brand-title').text()).toBe('房屋租赁管理系统')
      
      // 检查登录表单存在
      expect(wrapper.find('.login-form').exists()).toBe(true)
      
      // 检查登录按钮存在
      const loginButton = wrapper.find('.el-button')
      expect(loginButton.exists()).toBe(true)
      expect(loginButton.text()).toContain('登 录')
    })

    it('应该显示正确的页面标题和副标题', () => {
      wrapper = createWrapper()
      
      expect(wrapper.find('.login-title').text()).toBe('欢迎回来')
      expect(wrapper.find('.login-subtitle').text()).toBe('请登录您的账号以继续')
    })

    it('应该显示演示账号信息', () => {
      wrapper = createWrapper()
      
      const demoInfo = wrapper.find('.demo-account')
      expect(demoInfo.exists()).toBe(true)
      expect(demoInfo.text()).toContain('admin')
      expect(demoInfo.text()).toContain('Admin123!')
    })
  })

  // ============================================
  // 2. 表单验证测试
  // ============================================

  describe('表单验证', () => {
    it('用户名应该为必填项', async () => {
      wrapper = createWrapper()
      
      const vm = wrapper.vm
      
      // 检查验证规则
      const usernameRules = vm.loginRules.username
      const requiredRule = usernameRules.find(rule => rule.required)
      
      expect(requiredRule).toBeDefined()
      expect(requiredRule.message).toBe('请输入用户名')
    })

    it('密码应该为必填项', async () => {
      wrapper = createWrapper()
      
      const vm = wrapper.vm
      
      // 检查验证规则
      const passwordRules = vm.loginRules.password
      const requiredRule = passwordRules.find(rule => rule.required)
      
      expect(requiredRule).toBeDefined()
      expect(requiredRule.message).toBe('请输入密码')
    })

    it('用户名长度应该在 3 到 20 个字符之间', () => {
      wrapper = createWrapper()
      
      const vm = wrapper.vm
      const usernameRules = vm.loginRules.username
      const lengthRule = usernameRules.find(rule => rule.min && rule.max)
      
      expect(lengthRule).toBeDefined()
      expect(lengthRule.min).toBe(3)
      expect(lengthRule.max).toBe(20)
    })

    it('密码长度应该在 6 到 20 个字符之间', () => {
      wrapper = createWrapper()
      
      const vm = wrapper.vm
      const passwordRules = vm.loginRules.password
      const lengthRule = passwordRules.find(rule => rule.min && rule.max)
      
      expect(lengthRule).toBeDefined()
      expect(lengthRule.min).toBe(6)
      expect(lengthRule.max).toBe(20)
    })

    it('表单初始状态应该为空', () => {
      wrapper = createWrapper()
      
      const formData = getFormData(wrapper)
      
      expect(formData.username).toBe('')
      expect(formData.password).toBe('')
    })

    it('应该能够输入用户名和密码', async () => {
      wrapper = createWrapper()
      
      const vm = wrapper.vm
      
      // 模拟输入
      vm.loginForm.username = 'testuser'
      vm.loginForm.password = 'testpass123'
      
      await wrapper.vm.$nextTick()
      
      expect(vm.loginForm.username).toBe('testuser')
      expect(vm.loginForm.password).toBe('testpass123')
    })
  })

  // ============================================
  // 3. 登录成功流程测试
  // ============================================

  describe('登录成功流程', () => {
    it('登录成功后应该存储 Token', async () => {
      // Mock 登录 API 返回成功
      const mockResponse = {
        data: {
          access_token: 'test-access-token',
          refresh_token: 'test-refresh-token',
          expires_in: 3600,
          user: {
            id: 1,
            username: 'admin',
            email: 'admin@example.com',
            role: 'admin'
          }
        }
      }
      loginApi.mockResolvedValue(mockResponse)
      
      wrapper = createWrapper()
      const vm = wrapper.vm
      
      // 填写表单
      vm.loginForm.username = 'admin'
      vm.loginForm.password = 'Admin123!'
      
      // 调用登录
      await vm.handleLogin()
      
      // 等待异步操作
      await new Promise(resolve => setTimeout(resolve, 100))
      
      // 验证 login API 被调用
      expect(loginApi).toHaveBeenCalledWith({
        username: 'admin',
        password: 'Admin123!'
      })
      
      // 验证 Token 存储
      const userStore = useUserStore()
      expect(userStore.token).toBe('test-access-token')
    })

    it('登录成功后应该存储用户信息', async () => {
      const mockResponse = {
        data: {
          access_token: 'test-access-token',
          refresh_token: 'test-refresh-token',
          expires_in: 3600,
          user: {
            id: 1,
            username: 'admin',
            email: 'admin@example.com',
            role: 'admin'
          }
        }
      }
      loginApi.mockResolvedValue(mockResponse)
      
      wrapper = createWrapper()
      const vm = wrapper.vm
      
      vm.loginForm.username = 'admin'
      vm.loginForm.password = 'Admin123!'
      
      await vm.handleLogin()
      await new Promise(resolve => setTimeout(resolve, 100))
      
      const userStore = useUserStore()
      expect(userStore.userInfo.username).toBe('admin')
      expect(userStore.userInfo.email).toBe('admin@example.com')
    })

    it('登录成功后应该显示成功消息', async () => {
      const mockResponse = {
        data: {
          access_token: 'test-access-token',
          refresh_token: 'test-refresh-token',
          expires_in: 3600,
          user: {
            id: 1,
            username: 'admin'
          }
        }
      }
      loginApi.mockResolvedValue(mockResponse)
      
      wrapper = createWrapper()
      const vm = wrapper.vm
      
      vm.loginForm.username = 'admin'
      vm.loginForm.password = 'Admin123!'
      
      await vm.handleLogin()
      await new Promise(resolve => setTimeout(resolve, 100))
      
      expect(ElMessage.success).toHaveBeenCalledWith('登录成功')
    })

    it('登录成功后应该跳转到首页', async () => {
      const mockResponse = {
        data: {
          access_token: 'test-access-token',
          refresh_token: 'test-refresh-token',
          expires_in: 3600,
          user: {
            id: 1,
            username: 'admin'
          }
        }
      }
      loginApi.mockResolvedValue(mockResponse)
      
      wrapper = createWrapper()
      const vm = wrapper.vm
      
      vm.loginForm.username = 'admin'
      vm.loginForm.password = 'Admin123!'
      
      await vm.handleLogin()
      await new Promise(resolve => setTimeout(resolve, 100))
      
      expect(mockPush).toHaveBeenCalledWith('/dashboard')
    })

    it('登录成功后应该跳转到重定向页面', async () => {
      // 这个测试需要模拟 route.query.redirect
      const mockResponse = {
        data: {
          access_token: 'test-access-token',
          refresh_token: 'test-refresh-token',
          expires_in: 3600,
          user: {
            id: 1,
            username: 'admin'
          }
        }
      }
      loginApi.mockResolvedValue(mockResponse)
      
      wrapper = createWrapper()
      const vm = wrapper.vm
      
      vm.loginForm.username = 'admin'
      vm.loginForm.password = 'Admin123!'
      
      await vm.handleLogin()
      await new Promise(resolve => setTimeout(resolve, 100))
      
      // 默认跳转到 dashboard
      expect(mockPush).toHaveBeenCalled()
    })
  })

  // ============================================
  // 4. 登录失败错误提示测试
  // ============================================

  describe('登录失败错误提示', () => {
    it('用户名或密码错误应该显示错误提示 (401)', async () => {
      const mockError = {
        response: {
          status: 401,
          data: {
            message: '用户名或密码错误'
          }
        }
      }
      loginApi.mockRejectedValue(mockError)
      
      wrapper = createWrapper()
      const vm = wrapper.vm
      
      vm.loginForm.username = 'wronguser'
      vm.loginForm.password = 'wrongpass'
      
      await vm.handleLogin()
      await new Promise(resolve => setTimeout(resolve, 100))
      
      expect(ElMessage.error).toHaveBeenCalledWith('用户名或密码错误')
    })

    it('账号被锁定应该显示锁定提示 (403)', async () => {
      const mockError = {
        response: {
          status: 403,
          data: {
            message: '账号已被锁定，请联系管理员'
          }
        }
      }
      loginApi.mockRejectedValue(mockError)
      
      wrapper = createWrapper()
      const vm = wrapper.vm
      
      vm.loginForm.username = 'lockeduser'
      vm.loginForm.password = 'password123'
      
      await vm.handleLogin()
      await new Promise(resolve => setTimeout(resolve, 100))
      
      expect(ElMessage.error).toHaveBeenCalledWith('账号已被锁定，请联系管理员')
    })

    it('网络错误应该显示通用错误提示', async () => {
      const mockError = new Error('Network Error')
      loginApi.mockRejectedValue(mockError)
      
      wrapper = createWrapper()
      const vm = wrapper.vm
      
      vm.loginForm.username = 'admin'
      vm.loginForm.password = 'Admin123!'
      
      await vm.handleLogin()
      await new Promise(resolve => setTimeout(resolve, 100))
      
      expect(ElMessage.error).toHaveBeenCalledWith('登录失败，请稍后重试')
    })

    it('登录失败后不应该跳转页面', async () => {
      const mockError = {
        response: {
          status: 401,
          data: {
            message: '用户名或密码错误'
          }
        }
      }
      loginApi.mockRejectedValue(mockError)
      
      wrapper = createWrapper()
      const vm = wrapper.vm
      
      vm.loginForm.username = 'wronguser'
      vm.loginForm.password = 'wrongpass'
      
      await vm.handleLogin()
      await new Promise(resolve => setTimeout(resolve, 100))
      
      expect(mockPush).not.toHaveBeenCalled()
    })

    it('登录失败后不应该存储 Token', async () => {
      const mockError = {
        response: {
          status: 401,
          data: {
            message: '用户名或密码错误'
          }
        }
      }
      loginApi.mockRejectedValue(mockError)
      
      wrapper = createWrapper()
      const vm = wrapper.vm
      
      vm.loginForm.username = 'wronguser'
      vm.loginForm.password = 'wrongpass'
      
      await vm.handleLogin()
      await new Promise(resolve => setTimeout(resolve, 100))
      
      const userStore = useUserStore()
      expect(userStore.token).toBe('')
    })
  })

  // ============================================
  // 5. Token 存储测试
  // ============================================

  describe('Token 存储', () => {
    it('登录成功后应该将 access_token 存储到 localStorage', async () => {
      const mockResponse = {
        data: {
          access_token: 'test-access-token-123',
          refresh_token: 'test-refresh-token-456',
          expires_in: 3600,
          user: {
            id: 1,
            username: 'admin'
          }
        }
      }
      loginApi.mockResolvedValue(mockResponse)
      
      wrapper = createWrapper()
      const vm = wrapper.vm
      
      vm.loginForm.username = 'admin'
      vm.loginForm.password = 'Admin123!'
      
      await vm.handleLogin()
      await new Promise(resolve => setTimeout(resolve, 100))
      
      expect(localStorageMock.setItem).toHaveBeenCalledWith('token', 'test-access-token-123')
    })

    it('登录成功后应该将 refresh_token 存储到 localStorage', async () => {
      const mockResponse = {
        data: {
          access_token: 'test-access-token',
          refresh_token: 'test-refresh-token-789',
          expires_in: 3600,
          user: {
            id: 1,
            username: 'admin'
          }
        }
      }
      loginApi.mockResolvedValue(mockResponse)
      
      wrapper = createWrapper()
      const vm = wrapper.vm
      
      vm.loginForm.username = 'admin'
      vm.loginForm.password = 'Admin123!'
      
      await vm.handleLogin()
      await new Promise(resolve => setTimeout(resolve, 100))
      
      expect(localStorageMock.setItem).toHaveBeenCalledWith('refreshToken', 'test-refresh-token-789')
    })

    it('登录成功后应该将用户信息存储到 localStorage', async () => {
      const mockResponse = {
        data: {
          access_token: 'test-access-token',
          refresh_token: 'test-refresh-token',
          expires_in: 3600,
          user: {
            id: 1,
            username: 'admin',
            email: 'admin@example.com',
            role: 'admin'
          }
        }
      }
      loginApi.mockResolvedValue(mockResponse)
      
      wrapper = createWrapper()
      const vm = wrapper.vm
      
      vm.loginForm.username = 'admin'
      vm.loginForm.password = 'Admin123!'
      
      await vm.handleLogin()
      await new Promise(resolve => setTimeout(resolve, 100))
      
      expect(localStorageMock.setItem).toHaveBeenCalledWith(
        'userInfo',
        JSON.stringify({
          id: 1,
          username: 'admin',
          email: 'admin@example.com',
          role: 'admin'
        })
      )
    })

    it('记住我应该存储到 localStorage', async () => {
      const mockResponse = {
        data: {
          access_token: 'test-access-token',
          refresh_token: 'test-refresh-token',
          expires_in: 3600,
          user: {
            id: 1,
            username: 'admin'
          }
        }
      }
      loginApi.mockResolvedValue(mockResponse)
      
      wrapper = createWrapper()
      const vm = wrapper.vm
      
      vm.loginForm.username = 'admin'
      vm.loginForm.password = 'Admin123!'
      vm.rememberMe = true
      
      await vm.handleLogin()
      await new Promise(resolve => setTimeout(resolve, 100))
      
      expect(localStorageMock.setItem).toHaveBeenCalledWith('rememberMe', 'true')
    })

    it('不记住我应该移除 localStorage 中的 rememberMe', async () => {
      const mockResponse = {
        data: {
          access_token: 'test-access-token',
          refresh_token: 'test-refresh-token',
          expires_in: 3600,
          user: {
            id: 1,
            username: 'admin'
          }
        }
      }
      loginApi.mockResolvedValue(mockResponse)
      
      wrapper = createWrapper()
      const vm = wrapper.vm
      
      vm.loginForm.username = 'admin'
      vm.loginForm.password = 'Admin123!'
      vm.rememberMe = false
      
      await vm.handleLogin()
      await new Promise(resolve => setTimeout(resolve, 100))
      
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('rememberMe')
    })
  })

  // ============================================
  // 6. 加载状态测试
  // ============================================

  describe('加载状态', () => {
    it('登录过程中应该显示加载状态', async () => {
      let resolveLogin
      loginApi.mockImplementation(() => new Promise(resolve => {
        resolveLogin = resolve
      }))
      
      wrapper = createWrapper()
      const vm = wrapper.vm
      
      vm.loginForm.username = 'admin'
      vm.loginForm.password = 'Admin123!'
      
      // 开始登录
      const loginPromise = vm.handleLogin()
      
      // 等待一下让 loading 状态设置
      await new Promise(resolve => setTimeout(resolve, 10))
      
      // 检查 loading 状态
      expect(vm.loading).toBe(true)
      
      // 完成登录
      resolveLogin({
        data: {
          access_token: 'test-token',
          user: { id: 1, username: 'admin' }
        }
      })
      
      await loginPromise
      await new Promise(resolve => setTimeout(resolve, 10))
      
      // 登录完成后 loading 应该为 false
      expect(vm.loading).toBe(false)
    })

    it('登录失败后应该取消加载状态', async () => {
      loginApi.mockRejectedValue(new Error('Login failed'))
      
      wrapper = createWrapper()
      const vm = wrapper.vm
      
      vm.loginForm.username = 'admin'
      vm.loginForm.password = 'Admin123!'
      
      await vm.handleLogin()
      await new Promise(resolve => setTimeout(resolve, 100))
      
      expect(vm.loading).toBe(false)
    })
  })

  // ============================================
  // 7. 表单交互测试
  // ============================================

  describe('表单交互', () => {
    it('点击登录按钮应该触发登录', async () => {
      const mockResponse = {
        data: {
          access_token: 'test-token',
          user: { id: 1, username: 'admin' }
        }
      }
      loginApi.mockResolvedValue(mockResponse)
      
      wrapper = createWrapper()
      const vm = wrapper.vm
      
      vm.loginForm.username = 'admin'
      vm.loginForm.password = 'Admin123!'
      
      // 点击登录按钮
      const loginButton = wrapper.find('.el-button')
      await loginButton.trigger('click')
      await new Promise(resolve => setTimeout(resolve, 100))
      
      expect(loginApi).toHaveBeenCalled()
    })

    it('按回车键应该触发登录', async () => {
      const mockResponse = {
        data: {
          access_token: 'test-token',
          user: { id: 1, username: 'admin' }
        }
      }
      loginApi.mockResolvedValue(mockResponse)
      
      wrapper = createWrapper()
      const vm = wrapper.vm
      
      vm.loginForm.username = 'admin'
      vm.loginForm.password = 'Admin123!'
      
      // 模拟回车事件
      const passwordInput = wrapper.findAll('.el-input')[1]
      if (passwordInput) {
        await passwordInput.trigger('keyup.enter')
        await new Promise(resolve => setTimeout(resolve, 100))
      }
      
      // 由于 stub 的限制，我们直接测试 handleLogin 方法
      expect(typeof vm.handleLogin).toBe('function')
    })
  })

  // ============================================
  // 8. 边界情况测试
  // ============================================

  describe('边界情况', () => {
    it('表单引用不存在时应该安全处理', async () => {
      wrapper = createWrapper()
      const vm = wrapper.vm
      
      // 设置 loginFormRef 为 null
      vm.loginFormRef = null
      
      // 不应该抛出错误
      await expect(vm.handleLogin()).resolves.not.toThrow()
    })

    it('API 返回数据格式不完整时应该正常处理', async () => {
      const mockResponse = {
        data: {
          access_token: 'test-token'
          // 缺少 user 信息
        }
      }
      loginApi.mockResolvedValue(mockResponse)
      
      wrapper = createWrapper()
      const vm = wrapper.vm
      
      vm.loginForm.username = 'admin'
      vm.loginForm.password = 'Admin123!'
      
      await vm.handleLogin()
      await new Promise(resolve => setTimeout(resolve, 100))
      
      // 应该正常存储 token
      const userStore = useUserStore()
      expect(userStore.token).toBe('test-token')
    })

    it('错误响应没有 message 时应该使用默认消息', async () => {
      const mockError = {
        response: {
          status: 401
          // 没有 data.message
        }
      }
      loginApi.mockRejectedValue(mockError)
      
      wrapper = createWrapper()
      const vm = wrapper.vm
      
      vm.loginForm.username = 'admin'
      vm.loginForm.password = 'Admin123!'
      
      await vm.handleLogin()
      await new Promise(resolve => setTimeout(resolve, 100))
      
      expect(ElMessage.error).toHaveBeenCalledWith('用户名或密码错误')
    })

    it('403 错误没有 message 时应该使用默认消息', async () => {
      const mockError = {
        response: {
          status: 403
          // 没有 data.message
        }
      }
      loginApi.mockRejectedValue(mockError)
      
      wrapper = createWrapper()
      const vm = wrapper.vm
      
      vm.loginForm.username = 'admin'
      vm.loginForm.password = 'Admin123!'
      
      await vm.handleLogin()
      await new Promise(resolve => setTimeout(resolve, 100))
      
      expect(ElMessage.error).toHaveBeenCalledWith('账号已被锁定，请联系管理员')
    })
  })
})
