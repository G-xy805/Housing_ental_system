/**
 * 支付管理页面测试用例
 * 测试范围：
 * 1. 支付列表展示
 * 2. 支付状态筛选
 * 3. 支付操作（确认支付）
 * 4. 滞纳金显示
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createRouter, createWebHistory } from 'vue-router'
import PaymentList from '@/views/payments/PaymentList.vue'
import { useUserStore } from '@/store/user'
import * as paymentApi from '@/api/payment'
import * as contractApi from '@/api/contract'

// ============================================
// Mock API 模块
// ============================================

vi.mock('@/api/payment', () => ({
  getPaymentList: vi.fn(),
  getPaymentDetail: vi.fn(),
  createPayment: vi.fn(),
  updatePayment: vi.fn(),
  deletePayment: vi.fn(),
  getOverduePayments: vi.fn(),
  updateLateFees: vi.fn(),
  verifyPayment: vi.fn()
}))

vi.mock('@/api/contract', () => ({
  getContractList: vi.fn()
}))

// ============================================
// Mock Element Plus
// ============================================

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
// Mock Element Plus Icons
// ============================================

vi.mock('@element-plus/icons-vue', () => ({
  Plus: { name: 'Plus', template: '<svg><path d="M1"/></svg>' },
  Search: { name: 'Search', template: '<svg><path d="M1"/></svg>' },
  Refresh: { name: 'Refresh', template: '<svg><path d="M1"/></svg>' },
  Bell: { name: 'Bell', template: '<svg><path d="M1"/></svg>' },
  Coin: { name: 'Coin', template: '<svg><path d="M1"/></svg>' },
  View: { name: 'View', template: '<svg><path d="M1"/></svg>' },
  Delete: { name: 'Delete', template: '<svg><path d="M1"/></svg>' },
  Edit: { name: 'Edit', template: '<svg><path d="M1"/></svg>' }
}))

// ============================================
// 测试数据
// ============================================

const mockPayments = [
  {
    id: 1,
    payment_no: 'PY2024011500000001',
    contract_no: 'HT2024011500000001',
    contract_id: 1,
    tenant_name: '张租客',
    tenant_phone: '13800138001',
    room_no: '101',
    house_address: '北京市朝阳区某某小区1号楼',
    amount: 5000.00,
    paid_amount: 5000.00,
    payment_type: 'rent',
    payment_method: 'wechat',
    status: 'paid',
    due_date: '2024-01-15',
    payment_date: '2024-01-14',
    late_fee: 0,
    overdue_days: 0,
    deposit_amount: 5000.00,
    deduction_amount: 0,
    remark: '',
    created_at: '2024-01-10T10:00:00'
  },
  {
    id: 2,
    payment_no: 'PY2024011500000002',
    contract_no: 'HT2024011500000002',
    contract_id: 2,
    tenant_name: '李租客',
    tenant_phone: '13800138002',
    room_no: '102',
    house_address: '北京市朝阳区某某小区1号楼',
    amount: 3800.00,
    paid_amount: 0,
    payment_type: 'rent',
    payment_method: null,
    status: 'pending',
    due_date: '2024-01-20',
    payment_date: null,
    late_fee: 0,
    overdue_days: 0,
    deposit_amount: 3800.00,
    deduction_amount: 0,
    remark: '',
    created_at: '2024-01-10T10:00:00'
  },
  {
    id: 3,
    payment_no: 'PY2024011500000003',
    contract_no: 'HT2024011500000003',
    contract_id: 3,
    tenant_name: '王租客',
    tenant_phone: '13800138003',
    room_no: '201',
    house_address: '北京市海淀区某某路2号',
    amount: 4500.00,
    paid_amount: 2000.00,
    payment_type: 'rent',
    payment_method: 'alipay',
    status: 'partial',
    due_date: '2024-01-10',
    payment_date: '2024-01-12',
    late_fee: 0,
    overdue_days: 0,
    deposit_amount: 4500.00,
    deduction_amount: 0,
    remark: '部分支付',
    created_at: '2024-01-05T10:00:00'
  },
  {
    id: 4,
    payment_no: 'PY2024011500000004',
    contract_no: 'HT2024011500000004',
    contract_id: 4,
    tenant_name: '赵租客',
    tenant_phone: '13800138004',
    room_no: '202',
    house_address: '北京市海淀区某某路2号',
    amount: 6000.00,
    paid_amount: 0,
    payment_type: 'rent',
    payment_method: null,
    status: 'overdue',
    due_date: '2024-01-01',
    payment_date: null,
    late_fee: 180.00,
    overdue_days: 60,
    deposit_amount: 6000.00,
    deduction_amount: 0,
    remark: '',
    created_at: '2023-12-25T10:00:00'
  }
]

const mockOverduePayments = [
  {
    id: 4,
    payment_no: 'PY2024011500000004',
    contract_no: 'HT2024011500000004',
    tenant_name: '赵租客',
    room_no: '202',
    amount: 6000.00,
    status: 'overdue',
    overdue_days: 60,
    late_fee: 180.00
  }
]

const mockContracts = [
  {
    id: 1,
    contract_no: 'HT2024011500000001',
    tenant_name: '张租客',
    tenant_phone: '13800138001',
    house_address: '北京市朝阳区某某小区1号楼',
    room_no: '101',
    rent_amount: 5000.00,
    deposit_amount: 5000.00,
    start_date: '2024-01-01',
    end_date: '2024-12-31',
    status: 'active'
  },
  {
    id: 2,
    contract_no: 'HT2024011500000002',
    tenant_name: '李租客',
    tenant_phone: '13800138002',
    house_address: '北京市朝阳区某某小区1号楼',
    room_no: '102',
    rent_amount: 3800.00,
    deposit_amount: 3800.00,
    start_date: '2024-01-01',
    end_date: '2024-12-31',
    status: 'active'
  }
]

const mockPaymentDetail = {
  id: 1,
  payment_no: 'PY2024011500000001',
  contract_no: 'HT2024011500000001',
  contract_id: 1,
  tenant_name: '张租客',
  tenant_phone: '13800138001',
  room_no: '101',
  house_address: '北京市朝阳区某某小区1号楼',
  amount: 5000.00,
  paid_amount: 5000.00,
  payment_type: 'rent',
  payment_method: 'wechat',
  status: 'paid',
  due_date: '2024-01-15',
  payment_date: '2024-01-14',
  late_fee: 0,
  overdue_days: 0,
  deposit_amount: 5000.00,
  deduction_amount: 0,
  remark: '',
  voucher_urls: [],
  created_at: '2024-01-10T10:00:00'
}

// ============================================
// 创建测试路由器
// ============================================

function createTestRouter() {
  return createRouter({
    history: createWebHistory(),
    routes: [
      { path: '/', component: { template: '<div>Home</div>' } },
      { path: '/payments', component: { template: '<div>Payments</div>' } }
    ]
  })
}

// ============================================
// 测试套件
// ============================================

describe('支付管理页面 - PaymentList.vue', () => {
  let wrapper
  let pinia
  let userStore
  let router

  beforeEach(async () => {
    // 重置所有模拟
    vi.clearAllMocks()
    
    // 创建新的 Pinia 实例
    pinia = createPinia()
    setActivePinia(pinia)
    
    // 创建路由器
    router = createTestRouter()
    await router.push('/payments')
    await router.isReady()
    
    // 初始化 userStore
    userStore = useUserStore()
    userStore.setUserInfo({
      id: 1,
      username: 'admin',
      role: 'admin',
      user_type: 'admin'
    })

    // 设置 API 模拟返回值
    paymentApi.getPaymentList.mockResolvedValue({
      success: true,
      data: {
        items: mockPayments,
        pagination: {
          total: 4,
          page: 1,
          per_page: 10,
          pages: 1
        }
      }
    })

    paymentApi.getOverduePayments.mockResolvedValue({
      success: true,
      data: { items: mockOverduePayments }
    })

    paymentApi.updateLateFees.mockResolvedValue({ success: true })

    paymentApi.getPaymentDetail.mockResolvedValue({
      success: true,
      data: mockPaymentDetail
    })

    contractApi.getContractList.mockResolvedValue({
      success: true,
      data: { items: mockContracts }
    })
  })

  afterEach(() => {
    if (wrapper) {
      wrapper.unmount()
    }
  })

  // ============================================
  // 1. 测试支付列表展示
  // ============================================
  describe('1. 支付列表展示', () => {
    it('1.1 页面加载时应该自动获取支付列表', async () => {
      wrapper = mount(PaymentList, {
        global: {
          plugins: [pinia, router],
          stubs: {
            'el-button': true,
            'el-input': true,
            'el-select': true,
            'el-option': true,
            'el-date-picker': true,
            'el-table': true,
            'el-table-column': true,
            'el-tag': true,
            'el-card': true,
            'el-pagination': true,
            'el-dialog': true,
            'el-form': true,
            'el-form-item': true,
            'el-input-number': true,
            'el-alert': true,
            'el-descriptions': true,
            'el-descriptions-item': true,
            'el-image': true,
            'el-icon': true
          }
        }
      })

      await flushPromises()

      // 验证 API 被调用
      expect(paymentApi.getPaymentList).toHaveBeenCalledTimes(1)
      expect(paymentApi.getOverduePayments).toHaveBeenCalledTimes(1)
      expect(paymentApi.updateLateFees).toHaveBeenCalledTimes(1)
    })

    it('1.2 应该正确显示支付列表数据', async () => {
      wrapper = mount(PaymentList, {
        global: {
          plugins: [pinia, router],
          stubs: {
            'el-button': true,
            'el-input': true,
            'el-select': true,
            'el-option': true,
            'el-date-picker': true,
            'el-table': true,
            'el-table-column': true,
            'el-tag': true,
            'el-card': true,
            'el-pagination': true,
            'el-dialog': true,
            'el-form': true,
            'el-form-item': true,
            'el-input-number': true,
            'el-alert': true,
            'el-descriptions': true,
            'el-descriptions-item': true,
            'el-image': true,
            'el-icon': true
          }
        }
      })

      await flushPromises()

      // 验证列表数据
      expect(wrapper.vm.paymentList).toHaveLength(4)
      expect(wrapper.vm.paymentList[0].tenant_name).toBe('张租客')
      expect(wrapper.vm.paymentList[1].tenant_name).toBe('李租客')
      expect(wrapper.vm.paymentList[2].tenant_name).toBe('王租客')
      expect(wrapper.vm.paymentList[3].tenant_name).toBe('赵租客')

      // 验证分页数据
      expect(wrapper.vm.pagination.total).toBe(4)
    })

    it('1.3 应该正确显示不同状态的标签', async () => {
      wrapper = mount(PaymentList, {
        global: {
          plugins: [pinia, router],
          stubs: {
            'el-button': true,
            'el-input': true,
            'el-select': true,
            'el-option': true,
            'el-date-picker': true,
            'el-table': true,
            'el-table-column': true,
            'el-tag': true,
            'el-card': true,
            'el-pagination': true,
            'el-dialog': true,
            'el-form': true,
            'el-form-item': true,
            'el-input-number': true,
            'el-alert': true,
            'el-descriptions': true,
            'el-descriptions-item': true,
            'el-image': true,
            'el-icon': true
          }
        }
      })

      await flushPromises()

      // 验证状态类型映射
      expect(wrapper.vm.getStatusType('pending')).toBe('warning')
      expect(wrapper.vm.getStatusType('paid')).toBe('success')
      expect(wrapper.vm.getStatusType('overdue')).toBe('danger')
      expect(wrapper.vm.getStatusType('partial')).toBe('info')

      // 验证状态文本映射
      expect(wrapper.vm.getStatusText('pending')).toBe('待支付')
      expect(wrapper.vm.getStatusText('paid')).toBe('已支付')
      expect(wrapper.vm.getStatusText('overdue')).toBe('逾期')
      expect(wrapper.vm.getStatusText('partial')).toBe('部分支付')
    })

    it('1.4 应该正确显示金额格式', async () => {
      wrapper = mount(PaymentList, {
        global: {
          plugins: [pinia, router],
          stubs: {
            'el-button': true,
            'el-input': true,
            'el-select': true,
            'el-option': true,
            'el-date-picker': true,
            'el-table': true,
            'el-table-column': true,
            'el-tag': true,
            'el-card': true,
            'el-pagination': true,
            'el-dialog': true,
            'el-form': true,
            'el-form-item': true,
            'el-input-number': true,
            'el-alert': true,
            'el-descriptions': true,
            'el-descriptions-item': true,
            'el-image': true,
            'el-icon': true
          }
        }
      })

      await flushPromises()

      // 验证金额数据
      expect(wrapper.vm.paymentList[0].amount).toBe(5000.00)
      expect(wrapper.vm.paymentList[0].paid_amount).toBe(5000.00)
      expect(wrapper.vm.paymentList[1].paid_amount).toBe(0)
    })

    it('1.5 加载数据时应该显示 loading 状态', async () => {
      // 模拟加载状态
      wrapper = mount(PaymentList, {
        global: {
          plugins: [pinia, router],
          stubs: {
            'el-button': true,
            'el-input': true,
            'el-select': true,
            'el-option': true,
            'el-date-picker': true,
            'el-table': true,
            'el-table-column': true,
            'el-tag': true,
            'el-card': true,
            'el-pagination': true,
            'el-dialog': true,
            'el-form': true,
            'el-form-item': true,
            'el-input-number': true,
            'el-alert': true,
            'el-descriptions': true,
            'el-descriptions-item': true,
            'el-image': true,
            'el-icon': true
          }
        }
      })

      // 验证 loading 状态为 true
      expect(wrapper.vm.loading).toBe(true)

      await flushPromises()

      // 验证 loading 状态为 false
      expect(wrapper.vm.loading).toBe(false)
    })

    it('1.6 加载失败时应该显示错误提示', async () => {
      const { ElMessage } = await import('element-plus')
      
      paymentApi.getPaymentList.mockRejectedValue(new Error('网络错误'))

      wrapper = mount(PaymentList, {
        global: {
          plugins: [pinia, router],
          stubs: {
            'el-button': true,
            'el-input': true,
            'el-select': true,
            'el-option': true,
            'el-date-picker': true,
            'el-table': true,
            'el-table-column': true,
            'el-tag': true,
            'el-card': true,
            'el-pagination': true,
            'el-dialog': true,
            'el-form': true,
            'el-form-item': true,
            'el-input-number': true,
            'el-alert': true,
            'el-descriptions': true,
            'el-descriptions-item': true,
            'el-image': true,
            'el-icon': true
          }
        }
      })

      await flushPromises()

      // 验证错误提示
      expect(ElMessage.error).toHaveBeenCalledWith('加载支付列表失败')
      expect(wrapper.vm.loading).toBe(false)
    })
  })

  // ============================================
  // 2. 测试支付状态筛选
  // ============================================
  describe('2. 支付状态筛选', () => {
    it('2.1 按关键词搜索应该正确传递参数', async () => {
      wrapper = mount(PaymentList, {
        global: {
          plugins: [pinia, router],
          stubs: {
            'el-button': true,
            'el-input': true,
            'el-select': true,
            'el-option': true,
            'el-date-picker': true,
            'el-table': true,
            'el-table-column': true,
            'el-tag': true,
            'el-card': true,
            'el-pagination': true,
            'el-dialog': true,
            'el-form': true,
            'el-form-item': true,
            'el-input-number': true,
            'el-alert': true,
            'el-descriptions': true,
            'el-descriptions-item': true,
            'el-image': true,
            'el-icon': true
          }
        }
      })

      await flushPromises()

      // 清除之前的调用
      paymentApi.getPaymentList.mockClear()

      // 设置搜索关键词
      wrapper.vm.searchForm.keyword = '张租客'
      wrapper.vm.handleSearch()
      await flushPromises()

      // 验证 API 被调用且参数正确
      expect(paymentApi.getPaymentList).toHaveBeenCalledWith(
        expect.objectContaining({
          keyword: '张租客'
        })
      )
    })

    it('2.2 按支付状态筛选应该正确传递参数', async () => {
      wrapper = mount(PaymentList, {
        global: {
          plugins: [pinia, router],
          stubs: {
            'el-button': true,
            'el-input': true,
            'el-select': true,
            'el-option': true,
            'el-date-picker': true,
            'el-table': true,
            'el-table-column': true,
            'el-tag': true,
            'el-card': true,
            'el-pagination': true,
            'el-dialog': true,
            'el-form': true,
            'el-form-item': true,
            'el-input-number': true,
            'el-alert': true,
            'el-descriptions': true,
            'el-descriptions-item': true,
            'el-image': true,
            'el-icon': true
          }
        }
      })

      await flushPromises()

      // 清除之前的调用
      paymentApi.getPaymentList.mockClear()

      // 设置状态筛选
      wrapper.vm.searchForm.status = 'paid'
      wrapper.vm.handleSearch()
      await flushPromises()

      // 验证 API 被调用且参数正确
      expect(paymentApi.getPaymentList).toHaveBeenCalledWith(
        expect.objectContaining({
          status: 'paid'
        })
      )
    })

    it('2.3 筛选待支付状态', async () => {
      wrapper = mount(PaymentList, {
        global: {
          plugins: [pinia, router],
          stubs: {
            'el-button': true,
            'el-input': true,
            'el-select': true,
            'el-option': true,
            'el-date-picker': true,
            'el-table': true,
            'el-table-column': true,
            'el-tag': true,
            'el-card': true,
            'el-pagination': true,
            'el-dialog': true,
            'el-form': true,
            'el-form-item': true,
            'el-input-number': true,
            'el-alert': true,
            'el-descriptions': true,
            'el-descriptions-item': true,
            'el-image': true,
            'el-icon': true
          }
        }
      })

      await flushPromises()

      // 清除之前的调用
      paymentApi.getPaymentList.mockClear()

      // 设置状态筛选
      wrapper.vm.searchForm.status = 'pending'
      wrapper.vm.handleSearch()
      await flushPromises()

      // 验证 API 被调用且参数正确
      expect(paymentApi.getPaymentList).toHaveBeenCalledWith(
        expect.objectContaining({
          status: 'pending'
        })
      )
    })

    it('2.4 筛选逾期状态', async () => {
      wrapper = mount(PaymentList, {
        global: {
          plugins: [pinia, router],
          stubs: {
            'el-button': true,
            'el-input': true,
            'el-select': true,
            'el-option': true,
            'el-date-picker': true,
            'el-table': true,
            'el-table-column': true,
            'el-tag': true,
            'el-card': true,
            'el-pagination': true,
            'el-dialog': true,
            'el-form': true,
            'el-form-item': true,
            'el-input-number': true,
            'el-alert': true,
            'el-descriptions': true,
            'el-descriptions-item': true,
            'el-image': true,
            'el-icon': true
          }
        }
      })

      await flushPromises()

      // 清除之前的调用
      paymentApi.getPaymentList.mockClear()

      // 设置状态筛选
      wrapper.vm.searchForm.status = 'overdue'
      wrapper.vm.handleSearch()
      await flushPromises()

      // 验证 API 被调用且参数正确
      expect(paymentApi.getPaymentList).toHaveBeenCalledWith(
        expect.objectContaining({
          status: 'overdue'
        })
      )
    })

    it('2.5 重置搜索条件应该清空所有筛选', async () => {
      wrapper = mount(PaymentList, {
        global: {
          plugins: [pinia, router],
          stubs: {
            'el-button': true,
            'el-input': true,
            'el-select': true,
            'el-option': true,
            'el-date-picker': true,
            'el-table': true,
            'el-table-column': true,
            'el-tag': true,
            'el-card': true,
            'el-pagination': true,
            'el-dialog': true,
            'el-form': true,
            'el-form-item': true,
            'el-input-number': true,
            'el-alert': true,
            'el-descriptions': true,
            'el-descriptions-item': true,
            'el-image': true,
            'el-icon': true
          }
        }
      })

      await flushPromises()

      // 设置搜索条件
      wrapper.vm.searchForm.keyword = '张'
      wrapper.vm.searchForm.status = 'paid'

      // 重置
      wrapper.vm.handleReset()
      await flushPromises()

      // 验证搜索条件被清空
      expect(wrapper.vm.searchForm.keyword).toBe('')
      expect(wrapper.vm.searchForm.status).toBe('')
      expect(wrapper.vm.pagination.page).toBe(1)
    })
  })

  // ============================================
  // 3. 测试支付操作（确认支付）
  // ============================================
  describe('3. 支付操作（确认支付）', () => {
    it('3.1 点击设置状态按钮应该打开对话框', async () => {
      wrapper = mount(PaymentList, {
        global: {
          plugins: [pinia, router],
          stubs: {
            'el-button': true,
            'el-input': true,
            'el-select': true,
            'el-option': true,
            'el-date-picker': true,
            'el-table': true,
            'el-table-column': true,
            'el-tag': true,
            'el-card': true,
            'el-pagination': true,
            'el-dialog': true,
            'el-form': true,
            'el-form-item': true,
            'el-input-number': true,
            'el-alert': true,
            'el-descriptions': true,
            'el-descriptions-item': true,
            'el-image': true,
            'el-icon': true
          }
        }
      })

      await flushPromises()

      // 点击设置状态按钮
      wrapper.vm.handleSetStatus(mockPayments[1])
      await flushPromises()

      // 验证对话框状态
      expect(wrapper.vm.statusDialogVisible).toBe(true)
      expect(wrapper.vm.currentPayment.id).toBe(2)
      expect(wrapper.vm.statusForm.status).toBe('pending')
    })

    it('3.2 确认支付应该调用 updatePayment API', async () => {
      const { ElMessage } = await import('element-plus')
      
      paymentApi.updatePayment.mockResolvedValue({
        success: true,
        data: { ...mockPayments[1], status: 'paid', paid_amount: 3800 }
      })

      wrapper = mount(PaymentList, {
        global: {
          plugins: [pinia, router],
          stubs: {
            'el-button': true,
            'el-input': true,
            'el-select': true,
            'el-option': true,
            'el-date-picker': true,
            'el-table': true,
            'el-table-column': true,
            'el-tag': true,
            'el-card': true,
            'el-pagination': true,
            'el-dialog': true,
            'el-form': true,
            'el-form-item': true,
            'el-input-number': true,
            'el-alert': true,
            'el-descriptions': true,
            'el-descriptions-item': true,
            'el-image': true,
            'el-icon': true
          }
        }
      })

      await flushPromises()

      // 打开设置状态对话框
      wrapper.vm.handleSetStatus(mockPayments[1])
      await flushPromises()

      // 设置状态为已支付
      wrapper.vm.statusForm.status = 'paid'

      // 提交
      await wrapper.vm.handleStatusSubmit()
      await flushPromises()

      // 验证 API 被调用
      expect(paymentApi.updatePayment).toHaveBeenCalledWith(
        2,
        expect.objectContaining({
          status: 'paid'
        })
      )
      expect(ElMessage.success).toHaveBeenCalledWith('状态设置成功')
      expect(wrapper.vm.statusDialogVisible).toBe(false)
    })

    it('3.3 部分支付应该设置实际缴纳金额', async () => {
      paymentApi.updatePayment.mockResolvedValue({
        success: true,
        data: { ...mockPayments[1], status: 'partial', paid_amount: 2000 }
      })

      wrapper = mount(PaymentList, {
        global: {
          plugins: [pinia, router],
          stubs: {
            'el-button': true,
            'el-input': true,
            'el-select': true,
            'el-option': true,
            'el-date-picker': true,
            'el-table': true,
            'el-table-column': true,
            'el-tag': true,
            'el-card': true,
            'el-pagination': true,
            'el-dialog': true,
            'el-form': true,
            'el-form-item': true,
            'el-input-number': true,
            'el-alert': true,
            'el-descriptions': true,
            'el-descriptions-item': true,
            'el-image': true,
            'el-icon': true
          }
        }
      })

      await flushPromises()

      // 打开设置状态对话框
      wrapper.vm.handleSetStatus(mockPayments[1])
      await flushPromises()

      // 设置状态为部分支付
      wrapper.vm.statusForm.status = 'partial'
      wrapper.vm.statusForm.paid_amount = 2000

      // 提交
      await wrapper.vm.handleStatusSubmit()
      await flushPromises()

      // 验证 API 被调用
      expect(paymentApi.updatePayment).toHaveBeenCalledWith(
        2,
        expect.objectContaining({
          status: 'partial',
          paid_amount: 2000
        })
      )
    })

    it('3.4 确认支付成功后应该刷新列表', async () => {
      paymentApi.updatePayment.mockResolvedValue({
        success: true,
        data: { ...mockPayments[1], status: 'paid' }
      })

      wrapper = mount(PaymentList, {
        global: {
          plugins: [pinia, router],
          stubs: {
            'el-button': true,
            'el-input': true,
            'el-select': true,
            'el-option': true,
            'el-date-picker': true,
            'el-table': true,
            'el-table-column': true,
            'el-tag': true,
            'el-card': true,
            'el-pagination': true,
            'el-dialog': true,
            'el-form': true,
            'el-form-item': true,
            'el-input-number': true,
            'el-alert': true,
            'el-descriptions': true,
            'el-descriptions-item': true,
            'el-image': true,
            'el-icon': true
          }
        }
      })

      await flushPromises()

      // 清除之前的调用
      paymentApi.getPaymentList.mockClear()

      // 打开设置状态对话框并提交
      wrapper.vm.handleSetStatus(mockPayments[1])
      await flushPromises()

      wrapper.vm.statusForm.status = 'paid'
      await wrapper.vm.handleStatusSubmit()
      await flushPromises()

      // 验证列表被刷新
      expect(paymentApi.getPaymentList).toHaveBeenCalledTimes(1)
    })

    it('3.5 从已支付状态更改为其他状态应该显示确认提示', async () => {
      const { ElMessageBox } = await import('element-plus')
      
      ElMessageBox.confirm.mockResolvedValue('confirm')

      paymentApi.updatePayment.mockResolvedValue({
        success: true
      })

      wrapper = mount(PaymentList, {
        global: {
          plugins: [pinia, router],
          stubs: {
            'el-button': true,
            'el-input': true,
            'el-select': true,
            'el-option': true,
            'el-date-picker': true,
            'el-table': true,
            'el-table-column': true,
            'el-tag': true,
            'el-card': true,
            'el-pagination': true,
            'el-dialog': true,
            'el-form': true,
            'el-form-item': true,
            'el-input-number': true,
            'el-alert': true,
            'el-descriptions': true,
            'el-descriptions-item': true,
            'el-image': true,
            'el-icon': true
          }
        }
      })

      await flushPromises()

      // 打开设置状态对话框（已支付的记录）
      wrapper.vm.handleSetStatus(mockPayments[0])
      await flushPromises()

      // 设置状态为待支付
      wrapper.vm.statusForm.status = 'pending'

      // 提交
      await wrapper.vm.handleStatusSubmit()
      await flushPromises()

      // 验证确认对话框被调用
      expect(ElMessageBox.confirm).toHaveBeenCalledWith(
        expect.stringContaining('已支付状态'),
        '状态变更确认',
        expect.objectContaining({
          type: 'warning'
        })
      )
    })

    it('3.6 取消状态变更不应该调用 API', async () => {
      const { ElMessageBox } = await import('element-plus')
      
      ElMessageBox.confirm.mockRejectedValue(new Error('cancel'))

      wrapper = mount(PaymentList, {
        global: {
          plugins: [pinia, router],
          stubs: {
            'el-button': true,
            'el-input': true,
            'el-select': true,
            'el-option': true,
            'el-date-picker': true,
            'el-table': true,
            'el-table-column': true,
            'el-tag': true,
            'el-card': true,
            'el-pagination': true,
            'el-dialog': true,
            'el-form': true,
            'el-form-item': true,
            'el-input-number': true,
            'el-alert': true,
            'el-descriptions': true,
            'el-descriptions-item': true,
            'el-image': true,
            'el-icon': true
          }
        }
      })

      await flushPromises()

      // 打开设置状态对话框（已支付的记录）
      wrapper.vm.handleSetStatus(mockPayments[0])
      await flushPromises()

      // 设置状态为待支付
      wrapper.vm.statusForm.status = 'pending'

      // 提交（会取消）
      await wrapper.vm.handleStatusSubmit()
      await flushPromises()

      // 验证 API 没有被调用
      expect(paymentApi.updatePayment).not.toHaveBeenCalled()
    })
  })

  // ============================================
  // 4. 测试滞纳金显示
  // ============================================
  describe('4. 滞纳金显示', () => {
    it('4.1 逾期支付记录应该显示滞纳金', async () => {
      wrapper = mount(PaymentList, {
        global: {
          plugins: [pinia, router],
          stubs: {
            'el-button': true,
            'el-input': true,
            'el-select': true,
            'el-option': true,
            'el-date-picker': true,
            'el-table': true,
            'el-table-column': true,
            'el-tag': true,
            'el-card': true,
            'el-pagination': true,
            'el-dialog': true,
            'el-form': true,
            'el-form-item': true,
            'el-input-number': true,
            'el-alert': true,
            'el-descriptions': true,
            'el-descriptions-item': true,
            'el-image': true,
            'el-icon': true
          }
        }
      })

      await flushPromises()

      // 验证逾期列表
      expect(wrapper.vm.overdueList).toHaveLength(1)
      expect(wrapper.vm.overdueList[0].late_fee).toBe(180.00)
      expect(wrapper.vm.overdueList[0].overdue_days).toBe(60)
    })

    it('4.2 应该正确计算滞纳金', async () => {
      wrapper = mount(PaymentList, {
        global: {
          plugins: [pinia, router],
          stubs: {
            'el-button': true,
            'el-input': true,
            'el-select': true,
            'el-option': true,
            'el-date-picker': true,
            'el-table': true,
            'el-table-column': true,
            'el-tag': true,
            'el-card': true,
            'el-pagination': true,
            'el-dialog': true,
            'el-form': true,
            'el-form-item': true,
            'el-input-number': true,
            'el-alert': true,
            'el-descriptions': true,
            'el-descriptions-item': true,
            'el-image': true,
            'el-icon': true
          }
        }
      })

      await flushPromises()

      // 验证滞纳金计算
      // 滞纳金 = 应缴金额 × 日利率 × 逾期天数
      // 6000 * 0.0005 * 60 = 180
      const overduePayment = wrapper.vm.paymentList.find(p => p.status === 'overdue')
      expect(overduePayment.late_fee).toBe(180.00)
    })

    it('4.3 页面加载时应该更新滞纳金', async () => {
      wrapper = mount(PaymentList, {
        global: {
          plugins: [pinia, router],
          stubs: {
            'el-button': true,
            'el-input': true,
            'el-select': true,
            'el-option': true,
            'el-date-picker': true,
            'el-table': true,
            'el-table-column': true,
            'el-tag': true,
            'el-card': true,
            'el-pagination': true,
            'el-dialog': true,
            'el-form': true,
            'el-form-item': true,
            'el-input-number': true,
            'el-alert': true,
            'el-descriptions': true,
            'el-descriptions-item': true,
            'el-image': true,
            'el-icon': true
          }
        }
      })

      await flushPromises()

      // 验证滞纳金更新 API 被调用
      expect(paymentApi.updateLateFees).toHaveBeenCalledTimes(1)
    })

    it('4.4 查看详情应该显示滞纳金信息', async () => {
      paymentApi.getPaymentDetail.mockResolvedValue({
        success: true,
        data: mockPayments[3] // 逾期支付记录
      })

      wrapper = mount(PaymentList, {
        global: {
          plugins: [pinia, router],
          stubs: {
            'el-button': true,
            'el-input': true,
            'el-select': true,
            'el-option': true,
            'el-date-picker': true,
            'el-table': true,
            'el-table-column': true,
            'el-tag': true,
            'el-card': true,
            'el-pagination': true,
            'el-dialog': true,
            'el-form': true,
            'el-form-item': true,
            'el-input-number': true,
            'el-alert': true,
            'el-descriptions': true,
            'el-descriptions-item': true,
            'el-image': true,
            'el-icon': true
          }
        }
      })

      await flushPromises()

      // 查看详情
      await wrapper.vm.handleView(mockPayments[3])
      await flushPromises()

      // 验证详情对话框状态
      expect(wrapper.vm.detailVisible).toBe(true)
      expect(wrapper.vm.currentPayment.late_fee).toBe(180.00)
      expect(wrapper.vm.currentPayment.overdue_days).toBe(60)
    })

    it('4.5 逾期提醒应该正确显示', async () => {
      wrapper = mount(PaymentList, {
        global: {
          plugins: [pinia, router],
          stubs: {
            'el-button': true,
            'el-input': true,
            'el-select': true,
            'el-option': true,
            'el-date-picker': true,
            'el-table': true,
            'el-table-column': true,
            'el-tag': true,
            'el-card': true,
            'el-pagination': true,
            'el-dialog': true,
            'el-form': true,
            'el-form-item': true,
            'el-input-number': true,
            'el-alert': true,
            'el-descriptions': true,
            'el-descriptions-item': true,
            'el-image': true,
            'el-icon': true
          }
        }
      })

      await flushPromises()

      // 验证逾期提醒数据
      expect(wrapper.vm.overdueList).toHaveLength(1)
      expect(wrapper.vm.overdueList[0].contract_no).toBe('HT2024011500000004')
      expect(wrapper.vm.overdueList[0].tenant_name).toBe('赵租客')
      expect(wrapper.vm.overdueList[0].overdue_days).toBe(60)
    })

    it('4.6 批量催缴功能', async () => {
      const { ElMessage, ElMessageBox } = await import('element-plus')
      
      ElMessageBox.confirm.mockResolvedValue('confirm')

      wrapper = mount(PaymentList, {
        global: {
          plugins: [pinia, router],
          stubs: {
            'el-button': true,
            'el-input': true,
            'el-select': true,
            'el-option': true,
            'el-date-picker': true,
            'el-table': true,
            'el-table-column': true,
            'el-tag': true,
            'el-card': true,
            'el-pagination': true,
            'el-dialog': true,
            'el-form': true,
            'el-form-item': true,
            'el-input-number': true,
            'el-alert': true,
            'el-descriptions': true,
            'el-descriptions-item': true,
            'el-image': true,
            'el-icon': true
          }
        }
      })

      await flushPromises()

      // 执行批量催缴
      await wrapper.vm.handleBatchRemind()
      await flushPromises()

      // 验证确认对话框被调用
      expect(ElMessageBox.confirm).toHaveBeenCalledWith(
        '确定要向 1 位逾期租客发送催缴通知吗？',
        '批量催缴',
        expect.objectContaining({
          type: 'warning'
        })
      )

      // 验证成功提示
      expect(ElMessage.success).toHaveBeenCalledWith('已向 1 位租客发送催缴通知')
    })

    it('4.7 取消批量催缴', async () => {
      const { ElMessage, ElMessageBox } = await import('element-plus')
      
      ElMessageBox.confirm.mockRejectedValue(new Error('cancel'))

      wrapper = mount(PaymentList, {
        global: {
          plugins: [pinia, router],
          stubs: {
            'el-button': true,
            'el-input': true,
            'el-select': true,
            'el-option': true,
            'el-date-picker': true,
            'el-table': true,
            'el-table-column': true,
            'el-tag': true,
            'el-card': true,
            'el-pagination': true,
            'el-dialog': true,
            'el-form': true,
            'el-form-item': true,
            'el-input-number': true,
            'el-alert': true,
            'el-descriptions': true,
            'el-descriptions-item': true,
            'el-image': true,
            'el-icon': true
          }
        }
      })

      await flushPromises()

      // 清除之前的调用记录
      ElMessage.success.mockClear()

      // 执行批量催缴（取消）
      await wrapper.vm.handleBatchRemind()
      await flushPromises()

      // 验证成功提示没有被调用
      expect(ElMessage.success).not.toHaveBeenCalled()
    })
  })

  // ============================================
  // 5. 测试其他功能
  // ============================================
  describe('5. 其他功能', () => {
    it('5.1 查看支付详情', async () => {
      wrapper = mount(PaymentList, {
        global: {
          plugins: [pinia, router],
          stubs: {
            'el-button': true,
            'el-input': true,
            'el-select': true,
            'el-option': true,
            'el-date-picker': true,
            'el-table': true,
            'el-table-column': true,
            'el-tag': true,
            'el-card': true,
            'el-pagination': true,
            'el-dialog': true,
            'el-form': true,
            'el-form-item': true,
            'el-input-number': true,
            'el-alert': true,
            'el-descriptions': true,
            'el-descriptions-item': true,
            'el-image': true,
            'el-icon': true
          }
        }
      })

      await flushPromises()

      // 查看详情
      await wrapper.vm.handleView(mockPayments[0])
      await flushPromises()

      // 验证详情 API 被调用
      expect(paymentApi.getPaymentDetail).toHaveBeenCalledWith(1)

      // 验证详情对话框状态
      expect(wrapper.vm.detailVisible).toBe(true)
      expect(wrapper.vm.currentPayment.tenant_name).toBe('张租客')
    })

    it('5.2 删除支付记录', async () => {
      const { ElMessage, ElMessageBox } = await import('element-plus')
      
      paymentApi.deletePayment.mockResolvedValue({ success: true })

      ElMessageBox.confirm.mockResolvedValue('confirm')

      wrapper = mount(PaymentList, {
        global: {
          plugins: [pinia, router],
          stubs: {
            'el-button': true,
            'el-input': true,
            'el-select': true,
            'el-option': true,
            'el-date-picker': true,
            'el-table': true,
            'el-table-column': true,
            'el-tag': true,
            'el-card': true,
            'el-pagination': true,
            'el-dialog': true,
            'el-form': true,
            'el-form-item': true,
            'el-input-number': true,
            'el-alert': true,
            'el-descriptions': true,
            'el-descriptions-item': true,
            'el-image': true,
            'el-icon': true
          }
        }
      })

      await flushPromises()

      // 删除支付记录
      await wrapper.vm.handleDeletePayment(mockPayments[0])
      await flushPromises()

      // 验证确认对话框被调用
      expect(ElMessageBox.confirm).toHaveBeenCalled()

      // 验证删除 API 被调用
      expect(paymentApi.deletePayment).toHaveBeenCalledWith(1)
      expect(ElMessage.success).toHaveBeenCalledWith('删除成功')
    })

    it('5.3 取消删除支付记录', async () => {
      const { ElMessageBox } = await import('element-plus')
      
      ElMessageBox.confirm.mockRejectedValue(new Error('cancel'))

      wrapper = mount(PaymentList, {
        global: {
          plugins: [pinia, router],
          stubs: {
            'el-button': true,
            'el-input': true,
            'el-select': true,
            'el-option': true,
            'el-date-picker': true,
            'el-table': true,
            'el-table-column': true,
            'el-tag': true,
            'el-card': true,
            'el-pagination': true,
            'el-dialog': true,
            'el-form': true,
            'el-form-item': true,
            'el-input-number': true,
            'el-alert': true,
            'el-descriptions': true,
            'el-descriptions-item': true,
            'el-image': true,
            'el-icon': true
          }
        }
      })

      await flushPromises()

      // 取消删除
      await wrapper.vm.handleDeletePayment(mockPayments[0])
      await flushPromises()

      // 验证删除 API 没有被调用
      expect(paymentApi.deletePayment).not.toHaveBeenCalled()
    })

    it('5.4 新增租金对话框', async () => {
      wrapper = mount(PaymentList, {
        global: {
          plugins: [pinia, router],
          stubs: {
            'el-button': true,
            'el-input': true,
            'el-select': true,
            'el-option': true,
            'el-date-picker': true,
            'el-table': true,
            'el-table-column': true,
            'el-tag': true,
            'el-card': true,
            'el-pagination': true,
            'el-dialog': true,
            'el-form': true,
            'el-form-item': true,
            'el-input-number': true,
            'el-alert': true,
            'el-descriptions': true,
            'el-descriptions-item': true,
            'el-image': true,
            'el-icon': true
          }
        }
      })

      await flushPromises()

      // 打开新增对话框
      wrapper.vm.handleAddPayment()
      await flushPromises()

      // 验证对话框状态
      expect(wrapper.vm.addDialogVisible).toBe(true)
      expect(contractApi.getContractList).toHaveBeenCalled()
    })

    it('5.5 编辑租金对话框', async () => {
      wrapper = mount(PaymentList, {
        global: {
          plugins: [pinia, router],
          stubs: {
            'el-button': true,
            'el-input': true,
            'el-select': true,
            'el-option': true,
            'el-date-picker': true,
            'el-table': true,
            'el-table-column': true,
            'el-tag': true,
            'el-card': true,
            'el-pagination': true,
            'el-dialog': true,
            'el-form': true,
            'el-form-item': true,
            'el-input-number': true,
            'el-alert': true,
            'el-descriptions': true,
            'el-descriptions-item': true,
            'el-image': true,
            'el-icon': true
          }
        }
      })

      await flushPromises()

      // 打开编辑对话框
      await wrapper.vm.handleEditPayment(mockPayments[0])
      await flushPromises()

      // 验证对话框状态
      expect(wrapper.vm.editDialogVisible).toBe(true)
      expect(wrapper.vm.editForm.id).toBe(1)
      expect(wrapper.vm.editForm.amount).toBe(5000.00)
    })

    it('5.6 押金退还对话框', async () => {
      wrapper = mount(PaymentList, {
        global: {
          plugins: [pinia, router],
          stubs: {
            'el-button': true,
            'el-input': true,
            'el-select': true,
            'el-option': true,
            'el-date-picker': true,
            'el-table': true,
            'el-table-column': true,
            'el-tag': true,
            'el-card': true,
            'el-pagination': true,
            'el-dialog': true,
            'el-form': true,
            'el-form-item': true,
            'el-input-number': true,
            'el-alert': true,
            'el-descriptions': true,
            'el-descriptions-item': true,
            'el-image': true,
            'el-icon': true
          }
        }
      })

      await flushPromises()

      // 打开押金退还对话框
      wrapper.vm.handleRefundDeposit(mockPayments[0])
      await flushPromises()

      // 验证对话框状态
      expect(wrapper.vm.refundDialogVisible).toBe(true)
      expect(wrapper.vm.currentPayment.id).toBe(1)
      expect(wrapper.vm.refundForm.refund_amount).toBe(5000.00)
    })

    it('5.7 支付方式文本映射', async () => {
      wrapper = mount(PaymentList, {
        global: {
          plugins: [pinia, router],
          stubs: {
            'el-button': true,
            'el-input': true,
            'el-select': true,
            'el-option': true,
            'el-date-picker': true,
            'el-table': true,
            'el-table-column': true,
            'el-tag': true,
            'el-card': true,
            'el-pagination': true,
            'el-dialog': true,
            'el-form': true,
            'el-form-item': true,
            'el-input-number': true,
            'el-alert': true,
            'el-descriptions': true,
            'el-descriptions-item': true,
            'el-image': true,
            'el-icon': true
          }
        }
      })

      await flushPromises()

      // 验证支付方式文本映射
      expect(wrapper.vm.getPaymentMethodText('wechat')).toBe('微信支付')
      expect(wrapper.vm.getPaymentMethodText('alipay')).toBe('支付宝')
      expect(wrapper.vm.getPaymentMethodText('bank')).toBe('银行卡转账')
      expect(wrapper.vm.getPaymentMethodText('cash')).toBe('现金支付')
    })

    it('5.8 行类名（逾期行高亮）', async () => {
      wrapper = mount(PaymentList, {
        global: {
          plugins: [pinia, router],
          stubs: {
            'el-button': true,
            'el-input': true,
            'el-select': true,
            'el-option': true,
            'el-date-picker': true,
            'el-table': true,
            'el-table-column': true,
            'el-tag': true,
            'el-card': true,
            'el-pagination': true,
            'el-dialog': true,
            'el-form': true,
            'el-form-item': true,
            'el-input-number': true,
            'el-alert': true,
            'el-descriptions': true,
            'el-descriptions-item': true,
            'el-image': true,
            'el-icon': true
          }
        }
      })

      await flushPromises()

      // 验证行类名
      expect(wrapper.vm.getRowClassName({ row: { status: 'overdue' } })).toBe('overdue-row')
      expect(wrapper.vm.getRowClassName({ row: { status: 'paid' } })).toBe('')
    })
  })
})
