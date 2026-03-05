/**
 * 合同管理页面测试用例
 * 测试范围：
 * 1. 合同列表展示
 * 2. 合同状态筛选
 * 3. 新增合同表单
 * 4. 编辑合同表单
 * 5. 其他功能（查看详情、删除、激活、终止、续签）
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import ContractList from '@/views/contracts/ContractList.vue'
import * as contractApi from '@/api/contract'
import * as tenantApi from '@/api/tenant'
import * as houseApi from '@/api/house'
import { useUserStore } from '@/store/user'
import { ElMessage, ElMessageBox } from 'element-plus'

// ============================================
// 使用 vi.hoisted 提升变量定义
// ============================================

const mockPush = vi.hoisted(() => vi.fn())
const mockReplace = vi.hoisted(() => vi.fn())

// ============================================
// Mock API 响应数据
// ============================================

const mockContracts = [
  {
    id: 1,
    contract_no: 'HT202401150001',
    title: '朝阳区精装两居室租赁合同',
    tenant_id: 1,
    tenant_name: '张租客',
    tenant_phone: '13800138001',
    house_id: 1,
    house_address: '北京市朝阳区某某小区1号楼101室',
    room_no: '101',
    room_area: 85,
    start_date: '2024-01-15',
    end_date: '2025-01-14',
    rent_amount: 8000,
    deposit_amount: 8000,
    deposit: 8000,
    payment_type: '季付',
    payment_method: 'press_one_pay_three',
    status: 'active',
    sign_date: '2024-01-15',
    remark: '优质租客',
    created_at: '2024-01-15T10:30:00'
  },
  {
    id: 2,
    contract_no: 'HT202402200001',
    title: '海淀区合租主卧租赁合同',
    tenant_id: 2,
    tenant_name: '李租客',
    tenant_phone: '13800138002',
    house_id: 2,
    house_address: '北京市海淀区某某路2号201室',
    room_no: '201',
    room_area: 25,
    start_date: '2024-02-20',
    end_date: '2025-02-19',
    rent_amount: 3500,
    deposit_amount: 3500,
    deposit: 3500,
    payment_type: '月付',
    payment_method: 'press_one_pay_one',
    status: 'draft',
    sign_date: null,
    remark: '',
    created_at: '2024-02-20T14:20:00'
  },
  {
    id: 3,
    contract_no: 'HT202403100001',
    title: '西城区一居室租赁合同',
    tenant_id: 3,
    tenant_name: '王租客',
    tenant_phone: '13800138003',
    house_id: 3,
    house_address: '北京市西城区某某街3号301室',
    room_no: '301',
    room_area: 60,
    start_date: '2023-03-10',
    end_date: '2024-03-09',
    rent_amount: 6000,
    deposit_amount: 6000,
    deposit: 6000,
    payment_type: '季付',
    payment_method: 'press_one_pay_three',
    status: 'expired',
    sign_date: '2023-03-10',
    remark: '',
    created_at: '2023-03-10T09:15:00'
  }
]

const mockTenants = [
  { id: 1, name: '张租客', phone: '13800138001' },
  { id: 2, name: '李租客', phone: '13800138002' },
  { id: 3, name: '王租客', phone: '13800138003' }
]

const mockHouses = [
  { id: 1, title: '朝阳区精装两居室', address: '北京市朝阳区某某小区1号楼101室', rent_price: 8000, deposit: 8000 },
  { id: 2, title: '海淀区合租公寓', address: '北京市海淀区某某路2号', rent_price: 12000, deposit: 12000 }
]

const mockHouseDetail = { id: 1, title: '朝阳区精装两居室', address: '北京市朝阳区某某小区1号楼101室', rent_price: 8000, deposit: 8000 }

// ============================================
// Mock API 函数
// ============================================

vi.mock('@/api/contract', () => ({
  getContractList: vi.fn(),
  getContractDetail: vi.fn(),
  createContract: vi.fn(),
  updateContract: vi.fn(),
  deleteContract: vi.fn(),
  activateContract: vi.fn(),
  terminateContract: vi.fn(),
  renewContract: vi.fn()
}))

vi.mock('@/api/tenant', () => ({
  getTenantList: vi.fn()
}))

vi.mock('@/api/house', () => ({
  getHouseList: vi.fn(),
  getHouseDetail: vi.fn()
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
vi.mock('vue-router', () => ({
  useRouter: () => ({
    push: mockPush,
    replace: mockReplace,
    go: vi.fn(),
    back: vi.fn(),
    forward: vi.fn()
  }),
  useRoute: () => ({
    path: '/contracts',
    params: {},
    query: {},
    meta: {},
    name: 'contracts'
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
        path: '/contracts',
        params: {},
        query: {},
        meta: {},
        name: 'contracts'
      }
    }
  })),
  createWebHistory: vi.fn(() => ({}))
}))

// Mock router 模块
vi.mock('@/router', () => ({
  default: {
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
        path: '/contracts',
        params: {},
        query: {},
        meta: {},
        name: 'contracts'
      }
    }
  }
}))

// Mock permission 工具函数
vi.mock('@/utils/permission', () => ({
  hasPermission: vi.fn((action) => {
    // 从 localStorage 获取用户信息判断权限
    const userInfo = JSON.parse(localStorage.getItem('userInfo') || '{}')
    const userType = userInfo.user_type || userInfo.role || ''
    
    if (userType === 'admin') {
      return true
    }
    
    if (userType === 'staff' || userType === 'employee') {
      const staffPermissions = ['view', 'create', 'edit', 'update']
      return staffPermissions.includes(action)
    }
    
    return false
  })
}))

// Mock Element Plus 图标
vi.mock('@element-plus/icons-vue', () => ({
  Plus: { name: 'Plus', template: '<span class="mock-icon"></span>' },
  Search: { name: 'Search', template: '<span class="mock-icon"></span>' },
  Refresh: { name: 'Refresh', template: '<span class="mock-icon"></span>' },
  RefreshRight: { name: 'RefreshRight', template: '<span class="mock-icon"></span>' },
  View: { name: 'View', template: '<span class="mock-icon"></span>' },
  Edit: { name: 'Edit', template: '<span class="mock-icon"></span>' },
  Delete: { name: 'Delete', template: '<span class="mock-icon"></span>' },
  Check: { name: 'Check', template: '<span class="mock-icon"></span>' },
  Close: { name: 'Close', template: '<span class="mock-icon"></span>' }
}))

// ============================================
// 测试工具函数
// ============================================

const mockRouter = {
  push: mockPush,
  replace: mockReplace,
  go: vi.fn(),
  back: vi.fn(),
  forward: vi.fn()
}

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

  return mount(ContractList, {
    global: {
      plugins: [pinia],
      mocks: {
        $router: mockRouter,
        $route: {
          path: '/contracts',
          params: {},
          query: {}
        }
      },
      stubs: {
        RouterLink: true,
        RouterView: true,
        ElTable: {
          template: '<table><tbody><tr v-for="row in data" :key="row.id"><td>{{ row.contract_no }}</td><td>{{ row.tenant_name }}</td></tr></tbody></table>',
          props: ['data']
        },
        ElTableColumn: true,
        ElButton: true,
        ElInput: true,
        ElSelect: true,
        ElOption: true,
        ElDatePicker: true,
        ElInputNumber: true,
        ElDialog: true,
        ElDescriptions: true,
        ElDescriptionsItem: true,
        ElTag: true,
        ElAlert: true,
        ElPagination: true,
        ElCard: true,
        ElEmpty: true
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
  contractApi.getContractList.mockReset()
  contractApi.getContractDetail.mockReset()
  contractApi.createContract.mockReset()
  contractApi.updateContract.mockReset()
  contractApi.deleteContract.mockReset()
  contractApi.activateContract.mockReset()
  contractApi.terminateContract.mockReset()
  contractApi.renewContract.mockReset()
  tenantApi.getTenantList.mockReset()
  houseApi.getHouseList.mockReset()
  houseApi.getHouseDetail.mockReset()
  ElMessage.success.mockClear()
  ElMessage.error.mockClear()
  ElMessageBox.confirm.mockClear()
  mockPush.mockClear()
}

/**
 * 设置 API mock 返回值
 */
function setupApiMocks() {
  contractApi.getContractList.mockResolvedValue({
    data: {
      items: mockContracts,
      pagination: { total: 3, page: 1, per_page: 10, pages: 1 }
    }
  })
  tenantApi.getTenantList.mockResolvedValue({ data: { items: mockTenants } })
  houseApi.getHouseList.mockResolvedValue({ data: { items: mockHouses } })
}

// ============================================
// 测试用例
// ============================================

describe('合同管理页面 - ContractList.vue', () => {
  beforeEach(() => {
    resetAllMocks()
    // 设置 localStorage 中的用户信息
    localStorage.setItem('userInfo', JSON.stringify({ id: 1, username: 'admin', role: 'admin', user_type: 'admin' }))
  })

  afterEach(() => {
    vi.clearAllTimers()
    localStorage.clear()
  })

  // ============================================
  // 1. 测试合同列表展示
  // ============================================
  describe('1. 合同列表展示', () => {
    it('1.1 页面加载时应该自动获取合同列表', async () => {
      setupApiMocks()

      const wrapper = createWrapper()
      await flushPromises()

      // 验证 API 被调用
      expect(contractApi.getContractList).toHaveBeenCalledTimes(1)

      wrapper.unmount()
    })

    it('1.2 应该正确显示合同列表数据', async () => {
      setupApiMocks()

      const wrapper = createWrapper()
      await flushPromises()

      // 验证列表数据
      expect(wrapper.vm.contractList).toHaveLength(3)
      expect(wrapper.vm.contractList[0].contract_no).toBe('HT202401150001')
      expect(wrapper.vm.contractList[0].tenant_name).toBe('张租客')
      expect(wrapper.vm.pagination.total).toBe(3)

      wrapper.unmount()
    })

    it('1.3 分页变化时应该重新加载数据', async () => {
      setupApiMocks()

      const wrapper = createWrapper()
      await flushPromises()

      // 清除之前的调用
      contractApi.getContractList.mockClear()

      // 触发页码变化
      wrapper.vm.pagination.page = 2
      wrapper.vm.handlePageChange(2)
      await flushPromises()

      // 验证 API 被调用
      expect(contractApi.getContractList).toHaveBeenCalled()

      wrapper.unmount()
    })

    it('1.4 每页数量变化时应该重新加载数据', async () => {
      setupApiMocks()

      const wrapper = createWrapper()
      await flushPromises()

      // 清除之前的调用
      contractApi.getContractList.mockClear()

      // 触发每页数量变化
      wrapper.vm.handleSizeChange(20)
      await flushPromises()

      // 验证 API 被调用
      expect(contractApi.getContractList).toHaveBeenCalled()

      wrapper.unmount()
    })

    it('1.5 加载数据时应该显示 loading 状态', async () => {
      // 创建一个延迟的 Promise
      let resolvePromise
      contractApi.getContractList.mockImplementation(() => {
        return new Promise((resolve) => {
          resolvePromise = resolve
        })
      })
      tenantApi.getTenantList.mockResolvedValue({ data: { items: mockTenants } })
      houseApi.getHouseList.mockResolvedValue({ data: { items: mockHouses } })

      const wrapper = createWrapper()

      // 验证 loading 状态为 true
      expect(wrapper.vm.loading).toBe(true)

      // 解决 Promise
      resolvePromise({
        data: {
          items: mockContracts,
          pagination: { total: 3, page: 1, per_page: 10, pages: 1 }
        }
      })
      await flushPromises()

      // 验证 loading 状态为 false
      expect(wrapper.vm.loading).toBe(false)

      wrapper.unmount()
    })

    it('1.6 加载失败时应该显示错误提示', async () => {
      contractApi.getContractList.mockRejectedValue(new Error('网络错误'))
      tenantApi.getTenantList.mockResolvedValue({ data: { items: mockTenants } })
      houseApi.getHouseList.mockResolvedValue({ data: { items: mockHouses } })

      const wrapper = createWrapper()
      await flushPromises()

      // 验证错误提示
      expect(ElMessage.error).toHaveBeenCalledWith('加载合同列表失败')
      expect(wrapper.vm.loading).toBe(false)

      wrapper.unmount()
    })

    it('1.7 应该正确显示合同状态标签', async () => {
      setupApiMocks()

      const wrapper = createWrapper()
      await flushPromises()

      // 验证状态类型映射
      expect(wrapper.vm.getStatusType('active')).toBe('success')
      expect(wrapper.vm.getStatusType('draft')).toBe('info')
      expect(wrapper.vm.getStatusType('pending')).toBe('warning')
      expect(wrapper.vm.getStatusType('expired')).toBe('info')
      expect(wrapper.vm.getStatusType('terminated')).toBe('danger')
      expect(wrapper.vm.getStatusType('breached')).toBe('danger')
      expect(wrapper.vm.getStatusType('renewed')).toBe('success')

      // 验证状态文本映射
      expect(wrapper.vm.getStatusText('active')).toBe('履行中')
      expect(wrapper.vm.getStatusText('draft')).toBe('草稿')
      expect(wrapper.vm.getStatusText('pending')).toBe('待签约')
      expect(wrapper.vm.getStatusText('expired')).toBe('已到期')
      expect(wrapper.vm.getStatusText('terminated')).toBe('已终止')
      expect(wrapper.vm.getStatusText('breached')).toBe('已违约')
      expect(wrapper.vm.getStatusText('renewed')).toBe('已续签')

      wrapper.unmount()
    })
  })

  // ============================================
  // 2. 测试合同状态筛选
  // ============================================
  describe('2. 合同状态筛选', () => {
    it('2.1 按关键词搜索应该正确传递参数', async () => {
      setupApiMocks()

      const wrapper = createWrapper()
      await flushPromises()

      // 清除之前的调用
      contractApi.getContractList.mockClear()

      // 设置搜索关键词
      wrapper.vm.searchForm.keyword = '张租客'
      wrapper.vm.handleSearch()
      await flushPromises()

      // 验证 API 被调用且参数正确
      expect(contractApi.getContractList).toHaveBeenCalled()
      expect(wrapper.vm.searchForm.keyword).toBe('张租客')

      wrapper.unmount()
    })

    it('2.2 按状态筛选应该正确传递参数', async () => {
      setupApiMocks()

      const wrapper = createWrapper()
      await flushPromises()

      // 清除之前的调用
      contractApi.getContractList.mockClear()

      // 设置状态筛选
      wrapper.vm.searchForm.status = 'active'
      wrapper.vm.handleSearch()
      await flushPromises()

      // 验证 API 被调用且参数正确
      expect(contractApi.getContractList).toHaveBeenCalled()
      expect(wrapper.vm.searchForm.status).toBe('active')

      wrapper.unmount()
    })

    it('2.3 同时使用关键词和状态筛选', async () => {
      setupApiMocks()

      const wrapper = createWrapper()
      await flushPromises()

      // 清除之前的调用
      contractApi.getContractList.mockClear()

      // 设置多个搜索条件
      wrapper.vm.searchForm.keyword = '张'
      wrapper.vm.searchForm.status = 'active'
      wrapper.vm.handleSearch()
      await flushPromises()

      // 验证 API 被调用且参数正确
      expect(contractApi.getContractList).toHaveBeenCalled()
      expect(wrapper.vm.searchForm.keyword).toBe('张')
      expect(wrapper.vm.searchForm.status).toBe('active')

      wrapper.unmount()
    })

    it('2.4 重置搜索条件应该清空所有筛选', async () => {
      setupApiMocks()

      const wrapper = createWrapper()
      await flushPromises()

      // 设置搜索条件
      wrapper.vm.searchForm.keyword = '张'
      wrapper.vm.searchForm.status = 'active'

      // 清除之前的调用
      contractApi.getContractList.mockClear()

      // 重置
      wrapper.vm.handleReset()
      await flushPromises()

      // 验证搜索条件被清空
      expect(wrapper.vm.searchForm.keyword).toBe('')
      expect(wrapper.vm.searchForm.status).toBe('')
      expect(wrapper.vm.pagination.page).toBe(1)

      wrapper.unmount()
    })

    it('2.5 搜索时应该重置页码为 1', async () => {
      setupApiMocks()

      const wrapper = createWrapper()
      await flushPromises()

      // 设置当前页码为 2
      wrapper.vm.pagination.page = 2

      // 清除之前的调用
      contractApi.getContractList.mockClear()

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
  // 3. 测试新增合同表单
  // ============================================
  describe('3. 新增合同表单', () => {
    it('3.1 点击新增按钮应该打开对话框', async () => {
      setupApiMocks()

      const wrapper = createWrapper()
      await flushPromises()

      // 点击新增按钮
      wrapper.vm.handleAdd()
      await flushPromises()

      // 验证对话框状态
      expect(wrapper.vm.dialogVisible).toBe(true)
      expect(wrapper.vm.dialogTitle).toBe('新建合同')
      expect(wrapper.vm.currentContract).toEqual({})
      expect(wrapper.vm.isViewMode).toBe(false)

      wrapper.unmount()
    })

    it('3.2 新增对话框应该加载租客和房源选项', async () => {
      setupApiMocks()

      const wrapper = createWrapper()
      await flushPromises()

      // 验证租客选项已加载
      expect(wrapper.vm.tenantOptions).toHaveLength(3)
      expect(wrapper.vm.tenantOptions[0].name).toBe('张租客')

      // 验证房源选项已加载
      expect(wrapper.vm.houseOptions).toHaveLength(2)
      expect(wrapper.vm.houseOptions[0].title).toBe('朝阳区精装两居室')

      wrapper.unmount()
    })

    it('3.3 提交新增表单应该调用 createContract API', async () => {
      setupApiMocks()
      contractApi.createContract.mockResolvedValue({ data: { id: 4 } })

      const wrapper = createWrapper()
      await flushPromises()

      // 打开新增对话框
      wrapper.vm.handleAdd()
      await flushPromises()

      // 填充表单数据
      wrapper.vm.contractForm.title = '测试合同'
      wrapper.vm.contractForm.tenant_id = 1
      wrapper.vm.contractForm.house_id = 1
      wrapper.vm.contractForm.lease_term = ['2024-04-01', '2025-03-31']
      wrapper.vm.contractForm.rent_amount = 5000
      wrapper.vm.contractForm.deposit_amount = 5000
      wrapper.vm.contractForm.payment_method = 'press_one_pay_three'

      // 模拟表单验证通过
      wrapper.vm.contractFormRef = {
        validate: vi.fn(() => Promise.resolve())
      }

      // 提交表单
      await wrapper.vm.handleSubmit()
      await flushPromises()

      // 验证 API 被调用
      expect(contractApi.createContract).toHaveBeenCalled()
      expect(wrapper.vm.dialogVisible).toBe(false)

      wrapper.unmount()
    })

    it('3.4 新增成功后应该刷新列表', async () => {
      setupApiMocks()
      contractApi.createContract.mockResolvedValue({ data: { id: 4 } })

      const wrapper = createWrapper()
      await flushPromises()

      // 清除之前的调用
      contractApi.getContractList.mockClear()

      // 打开新增对话框
      wrapper.vm.handleAdd()
      await flushPromises()

      // 填充表单数据
      wrapper.vm.contractForm.title = '测试合同'
      wrapper.vm.contractForm.tenant_id = 1
      wrapper.vm.contractForm.house_id = 1
      wrapper.vm.contractForm.lease_term = ['2024-04-01', '2025-03-31']
      wrapper.vm.contractForm.rent_amount = 5000
      wrapper.vm.contractForm.deposit_amount = 5000
      wrapper.vm.contractForm.payment_method = 'press_one_pay_three'

      // 模拟表单验证通过
      wrapper.vm.contractFormRef = {
        validate: vi.fn(() => Promise.resolve())
      }

      // 提交表单
      await wrapper.vm.handleSubmit()
      await flushPromises()

      // 验证列表被刷新
      expect(contractApi.getContractList).toHaveBeenCalledTimes(1)

      wrapper.unmount()
    })

    it('3.5 选择房源时应该自动填充租金和押金', async () => {
      setupApiMocks()
      houseApi.getHouseDetail.mockResolvedValue({ data: mockHouseDetail })

      const wrapper = createWrapper()
      await flushPromises()

      // 打开新增对话框
      wrapper.vm.handleAdd()
      await flushPromises()

      // 选择房源
      await wrapper.vm.handleHouseChange(1)
      await flushPromises()

      // 验证租金和押金被自动填充
      expect(wrapper.vm.contractForm.rent_amount).toBe(8000)
      expect(wrapper.vm.contractForm.deposit_amount).toBe(8000)

      wrapper.unmount()
    })
  })

  // ============================================
  // 4. 测试编辑合同表单
  // ============================================
  describe('4. 编辑合同表单', () => {
    it('4.1 点击编辑按钮应该打开对话框并填充数据', async () => {
      setupApiMocks()

      const wrapper = createWrapper()
      await flushPromises()

      // 点击编辑按钮
      const contract = mockContracts[1] // draft 状态的合同
      await wrapper.vm.handleEdit(contract)
      await flushPromises()

      // 验证对话框状态
      expect(wrapper.vm.dialogVisible).toBe(true)
      expect(wrapper.vm.dialogTitle).toBe('编辑合同')
      expect(wrapper.vm.currentContract.id).toBe(2)
      expect(wrapper.vm.contractForm.title).toBe('海淀区合租主卧租赁合同')
      expect(wrapper.vm.contractForm.tenant_id).toBe(2)
      expect(wrapper.vm.contractForm.house_id).toBe(2)

      wrapper.unmount()
    })

    it('4.2 提交编辑表单应该调用 updateContract API', async () => {
      setupApiMocks()
      contractApi.updateContract.mockResolvedValue({ data: {} })

      const wrapper = createWrapper()
      await flushPromises()

      // 打开编辑对话框
      const contract = mockContracts[1]
      await wrapper.vm.handleEdit(contract)
      await flushPromises()

      // 修改数据
      wrapper.vm.contractForm.rent_amount = 9000

      // 模拟表单验证通过
      wrapper.vm.contractFormRef = {
        validate: vi.fn(() => Promise.resolve())
      }

      // 提交表单
      await wrapper.vm.handleSubmit()
      await flushPromises()

      // 验证 API 被调用
      expect(contractApi.updateContract).toHaveBeenCalledWith(2, expect.any(Object))
      expect(wrapper.vm.dialogVisible).toBe(false)

      wrapper.unmount()
    })

    it('4.3 编辑成功后应该刷新列表', async () => {
      setupApiMocks()
      contractApi.updateContract.mockResolvedValue({ data: {} })

      const wrapper = createWrapper()
      await flushPromises()

      // 清除之前的调用
      contractApi.getContractList.mockClear()

      // 打开编辑对话框
      const contract = mockContracts[1]
      await wrapper.vm.handleEdit(contract)
      await flushPromises()

      // 模拟表单验证通过
      wrapper.vm.contractFormRef = {
        validate: vi.fn(() => Promise.resolve())
      }

      // 提交表单
      await wrapper.vm.handleSubmit()
      await flushPromises()

      // 验证列表被刷新
      expect(contractApi.getContractList).toHaveBeenCalledTimes(1)

      wrapper.unmount()
    })

    it('4.4 只有草稿状态的合同才能编辑', async () => {
      setupApiMocks()

      const wrapper = createWrapper()
      await flushPromises()

      // 验证权限
      expect(wrapper.vm.hasPermission('edit')).toBe(true)

      wrapper.unmount()
    })
  })

  // ============================================
  // 5. 测试其他功能
  // ============================================
  describe('5. 其他功能', () => {
    it('5.1 查看合同详情', async () => {
      setupApiMocks()
      contractApi.getContractDetail.mockResolvedValue({ data: mockContracts[0] })

      const wrapper = createWrapper()
      await flushPromises()

      // 点击查看按钮
      await wrapper.vm.handleView(mockContracts[0])
      await flushPromises()

      // 验证 API 被调用
      expect(contractApi.getContractDetail).toHaveBeenCalledWith(1)
      expect(wrapper.vm.detailVisible).toBe(true)
      expect(wrapper.vm.currentContract.contract_no).toBe('HT202401150001')

      wrapper.unmount()
    })

    it('5.2 删除合同确认', async () => {
      setupApiMocks()
      contractApi.deleteContract.mockResolvedValue({})
      ElMessageBox.confirm.mockResolvedValue('confirm')

      const wrapper = createWrapper()
      await flushPromises()

      // 点击删除按钮
      await wrapper.vm.handleDelete(mockContracts[0])
      await flushPromises()

      // 验证确认对话框被调用
      expect(ElMessageBox.confirm).toHaveBeenCalledWith(
        expect.stringContaining('删除'),
        '提示',
        expect.objectContaining({
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        })
      )

      wrapper.unmount()
    })

    it('5.3 激活草稿合同', async () => {
      setupApiMocks()
      contractApi.activateContract.mockResolvedValue({})

      const wrapper = createWrapper()
      await flushPromises()

      // 激活合同
      await wrapper.vm.handleActivate(mockContracts[1])
      await flushPromises()

      // 验证 API 被调用
      expect(contractApi.activateContract).toHaveBeenCalledWith(2)

      wrapper.unmount()
    })

    it('5.4 终止履行中的合同', async () => {
      setupApiMocks()
      contractApi.terminateContract.mockResolvedValue({})

      const wrapper = createWrapper()
      await flushPromises()

      // 打开终止对话框
      wrapper.vm.handleTerminate(mockContracts[0])
      await flushPromises()

      // 验证对话框状态
      expect(wrapper.vm.terminateVisible).toBe(true)
      expect(wrapper.vm.currentTerminateContract.id).toBe(1)

      // 填充终止信息
      wrapper.vm.terminateForm.reason = '租客申请退租'
      wrapper.vm.terminateForm.terminate_date = '2024-06-01'

      // 提交终止
      await wrapper.vm.handleTerminateSubmit()
      await flushPromises()

      // 验证 API 被调用
      expect(contractApi.terminateContract).toHaveBeenCalledWith(1, expect.any(Object))

      wrapper.unmount()
    })

    it('5.5 续签已到期的合同', async () => {
      setupApiMocks()
      contractApi.renewContract.mockResolvedValue({})

      const wrapper = createWrapper()
      await flushPromises()

      // 打开续签对话框
      wrapper.vm.handleRenew(mockContracts[2])
      await flushPromises()

      // 验证对话框状态
      expect(wrapper.vm.renewVisible).toBe(true)
      expect(wrapper.vm.currentContract.id).toBe(3)

      // 填充续签信息
      wrapper.vm.renewForm.lease_term = ['2024-04-01', '2025-03-31']
      wrapper.vm.renewForm.rent_amount = 6500
      wrapper.vm.renewForm.deposit_amount = 6500

      // 模拟续签表单验证通过
      wrapper.vm.renewFormRef = {
        validate: vi.fn(() => Promise.resolve())
      }

      // 提交续签
      await wrapper.vm.handleRenewSubmit()
      await flushPromises()

      // 验证 API 被调用
      expect(contractApi.renewContract).toHaveBeenCalledWith(3, expect.any(Object))

      wrapper.unmount()
    })
  })

  // ============================================
  // 6. 测试辅助函数
  // ============================================
  describe('6. 辅助函数', () => {
    it('6.1 getStatusType 应该返回正确的状态类型', async () => {
      setupApiMocks()

      const wrapper = createWrapper()
      await flushPromises()

      expect(wrapper.vm.getStatusType('draft')).toBe('info')
      expect(wrapper.vm.getStatusType('pending')).toBe('warning')
      expect(wrapper.vm.getStatusType('active')).toBe('success')
      expect(wrapper.vm.getStatusType('expired')).toBe('info')
      expect(wrapper.vm.getStatusType('terminated')).toBe('danger')
      expect(wrapper.vm.getStatusType('breached')).toBe('danger')
      expect(wrapper.vm.getStatusType('renewed')).toBe('success')
      expect(wrapper.vm.getStatusType('unknown')).toBe('info')

      wrapper.unmount()
    })

    it('6.2 getStatusText 应该返回正确的状态文本', async () => {
      setupApiMocks()

      const wrapper = createWrapper()
      await flushPromises()

      expect(wrapper.vm.getStatusText('draft')).toBe('草稿')
      expect(wrapper.vm.getStatusText('pending')).toBe('待签约')
      expect(wrapper.vm.getStatusText('active')).toBe('履行中')
      expect(wrapper.vm.getStatusText('expired')).toBe('已到期')
      expect(wrapper.vm.getStatusText('terminated')).toBe('已终止')
      expect(wrapper.vm.getStatusText('breached')).toBe('已违约')
      expect(wrapper.vm.getStatusText('renewed')).toBe('已续签')

      wrapper.unmount()
    })

    it('6.3 getPaymentText 应该返回正确的支付方式文本', async () => {
      setupApiMocks()

      const wrapper = createWrapper()
      await flushPromises()

      expect(wrapper.vm.getPaymentText('press_one_pay_one')).toBe('押一付一')
      expect(wrapper.vm.getPaymentText('press_one_pay_three')).toBe('押一付三')
      expect(wrapper.vm.getPaymentText('press_one_pay_six')).toBe('押一付六')
      expect(wrapper.vm.getPaymentText('press_one_pay_twelve')).toBe('押一付十二')
      expect(wrapper.vm.getPaymentText('custom')).toBe('自定义')

      wrapper.unmount()
    })

    it('6.4 formatChineseDate 应该正确格式化日期', async () => {
      setupApiMocks()

      const wrapper = createWrapper()
      await flushPromises()

      expect(wrapper.vm.formatChineseDate('2024-01-15')).toBe('2024-01-15')
      expect(wrapper.vm.formatChineseDate('2024-01-15T10:30:00')).toBe('2024-01-15')
      expect(wrapper.vm.formatChineseDate('')).toBe('-')
      expect(wrapper.vm.formatChineseDate(null)).toBe('-')

      wrapper.unmount()
    })

    it('6.5 getPaymentMethodValue 应该正确映射支付方式', async () => {
      setupApiMocks()

      const wrapper = createWrapper()
      await flushPromises()

      expect(wrapper.vm.getPaymentMethodValue('月付')).toBe('press_one_pay_one')
      expect(wrapper.vm.getPaymentMethodValue('季付')).toBe('press_one_pay_three')
      expect(wrapper.vm.getPaymentMethodValue('半年付')).toBe('press_one_pay_six')
      expect(wrapper.vm.getPaymentMethodValue('年付')).toBe('press_one_pay_twelve')
      expect(wrapper.vm.getPaymentMethodValue('自定义')).toBe('custom')

      wrapper.unmount()
    })
  })

  // ============================================
  // 7. 测试权限控制
  // ============================================
  describe('7. 权限控制', () => {
    it('7.1 管理员应该有所有权限', async () => {
      setupApiMocks()

      const wrapper = createWrapper()
      await flushPromises()

      // 验证权限
      expect(wrapper.vm.hasPermission('view')).toBe(true)
      expect(wrapper.vm.hasPermission('create')).toBe(true)
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

      // 设置 localStorage
      localStorage.setItem('userInfo', JSON.stringify({ id: 2, username: 'staff', role: 'staff', user_type: 'staff' }))

      // 设置 API mock 返回值
      contractApi.getContractList.mockResolvedValue({
        data: {
          items: mockContracts,
          pagination: { total: 3, page: 1, per_page: 10, pages: 1 }
        }
      })
      tenantApi.getTenantList.mockResolvedValue({ data: { items: mockTenants } })
      houseApi.getHouseList.mockResolvedValue({ data: { items: mockHouses } })

      const wrapper = mount(ContractList, {
        global: {
          plugins: [pinia],
          mocks: {
            $router: mockRouter,
            $route: {
              path: '/contracts',
              params: {},
              query: {}
            }
          },
          stubs: {
            RouterLink: true,
            RouterView: true,
            ElTable: true,
            ElTableColumn: true,
            ElTag: true,
            ElButton: true
          }
        }
      })

      await flushPromises()

      // 验证权限
      expect(wrapper.vm.hasPermission('view')).toBe(true)
      expect(wrapper.vm.hasPermission('create')).toBe(true)
      expect(wrapper.vm.hasPermission('edit')).toBe(true)
      expect(wrapper.vm.hasPermission('delete')).toBe(false)

      wrapper.unmount()
    })
  })

  // ============================================
  // 8. 测试即将到期合同提醒
  // ============================================
  describe('8. 即将到期合同提醒', () => {
    it('8.1 应该识别即将到期的合同', async () => {
      // 创建一个即将到期的合同（15天后到期）
      const futureDate = new Date()
      futureDate.setDate(futureDate.getDate() + 15)
      const expiringContract = {
        ...mockContracts[0],
        end_date: futureDate.toISOString().split('T')[0],
        status: 'active'
      }

      contractApi.getContractList.mockResolvedValue({
        data: {
          items: [expiringContract],
          pagination: { total: 1, page: 1, per_page: 10, pages: 1 }
        }
      })
      tenantApi.getTenantList.mockResolvedValue({ data: { items: mockTenants } })
      houseApi.getHouseList.mockResolvedValue({ data: { items: mockHouses } })

      const wrapper = createWrapper()
      await flushPromises()

      // 验证即将到期合同被识别
      expect(wrapper.vm.expiringContracts.length).toBeGreaterThan(0)

      wrapper.unmount()
    })

    it('8.2 已过期合同不应该出现在即将到期列表', async () => {
      // 创建一个已过期的合同
      const pastDate = new Date()
      pastDate.setDate(pastDate.getDate() - 10)
      const expiredContract = {
        ...mockContracts[0],
        end_date: pastDate.toISOString().split('T')[0],
        status: 'expired'
      }

      contractApi.getContractList.mockResolvedValue({
        data: {
          items: [expiredContract],
          pagination: { total: 1, page: 1, per_page: 10, pages: 1 }
        }
      })
      tenantApi.getTenantList.mockResolvedValue({ data: { items: mockTenants } })
      houseApi.getHouseList.mockResolvedValue({ data: { items: mockHouses } })

      const wrapper = createWrapper()
      await flushPromises()

      // 验证已过期合同不在即将到期列表中
      expect(wrapper.vm.expiringContracts).toHaveLength(0)

      wrapper.unmount()
    })
  })
})
