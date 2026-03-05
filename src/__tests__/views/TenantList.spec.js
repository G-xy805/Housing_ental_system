/**
 * 租客管理页面测试用例
 * 测试范围：
 * 1. 租客列表展示
 * 2. 租客搜索
 * 3. 新增租客表单
 * 4. 编辑租客表单
 * 5. 其他功能（删除、状态变更、详情查看等）
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import TenantList from '@/views/tenants/TenantList.vue'
import * as tenantApi from '@/api/tenant'
import { useUserStore } from '@/store/user'
import { ElMessage, ElMessageBox } from 'element-plus'

// ============================================
// Mock API 响应数据
// ============================================

const mockTenants = [
  {
    id: 1,
    name: '张三',
    phone: '13800138001',
    id_card: '110101199001011234',
    email: 'zhangsan@example.com',
    emergency_contact: '张父',
    emergency_phone: '13900139001',
    emergency_relation: '父亲',
    company: '某科技公司',
    occupation: '工程师',
    status: 'active',
    contracts_count: 2,
    remark: '优质租客',
    created_at: '2024-01-15T10:30:00'
  },
  {
    id: 2,
    name: '李四',
    phone: '13800138002',
    id_card: '110101199002021234',
    email: 'lisi@example.com',
    emergency_contact: '李母',
    emergency_phone: '13900139002',
    emergency_relation: '母亲',
    company: '某贸易公司',
    occupation: '销售',
    status: 'expired',
    contracts_count: 1,
    remark: '',
    created_at: '2024-02-20T14:20:00'
  },
  {
    id: 3,
    name: '王五',
    phone: '13800138003',
    id_card: '110101199003031234',
    email: 'wangwu@example.com',
    emergency_contact: '王妻',
    emergency_phone: '13900139003',
    emergency_relation: '配偶',
    company: '',
    occupation: '',
    status: 'blacklisted',
    contracts_count: 0,
    remark: '违规租客',
    created_at: '2024-03-10T09:15:00'
  }
]

const mockTenantDetail = {
  id: 1,
  name: '张三',
  phone: '13800138001',
  id_card: '110101199001011234',
  email: 'zhangsan@example.com',
  emergency_contact: '张父',
  emergency_phone: '13900139001',
  emergency_relation: '父亲',
  company: '某科技公司',
  occupation: '工程师',
  status: 'active',
  contracts_count: 2,
  remark: '优质租客',
  created_at: '2024-01-15T10:30:00'
}

const mockStatistics = {
  total: 10,
  by_status: {
    active: 6,
    expired: 3,
    blacklisted: 1
  }
}

const mockContracts = [
  {
    id: 1,
    contract_no: 'HT202401150001',
    house_name: '朝阳区精装两居室',
    start_date: '2024-01-15',
    end_date: '2025-01-14',
    monthly_rent: 5000,
    status: 'active'
  },
  {
    id: 2,
    contract_no: 'HT202402200001',
    house_name: '海淀区合租主卧',
    start_date: '2024-02-20',
    end_date: '2025-02-19',
    monthly_rent: 3000,
    status: 'expired'
  }
]

// ============================================
// Mock API 函数
// ============================================

// Mock router first (before other imports)
vi.mock('@/router', () => ({
  default: {
    beforeEach: vi.fn(),
    afterEach: vi.fn(),
    onError: vi.fn(),
    push: vi.fn(),
    replace: vi.fn(),
    go: vi.fn(),
    back: vi.fn(),
    currentRoute: {
      value: {
        path: '/tenants',
        params: {},
        query: {},
        meta: {}
      }
    }
  }
}))

// Mock request module
vi.mock('@/api/request', () => ({
  default: {
    get: vi.fn(() => Promise.resolve({ data: {} })),
    post: vi.fn(() => Promise.resolve({ data: {} })),
    put: vi.fn(() => Promise.resolve({ data: {} })),
    delete: vi.fn(() => Promise.resolve({ data: {} })),
    interceptors: {
      request: { use: vi.fn() },
      response: { use: vi.fn() }
    }
  }
}))

vi.mock('@/api/tenant', () => ({
  getTenantList: vi.fn(),
  getTenantDetail: vi.fn(),
  createTenant: vi.fn(),
  updateTenant: vi.fn(),
  deleteTenant: vi.fn(),
  getTenantStats: vi.fn(),
  getTenantContracts: vi.fn()
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

// Mock vue-router
vi.mock('vue-router', () => {
  const mockRouter = {
    push: vi.fn(),
    replace: vi.fn(),
    go: vi.fn(),
    back: vi.fn(),
    beforeEach: vi.fn(),
    afterEach: vi.fn(),
    onError: vi.fn(),
    currentRoute: {
      value: {
        path: '/tenants',
        params: {},
        query: {},
        meta: {}
      }
    }
  }
  return {
    useRouter: () => mockRouter,
    useRoute: () => ({
      path: '/tenants',
      params: {},
      query: {},
      meta: {}
    }),
    createRouter: vi.fn(() => mockRouter),
    createWebHistory: vi.fn(() => ({})),
    RouterLink: { name: 'RouterLink', template: '<a><slot /></a>' },
    RouterView: { name: 'RouterView', template: '<div><slot /></div>' }
  }
})

// Mock @element-plus/icons-vue
vi.mock('@element-plus/icons-vue', () => ({
  Plus: { name: 'Plus', template: '<i>plus</i>' },
  Search: { name: 'Search', template: '<i>search</i>' },
  Refresh: { name: 'Refresh', template: '<i>refresh</i>' },
  User: { name: 'User', template: '<i>user</i>' },
  CircleCheck: { name: 'CircleCheck', template: '<i>circle-check</i>' },
  CircleClose: { name: 'CircleClose', template: '<i>circle-close</i>' },
  Warning: { name: 'Warning', template: '<i>warning</i>' },
  ArrowDown: { name: 'ArrowDown', template: '<i>arrow-down</i>' }
}))

// Mock dayjs
vi.mock('dayjs', () => ({
  default: (date) => ({
    format: (formatStr) => {
      if (!date) return '-'
      // Simple format implementation
      const d = new Date(date)
      if (isNaN(d.getTime())) return '-'
      const year = d.getFullYear()
      const month = String(d.getMonth() + 1).padStart(2, '0')
      const day = String(d.getDate()).padStart(2, '0')
      const hours = String(d.getHours()).padStart(2, '0')
      const minutes = String(d.getMinutes()).padStart(2, '0')
      if (formatStr === 'YYYY-MM-DD HH:mm') {
        return `${year}-${month}-${day} ${hours}:${minutes}`
      }
      return `${year}-${month}-${day}`
    }
  })
}))

const mockPush = vi.fn()
const mockRouter = {
  push: mockPush,
  replace: vi.fn(),
  go: vi.fn(),
  back: vi.fn()
}

// ============================================
// 测试工具函数
// ============================================

/**
 * 创建组件包装器
 */
function createWrapper(options = {}) {
  const pinia = createPinia()
  setActivePinia(pinia)

  // 设置用户 store
  const userStore = useUserStore()
  userStore.setUserInfo({
    id: 1,
    username: 'admin',
    role: 'admin',
    user_type: 'admin'
  })

  return mount(TenantList, {
    global: {
      plugins: [pinia],
      mocks: {
        $router: mockRouter,
        $route: {
          path: '/tenants',
          params: {},
          query: {}
        }
      },
      stubs: {
        'el-card': true,
        'el-button': true,
        'el-input': true,
        'el-select': true,
        'el-option': true,
        'el-form': true,
        'el-form-item': true,
        'el-table': true,
        'el-table-column': true,
        'el-tag': true,
        'el-dialog': true,
        'el-pagination': true,
        'el-row': true,
        'el-col': true,
        'el-icon': true,
        'el-divider': true,
        'el-dropdown': true,
        'el-dropdown-menu': true,
        'el-dropdown-item': true,
        'el-descriptions': true,
        'el-descriptions-item': true,
        'el-link': true,
        RouterLink: true,
        RouterView: true
      }
    },
    ...options
  })
}

/**
 * 重置所有模拟
 */
function resetAllMocks() {
  vi.clearAllMocks()
  tenantApi.getTenantList.mockReset()
  tenantApi.getTenantDetail.mockReset()
  tenantApi.createTenant.mockReset()
  tenantApi.updateTenant.mockReset()
  tenantApi.deleteTenant.mockReset()
  tenantApi.getTenantStats.mockReset()
  tenantApi.getTenantContracts.mockReset()
  ElMessage.success.mockClear()
  ElMessage.error.mockClear()
  ElMessageBox.confirm.mockClear()
  mockPush.mockClear()
}

// ============================================
// 测试用例
// ============================================

describe('租客管理页面 - TenantList.vue', () => {
  beforeEach(() => {
    resetAllMocks()
  })

  afterEach(() => {
    vi.clearAllTimers()
  })

  // ============================================
  // 1. 测试租客列表展示
  // ============================================
  describe('1. 租客列表展示', () => {
    it('1.1 页面加载时应该自动获取租客列表', async () => {
      // 设置 mock 返回值
      tenantApi.getTenantList.mockResolvedValue({
        data: {
          items: mockTenants,
          pagination: {
            total: 3,
            page: 1,
            per_page: 20,
            pages: 1
          }
        }
      })

      tenantApi.getTenantStats.mockResolvedValue({
        data: mockStatistics
      })

      const wrapper = createWrapper()
      await flushPromises()

      // 验证 API 被调用
      expect(tenantApi.getTenantList).toHaveBeenCalledTimes(1)
      expect(tenantApi.getTenantList).toHaveBeenCalledWith({
        page: 1,
        per_page: 20,
        keyword: '',
        status: ''
      })

      wrapper.unmount()
    })

    it('1.2 应该正确显示租客列表数据', async () => {
      tenantApi.getTenantList.mockResolvedValue({
        data: {
          items: mockTenants,
          pagination: {
            total: 3,
            page: 1,
            per_page: 20,
            pages: 1
          }
        }
      })

      tenantApi.getTenantStats.mockResolvedValue({
        data: mockStatistics
      })

      const wrapper = createWrapper()
      await flushPromises()

      // 验证列表数据
      expect(wrapper.vm.tenantList).toHaveLength(3)
      expect(wrapper.vm.tenantList[0].name).toBe('张三')
      expect(wrapper.vm.tenantList[1].name).toBe('李四')
      expect(wrapper.vm.tenantList[2].name).toBe('王五')

      // 验证分页数据
      expect(wrapper.vm.pagination.total).toBe(3)

      wrapper.unmount()
    })

    it('1.3 应该正确显示统计信息', async () => {
      tenantApi.getTenantList.mockResolvedValue({
        data: {
          items: mockTenants,
          pagination: { total: 3, page: 1, per_page: 20, pages: 1 }
        }
      })

      tenantApi.getTenantStats.mockResolvedValue({
        data: mockStatistics
      })

      const wrapper = createWrapper()
      await flushPromises()

      // 验证统计信息
      expect(wrapper.vm.statistics.total).toBe(10)
      expect(wrapper.vm.statistics.active).toBe(6)
      expect(wrapper.vm.statistics.expired).toBe(3)
      expect(wrapper.vm.statistics.blacklisted).toBe(1)

      wrapper.unmount()
    })

    it('1.4 分页变化时应该重新加载数据', async () => {
      tenantApi.getTenantList.mockResolvedValue({
        data: {
          items: mockTenants,
          pagination: {
            total: 30,
            page: 2,
            per_page: 20,
            pages: 2
          }
        }
      })

      tenantApi.getTenantStats.mockResolvedValue({
        data: mockStatistics
      })

      const wrapper = createWrapper()
      await flushPromises()

      // 清除之前的调用
      tenantApi.getTenantList.mockClear()

      // 触发页码变化
      wrapper.vm.handlePageChange(2)
      await flushPromises()

      // 验证 API 被调用且页码正确
      expect(tenantApi.getTenantList).toHaveBeenCalledWith({
        page: 2,
        per_page: 20,
        keyword: '',
        status: ''
      })

      wrapper.unmount()
    })

    it('1.5 每页数量变化时应该重新加载数据', async () => {
      tenantApi.getTenantList.mockResolvedValue({
        data: {
          items: mockTenants,
          pagination: {
            total: 30,
            page: 1,
            per_page: 50,
            pages: 1
          }
        }
      })

      tenantApi.getTenantStats.mockResolvedValue({
        data: mockStatistics
      })

      const wrapper = createWrapper()
      await flushPromises()

      // 清除之前的调用
      tenantApi.getTenantList.mockClear()

      // 触发每页数量变化
      wrapper.vm.handleSizeChange(50)
      await flushPromises()

      // 验证 API 被调用且参数正确
      expect(tenantApi.getTenantList).toHaveBeenCalledWith({
        page: 1,
        per_page: 50,
        keyword: '',
        status: ''
      })

      wrapper.unmount()
    })

    it('1.6 加载数据时应该显示 loading 状态', async () => {
      // 创建一个延迟的 Promise
      let resolvePromise
      tenantApi.getTenantList.mockImplementation(() => {
        return new Promise((resolve) => {
          resolvePromise = resolve
        })
      })

      tenantApi.getTenantStats.mockResolvedValue({
        data: mockStatistics
      })

      const wrapper = createWrapper()

      // 验证 loading 状态为 true
      expect(wrapper.vm.loading).toBe(true)

      // 解决 Promise
      resolvePromise({
        data: {
          items: mockTenants,
          pagination: { total: 3, page: 1, per_page: 20, pages: 1 }
        }
      })
      await flushPromises()

      // 验证 loading 状态为 false
      expect(wrapper.vm.loading).toBe(false)

      wrapper.unmount()
    })

    it('1.7 加载失败时应该显示错误提示', async () => {
      tenantApi.getTenantList.mockRejectedValue(new Error('网络错误'))

      tenantApi.getTenantStats.mockResolvedValue({
        data: mockStatistics
      })

      const wrapper = createWrapper()
      await flushPromises()

      // 验证错误提示
      expect(ElMessage.error).toHaveBeenCalledWith('加载租客列表失败')
      expect(wrapper.vm.loading).toBe(false)

      wrapper.unmount()
    })
  })

  // ============================================
  // 2. 测试租客搜索
  // ============================================
  describe('2. 租客搜索', () => {
    it('2.1 按关键词搜索应该正确传递参数', async () => {
      tenantApi.getTenantList.mockResolvedValue({
        data: {
          items: [mockTenants[0]],
          pagination: { total: 1, page: 1, per_page: 20, pages: 1 }
        }
      })

      tenantApi.getTenantStats.mockResolvedValue({
        data: mockStatistics
      })

      const wrapper = createWrapper()
      await flushPromises()

      // 清除之前的调用
      tenantApi.getTenantList.mockClear()

      // 设置搜索关键词
      wrapper.vm.searchForm.keyword = '张三'
      wrapper.vm.handleSearch()
      await flushPromises()

      // 验证 API 被调用且参数正确
      expect(tenantApi.getTenantList).toHaveBeenCalledWith({
        page: 1,
        per_page: 20,
        keyword: '张三',
        status: ''
      })

      wrapper.unmount()
    })

    it('2.2 按状态筛选应该正确传递参数', async () => {
      tenantApi.getTenantList.mockResolvedValue({
        data: {
          items: [mockTenants[0]],
          pagination: { total: 1, page: 1, per_page: 20, pages: 1 }
        }
      })

      tenantApi.getTenantStats.mockResolvedValue({
        data: mockStatistics
      })

      const wrapper = createWrapper()
      await flushPromises()

      // 清除之前的调用
      tenantApi.getTenantList.mockClear()

      // 设置状态筛选
      wrapper.vm.searchForm.status = 'active'
      wrapper.vm.handleSearch()
      await flushPromises()

      // 验证 API 被调用且参数正确
      expect(tenantApi.getTenantList).toHaveBeenCalledWith({
        page: 1,
        per_page: 20,
        keyword: '',
        status: 'active'
      })

      wrapper.unmount()
    })

    it('2.3 同时使用关键词和状态筛选', async () => {
      tenantApi.getTenantList.mockResolvedValue({
        data: {
          items: [mockTenants[0]],
          pagination: { total: 1, page: 1, per_page: 20, pages: 1 }
        }
      })

      tenantApi.getTenantStats.mockResolvedValue({
        data: mockStatistics
      })

      const wrapper = createWrapper()
      await flushPromises()

      // 清除之前的调用
      tenantApi.getTenantList.mockClear()

      // 设置搜索条件
      wrapper.vm.searchForm.keyword = '张'
      wrapper.vm.searchForm.status = 'active'
      wrapper.vm.handleSearch()
      await flushPromises()

      // 验证 API 被调用且参数正确
      expect(tenantApi.getTenantList).toHaveBeenCalledWith({
        page: 1,
        per_page: 20,
        keyword: '张',
        status: 'active'
      })

      wrapper.unmount()
    })

    it('2.4 重置搜索条件应该清空所有筛选', async () => {
      tenantApi.getTenantList.mockResolvedValue({
        data: {
          items: mockTenants,
          pagination: { total: 3, page: 1, per_page: 20, pages: 1 }
        }
      })

      tenantApi.getTenantStats.mockResolvedValue({
        data: mockStatistics
      })

      const wrapper = createWrapper()
      await flushPromises()

      // 设置搜索条件
      wrapper.vm.searchForm.keyword = '张'
      wrapper.vm.searchForm.status = 'active'

      // 清除之前的调用
      tenantApi.getTenantList.mockClear()

      // 重置
      wrapper.vm.handleReset()
      await flushPromises()

      // 验证搜索条件被清空
      expect(wrapper.vm.searchForm.keyword).toBe('')
      expect(wrapper.vm.searchForm.status).toBe('')
      expect(wrapper.vm.pagination.page).toBe(1)

      // 验证 API 被调用
      expect(tenantApi.getTenantList).toHaveBeenCalledWith({
        page: 1,
        per_page: 20,
        keyword: '',
        status: ''
      })

      wrapper.unmount()
    })

    it('2.5 搜索时应该重置页码为 1', async () => {
      tenantApi.getTenantList.mockResolvedValue({
        data: {
          items: mockTenants,
          pagination: { total: 30, page: 1, per_page: 20, pages: 2 }
        }
      })

      tenantApi.getTenantStats.mockResolvedValue({
        data: mockStatistics
      })

      const wrapper = createWrapper()
      await flushPromises()

      // 设置当前页码为 2
      wrapper.vm.pagination.page = 2

      // 清除之前的调用
      tenantApi.getTenantList.mockClear()

      // 搜索
      wrapper.vm.searchForm.keyword = '张'
      wrapper.vm.handleSearch()
      await flushPromises()

      // 验证页码被重置为 1
      expect(wrapper.vm.pagination.page).toBe(1)

      wrapper.unmount()
    })
  })

  // ============================================
  // 3. 测试新增租客表单
  // ============================================
  describe('3. 新增租客表单', () => {
    it('3.1 点击新增按钮应该打开对话框', async () => {
      tenantApi.getTenantList.mockResolvedValue({
        data: {
          items: mockTenants,
          pagination: { total: 3, page: 1, per_page: 20, pages: 1 }
        }
      })

      tenantApi.getTenantStats.mockResolvedValue({
        data: mockStatistics
      })

      const wrapper = createWrapper()
      await flushPromises()

      // 点击新增按钮
      wrapper.vm.handleAdd()
      await flushPromises()

      // 验证对话框状态
      expect(wrapper.vm.dialogVisible).toBe(true)
      expect(wrapper.vm.dialogTitle).toBe('新增租客')
      expect(wrapper.vm.currentTenant).toEqual({})

      wrapper.unmount()
    })

    it('3.2 新增对话框应该重置表单数据', async () => {
      tenantApi.getTenantList.mockResolvedValue({
        data: {
          items: mockTenants,
          pagination: { total: 3, page: 1, per_page: 20, pages: 1 }
        }
      })

      tenantApi.getTenantStats.mockResolvedValue({
        data: mockStatistics
      })

      const wrapper = createWrapper()
      await flushPromises()

      // 先编辑一个租客，设置表单数据
      wrapper.vm.tenantForm.name = '已存在的名字'
      wrapper.vm.tenantForm.phone = '13800138000'

      // 点击新增按钮
      wrapper.vm.handleAdd()
      await flushPromises()

      // 验证表单数据被重置
      expect(wrapper.vm.tenantForm.name).toBe('')
      expect(wrapper.vm.tenantForm.phone).toBe('')
      expect(wrapper.vm.tenantForm.id_card).toBe('')
      expect(wrapper.vm.tenantForm.email).toBe('')

      wrapper.unmount()
    })

    it('3.3 提交新增表单应该调用 createTenant API', async () => {
      tenantApi.getTenantList.mockResolvedValue({
        data: {
          items: mockTenants,
          pagination: { total: 3, page: 1, per_page: 20, pages: 1 }
        }
      })

      tenantApi.getTenantStats.mockResolvedValue({
        data: mockStatistics
      })

      tenantApi.createTenant.mockResolvedValue({
        data: { id: 4, ...mockTenantDetail }
      })

      const wrapper = createWrapper()
      await flushPromises()

      // 打开新增对话框
      wrapper.vm.handleAdd()
      await flushPromises()

      // 模拟表单数据
      wrapper.vm.tenantForm.name = '新租客'
      wrapper.vm.tenantForm.phone = '13900139000'
      wrapper.vm.tenantForm.id_card = '110101199004041234'
      wrapper.vm.tenantForm.email = 'new@example.com'

      // 模拟表单验证通过
      wrapper.vm.tenantFormRef = {
        validate: vi.fn((callback) => callback(true))
      }

      // 提交表单
      await wrapper.vm.handleSubmit()
      await flushPromises()

      // 验证 API 被调用
      expect(tenantApi.createTenant).toHaveBeenCalled()
      expect(ElMessage.success).toHaveBeenCalledWith('创建成功')
      expect(wrapper.vm.dialogVisible).toBe(false)

      wrapper.unmount()
    })

    it('3.4 新增成功后应该刷新列表和统计', async () => {
      tenantApi.getTenantList.mockResolvedValue({
        data: {
          items: mockTenants,
          pagination: { total: 3, page: 1, per_page: 20, pages: 1 }
        }
      })

      tenantApi.getTenantStats.mockResolvedValue({
        data: mockStatistics
      })

      tenantApi.createTenant.mockResolvedValue({
        data: { id: 4 }
      })

      const wrapper = createWrapper()
      await flushPromises()

      // 清除之前的调用
      tenantApi.getTenantList.mockClear()
      tenantApi.getTenantStats.mockClear()

      // 打开新增对话框
      wrapper.vm.handleAdd()
      await flushPromises()

      // 模拟表单数据
      wrapper.vm.tenantForm.name = '新租客'
      wrapper.vm.tenantForm.phone = '13900139000'

      // 模拟表单验证通过
      wrapper.vm.tenantFormRef = {
        validate: vi.fn((callback) => callback(true))
      }

      // 提交表单
      await wrapper.vm.handleSubmit()
      await flushPromises()

      // 验证列表和统计被刷新
      expect(tenantApi.getTenantList).toHaveBeenCalledTimes(1)
      expect(tenantApi.getTenantStats).toHaveBeenCalledTimes(1)

      wrapper.unmount()
    })

    it('3.5 新增失败应该显示错误提示', async () => {
      tenantApi.getTenantList.mockResolvedValue({
        data: {
          items: mockTenants,
          pagination: { total: 3, page: 1, per_page: 20, pages: 1 }
        }
      })

      tenantApi.getTenantStats.mockResolvedValue({
        data: mockStatistics
      })

      tenantApi.createTenant.mockRejectedValue({
        message: '手机号已被使用'
      })

      const wrapper = createWrapper()
      await flushPromises()

      // 打开新增对话框
      wrapper.vm.handleAdd()
      await flushPromises()

      // 模拟表单数据
      wrapper.vm.tenantForm.name = '新租客'
      wrapper.vm.tenantForm.phone = '13800138001'

      // 模拟表单验证通过
      wrapper.vm.tenantFormRef = {
        validate: vi.fn((callback) => callback(true))
      }

      // 提交表单
      await wrapper.vm.handleSubmit()
      await flushPromises()

      // 验证错误提示
      expect(ElMessage.error).toHaveBeenCalledWith('手机号已被使用')
      expect(wrapper.vm.dialogVisible).toBe(true) // 对话框保持打开

      wrapper.unmount()
    })

    it('3.6 表单验证失败不应该提交', async () => {
      tenantApi.getTenantList.mockResolvedValue({
        data: {
          items: mockTenants,
          pagination: { total: 3, page: 1, per_page: 20, pages: 1 }
        }
      })

      tenantApi.getTenantStats.mockResolvedValue({
        data: mockStatistics
      })

      const wrapper = createWrapper()
      await flushPromises()

      // 打开新增对话框
      wrapper.vm.handleAdd()
      await flushPromises()

      // 模拟表单验证失败
      wrapper.vm.tenantFormRef = {
        validate: vi.fn((callback) => callback(false))
      }

      // 提交表单
      await wrapper.vm.handleSubmit()
      await flushPromises()

      // 验证 API 没有被调用
      expect(tenantApi.createTenant).not.toHaveBeenCalled()

      wrapper.unmount()
    })
  })

  // ============================================
  // 4. 测试编辑租客表单
  // ============================================
  describe('4. 编辑租客表单', () => {
    it('4.1 点击编辑按钮应该打开对话框并填充数据', async () => {
      tenantApi.getTenantList.mockResolvedValue({
        data: {
          items: mockTenants,
          pagination: { total: 3, page: 1, per_page: 20, pages: 1 }
        }
      })

      tenantApi.getTenantStats.mockResolvedValue({
        data: mockStatistics
      })

      const wrapper = createWrapper()
      await flushPromises()

      // 点击编辑按钮
      wrapper.vm.handleEdit(mockTenants[0])
      await flushPromises()

      // 验证对话框状态
      expect(wrapper.vm.dialogVisible).toBe(true)
      expect(wrapper.vm.dialogTitle).toBe('编辑租客')
      expect(wrapper.vm.currentTenant.name).toBe('张三')
      expect(wrapper.vm.tenantForm.name).toBe('张三')
      expect(wrapper.vm.tenantForm.phone).toBe('13800138001')

      wrapper.unmount()
    })

    it('4.2 提交编辑表单应该调用 updateTenant API', async () => {
      tenantApi.getTenantList.mockResolvedValue({
        data: {
          items: mockTenants,
          pagination: { total: 3, page: 1, per_page: 20, pages: 1 }
        }
      })

      tenantApi.getTenantStats.mockResolvedValue({
        data: mockStatistics
      })

      tenantApi.updateTenant.mockResolvedValue({
        data: { ...mockTenantDetail, name: '张三更新' }
      })

      const wrapper = createWrapper()
      await flushPromises()

      // 打开编辑对话框
      wrapper.vm.handleEdit(mockTenants[0])
      await flushPromises()

      // 修改表单数据
      wrapper.vm.tenantForm.name = '张三更新'
      wrapper.vm.tenantForm.remark = '更新备注'

      // 模拟表单验证通过
      wrapper.vm.tenantFormRef = {
        validate: vi.fn((callback) => callback(true))
      }

      // 提交表单
      await wrapper.vm.handleSubmit()
      await flushPromises()

      // 验证 API 被调用
      expect(tenantApi.updateTenant).toHaveBeenCalledWith(1, expect.objectContaining({
        name: '张三更新',
        remark: '更新备注'
      }))
      expect(ElMessage.success).toHaveBeenCalledWith('编辑成功')
      expect(wrapper.vm.dialogVisible).toBe(false)

      wrapper.unmount()
    })

    it('4.3 编辑成功后应该刷新列表', async () => {
      tenantApi.getTenantList.mockResolvedValue({
        data: {
          items: mockTenants,
          pagination: { total: 3, page: 1, per_page: 20, pages: 1 }
        }
      })

      tenantApi.getTenantStats.mockResolvedValue({
        data: mockStatistics
      })

      tenantApi.updateTenant.mockResolvedValue({
        data: mockTenantDetail
      })

      const wrapper = createWrapper()
      await flushPromises()

      // 清除之前的调用
      tenantApi.getTenantList.mockClear()

      // 打开编辑对话框
      wrapper.vm.handleEdit(mockTenants[0])
      await flushPromises()

      // 模拟表单验证通过
      wrapper.vm.tenantFormRef = {
        validate: vi.fn((callback) => callback(true))
      }

      // 提交表单
      await wrapper.vm.handleSubmit()
      await flushPromises()

      // 验证列表被刷新
      expect(tenantApi.getTenantList).toHaveBeenCalledTimes(1)

      wrapper.unmount()
    })

    it('4.4 编辑失败应该显示错误提示', async () => {
      tenantApi.getTenantList.mockResolvedValue({
        data: {
          items: mockTenants,
          pagination: { total: 3, page: 1, per_page: 20, pages: 1 }
        }
      })

      tenantApi.getTenantStats.mockResolvedValue({
        data: mockStatistics
      })

      tenantApi.updateTenant.mockRejectedValue({
        message: '更新失败，请重试'
      })

      const wrapper = createWrapper()
      await flushPromises()

      // 打开编辑对话框
      wrapper.vm.handleEdit(mockTenants[0])
      await flushPromises()

      // 模拟表单验证通过
      wrapper.vm.tenantFormRef = {
        validate: vi.fn((callback) => callback(true))
      }

      // 提交表单
      await wrapper.vm.handleSubmit()
      await flushPromises()

      // 验证错误提示
      expect(ElMessage.error).toHaveBeenCalledWith('更新失败，请重试')
      expect(wrapper.vm.dialogVisible).toBe(true) // 对话框保持打开

      wrapper.unmount()
    })

    it('4.5 从详情对话框编辑租客', async () => {
      tenantApi.getTenantList.mockResolvedValue({
        data: {
          items: mockTenants,
          pagination: { total: 3, page: 1, per_page: 20, pages: 1 }
        }
      })

      tenantApi.getTenantStats.mockResolvedValue({
        data: mockStatistics
      })

      tenantApi.getTenantDetail.mockResolvedValue({
        data: mockTenantDetail
      })

      const wrapper = createWrapper()
      await flushPromises()

      // 打开详情对话框
      await wrapper.vm.handleView({ id: 1 })
      await flushPromises()

      expect(wrapper.vm.detailVisible).toBe(true)

      // 从详情编辑
      wrapper.vm.handleEditFromDetail()
      await flushPromises()

      // 验证详情对话框关闭
      expect(wrapper.vm.detailVisible).toBe(false)

      // 验证编辑对话框打开
      expect(wrapper.vm.dialogVisible).toBe(true)
      expect(wrapper.vm.dialogTitle).toBe('编辑租客')

      wrapper.unmount()
    })
  })

  // ============================================
  // 5. 测试其他功能
  // ============================================
  describe('5. 其他功能', () => {
    // 删除租客
    describe('5.1 删除租客', () => {
      it('5.1.1 点击删除按钮应该显示确认对话框', async () => {
        tenantApi.getTenantList.mockResolvedValue({
          data: {
            items: mockTenants,
            pagination: { total: 3, page: 1, per_page: 20, pages: 1 }
          }
        })

        tenantApi.getTenantStats.mockResolvedValue({
          data: mockStatistics
        })

        ElMessageBox.confirm.mockResolvedValue('confirm')

        const wrapper = createWrapper()
        await flushPromises()

        // 点击删除按钮
        wrapper.vm.handleDelete(mockTenants[0])
        await flushPromises()

        // 验证确认对话框被调用
        expect(ElMessageBox.confirm).toHaveBeenCalledWith(
          '确定要删除该租客吗？删除后不可恢复！',
          '警告',
          expect.objectContaining({
            confirmButtonText: '确定',
            cancelButtonText: '取消',
            type: 'warning'
          })
        )

        wrapper.unmount()
      })

      it('5.1.2 确认删除应该调用 deleteTenant API', async () => {
        tenantApi.getTenantList.mockResolvedValue({
          data: {
            items: mockTenants,
            pagination: { total: 3, page: 1, per_page: 20, pages: 1 }
          }
        })

        tenantApi.getTenantStats.mockResolvedValue({
          data: mockStatistics
        })

        tenantApi.deleteTenant.mockResolvedValue({})

        ElMessageBox.confirm.mockResolvedValue('confirm')

        const wrapper = createWrapper()
        await flushPromises()

        // 确认删除
        await wrapper.vm.handleDelete(mockTenants[0])
        await flushPromises()

        // 验证 API 被调用
        expect(tenantApi.deleteTenant).toHaveBeenCalledWith(1)
        expect(ElMessage.success).toHaveBeenCalledWith('删除成功')

        wrapper.unmount()
      })

      it('5.1.3 取消删除不应该调用 API', async () => {
        tenantApi.getTenantList.mockResolvedValue({
          data: {
            items: mockTenants,
            pagination: { total: 3, page: 1, per_page: 20, pages: 1 }
          }
        })

        tenantApi.getTenantStats.mockResolvedValue({
          data: mockStatistics
        })

        ElMessageBox.confirm.mockRejectedValue(new Error('cancel'))

        const wrapper = createWrapper()
        await flushPromises()

        // 取消删除
        await wrapper.vm.handleDelete(mockTenants[0])
        await flushPromises()

        // 验证删除 API 没有被调用
        expect(tenantApi.deleteTenant).not.toHaveBeenCalled()

        wrapper.unmount()
      })
    })

    // 变更租客状态
    describe('5.2 变更租客状态', () => {
      it('5.2.1 变更状态应该显示确认对话框', async () => {
        tenantApi.getTenantList.mockResolvedValue({
          data: {
            items: mockTenants,
            pagination: { total: 3, page: 1, per_page: 20, pages: 1 }
          }
        })

        tenantApi.getTenantStats.mockResolvedValue({
          data: mockStatistics
        })

        ElMessageBox.confirm.mockResolvedValue('confirm')

        const wrapper = createWrapper()
        await flushPromises()

        // 变更状态
        wrapper.vm.handleChangeStatus('expired', mockTenants[0])
        await flushPromises()

        // 验证确认对话框被调用
        expect(ElMessageBox.confirm).toHaveBeenCalledWith(
          expect.stringContaining('张三'),
          '提示',
          expect.objectContaining({
            confirmButtonText: '确定',
            cancelButtonText: '取消',
            type: 'warning'
          })
        )

        wrapper.unmount()
      })

      it('5.2.2 确认变更状态应该调用 updateTenant API', async () => {
        tenantApi.getTenantList.mockResolvedValue({
          data: {
            items: mockTenants,
            pagination: { total: 3, page: 1, per_page: 20, pages: 1 }
          }
        })

        tenantApi.getTenantStats.mockResolvedValue({
          data: mockStatistics
        })

        tenantApi.updateTenant.mockResolvedValue({})

        ElMessageBox.confirm.mockResolvedValue('confirm')

        const wrapper = createWrapper()
        await flushPromises()

        // 确认变更状态
        await wrapper.vm.handleChangeStatus('expired', mockTenants[0])
        await flushPromises()

        // 验证 API 被调用
        expect(tenantApi.updateTenant).toHaveBeenCalledWith(1, { status: 'expired' })
        expect(ElMessage.success).toHaveBeenCalledWith('状态修改成功')

        wrapper.unmount()
      })
    })

    // 查看租客详情
    describe('5.3 查看租客详情', () => {
      it('5.3.1 点击详情按钮应该加载并显示租客详情', async () => {
        tenantApi.getTenantList.mockResolvedValue({
          data: {
            items: mockTenants,
            pagination: { total: 3, page: 1, per_page: 20, pages: 1 }
          }
        })

        tenantApi.getTenantStats.mockResolvedValue({
          data: mockStatistics
        })

        tenantApi.getTenantDetail.mockResolvedValue({
          data: mockTenantDetail
        })

        const wrapper = createWrapper()
        await flushPromises()

        // 点击详情按钮
        await wrapper.vm.handleView({ id: 1 })
        await flushPromises()

        // 验证详情 API 被调用
        expect(tenantApi.getTenantDetail).toHaveBeenCalledWith(1)

        // 验证详情对话框状态
        expect(wrapper.vm.detailVisible).toBe(true)
        expect(wrapper.vm.currentTenant.name).toBe('张三')

        wrapper.unmount()
      })

      it('5.3.2 查看租客合同列表', async () => {
        tenantApi.getTenantList.mockResolvedValue({
          data: {
            items: mockTenants,
            pagination: { total: 3, page: 1, per_page: 20, pages: 1 }
          }
        })

        tenantApi.getTenantStats.mockResolvedValue({
          data: mockStatistics
        })

        tenantApi.getTenantDetail.mockResolvedValue({
          data: mockTenantDetail
        })

        tenantApi.getTenantContracts.mockResolvedValue({
          data: mockContracts
        })

        const wrapper = createWrapper()
        await flushPromises()

        // 打开详情对话框
        await wrapper.vm.handleView({ id: 1 })
        await flushPromises()

        // 查看合同列表
        await wrapper.vm.handleViewContracts({ id: 1 })
        await flushPromises()

        // 验证合同 API 被调用
        expect(tenantApi.getTenantContracts).toHaveBeenCalledWith(1)
        expect(wrapper.vm.contractsVisible).toBe(true)
        expect(wrapper.vm.tenantContracts).toHaveLength(2)

        wrapper.unmount()
      })
    })
  })

  // ============================================
  // 6. 测试辅助函数
  // ============================================
  describe('6. 辅助函数', () => {
    it('6.1 getStatusType 应该返回正确的状态类型', async () => {
      tenantApi.getTenantList.mockResolvedValue({
        data: {
          items: mockTenants,
          pagination: { total: 3, page: 1, per_page: 20, pages: 1 }
        }
      })

      tenantApi.getTenantStats.mockResolvedValue({
        data: mockStatistics
      })

      const wrapper = createWrapper()
      await flushPromises()

      expect(wrapper.vm.getStatusType('active')).toBe('success')
      expect(wrapper.vm.getStatusType('expired')).toBe('info')
      expect(wrapper.vm.getStatusType('blacklisted')).toBe('danger')
      expect(wrapper.vm.getStatusType('unknown')).toBe('info')

      wrapper.unmount()
    })

    it('6.2 getStatusText 应该返回正确的状态文本', async () => {
      tenantApi.getTenantList.mockResolvedValue({
        data: {
          items: mockTenants,
          pagination: { total: 3, page: 1, per_page: 20, pages: 1 }
        }
      })

      tenantApi.getTenantStats.mockResolvedValue({
        data: mockStatistics
      })

      const wrapper = createWrapper()
      await flushPromises()

      expect(wrapper.vm.getStatusText('active')).toBe('在租')
      expect(wrapper.vm.getStatusText('expired')).toBe('已退租')
      expect(wrapper.vm.getStatusText('blacklisted')).toBe('黑名单')

      wrapper.unmount()
    })

    it('6.3 formatDate 应该正确格式化日期', async () => {
      tenantApi.getTenantList.mockResolvedValue({
        data: {
          items: mockTenants,
          pagination: { total: 3, page: 1, per_page: 20, pages: 1 }
        }
      })

      tenantApi.getTenantStats.mockResolvedValue({
        data: mockStatistics
      })

      const wrapper = createWrapper()
      await flushPromises()

      expect(wrapper.vm.formatDate('2024-01-15T10:30:00')).toBe('2024-01-15 10:30')
      expect(wrapper.vm.formatDate('')).toBe('-')
      expect(wrapper.vm.formatDate(null)).toBe('-')

      wrapper.unmount()
    })

    it('6.4 getContractStatusType 应该返回正确的合同状态类型', async () => {
      tenantApi.getTenantList.mockResolvedValue({
        data: {
          items: mockTenants,
          pagination: { total: 3, page: 1, per_page: 20, pages: 1 }
        }
      })

      tenantApi.getTenantStats.mockResolvedValue({
        data: mockStatistics
      })

      const wrapper = createWrapper()
      await flushPromises()

      expect(wrapper.vm.getContractStatusType('active')).toBe('success')
      expect(wrapper.vm.getContractStatusType('expired')).toBe('info')
      expect(wrapper.vm.getContractStatusType('terminated')).toBe('danger')

      wrapper.unmount()
    })

    it('6.5 getContractStatusText 应该返回正确的合同状态文本', async () => {
      tenantApi.getTenantList.mockResolvedValue({
        data: {
          items: mockTenants,
          pagination: { total: 3, page: 1, per_page: 20, pages: 1 }
        }
      })

      tenantApi.getTenantStats.mockResolvedValue({
        data: mockStatistics
      })

      const wrapper = createWrapper()
      await flushPromises()

      expect(wrapper.vm.getContractStatusText('active')).toBe('生效中')
      expect(wrapper.vm.getContractStatusText('expired')).toBe('已到期')
      expect(wrapper.vm.getContractStatusText('terminated')).toBe('已终止')

      wrapper.unmount()
    })
  })
})
