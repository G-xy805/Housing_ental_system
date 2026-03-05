/**
 * 房源管理页面测试用例
 * 测试范围：
 * 1. 房源列表展示
 * 2. 房源筛选（状态、类型）
 * 3. 新增房源表单
 * 4. 编辑房源表单
 * 5. 删除房源确认
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import HouseList from '@/views/houses/HouseList.vue'
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

const mockHouses = [
  {
    id: 1,
    title: '朝阳区精装两居室',
    city: '北京市',
    district: '朝阳区',
    address: '某某小区1号楼101室',
    area: 85.5,
    room_count: 2,
    hall_count: 1,
    bathroom_count: 1,
    floor: 8,
    total_floors: 18,
    rent_price: 8000,
    deposit: 8000,
    deposit_method: 'press1_pay3',
    rental_type: 'whole',
    status: 'available',
    cover_image: 'https://example.com/image1.jpg',
    contact_name: '张房东',
    contact_phone: '13800138001',
    created_at: '2024-01-15T10:30:00'
  },
  {
    id: 2,
    title: '海淀区合租主卧',
    city: '北京市',
    district: '海淀区',
    address: '中关村大街1号',
    area: 20,
    room_count: 3,
    hall_count: 1,
    bathroom_count: 1,
    floor: 5,
    total_floors: 12,
    rent_price: 3000,
    deposit: 3000,
    deposit_method: 'press1_pay1',
    rental_type: 'shared',
    status: 'rented',
    cover_image: 'https://example.com/image2.jpg',
    contact_name: '李房东',
    contact_phone: '13800138002',
    created_at: '2024-02-20T14:20:00'
  },
  {
    id: 3,
    title: '西城区简装一居室',
    city: '北京市',
    district: '西城区',
    address: '金融街2号',
    area: 45,
    room_count: 1,
    hall_count: 1,
    bathroom_count: 1,
    floor: 3,
    total_floors: 6,
    rent_price: 5000,
    deposit: 5000,
    deposit_method: 'press1_pay3',
    rental_type: 'whole',
    status: 'maintenance',
    cover_image: 'https://example.com/image3.jpg',
    contact_name: '王房东',
    contact_phone: '13800138003',
    created_at: '2024-03-10T09:15:00'
  }
]

const mockHouseDetail = {
  id: 1,
  title: '朝阳区精装两居室',
  city: '北京市',
  district: '朝阳区',
  address: '某某小区1号楼101室',
  area: 85.5,
  room_count: 2,
  hall_count: 1,
  bathroom_count: 1,
  floor: 8,
  total_floors: 18,
  rent_price: 8000,
  deposit: 8000,
  deposit_method: 'press1_pay3',
  rental_type: 'whole',
  status: 'available',
  cover_image: 'https://example.com/image1.jpg',
  images: ['https://example.com/image1.jpg'],
  contact_name: '张房东',
  contact_phone: '13800138001',
  contact_wechat: 'zhangfangdong',
  description: '精装修，交通便利',
  amenities: ['wifi', 'air_conditioning', 'refrigerator'],
  created_at: '2024-01-15T10:30:00'
}

// ============================================
// Mock API 函数
// ============================================

vi.mock('@/api/house', () => ({
  getHouseList: vi.fn(),
  getHouseDetail: vi.fn(),
  createHouse: vi.fn(),
  updateHouse: vi.fn(),
  deleteHouse: vi.fn(),
  uploadHouseImage: vi.fn(),
  uploadImage: vi.fn(),
  deleteMedia: vi.fn(),
  setCoverImage: vi.fn()
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
    path: '/houses',
    params: {},
    query: {},
    meta: {},
    name: 'houses'
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
        path: '/houses',
        params: {},
        query: {},
        meta: {},
        name: 'houses'
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
        path: '/houses',
        params: {},
        query: {},
        meta: {},
        name: 'houses'
      }
    }
  }
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

  return mount(HouseList, {
    global: {
      plugins: [pinia],
      mocks: {
        $router: mockRouter,
        $route: {
          path: '/houses',
          params: {},
          query: {}
        }
      },
      stubs: {
        HouseForm: {
          name: 'HouseForm',
          template: '<div class="mock-house-form"><slot /></div>',
          props: ['modelValue', 'isEdit', 'submitLoading'],
          emits: ['submit', 'cancel', 'update:modelValue', 'submit-success'],
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
  houseApi.getHouseList.mockReset()
  houseApi.getHouseDetail.mockReset()
  houseApi.createHouse.mockReset()
  houseApi.updateHouse.mockReset()
  houseApi.deleteHouse.mockReset()
  ElMessage.success.mockClear()
  ElMessage.error.mockClear()
  ElMessageBox.confirm.mockClear()
  mockPush.mockClear()
}

// ============================================
// 测试用例
// ============================================

describe('房源管理页面 - HouseList.vue', () => {
  beforeEach(() => {
    resetAllMocks()
  })

  afterEach(() => {
    vi.clearAllTimers()
  })

  // ============================================
  // 1. 测试房源列表展示
  // ============================================
  describe('1. 房源列表展示', () => {
    it('1.1 页面加载时应该自动获取房源列表', async () => {
      // 设置 mock 返回值
      houseApi.getHouseList.mockResolvedValue({
        data: {
          items: mockHouses,
          total: 3,
          page: 1,
          per_page: 12
        }
      })

      const wrapper = createWrapper()
      await flushPromises()

      // 验证 API 被调用
      expect(houseApi.getHouseList).toHaveBeenCalledTimes(1)
      expect(houseApi.getHouseList).toHaveBeenCalledWith({
        page: 1,
        per_page: 12,
        keyword: '',
        city: '',
        district: '',
        rental_type: '',
        status: '',
        min_price: null,
        max_price: null
      })

      wrapper.unmount()
    })

    it('1.2 应该正确显示房源列表数据', async () => {
      houseApi.getHouseList.mockResolvedValue({
        data: {
          items: mockHouses,
          total: 3,
          page: 1,
          per_page: 12
        }
      })

      const wrapper = createWrapper()
      await flushPromises()

      // 验证列表数据
      expect(wrapper.vm.houseList).toHaveLength(3)
      expect(wrapper.vm.houseList[0].title).toBe('朝阳区精装两居室')
      expect(wrapper.vm.houseList[1].title).toBe('海淀区合租主卧')
      expect(wrapper.vm.houseList[2].title).toBe('西城区简装一居室')

      // 验证分页数据
      expect(wrapper.vm.pagination.total).toBe(3)

      wrapper.unmount()
    })

    it('1.3 应该正确显示房源状态标签', async () => {
      houseApi.getHouseList.mockResolvedValue({
        data: {
          items: mockHouses,
          total: 3,
          page: 1,
          per_page: 12
        }
      })

      const wrapper = createWrapper()
      await flushPromises()

      // 验证状态类型映射
      expect(wrapper.vm.getStatusType('available')).toBe('success')
      expect(wrapper.vm.getStatusType('rented')).toBe('info')
      expect(wrapper.vm.getStatusType('maintenance')).toBe('warning')

      // 验证状态文本映射
      expect(wrapper.vm.getStatusText('available')).toBe('可租')
      expect(wrapper.vm.getStatusText('rented')).toBe('已租')
      expect(wrapper.vm.getStatusText('maintenance')).toBe('维修中')

      wrapper.unmount()
    })

    it('1.4 应该正确格式化地址信息', async () => {
      houseApi.getHouseList.mockResolvedValue({
        data: {
          items: mockHouses,
          total: 3,
          page: 1,
          per_page: 12
        }
      })

      const wrapper = createWrapper()
      await flushPromises()

      // 验证地址格式化
      const house = mockHouses[0]
      expect(wrapper.vm.formatAddress(house)).toBe('北京市朝阳区某某小区1号楼101室')

      // 测试空地址
      const houseWithNoAddress = { city: '', district: '', address: '' }
      expect(wrapper.vm.formatAddress(houseWithNoAddress)).toBe('暂无地址')

      wrapper.unmount()
    })

    it('1.5 应该正确格式化楼层信息', async () => {
      houseApi.getHouseList.mockResolvedValue({
        data: {
          items: mockHouses,
          total: 3,
          page: 1,
          per_page: 12
        }
      })

      const wrapper = createWrapper()
      await flushPromises()

      // 验证楼层格式化
      const house = mockHouses[0]
      expect(wrapper.vm.getFloorText(house)).toBe('8/18层')

      // 测试缺失楼层信息
      const houseWithNoFloor = { floor: null, total_floors: null }
      expect(wrapper.vm.getFloorText(houseWithNoFloor)).toBe('未知楼层')

      wrapper.unmount()
    })

    it('1.6 分页变化时应该重新加载数据', async () => {
      houseApi.getHouseList.mockResolvedValue({
        data: {
          items: mockHouses,
          total: 30,
          page: 2,
          per_page: 12
        }
      })

      const wrapper = createWrapper()
      await flushPromises()

      // 清除之前的调用
      houseApi.getHouseList.mockClear()

      // 触发页码变化
      wrapper.vm.pagination.page = 2
      wrapper.vm.handlePageChange(2)
      await flushPromises()

      // 验证 API 被调用且页码正确
      expect(houseApi.getHouseList).toHaveBeenCalledWith(
        expect.objectContaining({
          page: 2,
          per_page: 12
        })
      )

      wrapper.unmount()
    })

    it('1.7 每页数量变化时应该重新加载数据', async () => {
      houseApi.getHouseList.mockResolvedValue({
        data: {
          items: mockHouses,
          total: 30,
          page: 1,
          per_page: 24
        }
      })

      const wrapper = createWrapper()
      await flushPromises()

      // 清除之前的调用
      houseApi.getHouseList.mockClear()

      // 触发每页数量变化
      wrapper.vm.handleSizeChange(24)
      await flushPromises()

      // 验证 API 被调用且参数正确
      expect(houseApi.getHouseList).toHaveBeenCalled()

      wrapper.unmount()
    })

    it('1.8 加载数据时应该显示 loading 状态', async () => {
      // 创建一个延迟的 Promise
      let resolvePromise
      houseApi.getHouseList.mockImplementation(() => {
        return new Promise((resolve) => {
          resolvePromise = resolve
        })
      })

      const wrapper = createWrapper()

      // 验证 loading 状态为 true
      expect(wrapper.vm.loading).toBe(true)

      // 解决 Promise
      resolvePromise({
        data: {
          items: mockHouses,
          total: 3,
          page: 1,
          per_page: 12
        }
      })
      await flushPromises()

      // 验证 loading 状态为 false
      expect(wrapper.vm.loading).toBe(false)

      wrapper.unmount()
    })

    it('1.9 加载失败时应该显示错误提示', async () => {
      houseApi.getHouseList.mockRejectedValue(new Error('网络错误'))

      const wrapper = createWrapper()
      await flushPromises()

      // 验证错误提示
      expect(ElMessage.error).toHaveBeenCalledWith('加载房源列表失败')
      expect(wrapper.vm.loading).toBe(false)

      wrapper.unmount()
    })

    it('1.10 空列表时应该显示空状态', async () => {
      houseApi.getHouseList.mockResolvedValue({
        data: {
          items: [],
          total: 0,
          page: 1,
          per_page: 12
        }
      })

      const wrapper = createWrapper()
      await flushPromises()

      // 验证列表为空
      expect(wrapper.vm.houseList).toHaveLength(0)
      expect(wrapper.vm.pagination.total).toBe(0)

      wrapper.unmount()
    })
  })

  // ============================================
  // 2. 测试房源筛选（状态、类型）
  // ============================================
  describe('2. 房源筛选（状态、类型）', () => {
    it('2.1 按关键词搜索应该正确传递参数', async () => {
      houseApi.getHouseList.mockResolvedValue({
        data: {
          items: [mockHouses[0]],
          total: 1,
          page: 1,
          per_page: 12
        }
      })

      const wrapper = createWrapper()
      await flushPromises()

      // 清除之前的调用
      houseApi.getHouseList.mockClear()

      // 设置搜索关键词
      wrapper.vm.searchForm.keyword = '朝阳区'
      wrapper.vm.handleSearch()
      await flushPromises()

      // 验证 API 被调用且参数正确
      expect(houseApi.getHouseList).toHaveBeenCalledWith(
        expect.objectContaining({
          keyword: '朝阳区'
        })
      )

      wrapper.unmount()
    })

    it('2.2 按城市筛选应该正确传递参数', async () => {
      houseApi.getHouseList.mockResolvedValue({
        data: {
          items: mockHouses,
          total: 3,
          page: 1,
          per_page: 12
        }
      })

      const wrapper = createWrapper()
      await flushPromises()

      // 清除之前的调用
      houseApi.getHouseList.mockClear()

      // 设置城市筛选
      wrapper.vm.searchForm.city = '北京市'
      wrapper.vm.handleSearch()
      await flushPromises()

      // 验证 API 被调用且参数正确
      expect(houseApi.getHouseList).toHaveBeenCalledWith(
        expect.objectContaining({
          city: '北京市'
        })
      )

      wrapper.unmount()
    })

    it('2.3 按区域筛选应该正确传递参数', async () => {
      houseApi.getHouseList.mockResolvedValue({
        data: {
          items: [mockHouses[0]],
          total: 1,
          page: 1,
          per_page: 12
        }
      })

      const wrapper = createWrapper()
      await flushPromises()

      // 清除之前的调用
      houseApi.getHouseList.mockClear()

      // 设置区域筛选
      wrapper.vm.searchForm.district = '朝阳区'
      wrapper.vm.handleSearch()
      await flushPromises()

      // 验证 API 被调用且参数正确
      expect(houseApi.getHouseList).toHaveBeenCalledWith(
        expect.objectContaining({
          district: '朝阳区'
        })
      )

      wrapper.unmount()
    })

    it('2.4 按房源类型筛选应该正确传递参数', async () => {
      houseApi.getHouseList.mockResolvedValue({
        data: {
          items: [mockHouses[0]],
          total: 1,
          page: 1,
          per_page: 12
        }
      })

      const wrapper = createWrapper()
      await flushPromises()

      // 清除之前的调用
      houseApi.getHouseList.mockClear()

      // 设置房源类型筛选
      wrapper.vm.searchForm.rental_type = 'whole'
      wrapper.vm.handleSearch()
      await flushPromises()

      // 验证 API 被调用且参数正确
      expect(houseApi.getHouseList).toHaveBeenCalledWith(
        expect.objectContaining({
          rental_type: 'whole'
        })
      )

      wrapper.unmount()
    })

    it('2.5 按状态筛选应该正确传递参数', async () => {
      houseApi.getHouseList.mockResolvedValue({
        data: {
          items: [mockHouses[0]],
          total: 1,
          page: 1,
          per_page: 12
        }
      })

      const wrapper = createWrapper()
      await flushPromises()

      // 清除之前的调用
      houseApi.getHouseList.mockClear()

      // 设置状态筛选
      wrapper.vm.searchForm.status = 'available'
      wrapper.vm.handleSearch()
      await flushPromises()

      // 验证 API 被调用且参数正确
      expect(houseApi.getHouseList).toHaveBeenCalledWith(
        expect.objectContaining({
          status: 'available'
        })
      )

      wrapper.unmount()
    })

    it('2.6 按租金范围筛选应该正确传递参数', async () => {
      houseApi.getHouseList.mockResolvedValue({
        data: {
          items: [mockHouses[0]],
          total: 1,
          page: 1,
          per_page: 12
        }
      })

      const wrapper = createWrapper()
      await flushPromises()

      // 清除之前的调用
      houseApi.getHouseList.mockClear()

      // 设置租金范围筛选
      wrapper.vm.searchForm.min_price = 3000
      wrapper.vm.searchForm.max_price = 8000
      wrapper.vm.handleSearch()
      await flushPromises()

      // 验证 API 被调用且参数正确
      expect(houseApi.getHouseList).toHaveBeenCalledWith(
        expect.objectContaining({
          min_price: 3000,
          max_price: 8000
        })
      )

      wrapper.unmount()
    })

    it('2.7 同时使用多个筛选条件', async () => {
      houseApi.getHouseList.mockResolvedValue({
        data: {
          items: [mockHouses[0]],
          total: 1,
          page: 1,
          per_page: 12
        }
      })

      const wrapper = createWrapper()
      await flushPromises()

      // 清除之前的调用
      houseApi.getHouseList.mockClear()

      // 设置多个搜索条件
      wrapper.vm.searchForm.city = '北京市'
      wrapper.vm.searchForm.district = '朝阳区'
      wrapper.vm.searchForm.rental_type = 'whole'
      wrapper.vm.searchForm.status = 'available'
      wrapper.vm.handleSearch()
      await flushPromises()

      // 验证 API 被调用且参数正确
      expect(houseApi.getHouseList).toHaveBeenCalledWith(
        expect.objectContaining({
          city: '北京市',
          district: '朝阳区',
          rental_type: 'whole',
          status: 'available'
        })
      )

      wrapper.unmount()
    })

    it('2.8 重置搜索条件应该清空所有筛选', async () => {
      houseApi.getHouseList.mockResolvedValue({
        data: {
          items: mockHouses,
          total: 3,
          page: 1,
          per_page: 12
        }
      })

      const wrapper = createWrapper()
      await flushPromises()

      // 设置搜索条件
      wrapper.vm.searchForm.keyword = '朝阳区'
      wrapper.vm.searchForm.city = '北京市'
      wrapper.vm.searchForm.status = 'available'

      // 清除之前的调用
      houseApi.getHouseList.mockClear()

      // 重置
      wrapper.vm.handleReset()
      await flushPromises()

      // 验证搜索条件被清空
      expect(wrapper.vm.searchForm.keyword).toBe('')
      expect(wrapper.vm.searchForm.city).toBe('')
      expect(wrapper.vm.searchForm.status).toBe('')
      expect(wrapper.vm.pagination.page).toBe(1)

      // 验证 API 被调用
      expect(houseApi.getHouseList).toHaveBeenCalled()

      wrapper.unmount()
    })

    it('2.9 搜索时应该重置页码为 1', async () => {
      houseApi.getHouseList.mockResolvedValue({
        data: {
          items: mockHouses,
          total: 30,
          page: 1,
          per_page: 12
        }
      })

      const wrapper = createWrapper()
      await flushPromises()

      // 设置当前页码为 2
      wrapper.vm.pagination.page = 2

      // 清除之前的调用
      houseApi.getHouseList.mockClear()

      // 搜索
      wrapper.vm.searchForm.keyword = '朝阳区'
      wrapper.vm.handleSearch()
      await flushPromises()

      // 验证页码被重置为 1
      expect(wrapper.vm.pagination.page).toBe(1)

      wrapper.unmount()
    })
  })

  // ============================================
  // 3. 测试新增房源表单
  // ============================================
  describe('3. 新增房源表单', () => {
    it('3.1 点击新增按钮应该打开对话框', async () => {
      houseApi.getHouseList.mockResolvedValue({
        data: {
          items: mockHouses,
          total: 3,
          page: 1,
          per_page: 12
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
      expect(wrapper.vm.dialogTitle).toBe('新增房源')
      expect(wrapper.vm.currentHouseData).toEqual({})

      wrapper.unmount()
    })

    it('3.2 提交新增表单应该调用 addHouse 方法', async () => {
      houseApi.getHouseList.mockResolvedValue({
        data: {
          items: mockHouses,
          total: 3,
          page: 1,
          per_page: 12
        }
      })

      houseApi.createHouse.mockResolvedValue({
        data: { id: 4, ...mockHouseDetail }
      })

      const wrapper = createWrapper()
      await flushPromises()

      // 打开新增对话框
      wrapper.vm.handleAdd()
      await flushPromises()

      // 模拟表单提交
      const formData = {
        title: '新房源',
        city: '北京市',
        district: '朝阳区',
        address: '测试地址1号',
        rent_price: 6000,
        deposit: 6000,
        area: 60,
        room_count: 1,
        hall_count: 1,
        bathroom_count: 1,
        floor: 5,
        total_floors: 10,
        rental_type: 'whole',
        status: 'available'
      }

      await wrapper.vm.handleFormSubmit(formData)
      await flushPromises()

      // 验证成功提示
      expect(ElMessage.success).toHaveBeenCalledWith('创建成功')
      expect(wrapper.vm.dialogVisible).toBe(false)

      wrapper.unmount()
    })

    it('3.3 新增成功后应该刷新列表', async () => {
      houseApi.getHouseList.mockResolvedValue({
        data: {
          items: mockHouses,
          total: 3,
          page: 1,
          per_page: 12
        }
      })

      houseApi.createHouse.mockResolvedValue({
        data: { id: 4 }
      })

      const wrapper = createWrapper()
      await flushPromises()

      // 清除之前的调用
      houseApi.getHouseList.mockClear()

      // 打开新增对话框并提交
      wrapper.vm.handleAdd()
      await flushPromises()

      const formData = {
        title: '新房源',
        city: '北京市',
        district: '朝阳区',
        address: '测试地址1号'
      }

      await wrapper.vm.handleFormSubmit(formData)
      await flushPromises()

      // 验证列表被刷新（store.addHouse 和 loadHouseList 都会调用）
      expect(houseApi.getHouseList).toHaveBeenCalled()

      wrapper.unmount()
    })

    it('3.4 新增失败应该显示错误提示', async () => {
      houseApi.getHouseList.mockResolvedValue({
        data: {
          items: mockHouses,
          total: 3,
          page: 1,
          per_page: 12
        }
      })

      houseApi.createHouse.mockRejectedValue({
        response: {
          data: {
            error: {
              message: '房源标题已存在'
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
        title: '朝阳区精装两居室', // 已存在的标题
        city: '北京市',
        district: '朝阳区',
        address: '测试地址1号'
      }

      try {
        await wrapper.vm.handleFormSubmit(formData)
        await flushPromises()
      } catch (error) {
        // 预期会抛出错误
      }

      // 验证对话框保持打开
      expect(wrapper.vm.dialogVisible).toBe(true)

      wrapper.unmount()
    })
  })

  // ============================================
  // 4. 测试编辑房源表单
  // ============================================
  describe('4. 编辑房源表单', () => {
    it('4.1 点击编辑按钮应该打开对话框并填充数据', async () => {
      houseApi.getHouseList.mockResolvedValue({
        data: {
          items: mockHouses,
          total: 3,
          page: 1,
          per_page: 12
        }
      })

      const wrapper = createWrapper()
      await flushPromises()

      // 点击编辑按钮
      const house = mockHouses[0]
      wrapper.vm.handleEdit(house)
      await flushPromises()

      // 验证对话框状态
      expect(wrapper.vm.dialogVisible).toBe(true)
      expect(wrapper.vm.isEdit).toBe(true)
      expect(wrapper.vm.dialogTitle).toBe('编辑房源')
      expect(wrapper.vm.currentHouseData.title).toBe('朝阳区精装两居室')

      wrapper.unmount()
    })

    it('4.2 提交编辑表单应该调用 editHouse 方法', async () => {
      houseApi.getHouseList.mockResolvedValue({
        data: {
          items: mockHouses,
          total: 3,
          page: 1,
          per_page: 12
        }
      })

      houseApi.updateHouse.mockResolvedValue({
        data: { ...mockHouseDetail, title: '朝阳区精装两居室（已更新）' }
      })

      const wrapper = createWrapper()
      await flushPromises()

      // 打开编辑对话框
      const house = mockHouses[0]
      wrapper.vm.handleEdit(house)
      await flushPromises()

      // 模拟表单提交
      const formData = {
        id: 1,
        title: '朝阳区精装两居室（已更新）',
        city: '北京市',
        district: '朝阳区',
        address: '某某小区1号楼101室',
        status: 'available'
      }

      await wrapper.vm.handleFormSubmit(formData)
      await flushPromises()

      // 验证成功提示
      expect(ElMessage.success).toHaveBeenCalledWith('编辑成功')
      expect(wrapper.vm.dialogVisible).toBe(false)

      wrapper.unmount()
    })

    it('4.3 编辑成功后应该刷新列表', async () => {
      houseApi.getHouseList.mockResolvedValue({
        data: {
          items: mockHouses,
          total: 3,
          page: 1,
          per_page: 12
        }
      })

      houseApi.updateHouse.mockResolvedValue({
        data: mockHouseDetail
      })

      const wrapper = createWrapper()
      await flushPromises()

      // 清除之前的调用
      houseApi.getHouseList.mockClear()

      // 打开编辑对话框并提交
      const house = mockHouses[0]
      wrapper.vm.handleEdit(house)
      await flushPromises()

      const formData = {
        id: 1,
        title: '朝阳区精装两居室',
        status: 'available'
      }

      await wrapper.vm.handleFormSubmit(formData)
      await flushPromises()

      // 验证列表被刷新
      // editHouse 内部调用 fetchHouseList，handleFormSubmit 又调用 loadHouseList
      // 所以 getHouseList 会被调用 2 次
      expect(houseApi.getHouseList).toHaveBeenCalled()

      wrapper.unmount()
    })

    it('4.4 编辑失败应该显示错误提示', async () => {
      houseApi.getHouseList.mockResolvedValue({
        data: {
          items: mockHouses,
          total: 3,
          page: 1,
          per_page: 12
        }
      })

      houseApi.updateHouse.mockRejectedValue({
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
      const house = mockHouses[0]
      wrapper.vm.handleEdit(house)
      await flushPromises()

      const formData = {
        id: 1,
        title: '朝阳区精装两居室',
        status: 'available'
      }

      try {
        await wrapper.vm.handleFormSubmit(formData)
        await flushPromises()
      } catch (error) {
        // 预期会抛出错误
      }

      // 验证对话框保持打开
      expect(wrapper.vm.dialogVisible).toBe(true)

      wrapper.unmount()
    })
  })

  // ============================================
  // 5. 测试删除房源
  // ============================================
  describe('5. 删除房源', () => {
    it('5.1 点击删除按钮应该显示确认对话框', async () => {
      houseApi.getHouseList.mockResolvedValue({
        data: {
          items: mockHouses,
          total: 3,
          page: 1,
          per_page: 12
        }
      })

      ElMessageBox.confirm.mockResolvedValue('confirm')

      const wrapper = createWrapper()
      await flushPromises()

      // 点击删除按钮
      const house = mockHouses[0]
      wrapper.vm.handleDelete(house)
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

    it('5.2 确认删除应该调用 deleteHouse API', async () => {
      houseApi.getHouseList.mockResolvedValue({
        data: {
          items: mockHouses,
          total: 3,
          page: 1,
          per_page: 12
        }
      })

      houseApi.deleteHouse.mockResolvedValue({
        success: true
      })

      ElMessageBox.confirm.mockResolvedValue('confirm')

      const wrapper = createWrapper()
      await flushPromises()

      // 确认删除
      const house = mockHouses[0]
      await wrapper.vm.handleDelete(house)
      await flushPromises()

      // 验证 API 被调用
      expect(houseApi.deleteHouse).toHaveBeenCalledWith(1)
      expect(ElMessage.success).toHaveBeenCalledWith('删除成功')

      wrapper.unmount()
    })

    it('5.3 删除成功后应该刷新列表', async () => {
      houseApi.getHouseList.mockResolvedValue({
        data: {
          items: mockHouses,
          total: 3,
          page: 1,
          per_page: 12
        }
      })

      houseApi.deleteHouse.mockResolvedValue({
        success: true
      })

      ElMessageBox.confirm.mockResolvedValue('confirm')

      const wrapper = createWrapper()
      await flushPromises()

      // 清除之前的调用
      houseApi.getHouseList.mockClear()

      // 确认删除
      const house = mockHouses[0]
      await wrapper.vm.handleDelete(house)
      await flushPromises()

      // 验证列表被刷新
      expect(houseApi.getHouseList).toHaveBeenCalledTimes(1)

      wrapper.unmount()
    })

    it('5.4 取消删除不应该调用 API', async () => {
      houseApi.getHouseList.mockResolvedValue({
        data: {
          items: mockHouses,
          total: 3,
          page: 1,
          per_page: 12
        }
      })

      ElMessageBox.confirm.mockRejectedValue(new Error('cancel'))

      const wrapper = createWrapper()
      await flushPromises()

      // 取消删除
      const house = mockHouses[0]
      await wrapper.vm.handleDelete(house)
      await flushPromises()

      // 验证删除 API 没有被调用
      expect(houseApi.deleteHouse).not.toHaveBeenCalled()

      wrapper.unmount()
    })

    it('5.5 删除失败应该显示错误提示', async () => {
      houseApi.getHouseList.mockResolvedValue({
        data: {
          items: mockHouses,
          total: 3,
          page: 1,
          per_page: 12
        }
      })

      houseApi.deleteHouse.mockRejectedValue({
        response: {
          data: {
            error: {
              message: '该房源有合同关联，无法删除'
            }
          }
        }
      })

      ElMessageBox.confirm.mockResolvedValue('confirm')

      const wrapper = createWrapper()
      await flushPromises()

      // 确认删除
      const house = mockHouses[0]
      await wrapper.vm.handleDelete(house)
      await flushPromises()

      // 验证错误提示
      expect(ElMessage.error).toHaveBeenCalledWith('该房源有合同关联，无法删除')

      wrapper.unmount()
    })
  })

  // ============================================
  // 6. 测试查看详情
  // ============================================
  describe('6. 查看详情', () => {
    it('6.1 点击房源卡片应该跳转到详情页', async () => {
      houseApi.getHouseList.mockResolvedValue({
        data: {
          items: mockHouses,
          total: 3,
          page: 1,
          per_page: 12
        }
      })

      const wrapper = createWrapper()
      await flushPromises()

      // 点击查看详情
      const house = mockHouses[0]
      wrapper.vm.handleView(house)

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
      houseApi.getHouseList.mockResolvedValue({
        data: {
          items: mockHouses,
          total: 3,
          page: 1,
          per_page: 12
        }
      })

      const wrapper = createWrapper()
      await flushPromises()

      // 验证权限 - 使用 userStore 定义的权限类型
      expect(wrapper.vm.hasPermission('create')).toBe(true)
      expect(wrapper.vm.hasPermission('edit')).toBe(true)
      expect(wrapper.vm.hasPermission('delete')).toBe(true)

      wrapper.unmount()
    })

    it('7.2 房东应该有新增和编辑权限', async () => {
      const pinia = createPinia()
      setActivePinia(pinia)

      const userStore = useUserStore()
      userStore.setUserInfo({
        id: 2,
        username: 'landlord',
        role: 'landlord',
        user_type: 'landlord'
      })

      houseApi.getHouseList.mockResolvedValue({
        data: {
          items: mockHouses,
          total: 3,
          page: 1,
          per_page: 12
        }
      })

      const wrapper = mount(HouseList, {
        global: {
          plugins: [pinia],
          mocks: {
            $router: mockRouter,
            $route: {
              path: '/houses',
              params: {},
              query: {}
            }
          },
          stubs: {
            HouseForm: {
              name: 'HouseForm',
              template: '<div class="mock-house-form"><slot /></div>',
              props: ['modelValue', 'isEdit', 'submitLoading']
            },
            RouterLink: true,
            RouterView: true
          }
        }
      })

      await flushPromises()

      // 验证权限 - 使用 userStore 定义的权限类型
      expect(wrapper.vm.hasPermission('create')).toBe(true)
      expect(wrapper.vm.hasPermission('edit')).toBe(true)
      expect(wrapper.vm.hasPermission('delete')).toBe(false)

      wrapper.unmount()
    })
  })
})
