/**
 * 房东管理页面测试用例
 * 测试范围：
 * 1. 列表数据加载和分页
 * 2. 搜索和筛选功能
 * 3. 新增房东表单
 * 4. 编辑房东表单
 * 5. 删除房东确认
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import LandlordList from '@/views/landlords/LandlordList.vue'
import * as landlordApi from '@/api/landlord'
import { useUserStore } from '@/store/user'
import { ElMessage, ElMessageBox } from 'element-plus'
// 从 mock 中导入 mock 函数
import { mockPush, mockReplace, mockGo, mockBack, mockBeforeEach, mockAfterEach, mockBeforeResolve, mockOnError } from 'vue-router'

// Mock vue-router - 所有 mock 函数都在回调内部创建
vi.mock('vue-router', () => {
  const mockPush = vi.fn()
  const mockReplace = vi.fn()
  const mockGo = vi.fn()
  const mockBack = vi.fn()
  const mockBeforeEach = vi.fn()
  const mockAfterEach = vi.fn()
  const mockBeforeResolve = vi.fn()
  const mockOnError = vi.fn()
  
  const mockRouter = {
    push: mockPush,
    replace: mockReplace,
    go: mockGo,
    back: mockBack,
    beforeEach: mockBeforeEach,
    afterEach: mockAfterEach,
    beforeResolve: mockBeforeResolve,
    onError: mockOnError,
    currentRoute: {
      value: {
        path: '/landlords',
        params: {},
        query: {},
        meta: {}
      }
    }
  }
  
  return {
    useRouter: () => mockRouter,
    useRoute: () => ({
      path: '/landlords',
      params: {},
      query: {}
    }),
    createRouter: vi.fn(() => mockRouter),
    createWebHistory: vi.fn(() => ({})),
    createWebHashHistory: vi.fn(() => ({})),
    createMemoryHistory: vi.fn(() => ({})),
    RouterView: { name: 'RouterView', template: '<div></div>' },
    RouterLink: { name: 'RouterLink', template: '<a><slot /></a>', props: ['to'] },
    // 导出 mock 函数以便在测试中使用
    __esModule: true,
    mockPush,
    mockReplace,
    mockGo,
    mockBack,
    mockBeforeEach,
    mockAfterEach,
    mockBeforeResolve,
    mockOnError
  }
})

// ============================================
// Mock API 响应数据
// ============================================

const mockLandlords = [
  {
    id: 1,
    name: '张房东',
    phone: '13800138001',
    id_card: '110101199001011234',
    bank_card: '6222001234567890123',
    bank_name: '中国工商银行',
    property_cert_no: '京房权证朝私字第123456号',
    property_address: '北京市朝阳区某某小区1号楼',
    status: 'active',
    houses_count: 3,
    contracts_count: 2,
    remark: '优质房东',
    created_at: '2024-01-15T10:30:00'
  },
  {
    id: 2,
    name: '李房东',
    phone: '13800138002',
    id_card: '110101199002021234',
    bank_card: '6222001234567890124',
    bank_name: '中国建设银行',
    property_cert_no: '京房权证海私字第654321号',
    property_address: '北京市海淀区某某路2号',
    status: 'inactive',
    houses_count: 1,
    contracts_count: 0,
    remark: '',
    created_at: '2024-02-20T14:20:00'
  },
  {
    id: 3,
    name: '王房东',
    phone: '13800138003',
    id_card: '110101199003031234',
    status: 'blacklisted',
    houses_count: 0,
    contracts_count: 0,
    remark: '违规操作',
    created_at: '2024-03-10T09:15:00'
  }
]

const mockLandlordDetail = {
  id: 1,
  name: '张房东',
  phone: '13800138001',
  id_card: '110101199001011234',
  bank_card: '6222001234567890123',
  bank_name: '中国工商银行',
  property_cert_no: '京房权证朝私字第123456号',
  property_address: '北京市朝阳区某某小区1号楼',
  status: 'active',
  houses_count: 3,
  contracts_count: 2,
  remark: '优质房东',
  created_at: '2024-01-15T10:30:00'
}

const mockHouses = [
  {
    id: 1,
    title: '朝阳区精装两居室',
    address: '北京市朝阳区某某小区1号楼101室',
    type: 'whole',
    rent_price: 8000,
    status: 'available'
  },
  {
    id: 2,
    title: '朝阳区合租主卧',
    address: '北京市朝阳区某某小区1号楼201室',
    type: 'shared',
    rent_price: 3000,
    status: 'rented'
  }
]

const mockContracts = [
  {
    id: 1,
    contract_no: 'LC202401150001',
    title: '张房东承包合同',
    amount: 500000,
    start_date: '2024-01-15',
    end_date: '2025-01-14',
    status: 'active'
  }
]

// ============================================
// Mock API 函数
// ============================================

vi.mock('@/api/landlord', () => ({
  getLandlordList: vi.fn(),
  getLandlordDetail: vi.fn(),
  createLandlord: vi.fn(),
  updateLandlord: vi.fn(),
  deleteLandlord: vi.fn(),
  getLandlordHouses: vi.fn(),
  getLandlordContracts: vi.fn()
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

  // 创建本地 mock router 对象
  const localMockRouter = {
    push: mockPush,
    replace: mockReplace,
    go: mockGo,
    back: mockBack,
    beforeEach: mockBeforeEach,
    afterEach: mockAfterEach,
    beforeResolve: mockBeforeResolve,
    onError: mockOnError,
    currentRoute: {
      value: {
        path: '/landlords',
        params: {},
        query: {},
        meta: {}
      }
    }
  }

  return mount(LandlordList, {
    global: {
      plugins: [pinia],
      mocks: {
        $router: localMockRouter,
        $route: {
          path: '/landlords',
          params: {},
          query: {}
        }
      },
      stubs: {
        LandlordForm: {
          name: 'LandlordForm',
          template: '<div class="mock-landlord-form"><slot /></div>',
          props: ['modelValue', 'isEdit', 'submitLoading', 'showDeleteButton', 'deleteDisabled'],
          emits: ['submit', 'cancel', 'delete', 'update:modelValue'],
          methods: {
            resetForm: vi.fn(),
            validate: vi.fn(() => Promise.resolve(true))
          }
        },
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
  landlordApi.getLandlordList.mockReset()
  landlordApi.getLandlordDetail.mockReset()
  landlordApi.createLandlord.mockReset()
  landlordApi.updateLandlord.mockReset()
  landlordApi.deleteLandlord.mockReset()
  landlordApi.getLandlordHouses.mockReset()
  landlordApi.getLandlordContracts.mockReset()
  ElMessage.success.mockClear()
  ElMessage.error.mockClear()
  ElMessageBox.confirm.mockClear()
  mockPush.mockClear()
}

// ============================================
// 测试用例
// ============================================

describe('房东管理页面 - LandlordList.vue', () => {
  beforeEach(() => {
    resetAllMocks()
  })

  afterEach(() => {
    vi.clearAllTimers()
  })

  // ============================================
  // 1. 测试列表数据加载和分页
  // ============================================
  describe('1. 列表数据加载和分页', () => {
    it('1.1 页面加载时应该自动获取房东列表', async () => {
      // 设置 mock 返回值
      landlordApi.getLandlordList.mockResolvedValue({
        success: true,
        data: {
          items: mockLandlords,
          pagination: {
            total: 3,
            page: 1,
            per_page: 10,
            pages: 1
          }
        }
      })

      const wrapper = createWrapper()
      await flushPromises()

      // 验证 API 被调用
      expect(landlordApi.getLandlordList).toHaveBeenCalledTimes(1)
      expect(landlordApi.getLandlordList).toHaveBeenCalledWith({
        page: 1,
        per_page: 10,
        keyword: '',
        status: ''
      })

      wrapper.unmount()
    })

    it('1.2 应该正确显示房东列表数据', async () => {
      landlordApi.getLandlordList.mockResolvedValue({
        success: true,
        data: {
          items: mockLandlords,
          pagination: {
            total: 3,
            page: 1,
            per_page: 10,
            pages: 1
          }
        }
      })

      const wrapper = createWrapper()
      await flushPromises()

      // 验证列表数据
      expect(wrapper.vm.landlordList).toHaveLength(3)
      expect(wrapper.vm.landlordList[0].name).toBe('张房东')
      expect(wrapper.vm.landlordList[1].name).toBe('李房东')
      expect(wrapper.vm.landlordList[2].name).toBe('王房东')

      // 验证分页数据
      expect(wrapper.vm.pagination.total).toBe(3)

      wrapper.unmount()
    })

    it('1.3 分页变化时应该重新加载数据', async () => {
      landlordApi.getLandlordList.mockResolvedValue({
        success: true,
        data: {
          items: mockLandlords,
          pagination: {
            total: 30,
            page: 2,
            per_page: 10,
            pages: 3
          }
        }
      })

      const wrapper = createWrapper()
      await flushPromises()

      // 清除之前的调用
      landlordApi.getLandlordList.mockClear()

      // 触发页码变化
      wrapper.vm.pagination.page = 2
      wrapper.vm.handlePageChange(2)
      await flushPromises()

      // 验证 API 被调用且页码正确
      expect(landlordApi.getLandlordList).toHaveBeenCalledWith({
        page: 2,
        per_page: 10,
        keyword: '',
        status: ''
      })

      wrapper.unmount()
    })

    it('1.4 每页数量变化时应该重新加载数据', async () => {
      landlordApi.getLandlordList.mockResolvedValue({
        success: true,
        data: {
          items: mockLandlords,
          pagination: {
            total: 30,
            page: 1,
            per_page: 20,
            pages: 2
          }
        }
      })

      const wrapper = createWrapper()
      await flushPromises()

      // 清除之前的调用
      landlordApi.getLandlordList.mockClear()

      // 触发每页数量变化
      wrapper.vm.handleSizeChange(20)
      await flushPromises()

      // 验证 API 被调用且参数正确
      expect(landlordApi.getLandlordList).toHaveBeenCalledWith({
        page: 1,
        per_page: 20,
        keyword: '',
        status: ''
      })

      wrapper.unmount()
    })

    it('1.5 加载数据时应该显示 loading 状态', async () => {
      // 创建一个延迟的 Promise
      let resolvePromise
      landlordApi.getLandlordList.mockImplementation(() => {
        return new Promise((resolve) => {
          resolvePromise = resolve
        })
      })

      const wrapper = createWrapper()

      // 验证 loading 状态为 true
      expect(wrapper.vm.loading).toBe(true)

      // 解决 Promise
      resolvePromise({
        success: true,
        data: {
          items: mockLandlords,
          pagination: { total: 3, page: 1, per_page: 10, pages: 1 }
        }
      })
      await flushPromises()

      // 验证 loading 状态为 false
      expect(wrapper.vm.loading).toBe(false)

      wrapper.unmount()
    })

    it('1.6 加载失败时应该显示错误提示', async () => {
      landlordApi.getLandlordList.mockRejectedValue(new Error('网络错误'))

      const wrapper = createWrapper()
      await flushPromises()

      // 验证错误提示
      expect(ElMessage.error).toHaveBeenCalledWith('加载房东列表失败')
      expect(wrapper.vm.loading).toBe(false)

      wrapper.unmount()
    })
  })

  // ============================================
  // 2. 测试搜索和筛选功能
  // ============================================
  describe('2. 搜索和筛选功能', () => {
    it('2.1 按关键词搜索应该正确传递参数', async () => {
      landlordApi.getLandlordList.mockResolvedValue({
        success: true,
        data: {
          items: [mockLandlords[0]],
          pagination: { total: 1, page: 1, per_page: 10, pages: 1 }
        }
      })

      const wrapper = createWrapper()
      await flushPromises()

      // 清除之前的调用
      landlordApi.getLandlordList.mockClear()

      // 设置搜索关键词
      wrapper.vm.searchForm.keyword = '张房东'
      wrapper.vm.handleSearch()
      await flushPromises()

      // 验证 API 被调用且参数正确
      expect(landlordApi.getLandlordList).toHaveBeenCalledWith({
        page: 1,
        per_page: 10,
        keyword: '张房东',
        status: ''
      })

      wrapper.unmount()
    })

    it('2.2 按状态筛选应该正确传递参数', async () => {
      landlordApi.getLandlordList.mockResolvedValue({
        success: true,
        data: {
          items: [mockLandlords[0]],
          pagination: { total: 1, page: 1, per_page: 10, pages: 1 }
        }
      })

      const wrapper = createWrapper()
      await flushPromises()

      // 清除之前的调用
      landlordApi.getLandlordList.mockClear()

      // 设置状态筛选
      wrapper.vm.searchForm.status = 'active'
      wrapper.vm.handleSearch()
      await flushPromises()

      // 验证 API 被调用且参数正确
      expect(landlordApi.getLandlordList).toHaveBeenCalledWith({
        page: 1,
        per_page: 10,
        keyword: '',
        status: 'active'
      })

      wrapper.unmount()
    })

    it('2.3 同时使用关键词和状态筛选', async () => {
      landlordApi.getLandlordList.mockResolvedValue({
        success: true,
        data: {
          items: [mockLandlords[0]],
          pagination: { total: 1, page: 1, per_page: 10, pages: 1 }
        }
      })

      const wrapper = createWrapper()
      await flushPromises()

      // 清除之前的调用
      landlordApi.getLandlordList.mockClear()

      // 设置搜索条件
      wrapper.vm.searchForm.keyword = '张'
      wrapper.vm.searchForm.status = 'active'
      wrapper.vm.handleSearch()
      await flushPromises()

      // 验证 API 被调用且参数正确
      expect(landlordApi.getLandlordList).toHaveBeenCalledWith({
        page: 1,
        per_page: 10,
        keyword: '张',
        status: 'active'
      })

      wrapper.unmount()
    })

    it('2.4 重置搜索条件应该清空所有筛选', async () => {
      landlordApi.getLandlordList.mockResolvedValue({
        success: true,
        data: {
          items: mockLandlords,
          pagination: { total: 3, page: 1, per_page: 10, pages: 1 }
        }
      })

      const wrapper = createWrapper()
      await flushPromises()

      // 设置搜索条件
      wrapper.vm.searchForm.keyword = '张'
      wrapper.vm.searchForm.status = 'active'

      // 清除之前的调用
      landlordApi.getLandlordList.mockClear()

      // 重置
      wrapper.vm.handleReset()
      await flushPromises()

      // 验证搜索条件被清空
      expect(wrapper.vm.searchForm.keyword).toBe('')
      expect(wrapper.vm.searchForm.status).toBe('')
      expect(wrapper.vm.pagination.page).toBe(1)

      // 验证 API 被调用
      expect(landlordApi.getLandlordList).toHaveBeenCalledWith({
        page: 1,
        per_page: 10,
        keyword: '',
        status: ''
      })

      wrapper.unmount()
    })

    it('2.5 搜索时应该重置页码为 1', async () => {
      landlordApi.getLandlordList.mockResolvedValue({
        success: true,
        data: {
          items: mockLandlords,
          pagination: { total: 30, page: 1, per_page: 10, pages: 3 }
        }
      })

      const wrapper = createWrapper()
      await flushPromises()

      // 设置当前页码为 2
      wrapper.vm.pagination.page = 2

      // 清除之前的调用
      landlordApi.getLandlordList.mockClear()

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
  // 3. 测试新增房东表单
  // ============================================
  describe('3. 新增房东表单', () => {
    it('3.1 点击新增按钮应该打开对话框', async () => {
      landlordApi.getLandlordList.mockResolvedValue({
        success: true,
        data: {
          items: mockLandlords,
          pagination: { total: 3, page: 1, per_page: 10, pages: 1 }
        }
      })

      const wrapper = createWrapper()
      await flushPromises()

      // 点击新增按钮
      wrapper.vm.handleAdd()
      await flushPromises()

      // 验证对话框状态
      expect(wrapper.vm.dialogVisible).toBe(true)
      expect(wrapper.vm.isEdit).toBe(false)
      expect(wrapper.vm.dialogTitle).toBe('新增房东')
      expect(wrapper.vm.currentLandlordData).toEqual({})

      wrapper.unmount()
    })

    it('3.2 提交新增表单应该调用 createLandlord API', async () => {
      landlordApi.getLandlordList.mockResolvedValue({
        success: true,
        data: {
          items: mockLandlords,
          pagination: { total: 3, page: 1, per_page: 10, pages: 1 }
        }
      })

      landlordApi.createLandlord.mockResolvedValue({
        success: true,
        data: { id: 4, ...mockLandlordDetail }
      })

      const wrapper = createWrapper()
      await flushPromises()

      // 打开新增对话框
      wrapper.vm.handleAdd()
      await flushPromises()

      // 模拟表单提交
      const formData = {
        name: '新房东',
        phone: '13900139000',
        id_card: '110101199004041234',
        bank_card: '6222001234567890125',
        bank_name: '中国银行',
        property_cert_no: '京房权证西私字第111111号',
        address: '北京市西城区某某街1号',
        remark: '测试新增'
      }

      await wrapper.vm.handleSubmit(formData)
      await flushPromises()

      // 验证 API 被调用
      expect(landlordApi.createLandlord).toHaveBeenCalledWith(formData)
      expect(ElMessage.success).toHaveBeenCalledWith('创建成功')
      expect(wrapper.vm.dialogVisible).toBe(false)

      wrapper.unmount()
    })

    it('3.3 新增成功后应该刷新列表', async () => {
      landlordApi.getLandlordList.mockResolvedValue({
        success: true,
        data: {
          items: mockLandlords,
          pagination: { total: 3, page: 1, per_page: 10, pages: 1 }
        }
      })

      landlordApi.createLandlord.mockResolvedValue({
        success: true,
        data: { id: 4 }
      })

      const wrapper = createWrapper()
      await flushPromises()

      // 清除之前的调用
      landlordApi.getLandlordList.mockClear()

      // 打开新增对话框并提交
      wrapper.vm.handleAdd()
      await flushPromises()

      const formData = {
        name: '新房东',
        phone: '13900139000',
        id_card: '110101199004041234'
      }

      await wrapper.vm.handleSubmit(formData)
      await flushPromises()

      // 验证列表被刷新
      expect(landlordApi.getLandlordList).toHaveBeenCalledTimes(1)

      wrapper.unmount()
    })

    it('3.4 新增失败应该显示错误提示', async () => {
      landlordApi.getLandlordList.mockResolvedValue({
        success: true,
        data: {
          items: mockLandlords,
          pagination: { total: 3, page: 1, per_page: 10, pages: 1 }
        }
      })

      landlordApi.createLandlord.mockRejectedValue({
        response: {
          data: {
            error: {
              message: '手机号已被使用'
            }
          }
        }
      })

      const wrapper = createWrapper()
      await flushPromises()

      // 打开新增对话框并提交
      wrapper.vm.handleAdd()
      await flushPromises()

      const formData = {
        name: '新房东',
        phone: '13800138001', // 已存在的手机号
        id_card: '110101199004041234'
      }

      await wrapper.vm.handleSubmit(formData)
      await flushPromises()

      // 验证错误提示
      expect(ElMessage.error).toHaveBeenCalledWith('手机号已被使用')
      expect(wrapper.vm.dialogVisible).toBe(true) // 对话框保持打开

      wrapper.unmount()
    })
  })

  // ============================================
  // 4. 测试编辑房东表单
  // ============================================
  describe('4. 编辑房东表单', () => {
    it('4.1 点击编辑按钮应该加载房东详情并打开对话框', async () => {
      landlordApi.getLandlordList.mockResolvedValue({
        success: true,
        data: {
          items: mockLandlords,
          pagination: { total: 3, page: 1, per_page: 10, pages: 1 }
        }
      })

      landlordApi.getLandlordDetail.mockResolvedValue({
        success: true,
        data: mockLandlordDetail
      })

      const wrapper = createWrapper()
      await flushPromises()

      // 点击编辑按钮
      await wrapper.vm.handleEdit({ id: 1, name: '张房东' })
      await flushPromises()

      // 验证详情 API 被调用
      expect(landlordApi.getLandlordDetail).toHaveBeenCalledWith(1)

      // 验证对话框状态
      expect(wrapper.vm.dialogVisible).toBe(true)
      expect(wrapper.vm.isEdit).toBe(true)
      expect(wrapper.vm.dialogTitle).toBe('编辑房东')
      expect(wrapper.vm.currentLandlordData.name).toBe('张房东')

      wrapper.unmount()
    })

    it('4.2 提交编辑表单应该调用 updateLandlord API', async () => {
      landlordApi.getLandlordList.mockResolvedValue({
        success: true,
        data: {
          items: mockLandlords,
          pagination: { total: 3, page: 1, per_page: 10, pages: 1 }
        }
      })

      landlordApi.getLandlordDetail.mockResolvedValue({
        success: true,
        data: mockLandlordDetail
      })

      landlordApi.updateLandlord.mockResolvedValue({
        success: true,
        data: { ...mockLandlordDetail, name: '张房东更新' }
      })

      const wrapper = createWrapper()
      await flushPromises()

      // 打开编辑对话框
      await wrapper.vm.handleEdit({ id: 1, name: '张房东' })
      await flushPromises()

      // 模拟表单提交
      const formData = {
        id: 1,
        name: '张房东更新',
        phone: '13800138001',
        status: 'active',
        remark: '更新备注'
      }

      await wrapper.vm.handleSubmit(formData)
      await flushPromises()

      // 验证 API 被调用
      expect(landlordApi.updateLandlord).toHaveBeenCalledWith(1, formData)
      expect(ElMessage.success).toHaveBeenCalledWith('编辑成功')
      expect(wrapper.vm.dialogVisible).toBe(false)

      wrapper.unmount()
    })

    it('4.3 编辑成功后应该刷新列表', async () => {
      landlordApi.getLandlordList.mockResolvedValue({
        success: true,
        data: {
          items: mockLandlords,
          pagination: { total: 3, page: 1, per_page: 10, pages: 1 }
        }
      })

      landlordApi.getLandlordDetail.mockResolvedValue({
        success: true,
        data: mockLandlordDetail
      })

      landlordApi.updateLandlord.mockResolvedValue({
        success: true,
        data: mockLandlordDetail
      })

      const wrapper = createWrapper()
      await flushPromises()

      // 清除之前的调用
      landlordApi.getLandlordList.mockClear()

      // 打开编辑对话框并提交
      await wrapper.vm.handleEdit({ id: 1, name: '张房东' })
      await flushPromises()

      const formData = {
        id: 1,
        name: '张房东',
        phone: '13800138001',
        status: 'active'
      }

      await wrapper.vm.handleSubmit(formData)
      await flushPromises()

      // 验证列表被刷新
      expect(landlordApi.getLandlordList).toHaveBeenCalledTimes(1)

      wrapper.unmount()
    })

    it('4.4 编辑失败应该显示错误提示', async () => {
      landlordApi.getLandlordList.mockResolvedValue({
        success: true,
        data: {
          items: mockLandlords,
          pagination: { total: 3, page: 1, per_page: 10, pages: 1 }
        }
      })

      landlordApi.getLandlordDetail.mockResolvedValue({
        success: true,
        data: mockLandlordDetail
      })

      landlordApi.updateLandlord.mockRejectedValue({
        response: {
          data: {
            error: {
              message: '更新失败，请重试'
            }
          }
        }
      })

      const wrapper = createWrapper()
      await flushPromises()

      // 打开编辑对话框并提交
      await wrapper.vm.handleEdit({ id: 1, name: '张房东' })
      await flushPromises()

      const formData = {
        id: 1,
        name: '张房东',
        phone: '13800138001',
        status: 'active'
      }

      await wrapper.vm.handleSubmit(formData)
      await flushPromises()

      // 验证错误提示
      expect(ElMessage.error).toHaveBeenCalledWith('更新失败，请重试')
      expect(wrapper.vm.dialogVisible).toBe(true) // 对话框保持打开

      wrapper.unmount()
    })

    it('4.5 从详情对话框编辑房东', async () => {
      landlordApi.getLandlordList.mockResolvedValue({
        success: true,
        data: {
          items: mockLandlords,
          pagination: { total: 3, page: 1, per_page: 10, pages: 1 }
        }
      })

      landlordApi.getLandlordDetail.mockResolvedValue({
        success: true,
        data: mockLandlordDetail
      })

      landlordApi.getLandlordHouses.mockResolvedValue({
        success: true,
        data: { houses: mockHouses }
      })

      landlordApi.getLandlordContracts.mockResolvedValue({
        success: true,
        data: { contracts: mockContracts }
      })

      const wrapper = createWrapper()
      await flushPromises()

      // 打开详情对话框
      await wrapper.vm.handleViewDetail({ id: 1 })
      await flushPromises()

      expect(wrapper.vm.detailVisible).toBe(true)

      // 清除之前的调用
      landlordApi.getLandlordDetail.mockClear()

      // 从详情编辑
      wrapper.vm.handleEditFromDetail()
      await flushPromises()

      // 验证详情对话框关闭
      expect(wrapper.vm.detailVisible).toBe(false)

      // 验证编辑对话框打开
      expect(wrapper.vm.dialogVisible).toBe(true)
      expect(wrapper.vm.isEdit).toBe(true)

      wrapper.unmount()
    })
  })

  // ============================================
  // 5. 测试删除房东确认
  // ============================================
  describe('5. 删除房东确认', () => {
    it('5.1 点击删除按钮应该显示确认对话框', async () => {
      landlordApi.getLandlordList.mockResolvedValue({
        success: true,
        data: {
          items: mockLandlords,
          pagination: { total: 3, page: 1, per_page: 10, pages: 1 }
        }
      })

      ElMessageBox.confirm.mockResolvedValue('confirm')

      const wrapper = createWrapper()
      await flushPromises()

      // 点击删除按钮
      wrapper.vm.handleDelete({ id: 1, name: '张房东' })
      await flushPromises()

      // 验证确认对话框被调用
      expect(ElMessageBox.confirm).toHaveBeenCalledWith(
        expect.stringContaining('张房东'),
        '提示',
        expect.objectContaining({
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        })
      )

      wrapper.unmount()
    })

    it('5.2 确认删除应该调用 deleteLandlord API', async () => {
      landlordApi.getLandlordList.mockResolvedValue({
        success: true,
        data: {
          items: mockLandlords,
          pagination: { total: 3, page: 1, per_page: 10, pages: 1 }
        }
      })

      landlordApi.deleteLandlord.mockResolvedValue({
        success: true
      })

      ElMessageBox.confirm.mockResolvedValue('confirm')

      const wrapper = createWrapper()
      await flushPromises()

      // 确认删除
      await wrapper.vm.handleDelete({ id: 1, name: '张房东' })
      await flushPromises()

      // 验证 API 被调用
      expect(landlordApi.deleteLandlord).toHaveBeenCalledWith(1)
      expect(ElMessage.success).toHaveBeenCalledWith('删除成功')

      wrapper.unmount()
    })

    it('5.3 删除成功后应该刷新列表', async () => {
      landlordApi.getLandlordList.mockResolvedValue({
        success: true,
        data: {
          items: mockLandlords,
          pagination: { total: 3, page: 1, per_page: 10, pages: 1 }
        }
      })

      landlordApi.deleteLandlord.mockResolvedValue({
        success: true
      })

      ElMessageBox.confirm.mockResolvedValue('confirm')

      const wrapper = createWrapper()
      await flushPromises()

      // 清除之前的调用
      landlordApi.getLandlordList.mockClear()

      // 确认删除
      await wrapper.vm.handleDelete({ id: 1, name: '张房东' })
      await flushPromises()

      // 验证列表被刷新
      expect(landlordApi.getLandlordList).toHaveBeenCalledTimes(1)

      wrapper.unmount()
    })

    it('5.4 取消删除不应该调用 API', async () => {
      landlordApi.getLandlordList.mockResolvedValue({
        success: true,
        data: {
          items: mockLandlords,
          pagination: { total: 3, page: 1, per_page: 10, pages: 1 }
        }
      })

      ElMessageBox.confirm.mockRejectedValue(new Error('cancel'))

      const wrapper = createWrapper()
      await flushPromises()

      // 取消删除
      await wrapper.vm.handleDelete({ id: 1, name: '张房东' })
      await flushPromises()

      // 验证删除 API 没有被调用
      expect(landlordApi.deleteLandlord).not.toHaveBeenCalled()

      wrapper.unmount()
    })

    it('5.5 删除失败应该显示错误提示', async () => {
      landlordApi.getLandlordList.mockResolvedValue({
        success: true,
        data: {
          items: mockLandlords,
          pagination: { total: 3, page: 1, per_page: 10, pages: 1 }
        }
      })

      landlordApi.deleteLandlord.mockRejectedValue({
        response: {
          data: {
            error: {
              message: '该房东有关联房源，无法删除'
            }
          }
        }
      })

      ElMessageBox.confirm.mockResolvedValue('confirm')

      const wrapper = createWrapper()
      await flushPromises()

      // 确认删除
      await wrapper.vm.handleDelete({ id: 1, name: '张房东' })
      await flushPromises()

      // 验证错误提示
      expect(ElMessage.error).toHaveBeenCalledWith('该房东有关联房源，无法删除')

      wrapper.unmount()
    })

    it('5.6 从编辑对话框删除房东', async () => {
      landlordApi.getLandlordList.mockResolvedValue({
        success: true,
        data: {
          items: mockLandlords,
          pagination: { total: 3, page: 1, per_page: 10, pages: 1 }
        }
      })

      landlordApi.getLandlordDetail.mockResolvedValue({
        success: true,
        data: mockLandlordDetail
      })

      landlordApi.deleteLandlord.mockResolvedValue({
        success: true
      })

      ElMessageBox.confirm.mockResolvedValue('confirm')

      const wrapper = createWrapper()
      await flushPromises()

      // 打开编辑对话框
      await wrapper.vm.handleEdit({ id: 1, name: '张房东' })
      await flushPromises()

      expect(wrapper.vm.dialogVisible).toBe(true)

      // 从对话框删除
      const formData = { id: 1, name: '张房东' }
      await wrapper.vm.handleDeleteFromDialog(formData)
      await flushPromises()

      // 验证删除 API 被调用
      expect(landlordApi.deleteLandlord).toHaveBeenCalledWith(1)
      expect(ElMessage.success).toHaveBeenCalledWith('删除成功')
      expect(wrapper.vm.dialogVisible).toBe(false)

      wrapper.unmount()
    })
  })

  // ============================================
  // 6. 测试查看详情功能
  // ============================================
  describe('6. 查看详情功能', () => {
    it('6.1 点击详情按钮应该加载并显示房东详情', async () => {
      landlordApi.getLandlordList.mockResolvedValue({
        success: true,
        data: {
          items: mockLandlords,
          pagination: { total: 3, page: 1, per_page: 10, pages: 1 }
        }
      })

      landlordApi.getLandlordDetail.mockResolvedValue({
        success: true,
        data: mockLandlordDetail
      })

      landlordApi.getLandlordHouses.mockResolvedValue({
        success: true,
        data: { houses: mockHouses }
      })

      landlordApi.getLandlordContracts.mockResolvedValue({
        success: true,
        data: { contracts: mockContracts }
      })

      const wrapper = createWrapper()
      await flushPromises()

      // 点击详情按钮
      await wrapper.vm.handleViewDetail({ id: 1 })
      await flushPromises()

      // 验证详情 API 被调用
      expect(landlordApi.getLandlordDetail).toHaveBeenCalledWith(1)
      expect(landlordApi.getLandlordHouses).toHaveBeenCalledWith(1, { page: 1, per_page: 100 })
      expect(landlordApi.getLandlordContracts).toHaveBeenCalledWith(1, { page: 1, per_page: 100 })

      // 验证详情对话框状态
      expect(wrapper.vm.detailVisible).toBe(true)
      expect(wrapper.vm.currentLandlord.name).toBe('张房东')
      expect(wrapper.vm.housesList).toHaveLength(2)
      expect(wrapper.vm.contractsList).toHaveLength(1)

      wrapper.unmount()
    })

    it('6.2 应该正确显示统计信息', async () => {
      landlordApi.getLandlordList.mockResolvedValue({
        success: true,
        data: {
          items: mockLandlords,
          pagination: { total: 3, page: 1, per_page: 10, pages: 1 }
        }
      })

      landlordApi.getLandlordDetail.mockResolvedValue({
        success: true,
        data: mockLandlordDetail
      })

      landlordApi.getLandlordHouses.mockResolvedValue({
        success: true,
        data: { houses: mockHouses }
      })

      landlordApi.getLandlordContracts.mockResolvedValue({
        success: true,
        data: { contracts: mockContracts }
      })

      const wrapper = createWrapper()
      await flushPromises()

      // 点击详情按钮
      await wrapper.vm.handleViewDetail({ id: 1 })
      await flushPromises()

      // 验证统计信息
      expect(wrapper.vm.statsData.houses_count).toBe(3)
      expect(wrapper.vm.statsData.contracts_count).toBe(2)

      wrapper.unmount()
    })

    it('6.3 查看房源应该跳转到房源详情页', async () => {
      landlordApi.getLandlordList.mockResolvedValue({
        success: true,
        data: {
          items: mockLandlords,
          pagination: { total: 3, page: 1, per_page: 10, pages: 1 }
        }
      })

      const wrapper = createWrapper()
      await flushPromises()

      // 查看房源
      wrapper.vm.handleViewHouse({ id: 1, title: '测试房源' })

      // 验证路由跳转
      expect(mockPush).toHaveBeenCalledWith('/houses/1')

      wrapper.unmount()
    })
  })

  // ============================================
  // 7. 测试权限控制
  // ============================================
  describe('7. 权限控制', () => {
    it('7.1 管理员应该有所有权限', async () => {
      landlordApi.getLandlordList.mockResolvedValue({
        success: true,
        data: {
          items: mockLandlords,
          pagination: { total: 3, page: 1, per_page: 10, pages: 1 }
        }
      })

      const wrapper = createWrapper()
      await flushPromises()

      // 验证权限
      expect(wrapper.vm.hasPermission('view')).toBe(true)
      expect(wrapper.vm.hasPermission('add')).toBe(true)
      expect(wrapper.vm.hasPermission('edit')).toBe(true)
      expect(wrapper.vm.hasPermission('delete')).toBe(true)

      wrapper.unmount()
    })

    it('7.2 普通员工应该没有删除权限', async () => {
      const pinia = createPinia()
      setActivePinia(pinia)

      const userStore = useUserStore()
      userStore.setUserInfo({
        id: 2,
        username: 'staff',
        role: 'staff',
        user_type: 'staff'
      })

      landlordApi.getLandlordList.mockResolvedValue({
        success: true,
        data: {
          items: mockLandlords,
          pagination: { total: 3, page: 1, per_page: 10, pages: 1 }
        }
      })

      // 创建本地 mock router 对象
      const localMockRouter = {
        push: mockPush,
        replace: mockReplace,
        go: mockGo,
        back: mockBack,
        beforeEach: mockBeforeEach,
        afterEach: mockAfterEach,
        beforeResolve: mockBeforeResolve,
        onError: mockOnError,
        currentRoute: {
          value: {
            path: '/landlords',
            params: {},
            query: {},
            meta: {}
          }
        }
      }

      const wrapper = mount(LandlordList, {
        global: {
          plugins: [pinia],
          mocks: {
            $router: localMockRouter,
            $route: {
              path: '/landlords',
              params: {},
              query: {}
            }
          },
          stubs: {
            LandlordForm: {
              name: 'LandlordForm',
              template: '<div class="mock-landlord-form"><slot /></div>',
              props: ['modelValue', 'isEdit', 'submitLoading', 'showDeleteButton', 'deleteDisabled']
            },
            RouterLink: true,
            RouterView: true
          }
        }
      })

      await flushPromises()

      // 验证权限
      expect(wrapper.vm.hasPermission('view')).toBe(true)
      expect(wrapper.vm.hasPermission('add')).toBe(true)
      expect(wrapper.vm.hasPermission('edit')).toBe(true)
      expect(wrapper.vm.hasPermission('delete')).toBe(false)

      wrapper.unmount()
    })
  })

  // ============================================
  // 8. 测试辅助函数
  // ============================================
  describe('8. 辅助函数', () => {
    it('8.1 getStatusType 应该返回正确的状态类型', async () => {
      landlordApi.getLandlordList.mockResolvedValue({
        success: true,
        data: {
          items: mockLandlords,
          pagination: { total: 3, page: 1, per_page: 10, pages: 1 }
        }
      })

      const wrapper = createWrapper()
      await flushPromises()

      expect(wrapper.vm.getStatusType('active')).toBe('success')
      expect(wrapper.vm.getStatusType('inactive')).toBe('info')
      expect(wrapper.vm.getStatusType('blacklisted')).toBe('danger')
      expect(wrapper.vm.getStatusType('unknown')).toBe('info')

      wrapper.unmount()
    })

    it('8.2 getStatusText 应该返回正确的状态文本', async () => {
      landlordApi.getLandlordList.mockResolvedValue({
        success: true,
        data: {
          items: mockLandlords,
          pagination: { total: 3, page: 1, per_page: 10, pages: 1 }
        }
      })

      const wrapper = createWrapper()
      await flushPromises()

      expect(wrapper.vm.getStatusText('active')).toBe('正常')
      expect(wrapper.vm.getStatusText('inactive')).toBe('停用')
      expect(wrapper.vm.getStatusText('blacklisted')).toBe('黑名单')

      wrapper.unmount()
    })

    it('8.3 maskIdCard 应该正确脱敏身份证号', async () => {
      landlordApi.getLandlordList.mockResolvedValue({
        success: true,
        data: {
          items: mockLandlords,
          pagination: { total: 3, page: 1, per_page: 10, pages: 1 }
        }
      })

      const wrapper = createWrapper()
      await flushPromises()

      expect(wrapper.vm.maskIdCard('110101199001011234')).toBe('110101********1234')
      expect(wrapper.vm.maskIdCard('')).toBe('-')
      expect(wrapper.vm.maskIdCard(null)).toBe('-')

      wrapper.unmount()
    })

    it('8.4 maskBankCard 应该正确脱敏银行卡号', async () => {
      landlordApi.getLandlordList.mockResolvedValue({
        success: true,
        data: {
          items: mockLandlords,
          pagination: { total: 3, page: 1, per_page: 10, pages: 1 }
        }
      })

      const wrapper = createWrapper()
      await flushPromises()

      expect(wrapper.vm.maskBankCard('6222001234567890123')).toBe('6222 **** **** 0123')
      expect(wrapper.vm.maskBankCard('')).toBe('-')
      expect(wrapper.vm.maskBankCard(null)).toBe('-')

      wrapper.unmount()
    })

    it('8.5 formatDate 应该正确格式化日期', async () => {
      landlordApi.getLandlordList.mockResolvedValue({
        success: true,
        data: {
          items: mockLandlords,
          pagination: { total: 3, page: 1, per_page: 10, pages: 1 }
        }
      })

      const wrapper = createWrapper()
      await flushPromises()

      expect(wrapper.vm.formatDate('2024-01-15T10:30:00')).toBe('2024-01-15 10:30:00')
      expect(wrapper.vm.formatDate('')).toBe('-')
      expect(wrapper.vm.formatDate(null)).toBe('-')

      wrapper.unmount()
    })
  })
})
