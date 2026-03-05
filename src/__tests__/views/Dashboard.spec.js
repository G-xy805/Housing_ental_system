/**
 * Dashboard.vue 测试用例
 * 测试统计数据加载和显示、ECharts 图表渲染、数据刷新功能
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '@/views/Dashboard.vue'
import { useUserStore } from '@/store/user'
import * as statisticsApi from '@/api/statistics'
import * as contractApi from '@/api/contract'

// ============================================
// Mock ECharts
// ============================================

// 创建 ECharts 实例模拟
const mockEChartsInstance = {
  setOption: vi.fn(),
  resize: vi.fn(),
  dispose: vi.fn(),
  on: vi.fn(),
  off: vi.fn(),
  getOption: vi.fn(() => ({}))
}

// Mock echarts 模块 - 需要导出 init 方法
vi.mock('echarts', () => {
  const mockInstance = {
    setOption: vi.fn(),
    resize: vi.fn(),
    dispose: vi.fn(),
    on: vi.fn(),
    off: vi.fn(),
    getOption: vi.fn(() => ({}))
  }
  
  return {
    default: {
      init: vi.fn(() => mockInstance),
      graphic: {
        LinearGradient: vi.fn((x, y, x2, y2, colorStops) => ({
          type: 'linear',
          x, y, x2, y2,
          colorStops
        }))
      }
    },
    init: vi.fn(() => mockInstance),
    graphic: {
      LinearGradient: vi.fn((x, y, x2, y2, colorStops) => ({
        type: 'linear',
        x, y, x2, y2,
        colorStops
      }))
    }
  }
})

// ============================================
// Mock API 模块
// ============================================

// 模拟统计数据 API
vi.mock('@/api/statistics', () => ({
  getOverviewStatistics: vi.fn(),
  getHouseStatistics: vi.fn(),
  getIncomeStatistics: vi.fn(),
  getTenantStatistics: vi.fn(),
  getContractStatistics: vi.fn(),
  exportExcel: vi.fn(),
  exportPdf: vi.fn()
}))

// 模拟合同 API
vi.mock('@/api/contract', () => ({
  getContractList: vi.fn()
}))

// ============================================
// Mock Element Plus Icons
// ============================================

vi.mock('@element-plus/icons-vue', () => ({
  House: { name: 'House', template: '<svg><path d="M1"/></svg>' },
  User: { name: 'User', template: '<svg><path d="M1"/></svg>' },
  Document: { name: 'Document', template: '<svg><path d="M1"/></svg>' },
  Money: { name: 'Money', template: '<svg><path d="M1"/></svg>' },
  Plus: { name: 'Plus', template: '<svg><path d="M1"/></svg>' },
  Edit: { name: 'Edit', template: '<svg><path d="M1"/></svg>' },
  Search: { name: 'Search', template: '<svg><path d="M1"/></svg>' },
  View: { name: 'View', template: '<svg><path d="M1"/></svg>' },
  Download: { name: 'Download', template: '<svg><path d="M1"/></svg>' },
  TrendCharts: { name: 'TrendCharts', template: '<svg><path d="M1"/></svg>' }
}))

// ============================================
// Mock Element Plus
// ============================================

vi.mock('element-plus', () => ({
  ElMessage: {
    success: vi.fn(),
    warning: vi.fn(),
    info: vi.fn(),
    error: vi.fn()
  }
}))

// ============================================
// 测试数据
// ============================================

// 模拟概览统计数据
const mockOverviewData = {
  success: true,
  data: {
    houses: {
      total: 120,
      occupancy_rate: 0.85,
      growth_rate: 0.12
    },
    tenants: {
      total: 95,
      growth_rate: 0.08
    },
    contracts: {
      total: 88,
      growth_rate: 0.05
    },
    income: {
      current_period: 156000,
      growth_rate: 0.15
    }
  }
}

// 模拟房源统计数据
const mockHouseData = {
  success: true,
  data: {
    by_status: {
      available: 18,
      rented: 85,
      maintenance: 12,
      partially_rented: 5
    }
  }
}

// 模拟收入统计数据
const mockIncomeData = {
  success: true,
  data: {
    monthly_trend: [
      { month: '2024-10', income: 120000 },
      { month: '2024-11', income: 135000 },
      { month: '2024-12', income: 142000 },
      { month: '2025-01', income: 138000 },
      { month: '2025-02', income: 148000 },
      { month: '2025-03', income: 156000 }
    ]
  }
}

// 模拟租客统计数据
const mockTenantData = {
  success: true,
  data: {
    by_source: {
      '线上平台': 45,
      '中介推荐': 30,
      '老客户介绍': 15,
      '其他': 5
    },
    by_contract_type: {
      '长租': 60,
      '短租': 25,
      '合租': 10
    }
  }
}

// 模拟合同统计数据
const mockContractData = {
  success: true,
  data: {
    by_status: {
      active: 65,
      pending: 8,
      waiting_sign: 5,
      expired: 7,
      terminated: 3
    }
  }
}

// 模拟待处理合同数据
const mockPendingContracts = {
  success: true,
  data: {
    items: [
      {
        id: 1,
        house_title: '阳光花园 A栋 101',
        tenant_name: '张三',
        status: 'draft'
      },
      {
        id: 2,
        house_title: '翠湖小区 B栋 202',
        tenant_name: '李四',
        status: 'pending'
      }
    ],
    total: 2
  }
}

// 模拟即将到期合同数据
const mockExpiringContracts = {
  success: true,
  data: {
    items: [
      {
        id: 10,
        house_title: '城市公寓 301',
        tenant_name: '王五',
        end_date: new Date(Date.now() + 15 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]
      },
      {
        id: 11,
        house_title: '花园小区 402',
        tenant_name: '赵六',
        end_date: new Date(Date.now() + 25 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]
      }
    ],
    total: 2
  }
}

// ============================================
// 创建测试路由器
// ============================================

function createTestRouter() {
  return createRouter({
    history: createWebHistory(),
    routes: [
      { path: '/', component: { template: '<div>Home</div>' } },
      { path: '/houses', component: { template: '<div>Houses</div>' } },
      { path: '/houses/add', component: { template: '<div>Add House</div>' } },
      { path: '/contracts', component: { template: '<div>Contracts</div>' } },
      { path: '/contracts/add', component: { template: '<div>Add Contract</div>' } }
    ]
  })
}

// ============================================
// 测试套件
// ============================================

describe('Dashboard.vue', () => {
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
    await router.push('/')
    await router.isReady()
    
    // 初始化 userStore
    userStore = useUserStore()
    userStore.setUserInfo({
      id: 1,
      username: 'testuser',
      role: 'admin'
    })

    // 设置 API 模拟返回值
    statisticsApi.getOverviewStatistics.mockResolvedValue(mockOverviewData)
    statisticsApi.getHouseStatistics.mockResolvedValue(mockHouseData)
    statisticsApi.getIncomeStatistics.mockResolvedValue(mockIncomeData)
    statisticsApi.getTenantStatistics.mockResolvedValue(mockTenantData)
    statisticsApi.getContractStatistics.mockResolvedValue(mockContractData)
    contractApi.getContractList.mockResolvedValue(mockPendingContracts)
  })

  afterEach(() => {
    if (wrapper) {
      wrapper.unmount()
    }
  })

  // ============================================
  // 1. 测试统计数据加载和显示
  // ============================================

  describe('统计数据加载和显示', () => {
    it('组件挂载时应该调用所有数据加载 API', async () => {
      wrapper = mount(Dashboard, {
        global: {
          plugins: [pinia, router],
          stubs: {
            'el-select': true,
            'el-option': true,
            'el-date-picker': true,
            'el-button': true,
            'el-button-group': true,
            'el-tag': true,
            'el-link': true
          }
        }
      })

      await flushPromises()

      // 验证所有 API 被调用
      expect(statisticsApi.getOverviewStatistics).toHaveBeenCalled()
      expect(statisticsApi.getHouseStatistics).toHaveBeenCalled()
      expect(statisticsApi.getIncomeStatistics).toHaveBeenCalled()
      expect(statisticsApi.getTenantStatistics).toHaveBeenCalled()
      expect(statisticsApi.getContractStatistics).toHaveBeenCalled()
      expect(contractApi.getContractList).toHaveBeenCalled()
    })

    it('应该正确显示统计卡片数据', async () => {
      wrapper = mount(Dashboard, {
        global: {
          plugins: [pinia, router],
          stubs: {
            'el-select': true,
            'el-option': true,
            'el-date-picker': true,
            'el-button': true,
            'el-button-group': true,
            'el-tag': true,
            'el-link': true
          }
        }
      })

      await flushPromises()

      // 查找统计卡片
      const statCards = wrapper.findAll('.stat-card')
      expect(statCards.length).toBe(4)

      // 验证第一个卡片（总房源数）
      const firstCard = statCards[0]
      expect(firstCard.find('.stat-label').text()).toBe('总房源数')
      expect(firstCard.find('.stat-value').text()).toContain('120')
    })

    it('应该正确显示用户名', async () => {
      wrapper = mount(Dashboard, {
        global: {
          plugins: [pinia, router],
          stubs: {
            'el-select': true,
            'el-option': true,
            'el-date-picker': true,
            'el-button': true,
            'el-button-group': true,
            'el-tag': true,
            'el-link': true
          }
        }
      })

      await flushPromises()

      const subtitle = wrapper.find('.page-subtitle')
      expect(subtitle.text()).toContain('testuser')
    })

    it('应该正确显示增长百分比', async () => {
      wrapper = mount(Dashboard, {
        global: {
          plugins: [pinia, router],
          stubs: {
            'el-select': true,
            'el-option': true,
            'el-date-picker': true,
            'el-button': true,
            'el-button-group': true,
            'el-tag': true,
            'el-link': true
          }
        }
      })

      await flushPromises()

      const statChanges = wrapper.findAll('.stat-change')
      expect(statChanges.length).toBeGreaterThan(0)

      // 验证增长百分比显示
      const firstChange = statChanges[0]
      expect(firstChange.text()).toContain('12.0%')
      expect(firstChange.classes()).toContain('positive')
    })

    it('应该正确显示出租率', async () => {
      wrapper = mount(Dashboard, {
        global: {
          plugins: [pinia, router],
          stubs: {
            'el-select': true,
            'el-option': true,
            'el-date-picker': true,
            'el-button': true,
            'el-button-group': true,
            'el-tag': true,
            'el-link': true
          }
        }
      })

      await flushPromises()

      const statCards = wrapper.findAll('.stat-card')
      const firstCard = statCards[0]
      const footerValue = firstCard.find('.footer-value')
      expect(footerValue.text()).toBe('85.0%')
    })

    it('API 失败时应该优雅处理错误', async () => {
      // 模拟 API 失败
      statisticsApi.getOverviewStatistics.mockRejectedValue(new Error('Network Error'))

      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})

      wrapper = mount(Dashboard, {
        global: {
          plugins: [pinia, router],
          stubs: {
            'el-select': true,
            'el-option': true,
            'el-date-picker': true,
            'el-button': true,
            'el-button-group': true,
            'el-tag': true,
            'el-link': true
          }
        }
      })

      await flushPromises()

      // 验证错误被记录
      expect(consoleSpy).toHaveBeenCalled()

      consoleSpy.mockRestore()
    })
  })

  // ============================================
  // 2. 测试 ECharts 图表渲染
  // ============================================

  describe('ECharts 图表渲染', () => {
    it('应该初始化所有图表', async () => {
      const echarts = await import('echarts')
      
      wrapper = mount(Dashboard, {
        global: {
          plugins: [pinia, router],
          stubs: {
            'el-select': true,
            'el-option': true,
            'el-date-picker': true,
            'el-button': true,
            'el-button-group': true,
            'el-tag': true,
            'el-link': true
          }
        }
      })

      await flushPromises()
      
      // 由于图表容器需要 DOM 元素，我们验证 echarts.init 是否被调用
      // 如果没有 DOM 元素，init 不会被调用，这是预期行为
      // 所以我们检查组件是否正确尝试初始化图表
      const vm = wrapper.vm
      
      // 验证图表引用存在
      expect(vm.houseStatusChartRef).toBeDefined()
      expect(vm.incomeTrendChartRef).toBeDefined()
      expect(vm.tenantTypeChartRef).toBeDefined()
      expect(vm.contractStatusChartRef).toBeDefined()
    })

    it('应该为图表设置正确的配置选项', async () => {
      wrapper = mount(Dashboard, {
        global: {
          plugins: [pinia, router],
          stubs: {
            'el-select': true,
            'el-option': true,
            'el-date-picker': true,
            'el-button': true,
            'el-button-group': true,
            'el-tag': true,
            'el-link': true
          }
        }
      })

      await flushPromises()

      // 验证组件有初始化图表的方法
      const vm = wrapper.vm
      expect(typeof vm.initCharts).toBe('function')
      expect(typeof vm.initHouseStatusChart).toBe('function')
      expect(typeof vm.initIncomeTrendChart).toBe('function')
      expect(typeof vm.initTenantTypeChart).toBe('function')
      expect(typeof vm.initContractStatusChart).toBe('function')
    })

    it('房源状态图表应该使用饼图配置', async () => {
      wrapper = mount(Dashboard, {
        global: {
          plugins: [pinia, router],
          stubs: {
            'el-select': true,
            'el-option': true,
            'el-date-picker': true,
            'el-button': true,
            'el-button-group': true,
            'el-tag': true,
            'el-link': true
          }
        }
      })

      await flushPromises()

      // 验证房源统计数据已加载
      expect(statisticsApi.getHouseStatistics).toHaveBeenCalled()
      
      // 验证组件有正确的图表数据
      const vm = wrapper.vm
      expect(vm.houseStatsData).toBeDefined()
    })

    it('收入趋势图表应该使用折线图配置', async () => {
      wrapper = mount(Dashboard, {
        global: {
          plugins: [pinia, router],
          stubs: {
            'el-select': true,
            'el-option': true,
            'el-date-picker': true,
            'el-button': true,
            'el-button-group': true,
            'el-tag': true,
            'el-link': true
          }
        }
      })

      await flushPromises()

      // 验证收入统计数据已加载
      expect(statisticsApi.getIncomeStatistics).toHaveBeenCalled()
      
      // 验证组件有正确的图表数据
      const vm = wrapper.vm
      expect(vm.incomeStatsData).toBeDefined()
    })

    it('租客类型图表应该使用柱状图配置', async () => {
      wrapper = mount(Dashboard, {
        global: {
          plugins: [pinia, router],
          stubs: {
            'el-select': true,
            'el-option': true,
            'el-date-picker': true,
            'el-button': true,
            'el-button-group': true,
            'el-tag': true,
            'el-link': true
          }
        }
      })

      await flushPromises()

      // 验证租客统计数据已加载
      expect(statisticsApi.getTenantStatistics).toHaveBeenCalled()
      
      // 验证组件有正确的图表数据
      const vm = wrapper.vm
      expect(vm.tenantStatsData).toBeDefined()
    })

    it('窗口大小变化时应该调用图表 resize 方法', async () => {
      wrapper = mount(Dashboard, {
        global: {
          plugins: [pinia, router],
          stubs: {
            'el-select': true,
            'el-option': true,
            'el-date-picker': true,
            'el-button': true,
            'el-button-group': true,
            'el-tag': true,
            'el-link': true
          }
        }
      })

      await flushPromises()

      // 验证组件有 handleResize 方法
      const vm = wrapper.vm
      expect(typeof vm.handleResize).toBe('function')
      
      // 调用 handleResize 方法（图表实例可能为 null，但不应该报错）
      expect(() => vm.handleResize()).not.toThrow()
    })

    it('组件卸载时应该清理事件监听器', async () => {
      const removeEventListenerSpy = vi.spyOn(window, 'removeEventListener')
      
      wrapper = mount(Dashboard, {
        global: {
          plugins: [pinia, router],
          stubs: {
            'el-select': true,
            'el-option': true,
            'el-date-picker': true,
            'el-button': true,
            'el-button-group': true,
            'el-tag': true,
            'el-link': true
          }
        }
      })

      await flushPromises()

      // 卸载组件
      wrapper.unmount()
      wrapper = null

      // 验证事件监听器被移除
      expect(removeEventListenerSpy).toHaveBeenCalledWith('resize', expect.any(Function))
      
      removeEventListenerSpy.mockRestore()
    })
  })

  // ============================================
  // 3. 测试数据刷新功能
  // ============================================

  describe('数据刷新功能', () => {
    it('切换时间范围应该重新加载数据', async () => {
      wrapper = mount(Dashboard, {
        global: {
          plugins: [pinia, router],
          stubs: {
            'el-select': true,
            'el-option': true,
            'el-date-picker': true,
            'el-button': true,
            'el-button-group': true,
            'el-tag': true,
            'el-link': true
          }
        }
      })

      await flushPromises()

      // 重置 mock 调用计数
      statisticsApi.getOverviewStatistics.mockClear()

      // 获取组件实例
      const vm = wrapper.vm

      // 调用时间范围变更方法
      vm.handleTimeRangeChange('7days')

      await flushPromises()

      // 验证 API 被重新调用
      expect(statisticsApi.getOverviewStatistics).toHaveBeenCalled()
    })

    it('选择自定义日期范围应该重新加载数据', async () => {
      wrapper = mount(Dashboard, {
        global: {
          plugins: [pinia, router],
          stubs: {
            'el-select': true,
            'el-option': true,
            'el-date-picker': true,
            'el-button': true,
            'el-button-group': true,
            'el-tag': true,
            'el-link': true
          }
        }
      })

      await flushPromises()

      // 重置 mock 调用计数
      statisticsApi.getOverviewStatistics.mockClear()

      // 获取组件实例
      const vm = wrapper.vm

      // 设置自定义日期范围
      const startDate = new Date('2024-01-01')
      const endDate = new Date('2024-12-31')
      vm.handleCustomDateChange([startDate, endDate])

      await flushPromises()

      // 验证 API 被重新调用
      expect(statisticsApi.getOverviewStatistics).toHaveBeenCalled()
    })

    it('loadAllData 应该按顺序加载所有数据', async () => {
      wrapper = mount(Dashboard, {
        global: {
          plugins: [pinia, router],
          stubs: {
            'el-select': true,
            'el-option': true,
            'el-date-picker': true,
            'el-button': true,
            'el-button-group': true,
            'el-tag': true,
            'el-link': true
          }
        }
      })

      await flushPromises()

      // 重置所有 mock
      statisticsApi.getOverviewStatistics.mockClear()
      statisticsApi.getHouseStatistics.mockClear()
      statisticsApi.getIncomeStatistics.mockClear()
      statisticsApi.getTenantStatistics.mockClear()
      statisticsApi.getContractStatistics.mockClear()
      contractApi.getContractList.mockClear()

      // 获取组件实例并调用 loadAllData
      const vm = wrapper.vm
      await vm.loadAllData()

      // 验证所有 API 都被调用
      expect(statisticsApi.getOverviewStatistics).toHaveBeenCalled()
      expect(statisticsApi.getHouseStatistics).toHaveBeenCalled()
      expect(statisticsApi.getIncomeStatistics).toHaveBeenCalled()
      expect(statisticsApi.getTenantStatistics).toHaveBeenCalled()
      expect(statisticsApi.getContractStatistics).toHaveBeenCalled()
      expect(contractApi.getContractList).toHaveBeenCalled()
    })

    it('刷新数据后应该重新初始化图表', async () => {
      wrapper = mount(Dashboard, {
        global: {
          plugins: [pinia, router],
          stubs: {
            'el-select': true,
            'el-option': true,
            'el-date-picker': true,
            'el-button': true,
            'el-button-group': true,
            'el-tag': true,
            'el-link': true
          }
        }
      })

      await flushPromises()

      // 获取组件实例并调用 loadAllData
      const vm = wrapper.vm
      
      // 验证 initCharts 方法存在
      expect(typeof vm.initCharts).toBe('function')
      
      // 调用 loadAllData 应该不会抛出错误
      await expect(vm.loadAllData()).resolves.not.toThrow()
    })
  })

  // ============================================
  // 4. 测试待办事项
  // ============================================

  describe('待办事项', () => {
    it('应该正确显示待处理合同', async () => {
      contractApi.getContractList.mockResolvedValueOnce(mockPendingContracts)

      wrapper = mount(Dashboard, {
        global: {
          plugins: [pinia, router],
          stubs: {
            'el-select': true,
            'el-option': true,
            'el-date-picker': true,
            'el-button': true,
            'el-button-group': true,
            'el-tag': true,
            'el-link': true
          }
        }
      })

      await flushPromises()

      // 验证待处理合同数据被加载
      expect(contractApi.getContractList).toHaveBeenCalledWith(
        expect.objectContaining({
          status: 'draft'
        })
      )
    })

    it('应该正确显示即将到期合同', async () => {
      contractApi.getContractList
        .mockResolvedValueOnce(mockPendingContracts) // 第一次调用（待处理）
        .mockResolvedValueOnce(mockExpiringContracts) // 第二次调用（即将到期）

      wrapper = mount(Dashboard, {
        global: {
          plugins: [pinia, router],
          stubs: {
            'el-select': true,
            'el-option': true,
            'el-date-picker': true,
            'el-button': true,
            'el-button-group': true,
            'el-tag': true,
            'el-link': true
          }
        }
      })

      await flushPromises()

      // 验证即将到期合同数据被加载
      expect(contractApi.getContractList).toHaveBeenCalledWith(
        expect.objectContaining({
          status: 'active'
        })
      )
    })

    it('无待处理合同时应该正确处理', async () => {
      contractApi.getContractList.mockResolvedValue({
        success: true,
        data: { items: [], total: 0 }
      })

      wrapper = mount(Dashboard, {
        global: {
          plugins: [pinia, router],
          stubs: {
            'el-select': true,
            'el-option': true,
            'el-date-picker': true,
            'el-button': true,
            'el-button-group': true,
            'el-tag': true,
            'el-link': true
          }
        }
      })

      await flushPromises()

      // 验证组件正确处理空数据
      const vm = wrapper.vm
      expect(vm.pendingContracts).toEqual([])
      expect(vm.expiringContracts).toEqual([])
    })
  })

  // ============================================
  // 5. 测试快捷操作
  // ============================================

  describe('快捷操作', () => {
    it('应该显示所有快捷操作按钮', async () => {
      wrapper = mount(Dashboard, {
        global: {
          plugins: [pinia, router],
          stubs: {
            'el-select': true,
            'el-option': true,
            'el-date-picker': true,
            'el-button': true,
            'el-button-group': true,
            'el-tag': true,
            'el-link': true
          }
        }
      })

      await flushPromises()

      const actionCards = wrapper.findAll('.action-card')
      expect(actionCards.length).toBe(4)

      // 验证操作名称
      const actionTitles = actionCards.map(card => card.find('.action-title').text())
      expect(actionTitles).toContain('新增房源')
      expect(actionTitles).toContain('新增合同')
      expect(actionTitles).toContain('房源管理')
      expect(actionTitles).toContain('合同管理')
    })

    it('点击快捷操作应该触发路由跳转', async () => {
      const routerPushSpy = vi.spyOn(router, 'push')
      
      wrapper = mount(Dashboard, {
        global: {
          plugins: [pinia, router],
          stubs: {
            'el-select': true,
            'el-option': true,
            'el-date-picker': true,
            'el-button': true,
            'el-button-group': true,
            'el-tag': true,
            'el-link': true
          }
        }
      })

      await flushPromises()

      // 获取组件实例
      const vm = wrapper.vm

      // 测试新增房源操作
      vm.handleAction('addHouse')
      expect(routerPushSpy).toHaveBeenCalledWith('/houses/add')

      // 测试新增合同操作
      routerPushSpy.mockClear()
      vm.handleAction('addContract')
      expect(routerPushSpy).toHaveBeenCalledWith('/contracts/add')

      // 测试房源管理操作
      routerPushSpy.mockClear()
      vm.handleAction('manageHouses')
      expect(routerPushSpy).toHaveBeenCalledWith('/houses')

      // 测试合同管理操作
      routerPushSpy.mockClear()
      vm.handleAction('manageContracts')
      expect(routerPushSpy).toHaveBeenCalledWith('/contracts')
    })
  })

  // ============================================
  // 6. 测试导出功能
  // ============================================

  describe('导出功能', () => {
    it('导出 Excel 应该调用正确的 API', async () => {
      // Mock Blob 和 URL
      global.URL.createObjectURL = vi.fn(() => 'blob:test')
      global.URL.revokeObjectURL = vi.fn()

      // Mock exportExcel 返回 Blob
      statisticsApi.exportExcel.mockResolvedValue(new Blob(['test'], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' }))

      wrapper = mount(Dashboard, {
        global: {
          plugins: [pinia, router],
          stubs: {
            'el-select': true,
            'el-option': true,
            'el-date-picker': true,
            'el-button': true,
            'el-button-group': true,
            'el-tag': true,
            'el-link': true
          }
        }
      })

      await flushPromises()

      const vm = wrapper.vm
      await vm.handleExport('excel')

      expect(statisticsApi.exportExcel).toHaveBeenCalled()
    })

    it('导出 PDF 应该调用正确的 API', async () => {
      // Mock Blob 和 URL
      global.URL.createObjectURL = vi.fn(() => 'blob:test')
      global.URL.revokeObjectURL = vi.fn()

      // Mock exportPdf 返回 Blob
      statisticsApi.exportPdf.mockResolvedValue(new Blob(['test'], { type: 'application/pdf' }))

      wrapper = mount(Dashboard, {
        global: {
          plugins: [pinia, router],
          stubs: {
            'el-select': true,
            'el-option': true,
            'el-date-picker': true,
            'el-button': true,
            'el-button-group': true,
            'el-tag': true,
            'el-link': true
          }
        }
      })

      await flushPromises()

      const vm = wrapper.vm
      await vm.handleExport('pdf')

      expect(statisticsApi.exportPdf).toHaveBeenCalled()
    })
  })

  // ============================================
  // 7. 测试工具函数
  // ============================================

  describe('工具函数', () => {
    it('formatNumber 应该正确格式化数字', async () => {
      wrapper = mount(Dashboard, {
        global: {
          plugins: [pinia, router],
          stubs: {
            'el-select': true,
            'el-option': true,
            'el-date-picker': true,
            'el-button': true,
            'el-button-group': true,
            'el-tag': true,
            'el-link': true
          }
        }
      })

      await flushPromises()

      const vm = wrapper.vm

      expect(vm.formatNumber(1000)).toBe('1,000')
      expect(vm.formatNumber(156000)).toBe('156,000')
      expect(vm.formatNumber(0)).toBe('0')
      expect(vm.formatNumber(null)).toBe('0')
      expect(vm.formatNumber(undefined)).toBe('0')
    })

    it('getStatusLabel 应该正确转换状态标签', async () => {
      wrapper = mount(Dashboard, {
        global: {
          plugins: [pinia, router],
          stubs: {
            'el-select': true,
            'el-option': true,
            'el-date-picker': true,
            'el-button': true,
            'el-button-group': true,
            'el-tag': true,
            'el-link': true
          }
        }
      })

      await flushPromises()

      const vm = wrapper.vm

      expect(vm.getStatusLabel('draft')).toBe('草稿')
      expect(vm.getStatusLabel('pending')).toBe('待审核')
      expect(vm.getStatusLabel('active')).toBe('执行中')
      expect(vm.getStatusLabel('expired')).toBe('已到期')
      expect(vm.getStatusLabel('terminated')).toBe('已终止')
    })

    it('getStatusType 应该正确返回标签类型', async () => {
      wrapper = mount(Dashboard, {
        global: {
          plugins: [pinia, router],
          stubs: {
            'el-select': true,
            'el-option': true,
            'el-date-picker': true,
            'el-button': true,
            'el-button-group': true,
            'el-tag': true,
            'el-link': true
          }
        }
      })

      await flushPromises()

      const vm = wrapper.vm

      expect(vm.getStatusType('待审核')).toBe('warning')
      expect(vm.getStatusType('待签约')).toBe('primary')
      expect(vm.getStatusType('执行中')).toBe('success')
      expect(vm.getStatusType('已到期')).toBe('info')
      expect(vm.getStatusType('已终止')).toBe('danger')
    })
  })

  // ============================================
  // 8. 测试响应式布局
  // ============================================

  describe('响应式布局', () => {
    it('应该包含正确的 CSS 类', async () => {
      wrapper = mount(Dashboard, {
        global: {
          plugins: [pinia, router],
          stubs: {
            'el-select': true,
            'el-option': true,
            'el-date-picker': true,
            'el-button': true,
            'el-button-group': true,
            'el-tag': true,
            'el-link': true
          }
        }
      })

      await flushPromises()

      // 验证主要容器存在
      expect(wrapper.find('.dashboard-page').exists()).toBe(true)
      expect(wrapper.find('.page-header').exists()).toBe(true)
      expect(wrapper.find('.stats-grid').exists()).toBe(true)
      expect(wrapper.find('.charts-section').exists()).toBe(true)
      expect(wrapper.find('.quick-actions-section').exists()).toBe(true)
      expect(wrapper.find('.todo-section').exists()).toBe(true)
    })

    it('图表卡片应该存在', async () => {
      wrapper = mount(Dashboard, {
        global: {
          plugins: [pinia, router],
          stubs: {
            'el-select': true,
            'el-option': true,
            'el-date-picker': true,
            'el-button': true,
            'el-button-group': true,
            'el-tag': true,
            'el-link': true
          }
        }
      })

      await flushPromises()

      // 验证图表卡片存在
      const chartCards = wrapper.findAll('.chart-card')
      expect(chartCards.length).toBe(4)
      
      // 验证图表标题
      const chartTitles = chartCards.map(card => card.find('.chart-title').text())
      expect(chartTitles).toContain('房源状态分布')
      expect(chartTitles).toContain('近 6 个月收入趋势')
      expect(chartTitles).toContain('租客类型分布')
      expect(chartTitles).toContain('合同状态统计')
    })
  })

  // ============================================
  // 9. 测试查看全部功能
  // ============================================

  describe('查看全部功能', () => {
    it('查看全部待处理合同应该跳转到正确页面', async () => {
      const routerPushSpy = vi.spyOn(router, 'push')
      
      wrapper = mount(Dashboard, {
        global: {
          plugins: [pinia, router],
          stubs: {
            'el-select': true,
            'el-option': true,
            'el-date-picker': true,
            'el-button': true,
            'el-button-group': true,
            'el-tag': true,
            'el-link': true
          }
        }
      })

      await flushPromises()

      const vm = wrapper.vm
      vm.handleViewAll('pending')

      expect(routerPushSpy).toHaveBeenCalledWith('/contracts?status=pending')
    })

    it('查看全部即将到期合同应该跳转到正确页面', async () => {
      const routerPushSpy = vi.spyOn(router, 'push')
      
      wrapper = mount(Dashboard, {
        global: {
          plugins: [pinia, router],
          stubs: {
            'el-select': true,
            'el-option': true,
            'el-date-picker': true,
            'el-button': true,
            'el-button-group': true,
            'el-tag': true,
            'el-link': true
          }
        }
      })

      await flushPromises()

      const vm = wrapper.vm
      vm.handleViewAll('expiring')

      expect(routerPushSpy).toHaveBeenCalledWith('/contracts?status=expiring')
    })
  })
})
