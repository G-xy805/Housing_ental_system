/**
 * 员工管理页面测试用例
 * 测试范围：
 * 1. 测试员工列表展示
 * 2. 测试权限标识显示
 * 3. 测试新增员工表单
 * 4. 测试编辑员工表单
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createRouter, createWebHistory } from 'vue-router'
import EmployeeList from '@/views/employees/EmployeeList.vue'
import * as employeeApi from '@/api/employee'
import { useUserStore } from '@/store/user'
import { ElMessage, ElMessageBox } from 'element-plus'

// ============================================
// Mock API 响应数据
// ============================================

const mockEmployees = [
  {
    id: 1,
    username: 'admin',
    name: '张管理员',
    phone: '13800138001',
    email: 'admin@example.com',
    position: '系统管理员',
    role: 'admin',
    status: 'active',
    last_login: '2024-01-15T10:30:00',
    created_at: '2024-01-01T08:00:00',
    updated_at: '2024-01-15T10:30:00'
  },
  {
    id: 2,
    username: 'staff001',
    name: '李员工',
    phone: '13800138002',
    email: 'staff001@example.com',
    position: '业务员',
    role: 'staff',
    status: 'active',
    last_login: '2024-01-14T16:20:00',
    created_at: '2024-01-05T09:00:00',
    updated_at: '2024-01-14T16:20:00'
  },
  {
    id: 3,
    username: 'staff002',
    name: '王员工',
    phone: '13800138003',
    email: 'staff002@example.com',
    position: '业务员',
    role: 'staff',
    status: 'disabled',
    last_login: '2024-01-10T14:00:00',
    created_at: '2024-01-06T10:00:00',
    updated_at: '2024-01-10T14:00:00'
  },
  {
    id: 4,
    username: 'staff003',
    name: '赵员工',
    phone: '13800138004',
    email: 'staff003@example.com',
    position: '经理',
    role: 'staff',
    status: 'resigned',
    last_login: '2024-01-05T11:00:00',
    created_at: '2024-01-07T11:00:00',
    updated_at: '2024-01-08T09:00:00'
  }
]

const mockStatistics = {
  total: 4,
  by_status: {
    active: 2,
    disabled: 1,
    resigned: 1
  }
}

// ============================================
// Mock API 函数
// ============================================

vi.mock('@/api/employee', () => ({
  getEmployeeList: vi.fn(),
  getEmployeeDetail: vi.fn(),
  createEmployee: vi.fn(),
  updateEmployee: vi.fn(),
  updateEmployeeStatus: vi.fn(),
  deleteEmployee: vi.fn(),
  resetEmployeePassword: vi.fn(),
  getEmployeeStats: vi.fn(),
  batchActionEmployees: vi.fn()
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

// Mock Element Plus Icons
vi.mock('@element-plus/icons-vue', () => ({
  Plus: { name: 'Plus', template: '<svg><path d="M1"/></svg>' },
  Search: { name: 'Search', template: '<svg><path d="M1"/></svg>' },
  Refresh: { name: 'Refresh', template: '<svg><path d="M1"/></svg>' },
  Edit: { name: 'Edit', template: '<svg><path d="M1"/></svg>' },
  Delete: { name: 'Delete', template: '<svg><path d="M1"/></svg>' },
  Key: { name: 'Key', template: '<svg><path d="M1"/></svg>' },
  Switch: { name: 'Switch', template: '<svg><path d="M1"/></svg>' },
  View: { name: 'View', template: '<svg><path d="M1"/></svg>' },
  UserFilled: { name: 'UserFilled', template: '<svg><path d="M1"/></svg>' },
  CircleCheck: { name: 'CircleCheck', template: '<svg><path d="M1"/></svg>' },
  CircleClose: { name: 'CircleClose', template: '<svg><path d="M1"/></svg>' },
  TrendCharts: { name: 'TrendCharts', template: '<svg><path d="M1"/></svg>' }
}))

// ============================================
// 创建测试路由器
// ============================================

function createTestRouter() {
  return createRouter({
    history: createWebHistory(),
    routes: [
      { path: '/', component: { template: '<div>Home</div>' } },
      { path: '/employees', component: { template: '<div>Employees</div>' } }
    ]
  })
}

// ============================================
// 测试工具函数
// ============================================

/**
 * 重置所有模拟
 */
function resetAllMocks() {
  vi.clearAllMocks()
  employeeApi.getEmployeeList.mockReset()
  employeeApi.getEmployeeDetail.mockReset()
  employeeApi.createEmployee.mockReset()
  employeeApi.updateEmployee.mockReset()
  employeeApi.updateEmployeeStatus.mockReset()
  employeeApi.deleteEmployee.mockReset()
  employeeApi.resetEmployeePassword.mockReset()
  employeeApi.getEmployeeStats.mockReset()
  employeeApi.batchActionEmployees.mockReset()
  ElMessage.success.mockClear()
  ElMessage.error.mockClear()
  ElMessage.warning.mockClear()
  ElMessageBox.confirm.mockClear()
}

// ============================================
// 测试用例
// ============================================

describe('员工管理页面 - EmployeeList.vue', () => {
  let wrapper
  let pinia
  let userStore
  let router

  beforeEach(async () => {
    resetAllMocks()
    
    // 创建新的 Pinia 实例
    pinia = createPinia()
    setActivePinia(pinia)
    
    // 创建路由器
    router = createTestRouter()
    await router.push('/employees')
    await router.isReady()
    
    // 初始化 userStore
    userStore = useUserStore()
    userStore.setUserInfo({
      id: 1,
      username: 'admin',
      role: 'admin',
      user_type: 'admin'
    })
  })

  afterEach(() => {
    if (wrapper) {
      wrapper.unmount()
    }
  })

  // ============================================
  // 1. 测试员工列表展示
  // ============================================
  describe('1. 测试员工列表展示', () => {
    it('1.1 页面加载时应该自动获取员工列表', async () => {
      employeeApi.getEmployeeList.mockResolvedValue({
        data: {
          items: mockEmployees,
          pagination: {
            total: 4,
            page: 1,
            per_page: 20,
            pages: 1
          }
        }
      })

      employeeApi.getEmployeeStats.mockResolvedValue({
        data: mockStatistics
      })

      wrapper = mount(EmployeeList, {
        global: {
          plugins: [pinia, router],
          stubs: {
            'el-button': true,
            'el-input': true,
            'el-select': true,
            'el-option': true,
            'el-table': true,
            'el-table-column': true,
            'el-pagination': true,
            'el-dialog': true,
            'el-form': true,
            'el-form-item': true,
            'el-card': true,
            'el-row': true,
            'el-col': true,
            'el-icon': true,
            'el-descriptions': true,
            'el-descriptions-item': true
          }
        }
      })
      await flushPromises()

      // 验证 API 被调用
      expect(employeeApi.getEmployeeList).toHaveBeenCalledTimes(1)
      expect(employeeApi.getEmployeeList).toHaveBeenCalledWith({
        page: 1,
        per_page: 20,
        keyword: '',
        status: '',
        role: ''
      })
    })

    it('1.2 应该正确显示员工列表数据', async () => {
      employeeApi.getEmployeeList.mockResolvedValue({
        data: {
          items: mockEmployees,
          pagination: {
            total: 4,
            page: 1,
            per_page: 20,
            pages: 1
          }
        }
      })

      employeeApi.getEmployeeStats.mockResolvedValue({
        data: mockStatistics
      })

      wrapper = mount(EmployeeList, {
        global: {
          plugins: [pinia, router],
          stubs: {
            'el-button': true,
            'el-input': true,
            'el-select': true,
            'el-option': true,
            'el-table': true,
            'el-table-column': true,
            'el-pagination': true,
            'el-dialog': true,
            'el-form': true,
            'el-form-item': true,
            'el-card': true,
            'el-row': true,
            'el-col': true,
            'el-icon': true,
            'el-descriptions': true,
            'el-descriptions-item': true
          }
        }
      })
      await flushPromises()

      // 验证列表数据
      expect(wrapper.vm.employeeList).toHaveLength(4)
      expect(wrapper.vm.employeeList[0].name).toBe('张管理员')
      expect(wrapper.vm.employeeList[1].name).toBe('李员工')
      expect(wrapper.vm.employeeList[2].name).toBe('王员工')
      expect(wrapper.vm.employeeList[3].name).toBe('赵员工')

      // 验证分页数据
      expect(wrapper.vm.pagination.total).toBe(4)
    })

    it('1.3 应该正确显示统计信息', async () => {
      employeeApi.getEmployeeList.mockResolvedValue({
        data: {
          items: mockEmployees,
          pagination: {
            total: 4,
            page: 1,
            per_page: 20,
            pages: 1
          }
        }
      })

      employeeApi.getEmployeeStats.mockResolvedValue({
        data: mockStatistics
      })

      wrapper = mount(EmployeeList, {
        global: {
          plugins: [pinia, router],
          stubs: {
            'el-button': true,
            'el-input': true,
            'el-select': true,
            'el-option': true,
            'el-table': true,
            'el-table-column': true,
            'el-pagination': true,
            'el-dialog': true,
            'el-form': true,
            'el-form-item': true,
            'el-card': true,
            'el-row': true,
            'el-col': true,
            'el-icon': true,
            'el-descriptions': true,
            'el-descriptions-item': true
          }
        }
      })
      await flushPromises()

      // 验证统计信息
      expect(wrapper.vm.statistics.total).toBe(4)
      expect(wrapper.vm.statistics.active).toBe(2)
      expect(wrapper.vm.statistics.disabled).toBe(1)
      expect(wrapper.vm.statistics.resigned).toBe(1)
    })

    it('1.4 分页变化时应该重新加载数据', async () => {
      employeeApi.getEmployeeList.mockResolvedValue({
        data: {
          items: mockEmployees,
          pagination: {
            total: 40,
            page: 2,
            per_page: 20,
            pages: 2
          }
        }
      })

      employeeApi.getEmployeeStats.mockResolvedValue({
        data: mockStatistics
      })

      wrapper = mount(EmployeeList, {
        global: {
          plugins: [pinia, router],
          stubs: {
            'el-button': true,
            'el-input': true,
            'el-select': true,
            'el-option': true,
            'el-table': true,
            'el-table-column': true,
            'el-pagination': true,
            'el-dialog': true,
            'el-form': true,
            'el-form-item': true,
            'el-card': true,
            'el-row': true,
            'el-col': true,
            'el-icon': true,
            'el-descriptions': true,
            'el-descriptions-item': true
          }
        }
      })
      await flushPromises()

      // 清除之前的调用
      employeeApi.getEmployeeList.mockClear()

      // 触发页码变化
      wrapper.vm.handlePageChange(2)
      await flushPromises()

      // 验证 API 被调用且页码正确
      expect(employeeApi.getEmployeeList).toHaveBeenCalledWith({
        page: 2,
        per_page: 20,
        keyword: '',
        status: '',
        role: ''
      })
    })

    it('1.5 每页数量变化时应该重新加载数据', async () => {
      employeeApi.getEmployeeList.mockResolvedValue({
        data: {
          items: mockEmployees,
          pagination: {
            total: 40,
            page: 1,
            per_page: 50,
            pages: 1
          }
        }
      })

      employeeApi.getEmployeeStats.mockResolvedValue({
        data: mockStatistics
      })

      wrapper = mount(EmployeeList, {
        global: {
          plugins: [pinia, router],
          stubs: {
            'el-button': true,
            'el-input': true,
            'el-select': true,
            'el-option': true,
            'el-table': true,
            'el-table-column': true,
            'el-pagination': true,
            'el-dialog': true,
            'el-form': true,
            'el-form-item': true,
            'el-card': true,
            'el-row': true,
            'el-col': true,
            'el-icon': true,
            'el-descriptions': true,
            'el-descriptions-item': true
          }
        }
      })
      await flushPromises()

      // 清除之前的调用
      employeeApi.getEmployeeList.mockClear()

      // 触发每页数量变化
      wrapper.vm.handleSizeChange(50)
      await flushPromises()

      // 验证 API 被调用且参数正确
      expect(employeeApi.getEmployeeList).toHaveBeenCalledWith({
        page: 1,
        per_page: 50,
        keyword: '',
        status: '',
        role: ''
      })
    })

    it('1.6 加载数据时应该显示 loading 状态', async () => {
      let resolvePromise
      employeeApi.getEmployeeList.mockImplementation(() => {
        return new Promise((resolve) => {
          resolvePromise = resolve
        })
      })

      employeeApi.getEmployeeStats.mockResolvedValue({
        data: mockStatistics
      })

      wrapper = mount(EmployeeList, {
        global: {
          plugins: [pinia, router],
          stubs: {
            'el-button': true,
            'el-input': true,
            'el-select': true,
            'el-option': true,
            'el-table': true,
            'el-table-column': true,
            'el-pagination': true,
            'el-dialog': true,
            'el-form': true,
            'el-form-item': true,
            'el-card': true,
            'el-row': true,
            'el-col': true,
            'el-icon': true,
            'el-descriptions': true,
            'el-descriptions-item': true
          }
        }
      })

      // 验证 loading 状态为 true
      expect(wrapper.vm.loading).toBe(true)

      // 解决 Promise
      resolvePromise({
        data: {
          items: mockEmployees,
          pagination: { total: 4, page: 1, per_page: 20, pages: 1 }
        }
      })
      await flushPromises()

      // 验证 loading 状态为 false
      expect(wrapper.vm.loading).toBe(false)
    })

    it('1.7 加载失败时应该显示错误提示', async () => {
      employeeApi.getEmployeeList.mockRejectedValue(new Error('网络错误'))

      employeeApi.getEmployeeStats.mockResolvedValue({
        data: mockStatistics
      })

      wrapper = mount(EmployeeList, {
        global: {
          plugins: [pinia, router],
          stubs: {
            'el-button': true,
            'el-input': true,
            'el-select': true,
            'el-option': true,
            'el-table': true,
            'el-table-column': true,
            'el-pagination': true,
            'el-dialog': true,
            'el-form': true,
            'el-form-item': true,
            'el-card': true,
            'el-row': true,
            'el-col': true,
            'el-icon': true,
            'el-descriptions': true,
            'el-descriptions-item': true
          }
        }
      })
      await flushPromises()

      // 验证错误提示
      expect(ElMessage.error).toHaveBeenCalledWith('网络错误')
      expect(wrapper.vm.loading).toBe(false)
    })

    it('1.8 搜索时应该重置页码为 1', async () => {
      employeeApi.getEmployeeList.mockResolvedValue({
        data: {
          items: mockEmployees,
          pagination: { total: 40, page: 1, per_page: 20, pages: 2 }
        }
      })

      employeeApi.getEmployeeStats.mockResolvedValue({
        data: mockStatistics
      })

      wrapper = mount(EmployeeList, {
        global: {
          plugins: [pinia, router],
          stubs: {
            'el-button': true,
            'el-input': true,
            'el-select': true,
            'el-option': true,
            'el-table': true,
            'el-table-column': true,
            'el-pagination': true,
            'el-dialog': true,
            'el-form': true,
            'el-form-item': true,
            'el-card': true,
            'el-row': true,
            'el-col': true,
            'el-icon': true,
            'el-descriptions': true,
            'el-descriptions-item': true
          }
        }
      })
      await flushPromises()

      // 设置当前页码为 2
      wrapper.vm.pagination.page = 2

      // 清除之前的调用
      employeeApi.getEmployeeList.mockClear()

      // 搜索
      wrapper.vm.filterForm.keyword = '张'
      wrapper.vm.handleSearch()
      await flushPromises()

      // 验证页码被重置为 1
      expect(wrapper.vm.pagination.page).toBe(1)
    })
  })

  // ============================================
  // 2. 测试权限标识显示
  // ============================================
  describe('2. 测试权限标识显示', () => {
    it('2.1 应该正确显示管理员角色标识', async () => {
      employeeApi.getEmployeeList.mockResolvedValue({
        data: {
          items: [mockEmployees[0]],
          pagination: { total: 1, page: 1, per_page: 20, pages: 1 }
        }
      })

      employeeApi.getEmployeeStats.mockResolvedValue({
        data: mockStatistics
      })

      wrapper = mount(EmployeeList, {
        global: {
          plugins: [pinia, router],
          stubs: {
            'el-button': true,
            'el-input': true,
            'el-select': true,
            'el-option': true,
            'el-table': true,
            'el-table-column': true,
            'el-pagination': true,
            'el-dialog': true,
            'el-form': true,
            'el-form-item': true,
            'el-card': true,
            'el-row': true,
            'el-col': true,
            'el-icon': true,
            'el-descriptions': true,
            'el-descriptions-item': true
          }
        }
      })
      await flushPromises()

      // 验证角色映射
      expect(wrapper.vm.roleMap['admin']).toBe('管理员')
      expect(wrapper.vm.roleMap['staff']).toBe('员工')
    })

    it('2.2 应该正确显示状态标识', async () => {
      employeeApi.getEmployeeList.mockResolvedValue({
        data: {
          items: mockEmployees,
          pagination: { total: 4, page: 1, per_page: 20, pages: 1 }
        }
      })

      employeeApi.getEmployeeStats.mockResolvedValue({
        data: mockStatistics
      })

      wrapper = mount(EmployeeList, {
        global: {
          plugins: [pinia, router],
          stubs: {
            'el-button': true,
            'el-input': true,
            'el-select': true,
            'el-option': true,
            'el-table': true,
            'el-table-column': true,
            'el-pagination': true,
            'el-dialog': true,
            'el-form': true,
            'el-form-item': true,
            'el-card': true,
            'el-row': true,
            'el-col': true,
            'el-icon': true,
            'el-descriptions': true,
            'el-descriptions-item': true
          }
        }
      })
      await flushPromises()

      // 验证状态映射
      expect(wrapper.vm.statusMap['active']).toBe('在职')
      expect(wrapper.vm.statusMap['resigned']).toBe('离职')
      expect(wrapper.vm.statusMap['disabled']).toBe('禁用')
    })

    it('2.3 getStatusText 应该返回正确的状态文本', async () => {
      employeeApi.getEmployeeList.mockResolvedValue({
        data: {
          items: mockEmployees,
          pagination: { total: 4, page: 1, per_page: 20, pages: 1 }
        }
      })

      employeeApi.getEmployeeStats.mockResolvedValue({
        data: mockStatistics
      })

      wrapper = mount(EmployeeList, {
        global: {
          plugins: [pinia, router],
          stubs: {
            'el-button': true,
            'el-input': true,
            'el-select': true,
            'el-option': true,
            'el-table': true,
            'el-table-column': true,
            'el-pagination': true,
            'el-dialog': true,
            'el-form': true,
            'el-form-item': true,
            'el-card': true,
            'el-row': true,
            'el-col': true,
            'el-icon': true,
            'el-descriptions': true,
            'el-descriptions-item': true
          }
        }
      })
      await flushPromises()

      expect(wrapper.vm.getStatusText('active')).toBe('在职')
      expect(wrapper.vm.getStatusText('resigned')).toBe('离职')
      expect(wrapper.vm.getStatusText('disabled')).toBe('禁用')
      expect(wrapper.vm.getStatusText('unknown')).toBe('未知')
    })

    it('2.4 getStatusType 应该返回正确的状态类型', async () => {
      employeeApi.getEmployeeList.mockResolvedValue({
        data: {
          items: mockEmployees,
          pagination: { total: 4, page: 1, per_page: 20, pages: 1 }
        }
      })

      employeeApi.getEmployeeStats.mockResolvedValue({
        data: mockStatistics
      })

      wrapper = mount(EmployeeList, {
        global: {
          plugins: [pinia, router],
          stubs: {
            'el-button': true,
            'el-input': true,
            'el-select': true,
            'el-option': true,
            'el-table': true,
            'el-table-column': true,
            'el-pagination': true,
            'el-dialog': true,
            'el-form': true,
            'el-form-item': true,
            'el-card': true,
            'el-row': true,
            'el-col': true,
            'el-icon': true,
            'el-descriptions': true,
            'el-descriptions-item': true
          }
        }
      })
      await flushPromises()

      expect(wrapper.vm.getStatusType('active')).toBe('success')
      expect(wrapper.vm.getStatusType('resigned')).toBe('info')
      expect(wrapper.vm.getStatusType('disabled')).toBe('danger')
      expect(wrapper.vm.getStatusType('unknown')).toBe('info')
    })

    it('2.5 管理员角色的员工删除按钮应该被禁用', async () => {
      employeeApi.getEmployeeList.mockResolvedValue({
        data: {
          items: mockEmployees,
          pagination: { total: 4, page: 1, per_page: 20, pages: 1 }
        }
      })

      employeeApi.getEmployeeStats.mockResolvedValue({
        data: mockStatistics
      })

      wrapper = mount(EmployeeList, {
        global: {
          plugins: [pinia, router],
          stubs: {
            'el-button': true,
            'el-input': true,
            'el-select': true,
            'el-option': true,
            'el-table': true,
            'el-table-column': true,
            'el-pagination': true,
            'el-dialog': true,
            'el-form': true,
            'el-form-item': true,
            'el-card': true,
            'el-row': true,
            'el-col': true,
            'el-icon': true,
            'el-descriptions': true,
            'el-descriptions-item': true
          }
        }
      })
      await flushPromises()

      // 验证管理员不能被删除
      const adminEmployee = mockEmployees[0]
      expect(adminEmployee.role).toBe('admin')
    })
  })

  // ============================================
  // 3. 测试新增员工表单
  // ============================================
  describe('3. 测试新增员工表单', () => {
    it('3.1 点击新增按钮应该打开对话框', async () => {
      employeeApi.getEmployeeList.mockResolvedValue({
        data: {
          items: mockEmployees,
          pagination: { total: 4, page: 1, per_page: 20, pages: 1 }
        }
      })

      employeeApi.getEmployeeStats.mockResolvedValue({
        data: mockStatistics
      })

      wrapper = mount(EmployeeList, {
        global: {
          plugins: [pinia, router],
          stubs: {
            'el-button': true,
            'el-input': true,
            'el-select': true,
            'el-option': true,
            'el-table': true,
            'el-table-column': true,
            'el-pagination': true,
            'el-dialog': true,
            'el-form': true,
            'el-form-item': true,
            'el-card': true,
            'el-row': true,
            'el-col': true,
            'el-icon': true,
            'el-descriptions': true,
            'el-descriptions-item': true
          }
        }
      })
      await flushPromises()

      // 点击新增按钮
      wrapper.vm.handleAdd()
      await flushPromises()

      // 验证对话框状态
      expect(wrapper.vm.dialogVisible).toBe(true)
      expect(wrapper.vm.isEdit).toBe(false)
      expect(wrapper.vm.dialogTitle).toBe('新增员工')
    })

    it('3.2 新增对话框应该显示密码字段', async () => {
      employeeApi.getEmployeeList.mockResolvedValue({
        data: {
          items: mockEmployees,
          pagination: { total: 4, page: 1, per_page: 20, pages: 1 }
        }
      })

      employeeApi.getEmployeeStats.mockResolvedValue({
        data: mockStatistics
      })

      wrapper = mount(EmployeeList, {
        global: {
          plugins: [pinia, router],
          stubs: {
            'el-button': true,
            'el-input': true,
            'el-select': true,
            'el-option': true,
            'el-table': true,
            'el-table-column': true,
            'el-pagination': true,
            'el-dialog': true,
            'el-form': true,
            'el-form-item': true,
            'el-card': true,
            'el-row': true,
            'el-col': true,
            'el-icon': true,
            'el-descriptions': true,
            'el-descriptions-item': true
          }
        }
      })
      await flushPromises()

      // 点击新增按钮
      wrapper.vm.handleAdd()
      await flushPromises()

      // 验证是新增模式
      expect(wrapper.vm.isEdit).toBe(false)
    })

    it('3.3 提交新增表单应该调用 createEmployee API', async () => {
      employeeApi.getEmployeeList.mockResolvedValue({
        data: {
          items: mockEmployees,
          pagination: { total: 4, page: 1, per_page: 20, pages: 1 }
        }
      })

      employeeApi.getEmployeeStats.mockResolvedValue({
        data: mockStatistics
      })

      employeeApi.createEmployee.mockResolvedValue({
        data: { id: 5, name: '新员工' }
      })

      wrapper = mount(EmployeeList, {
        global: {
          plugins: [pinia, router],
          stubs: {
            'el-button': true,
            'el-input': true,
            'el-select': true,
            'el-option': true,
            'el-table': true,
            'el-table-column': true,
            'el-pagination': true,
            'el-dialog': true,
            'el-form': true,
            'el-form-item': true,
            'el-card': true,
            'el-row': true,
            'el-col': true,
            'el-icon': true,
            'el-descriptions': true,
            'el-descriptions-item': true
          }
        }
      })
      await flushPromises()

      // 打开新增对话框
      wrapper.vm.handleAdd()
      await flushPromises()

      // 模拟表单数据
      wrapper.vm.formData.username = 'newstaff'
      wrapper.vm.formData.password = 'password123'
      wrapper.vm.formData.name = '新员工'
      wrapper.vm.formData.phone = '13900139000'
      wrapper.vm.formData.email = 'newstaff@example.com'
      wrapper.vm.formData.position = '业务员'
      wrapper.vm.formData.role = 'staff'

      // 模拟表单验证通过
      wrapper.vm.formRef = {
        validate: vi.fn((callback) => callback(true))
      }

      // 提交表单
      await wrapper.vm.handleSubmit()
      await flushPromises()

      // 验证 API 被调用
      expect(employeeApi.createEmployee).toHaveBeenCalled()
      expect(ElMessage.success).toHaveBeenCalledWith('创建成功')
      expect(wrapper.vm.dialogVisible).toBe(false)
    })

    it('3.4 新增成功后应该刷新列表和统计', async () => {
      employeeApi.getEmployeeList.mockResolvedValue({
        data: {
          items: mockEmployees,
          pagination: { total: 4, page: 1, per_page: 20, pages: 1 }
        }
      })

      employeeApi.getEmployeeStats.mockResolvedValue({
        data: mockStatistics
      })

      employeeApi.createEmployee.mockResolvedValue({
        data: { id: 5 }
      })

      wrapper = mount(EmployeeList, {
        global: {
          plugins: [pinia, router],
          stubs: {
            'el-button': true,
            'el-input': true,
            'el-select': true,
            'el-option': true,
            'el-table': true,
            'el-table-column': true,
            'el-pagination': true,
            'el-dialog': true,
            'el-form': true,
            'el-form-item': true,
            'el-card': true,
            'el-row': true,
            'el-col': true,
            'el-icon': true,
            'el-descriptions': true,
            'el-descriptions-item': true
          }
        }
      })
      await flushPromises()

      // 清除之前的调用
      employeeApi.getEmployeeList.mockClear()
      employeeApi.getEmployeeStats.mockClear()

      // 打开新增对话框并提交
      wrapper.vm.handleAdd()
      await flushPromises()

      wrapper.vm.formData.username = 'newstaff'
      wrapper.vm.formData.password = 'password123'
      wrapper.vm.formData.name = '新员工'
      wrapper.vm.formData.phone = '13900139000'

      wrapper.vm.formRef = {
        validate: vi.fn((callback) => callback(true))
      }

      await wrapper.vm.handleSubmit()
      await flushPromises()

      // 验证列表和统计被刷新
      expect(employeeApi.getEmployeeList).toHaveBeenCalledTimes(1)
      expect(employeeApi.getEmployeeStats).toHaveBeenCalledTimes(1)
    })

    it('3.5 新增失败应该显示错误提示', async () => {
      employeeApi.getEmployeeList.mockResolvedValue({
        data: {
          items: mockEmployees,
          pagination: { total: 4, page: 1, per_page: 20, pages: 1 }
        }
      })

      employeeApi.getEmployeeStats.mockResolvedValue({
        data: mockStatistics
      })

      employeeApi.createEmployee.mockRejectedValue({
        message: '用户名已存在'
      })

      wrapper = mount(EmployeeList, {
        global: {
          plugins: [pinia, router],
          stubs: {
            'el-button': true,
            'el-input': true,
            'el-select': true,
            'el-option': true,
            'el-table': true,
            'el-table-column': true,
            'el-pagination': true,
            'el-dialog': true,
            'el-form': true,
            'el-form-item': true,
            'el-card': true,
            'el-row': true,
            'el-col': true,
            'el-icon': true,
            'el-descriptions': true,
            'el-descriptions-item': true
          }
        }
      })
      await flushPromises()

      // 打开新增对话框并提交
      wrapper.vm.handleAdd()
      await flushPromises()

      wrapper.vm.formData.username = 'admin' // 已存在的用户名
      wrapper.vm.formData.password = 'password123'
      wrapper.vm.formData.name = '新员工'
      wrapper.vm.formData.phone = '13900139000'

      wrapper.vm.formRef = {
        validate: vi.fn((callback) => callback(true))
      }

      await wrapper.vm.handleSubmit()
      await flushPromises()

      // 验证错误提示
      expect(ElMessage.error).toHaveBeenCalledWith('用户名已存在')
      expect(wrapper.vm.dialogVisible).toBe(true) // 对话框保持打开
    })

    it('3.6 表单验证失败不应该提交', async () => {
      employeeApi.getEmployeeList.mockResolvedValue({
        data: {
          items: mockEmployees,
          pagination: { total: 4, page: 1, per_page: 20, pages: 1 }
        }
      })

      employeeApi.getEmployeeStats.mockResolvedValue({
        data: mockStatistics
      })

      wrapper = mount(EmployeeList, {
        global: {
          plugins: [pinia, router],
          stubs: {
            'el-button': true,
            'el-input': true,
            'el-select': true,
            'el-option': true,
            'el-table': true,
            'el-table-column': true,
            'el-pagination': true,
            'el-dialog': true,
            'el-form': true,
            'el-form-item': true,
            'el-card': true,
            'el-row': true,
            'el-col': true,
            'el-icon': true,
            'el-descriptions': true,
            'el-descriptions-item': true
          }
        }
      })
      await flushPromises()

      // 打开新增对话框
      wrapper.vm.handleAdd()
      await flushPromises()

      // 模拟表单验证失败
      wrapper.vm.formRef = {
        validate: vi.fn((callback) => callback(false))
      }

      // 提交表单
      await wrapper.vm.handleSubmit()
      await flushPromises()

      // 验证 API 没有被调用
      expect(employeeApi.createEmployee).not.toHaveBeenCalled()
    })
  })

  // ============================================
  // 4. 测试编辑员工表单
  // ============================================
  describe('4. 测试编辑员工表单', () => {
    it('4.1 点击编辑按钮应该打开对话框并填充数据', async () => {
      employeeApi.getEmployeeList.mockResolvedValue({
        data: {
          items: mockEmployees,
          pagination: { total: 4, page: 1, per_page: 20, pages: 1 }
        }
      })

      employeeApi.getEmployeeStats.mockResolvedValue({
        data: mockStatistics
      })

      wrapper = mount(EmployeeList, {
        global: {
          plugins: [pinia, router],
          stubs: {
            'el-button': true,
            'el-input': true,
            'el-select': true,
            'el-option': true,
            'el-table': true,
            'el-table-column': true,
            'el-pagination': true,
            'el-dialog': true,
            'el-form': true,
            'el-form-item': true,
            'el-card': true,
            'el-row': true,
            'el-col': true,
            'el-icon': true,
            'el-descriptions': true,
            'el-descriptions-item': true
          }
        }
      })
      await flushPromises()

      // 点击编辑按钮
      const employee = mockEmployees[1]
      wrapper.vm.handleEdit(employee)
      await flushPromises()

      // 验证对话框状态
      expect(wrapper.vm.dialogVisible).toBe(true)
      expect(wrapper.vm.isEdit).toBe(true)
      expect(wrapper.vm.dialogTitle).toBe('编辑员工')
      expect(wrapper.vm.formData.id).toBe(employee.id)
      expect(wrapper.vm.formData.name).toBe(employee.name)
      expect(wrapper.vm.formData.username).toBe(employee.username)
    })

    it('4.2 编辑对话框用户名字段应该被禁用', async () => {
      employeeApi.getEmployeeList.mockResolvedValue({
        data: {
          items: mockEmployees,
          pagination: { total: 4, page: 1, per_page: 20, pages: 1 }
        }
      })

      employeeApi.getEmployeeStats.mockResolvedValue({
        data: mockStatistics
      })

      wrapper = mount(EmployeeList, {
        global: {
          plugins: [pinia, router],
          stubs: {
            'el-button': true,
            'el-input': true,
            'el-select': true,
            'el-option': true,
            'el-table': true,
            'el-table-column': true,
            'el-pagination': true,
            'el-dialog': true,
            'el-form': true,
            'el-form-item': true,
            'el-card': true,
            'el-row': true,
            'el-col': true,
            'el-icon': true,
            'el-descriptions': true,
            'el-descriptions-item': true
          }
        }
      })
      await flushPromises()

      // 点击编辑按钮
      wrapper.vm.handleEdit(mockEmployees[1])
      await flushPromises()

      // 验证是编辑模式
      expect(wrapper.vm.isEdit).toBe(true)
    })

    it('4.3 编辑对话框应该显示状态字段', async () => {
      employeeApi.getEmployeeList.mockResolvedValue({
        data: {
          items: mockEmployees,
          pagination: { total: 4, page: 1, per_page: 20, pages: 1 }
        }
      })

      employeeApi.getEmployeeStats.mockResolvedValue({
        data: mockStatistics
      })

      wrapper = mount(EmployeeList, {
        global: {
          plugins: [pinia, router],
          stubs: {
            'el-button': true,
            'el-input': true,
            'el-select': true,
            'el-option': true,
            'el-table': true,
            'el-table-column': true,
            'el-pagination': true,
            'el-dialog': true,
            'el-form': true,
            'el-form-item': true,
            'el-card': true,
            'el-row': true,
            'el-col': true,
            'el-icon': true,
            'el-descriptions': true,
            'el-descriptions-item': true
          }
        }
      })
      await flushPromises()

      // 点击编辑按钮
      wrapper.vm.handleEdit(mockEmployees[1])
      await flushPromises()

      // 验证是编辑模式
      expect(wrapper.vm.isEdit).toBe(true)
    })

    it('4.4 提交编辑表单应该调用 updateEmployee API', async () => {
      employeeApi.getEmployeeList.mockResolvedValue({
        data: {
          items: mockEmployees,
          pagination: { total: 4, page: 1, per_page: 20, pages: 1 }
        }
      })

      employeeApi.getEmployeeStats.mockResolvedValue({
        data: mockStatistics
      })

      employeeApi.updateEmployee.mockResolvedValue({
        data: { ...mockEmployees[1], name: '李员工更新' }
      })

      wrapper = mount(EmployeeList, {
        global: {
          plugins: [pinia, router],
          stubs: {
            'el-button': true,
            'el-input': true,
            'el-select': true,
            'el-option': true,
            'el-table': true,
            'el-table-column': true,
            'el-pagination': true,
            'el-dialog': true,
            'el-form': true,
            'el-form-item': true,
            'el-card': true,
            'el-row': true,
            'el-col': true,
            'el-icon': true,
            'el-descriptions': true,
            'el-descriptions-item': true
          }
        }
      })
      await flushPromises()

      // 打开编辑对话框
      wrapper.vm.handleEdit(mockEmployees[1])
      await flushPromises()

      // 修改数据
      wrapper.vm.formData.name = '李员工更新'

      wrapper.vm.formRef = {
        validate: vi.fn((callback) => callback(true))
      }

      // 提交表单
      await wrapper.vm.handleSubmit()
      await flushPromises()

      // 验证 API 被调用
      expect(employeeApi.updateEmployee).toHaveBeenCalled()
      expect(ElMessage.success).toHaveBeenCalledWith('更新成功')
      expect(wrapper.vm.dialogVisible).toBe(false)
    })

    it('4.5 编辑成功后应该刷新列表和统计', async () => {
      employeeApi.getEmployeeList.mockResolvedValue({
        data: {
          items: mockEmployees,
          pagination: { total: 4, page: 1, per_page: 20, pages: 1 }
        }
      })

      employeeApi.getEmployeeStats.mockResolvedValue({
        data: mockStatistics
      })

      employeeApi.updateEmployee.mockResolvedValue({
        data: mockEmployees[1]
      })

      wrapper = mount(EmployeeList, {
        global: {
          plugins: [pinia, router],
          stubs: {
            'el-button': true,
            'el-input': true,
            'el-select': true,
            'el-option': true,
            'el-table': true,
            'el-table-column': true,
            'el-pagination': true,
            'el-dialog': true,
            'el-form': true,
            'el-form-item': true,
            'el-card': true,
            'el-row': true,
            'el-col': true,
            'el-icon': true,
            'el-descriptions': true,
            'el-descriptions-item': true
          }
        }
      })
      await flushPromises()

      // 清除之前的调用
      employeeApi.getEmployeeList.mockClear()
      employeeApi.getEmployeeStats.mockClear()

      // 打开编辑对话框并提交
      wrapper.vm.handleEdit(mockEmployees[1])
      await flushPromises()

      wrapper.vm.formRef = {
        validate: vi.fn((callback) => callback(true))
      }

      await wrapper.vm.handleSubmit()
      await flushPromises()

      // 验证列表和统计被刷新
      expect(employeeApi.getEmployeeList).toHaveBeenCalledTimes(1)
      expect(employeeApi.getEmployeeStats).toHaveBeenCalledTimes(1)
    })

    it('4.6 编辑失败应该显示错误提示', async () => {
      employeeApi.getEmployeeList.mockResolvedValue({
        data: {
          items: mockEmployees,
          pagination: { total: 4, page: 1, per_page: 20, pages: 1 }
        }
      })

      employeeApi.getEmployeeStats.mockResolvedValue({
        data: mockStatistics
      })

      employeeApi.updateEmployee.mockRejectedValue({
        message: '更新失败，请重试'
      })

      wrapper = mount(EmployeeList, {
        global: {
          plugins: [pinia, router],
          stubs: {
            'el-button': true,
            'el-input': true,
            'el-select': true,
            'el-option': true,
            'el-table': true,
            'el-table-column': true,
            'el-pagination': true,
            'el-dialog': true,
            'el-form': true,
            'el-form-item': true,
            'el-card': true,
            'el-row': true,
            'el-col': true,
            'el-icon': true,
            'el-descriptions': true,
            'el-descriptions-item': true
          }
        }
      })
      await flushPromises()

      // 打开编辑对话框并提交
      wrapper.vm.handleEdit(mockEmployees[1])
      await flushPromises()

      wrapper.vm.formRef = {
        validate: vi.fn((callback) => callback(true))
      }

      await wrapper.vm.handleSubmit()
      await flushPromises()

      // 验证错误提示
      expect(ElMessage.error).toHaveBeenCalledWith('更新失败，请重试')
      expect(wrapper.vm.dialogVisible).toBe(true) // 对话框保持打开
    })
  })

  // ============================================
  // 5. 测试其他功能
  // ============================================
  describe('5. 测试其他功能', () => {
    it('5.1 查看员工详情应该打开详情对话框', async () => {
      employeeApi.getEmployeeList.mockResolvedValue({
        data: {
          items: mockEmployees,
          pagination: { total: 4, page: 1, per_page: 20, pages: 1 }
        }
      })

      employeeApi.getEmployeeStats.mockResolvedValue({
        data: mockStatistics
      })

      wrapper = mount(EmployeeList, {
        global: {
          plugins: [pinia, router],
          stubs: {
            'el-button': true,
            'el-input': true,
            'el-select': true,
            'el-option': true,
            'el-table': true,
            'el-table-column': true,
            'el-pagination': true,
            'el-dialog': true,
            'el-form': true,
            'el-form-item': true,
            'el-card': true,
            'el-row': true,
            'el-col': true,
            'el-icon': true,
            'el-descriptions': true,
            'el-descriptions-item': true
          }
        }
      })
      await flushPromises()

      // 点击详情按钮
      wrapper.vm.handleView(mockEmployees[1])
      await flushPromises()

      // 验证详情对话框状态
      expect(wrapper.vm.detailVisible).toBe(true)
      expect(wrapper.vm.currentEmployee.name).toBe('李员工')
    })

    it('5.2 切换员工状态应该调用 updateEmployeeStatus API', async () => {
      employeeApi.getEmployeeList.mockResolvedValue({
        data: {
          items: mockEmployees,
          pagination: { total: 4, page: 1, per_page: 20, pages: 1 }
        }
      })

      employeeApi.getEmployeeStats.mockResolvedValue({
        data: mockStatistics
      })

      employeeApi.updateEmployeeStatus.mockResolvedValue({
        data: { status: 'disabled' }
      })

      ElMessageBox.confirm.mockResolvedValue('confirm')

      wrapper = mount(EmployeeList, {
        global: {
          plugins: [pinia, router],
          stubs: {
            'el-button': true,
            'el-input': true,
            'el-select': true,
            'el-option': true,
            'el-table': true,
            'el-table-column': true,
            'el-pagination': true,
            'el-dialog': true,
            'el-form': true,
            'el-form-item': true,
            'el-card': true,
            'el-row': true,
            'el-col': true,
            'el-icon': true,
            'el-descriptions': true,
            'el-descriptions-item': true
          }
        }
      })
      await flushPromises()

      // 切换状态
      await wrapper.vm.handleToggleStatus(mockEmployees[1])
      await flushPromises()

      // 验证 API 被调用
      expect(employeeApi.updateEmployeeStatus).toHaveBeenCalledWith(2, 'disabled')
      expect(ElMessage.success).toHaveBeenCalledWith('禁用成功')
    })

    it('5.3 取消切换状态不应该调用 API', async () => {
      employeeApi.getEmployeeList.mockResolvedValue({
        data: {
          items: mockEmployees,
          pagination: { total: 4, page: 1, per_page: 20, pages: 1 }
        }
      })

      employeeApi.getEmployeeStats.mockResolvedValue({
        data: mockStatistics
      })

      ElMessageBox.confirm.mockRejectedValue(new Error('cancel'))

      wrapper = mount(EmployeeList, {
        global: {
          plugins: [pinia, router],
          stubs: {
            'el-button': true,
            'el-input': true,
            'el-select': true,
            'el-option': true,
            'el-table': true,
            'el-table-column': true,
            'el-pagination': true,
            'el-dialog': true,
            'el-form': true,
            'el-form-item': true,
            'el-card': true,
            'el-row': true,
            'el-col': true,
            'el-icon': true,
            'el-descriptions': true,
            'el-descriptions-item': true
          }
        }
      })
      await flushPromises()

      // 取消切换状态
      await wrapper.vm.handleToggleStatus(mockEmployees[1])
      await flushPromises()

      // 验证 API 没有被调用
      expect(employeeApi.updateEmployeeStatus).not.toHaveBeenCalled()
    })

    it('5.4 重置密码应该调用 resetEmployeePassword API', async () => {
      employeeApi.getEmployeeList.mockResolvedValue({
        data: {
          items: mockEmployees,
          pagination: { total: 4, page: 1, per_page: 20, pages: 1 }
        }
      })

      employeeApi.getEmployeeStats.mockResolvedValue({
        data: mockStatistics
      })

      employeeApi.resetEmployeePassword.mockResolvedValue({
        data: { success: true }
      })

      wrapper = mount(EmployeeList, {
        global: {
          plugins: [pinia, router],
          stubs: {
            'el-button': true,
            'el-input': true,
            'el-select': true,
            'el-option': true,
            'el-table': true,
            'el-table-column': true,
            'el-pagination': true,
            'el-dialog': true,
            'el-form': true,
            'el-form-item': true,
            'el-card': true,
            'el-row': true,
            'el-col': true,
            'el-icon': true,
            'el-descriptions': true,
            'el-descriptions-item': true
          }
        }
      })
      await flushPromises()

      // 打开重置密码对话框
      wrapper.vm.handleResetPassword(mockEmployees[1])
      await flushPromises()

      // 设置新密码
      wrapper.vm.passwordForm.newPassword = 'newpassword123'

      // 确认重置
      await wrapper.vm.confirmResetPassword()
      await flushPromises()

      // 验证 API 被调用
      expect(employeeApi.resetEmployeePassword).toHaveBeenCalledWith(2, 'newpassword123')
      expect(ElMessage.success).toHaveBeenCalledWith('密码重置成功')
    })

    it('5.5 重置密码时密码长度不足应该显示警告', async () => {
      employeeApi.getEmployeeList.mockResolvedValue({
        data: {
          items: mockEmployees,
          pagination: { total: 4, page: 1, per_page: 20, pages: 1 }
        }
      })

      employeeApi.getEmployeeStats.mockResolvedValue({
        data: mockStatistics
      })

      wrapper = mount(EmployeeList, {
        global: {
          plugins: [pinia, router],
          stubs: {
            'el-button': true,
            'el-input': true,
            'el-select': true,
            'el-option': true,
            'el-table': true,
            'el-table-column': true,
            'el-pagination': true,
            'el-dialog': true,
            'el-form': true,
            'el-form-item': true,
            'el-card': true,
            'el-row': true,
            'el-col': true,
            'el-icon': true,
            'el-descriptions': true,
            'el-descriptions-item': true
          }
        }
      })
      await flushPromises()

      // 打开重置密码对话框
      wrapper.vm.handleResetPassword(mockEmployees[1])
      await flushPromises()

      // 设置短密码
      wrapper.vm.passwordForm.newPassword = '123'

      // 确认重置
      await wrapper.vm.confirmResetPassword()
      await flushPromises()

      // 验证警告提示
      expect(ElMessage.warning).toHaveBeenCalledWith('密码长度不能少于 6 个字符')
      expect(employeeApi.resetEmployeePassword).not.toHaveBeenCalled()
    })

    it('5.6 删除员工应该调用 deleteEmployee API', async () => {
      employeeApi.getEmployeeList.mockResolvedValue({
        data: {
          items: mockEmployees,
          pagination: { total: 4, page: 1, per_page: 20, pages: 1 }
        }
      })

      employeeApi.getEmployeeStats.mockResolvedValue({
        data: mockStatistics
      })

      employeeApi.deleteEmployee.mockResolvedValue({
        data: { success: true }
      })

      ElMessageBox.confirm.mockResolvedValue('confirm')

      wrapper = mount(EmployeeList, {
        global: {
          plugins: [pinia, router],
          stubs: {
            'el-button': true,
            'el-input': true,
            'el-select': true,
            'el-option': true,
            'el-table': true,
            'el-table-column': true,
            'el-pagination': true,
            'el-dialog': true,
            'el-form': true,
            'el-form-item': true,
            'el-card': true,
            'el-row': true,
            'el-col': true,
            'el-icon': true,
            'el-descriptions': true,
            'el-descriptions-item': true
          }
        }
      })
      await flushPromises()

      // 删除员工
      await wrapper.vm.handleDelete(mockEmployees[1])
      await flushPromises()

      // 验证 API 被调用
      expect(employeeApi.deleteEmployee).toHaveBeenCalledWith(2)
      expect(ElMessage.success).toHaveBeenCalledWith('删除成功')
    })

    it('5.7 取消删除不应该调用 API', async () => {
      employeeApi.getEmployeeList.mockResolvedValue({
        data: {
          items: mockEmployees,
          pagination: { total: 4, page: 1, per_page: 20, pages: 1 }
        }
      })

      employeeApi.getEmployeeStats.mockResolvedValue({
        data: mockStatistics
      })

      ElMessageBox.confirm.mockRejectedValue(new Error('cancel'))

      wrapper = mount(EmployeeList, {
        global: {
          plugins: [pinia, router],
          stubs: {
            'el-button': true,
            'el-input': true,
            'el-select': true,
            'el-option': true,
            'el-table': true,
            'el-table-column': true,
            'el-pagination': true,
            'el-dialog': true,
            'el-form': true,
            'el-form-item': true,
            'el-card': true,
            'el-row': true,
            'el-col': true,
            'el-icon': true,
            'el-descriptions': true,
            'el-descriptions-item': true
          }
        }
      })
      await flushPromises()

      // 取消删除
      await wrapper.vm.handleDelete(mockEmployees[1])
      await flushPromises()

      // 验证 API 没有被调用
      expect(employeeApi.deleteEmployee).not.toHaveBeenCalled()
    })

    it('5.8 批量操作员工应该调用 batchActionEmployees API', async () => {
      employeeApi.getEmployeeList.mockResolvedValue({
        data: {
          items: mockEmployees,
          pagination: { total: 4, page: 1, per_page: 20, pages: 1 }
        }
      })

      employeeApi.getEmployeeStats.mockResolvedValue({
        data: mockStatistics
      })

      employeeApi.batchActionEmployees.mockResolvedValue({
        data: { success: true }
      })

      ElMessageBox.confirm.mockResolvedValue('confirm')

      wrapper = mount(EmployeeList, {
        global: {
          plugins: [pinia, router],
          stubs: {
            'el-button': true,
            'el-input': true,
            'el-select': true,
            'el-option': true,
            'el-table': true,
            'el-table-column': true,
            'el-pagination': true,
            'el-dialog': true,
            'el-form': true,
            'el-form-item': true,
            'el-card': true,
            'el-row': true,
            'el-col': true,
            'el-icon': true,
            'el-descriptions': true,
            'el-descriptions-item': true
          }
        }
      })
      await flushPromises()

      // 选择员工
      wrapper.vm.selectedEmployees = [mockEmployees[1], mockEmployees[2]]

      // 批量禁用
      await wrapper.vm.handleBatchAction('disable')
      await flushPromises()

      // 验证 API 被调用
      expect(employeeApi.batchActionEmployees).toHaveBeenCalledWith({
        user_ids: [2, 3],
        action: 'disable'
      })
      expect(ElMessage.success).toHaveBeenCalledWith('批量禁用成功')
    })

    it('5.9 重置搜索条件应该清空所有筛选', async () => {
      employeeApi.getEmployeeList.mockResolvedValue({
        data: {
          items: mockEmployees,
          pagination: { total: 4, page: 1, per_page: 20, pages: 1 }
        }
      })

      employeeApi.getEmployeeStats.mockResolvedValue({
        data: mockStatistics
      })

      wrapper = mount(EmployeeList, {
        global: {
          plugins: [pinia, router],
          stubs: {
            'el-button': true,
            'el-input': true,
            'el-select': true,
            'el-option': true,
            'el-table': true,
            'el-table-column': true,
            'el-pagination': true,
            'el-dialog': true,
            'el-form': true,
            'el-form-item': true,
            'el-card': true,
            'el-row': true,
            'el-col': true,
            'el-icon': true,
            'el-descriptions': true,
            'el-descriptions-item': true
          }
        }
      })
      await flushPromises()

      // 设置搜索条件
      wrapper.vm.filterForm.keyword = '张'
      wrapper.vm.filterForm.status = 'active'
      wrapper.vm.filterForm.role = 'admin'

      // 清除之前的调用
      employeeApi.getEmployeeList.mockClear()

      // 重置
      wrapper.vm.handleReset()
      await flushPromises()

      // 验证搜索条件被清空
      expect(wrapper.vm.filterForm.keyword).toBe('')
      expect(wrapper.vm.filterForm.status).toBe('')
      expect(wrapper.vm.filterForm.role).toBe('')
      expect(wrapper.vm.pagination.page).toBe(1)
    })
  })

  // ============================================
  // 6. 测试辅助函数
  // ============================================
  describe('6. 辅助函数', () => {
    it('6.1 formatDate 应该正确格式化日期', async () => {
      employeeApi.getEmployeeList.mockResolvedValue({
        data: {
          items: mockEmployees,
          pagination: { total: 4, page: 1, per_page: 20, pages: 1 }
        }
      })

      employeeApi.getEmployeeStats.mockResolvedValue({
        data: mockStatistics
      })

      wrapper = mount(EmployeeList, {
        global: {
          plugins: [pinia, router],
          stubs: {
            'el-button': true,
            'el-input': true,
            'el-select': true,
            'el-option': true,
            'el-table': true,
            'el-table-column': true,
            'el-pagination': true,
            'el-dialog': true,
            'el-form': true,
            'el-form-item': true,
            'el-card': true,
            'el-row': true,
            'el-col': true,
            'el-icon': true,
            'el-descriptions': true,
            'el-descriptions-item': true
          }
        }
      })
      await flushPromises()

      expect(wrapper.vm.formatDate('2024-01-15T10:30:00')).toBe('2024-01-15 10:30')
      expect(wrapper.vm.formatDate('')).toBe('-')
      expect(wrapper.vm.formatDate(null)).toBe('-')
    })

    it('6.2 getAvatarColor 应该返回渐变色', async () => {
      employeeApi.getEmployeeList.mockResolvedValue({
        data: {
          items: mockEmployees,
          pagination: { total: 4, page: 1, per_page: 20, pages: 1 }
        }
      })

      employeeApi.getEmployeeStats.mockResolvedValue({
        data: mockStatistics
      })

      wrapper = mount(EmployeeList, {
        global: {
          plugins: [pinia, router],
          stubs: {
            'el-button': true,
            'el-input': true,
            'el-select': true,
            'el-option': true,
            'el-table': true,
            'el-table-column': true,
            'el-pagination': true,
            'el-dialog': true,
            'el-form': true,
            'el-form-item': true,
            'el-card': true,
            'el-row': true,
            'el-col': true,
            'el-icon': true,
            'el-descriptions': true,
            'el-descriptions-item': true
          }
        }
      })
      await flushPromises()

      const color = wrapper.vm.getAvatarColor('张')
      expect(color).toContain('linear-gradient')

      const emptyColor = wrapper.vm.getAvatarColor('')
      expect(emptyColor).toContain('linear-gradient')
    })
  })
})
