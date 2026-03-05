/**
 * 房源详情页面测试用例
 * 测试范围：
 * 1. 房源详情加载
 * 2. 房间列表展示
 * 3. 房间管理（新增、编辑、删除）
 * 4. 媒体文件管理
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import HouseDetail from '@/views/houses/HouseDetail.vue'
import * as houseApi from '@/api/house'
import { useUserStore } from '@/store/user'
import { useHouseStore } from '@/store/house'
import { ElMessage, ElMessageBox } from 'element-plus'

// ============================================
// 使用 vi.hoisted 提升变量定义
// ============================================

const mockPush = vi.hoisted(() => vi.fn())
const mockBack = vi.hoisted(() => vi.fn())

// ============================================
// Mock API 响应数据
// ============================================

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
  cover_image: 'https://example.com/cover1.jpg',
  images: [
    'https://example.com/image1.jpg',
    'https://example.com/image2.jpg'
  ],
  contact_name: '张房东',
  contact_phone: '13800138001',
  contact_wechat: 'zhangfangdong',
  description: '精装修，交通便利',
  amenities: ['wifi', 'air_conditioning', 'refrigerator'],
  orientation: 'south',
  decoration: 'fine',
  created_at: '2024-01-15T10:30:00',
  updated_at: '2024-01-20T14:20:00',
  latitude: 39.9042,
  longitude: 116.4074
}

const mockSharedHouseDetail = {
  ...mockHouseDetail,
  id: 2,
  title: '海淀区合租公寓',
  rental_type: 'shared',
  rooms: [
    {
      id: 1,
      room_number: '101',
      room_name: '主卧',
      area: 25.0,
      floor: 5,
      orientation: 'south',
      rent_price: 5000.0,
      deposit: 5000.0,
      status: 'available',
      is_master: true,
      description: '朝南，带阳台',
      room_count: 1,
      hall_count: 0,
      bathroom_count: 1
    },
    {
      id: 2,
      room_number: '102',
      room_name: '次卧A',
      area: 18.0,
      floor: 5,
      orientation: 'north',
      rent_price: 3800.0,
      deposit: 3800.0,
      status: 'rented',
      is_master: false,
      description: '朝北',
      room_count: 1,
      hall_count: 0,
      bathroom_count: 1
    },
    {
      id: 3,
      room_number: '103',
      room_name: '次卧B',
      area: 16.0,
      floor: 5,
      orientation: 'east',
      rent_price: 3500.0,
      deposit: 3500.0,
      status: 'available',
      is_master: false,
      description: '朝东',
      room_count: 1,
      hall_count: 0,
      bathroom_count: 1
    }
  ]
}

// ============================================
// Mock API 函数
// ============================================

vi.mock('@/api/house', () => ({
  getHouseDetail: vi.fn(),
  deleteHouse: vi.fn(),
  createRoom: vi.fn(),
  updateRoom: vi.fn(),
  deleteRoom: vi.fn(),
  getRoomList: vi.fn(),
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
    back: mockBack,
    go: vi.fn(),
    replace: vi.fn(),
    forward: vi.fn()
  }),
  useRoute: () => ({
    path: '/houses/1',
    params: { id: '1' },
    query: {},
    meta: {},
    name: 'house-detail'
  }),
  createRouter: vi.fn(() => ({
    push: mockPush,
    back: mockBack,
    go: vi.fn(),
    replace: vi.fn(),
    forward: vi.fn(),
    beforeEach: vi.fn(),
    afterEach: vi.fn(),
    beforeResolve: vi.fn(),
    onError: vi.fn(),
    currentRoute: {
      value: {
        path: '/houses/1',
        params: { id: '1' },
        query: {},
        meta: {},
        name: 'house-detail'
      }
    }
  })),
  createWebHistory: vi.fn(() => ({}))
}))

// Mock router 模块
vi.mock('@/router', () => ({
  default: {
    push: mockPush,
    back: mockBack,
    go: vi.fn(),
    replace: vi.fn(),
    forward: vi.fn(),
    beforeEach: vi.fn(),
    afterEach: vi.fn(),
    beforeResolve: vi.fn(),
    onError: vi.fn(),
    currentRoute: {
      value: {
        path: '/houses/1',
        params: { id: '1' },
        query: {},
        meta: {},
        name: 'house-detail'
      }
    }
  }
}))

// ============================================
// 测试工具函数
// ============================================

const mockRouter = {
  push: mockPush,
  back: mockBack,
  go: vi.fn(),
  replace: vi.fn(),
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

  return mount(HouseDetail, {
    global: {
      plugins: [pinia],
      mocks: {
        $router: mockRouter,
        $route: {
          path: '/houses/1',
          params: { id: '1' },
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
        RoomList: {
          name: 'RoomList',
          template: '<div class="mock-room-list"><slot /></div>',
          props: ['modelValue', 'showAddButton', 'showEditButton', 'showDeleteButton', 'loading'],
          emits: ['update:modelValue', 'add', 'edit', 'delete', 'view']
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
  houseApi.getHouseDetail.mockReset()
  houseApi.deleteHouse.mockReset()
  houseApi.createRoom.mockReset()
  houseApi.updateRoom.mockReset()
  houseApi.deleteRoom.mockReset()
  houseApi.uploadHouseImage.mockReset()
  houseApi.deleteMedia.mockReset()
  houseApi.setCoverImage.mockReset()
  ElMessage.success.mockClear()
  ElMessage.error.mockClear()
  ElMessageBox.confirm.mockClear()
  mockPush.mockClear()
  mockBack.mockClear()
}

// ============================================
// 测试用例
// ============================================

describe('房源详情页面 - HouseDetail.vue', () => {
  beforeEach(() => {
    resetAllMocks()
  })

  afterEach(() => {
    vi.clearAllTimers()
  })

  // ============================================
  // 1. 测试房源详情加载
  // ============================================
  describe('1. 房源详情加载', () => {
    it('1.1 页面加载时应该自动获取房源详情', async () => {
      houseApi.getHouseDetail.mockResolvedValue({
        data: mockHouseDetail
      })

      const wrapper = createWrapper()
      await flushPromises()

      // 验证 API 被调用
      expect(houseApi.getHouseDetail).toHaveBeenCalledTimes(1)
      expect(houseApi.getHouseDetail).toHaveBeenCalledWith('1')

      wrapper.unmount()
    })

    it('1.2 应该正确显示房源基本信息', async () => {
      houseApi.getHouseDetail.mockResolvedValue({
        data: mockHouseDetail
      })

      const wrapper = createWrapper()
      await flushPromises()

      // 验证房源数据
      expect(wrapper.vm.houseData.title).toBe('朝阳区精装两居室')
      expect(wrapper.vm.houseData.city).toBe('北京市')
      expect(wrapper.vm.houseData.district).toBe('朝阳区')
      expect(wrapper.vm.houseData.address).toBe('某某小区1号楼101室')
      expect(wrapper.vm.houseData.rent_price).toBe(8000)
      expect(wrapper.vm.houseData.area).toBe(85.5)

      wrapper.unmount()
    })

    it('1.3 应该正确显示房源状态标签', async () => {
      houseApi.getHouseDetail.mockResolvedValue({
        data: mockHouseDetail
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
      expect(wrapper.vm.getStatusText('partially_rented')).toBe('部分已租')

      wrapper.unmount()
    })

    it('1.4 应该正确显示房源类型', async () => {
      houseApi.getHouseDetail.mockResolvedValue({
        data: mockHouseDetail
      })

      const wrapper = createWrapper()
      await flushPromises()

      // 验证类型文本映射
      expect(wrapper.vm.getTypeText('whole')).toBe('整租')
      expect(wrapper.vm.getTypeText('shared')).toBe('合租')
      expect(wrapper.vm.getTypeText('apartment')).toBe('公寓')
      expect(wrapper.vm.getTypeText('villa')).toBe('别墅')

      wrapper.unmount()
    })

    it('1.5 应该正确显示押金方式', async () => {
      houseApi.getHouseDetail.mockResolvedValue({
        data: mockHouseDetail
      })

      const wrapper = createWrapper()
      await flushPromises()

      // 验证押金方式文本映射
      expect(wrapper.vm.getDepositText('press1_pay3')).toBe('押一付三')
      expect(wrapper.vm.getDepositText('press1_pay1')).toBe('押一付一')
      expect(wrapper.vm.getDepositText('press2_pay3')).toBe('押二付三')
      expect(wrapper.vm.getDepositText('negotiable')).toBe('面议')

      wrapper.unmount()
    })

    it('1.6 应该正确显示朝向信息', async () => {
      houseApi.getHouseDetail.mockResolvedValue({
        data: mockHouseDetail
      })

      const wrapper = createWrapper()
      await flushPromises()

      // 验证朝向文本映射
      expect(wrapper.vm.getOrientationText('south')).toBe('南')
      expect(wrapper.vm.getOrientationText('north')).toBe('北')
      expect(wrapper.vm.getOrientationText('east')).toBe('东')
      expect(wrapper.vm.getOrientationText('west')).toBe('西')
      expect(wrapper.vm.getOrientationText('southeast')).toBe('东南')
      expect(wrapper.vm.getOrientationText('southwest')).toBe('西南')
      expect(wrapper.vm.getOrientationText('northeast')).toBe('东北')
      expect(wrapper.vm.getOrientationText('northwest')).toBe('西北')

      wrapper.unmount()
    })

    it('1.7 应该正确显示装修情况', async () => {
      houseApi.getHouseDetail.mockResolvedValue({
        data: mockHouseDetail
      })

      const wrapper = createWrapper()
      await flushPromises()

      // 验证装修文本映射
      expect(wrapper.vm.getDecorationText('rough')).toBe('毛坯')
      expect(wrapper.vm.getDecorationText('simple')).toBe('简装')
      expect(wrapper.vm.getDecorationText('fine')).toBe('精装')
      expect(wrapper.vm.getDecorationText('luxury')).toBe('豪华装修')

      wrapper.unmount()
    })

    it('1.8 应该正确显示配套设施', async () => {
      houseApi.getHouseDetail.mockResolvedValue({
        data: mockHouseDetail
      })

      const wrapper = createWrapper()
      await flushPromises()

      // 验证配套设施文本映射
      expect(wrapper.vm.getAmenityText('wifi')).toBe('WiFi')
      expect(wrapper.vm.getAmenityText('air_conditioning')).toBe('空调')
      expect(wrapper.vm.getAmenityText('refrigerator')).toBe('冰箱')
      expect(wrapper.vm.getAmenityText('washing_machine')).toBe('洗衣机')
      expect(wrapper.vm.getAmenityText('water_heater')).toBe('热水器')

      wrapper.unmount()
    })

    it('1.9 应该正确处理 facilities 字段转换为 amenities', async () => {
      const houseWithFacilities = {
        ...mockHouseDetail,
        facilities: {
          wifi: true,
          air_conditioning: true,
          refrigerator: false
        },
        amenities: undefined
      }

      houseApi.getHouseDetail.mockResolvedValue({
        data: houseWithFacilities
      })

      const wrapper = createWrapper()
      await flushPromises()

      // 验证 facilities 被转换为 amenities
      expect(wrapper.vm.houseData.amenities).toContain('wifi')
      expect(wrapper.vm.houseData.amenities).toContain('air_conditioning')
      expect(wrapper.vm.houseData.amenities).not.toContain('refrigerator')

      wrapper.unmount()
    })

    it('1.10 加载数据时应该显示 loading 状态', async () => {
      // 创建一个延迟的 Promise
      let resolvePromise
      houseApi.getHouseDetail.mockImplementation(() => {
        return new Promise((resolve) => {
          resolvePromise = resolve
        })
      })

      const wrapper = createWrapper()

      // 验证 loading 状态为 true
      expect(wrapper.vm.loading).toBe(true)

      // 解决 Promise
      resolvePromise({
        data: mockHouseDetail
      })
      await flushPromises()

      // 验证 loading 状态为 false
      expect(wrapper.vm.loading).toBe(false)

      wrapper.unmount()
    })

    it('1.11 加载失败时应该显示错误提示', async () => {
      houseApi.getHouseDetail.mockRejectedValue(new Error('网络错误'))

      const wrapper = createWrapper()
      await flushPromises()

      // 验证错误提示
      expect(ElMessage.error).toHaveBeenCalledWith('加载房源详情失败')
      expect(wrapper.vm.loading).toBe(false)

      wrapper.unmount()
    })

    it('1.12 应该正确显示房东联系信息', async () => {
      houseApi.getHouseDetail.mockResolvedValue({
        data: mockHouseDetail
      })

      const wrapper = createWrapper()
      await flushPromises()

      // 验证房东信息
      expect(wrapper.vm.houseData.contact_name).toBe('张房东')
      expect(wrapper.vm.houseData.contact_phone).toBe('13800138001')
      expect(wrapper.vm.houseData.contact_wechat).toBe('zhangfangdong')

      wrapper.unmount()
    })

    it('1.13 应该正确格式化日期', async () => {
      houseApi.getHouseDetail.mockResolvedValue({
        data: mockHouseDetail
      })

      const wrapper = createWrapper()
      await flushPromises()

      // 验证日期格式化
      const formattedDate = wrapper.vm.formatDate('2024-01-15T10:30:00')
      expect(formattedDate).toBeTruthy()
      expect(formattedDate).not.toBe('暂无')

      // 测试空日期
      expect(wrapper.vm.formatDate(null)).toBe('暂无')
      expect(wrapper.vm.formatDate('')).toBe('暂无')

      wrapper.unmount()
    })
  })

  // ============================================
  // 2. 测试房间列表展示
  // ============================================
  describe('2. 房间列表展示', () => {
    it('2.1 合租房源应该显示房间列表', async () => {
      houseApi.getHouseDetail.mockResolvedValue({
        data: mockSharedHouseDetail
      })

      const wrapper = createWrapper()
      await flushPromises()

      // 验证房源类型为合租
      expect(wrapper.vm.houseData.rental_type).toBe('shared')

      // 验证房间数据
      expect(wrapper.vm.houseData.rooms).toHaveLength(3)
      expect(wrapper.vm.houseData.rooms[0].room_name).toBe('主卧')
      expect(wrapper.vm.houseData.rooms[1].room_name).toBe('次卧A')
      expect(wrapper.vm.houseData.rooms[2].room_name).toBe('次卧B')

      wrapper.unmount()
    })

    it('2.2 整租房源不应该显示房间列表', async () => {
      houseApi.getHouseDetail.mockResolvedValue({
        data: mockHouseDetail
      })

      const wrapper = createWrapper()
      await flushPromises()

      // 验证房源类型为整租
      expect(wrapper.vm.houseData.rental_type).toBe('whole')

      // 验证没有房间数据
      expect(wrapper.vm.houseData.rooms).toBeUndefined()

      wrapper.unmount()
    })

    it('2.3 应该正确显示房间状态', async () => {
      houseApi.getHouseDetail.mockResolvedValue({
        data: mockSharedHouseDetail
      })

      const wrapper = createWrapper()
      await flushPromises()

      // 验证房间状态
      const rooms = wrapper.vm.houseData.rooms
      expect(rooms[0].status).toBe('available')
      expect(rooms[1].status).toBe('rented')
      expect(rooms[2].status).toBe('available')

      wrapper.unmount()
    })

    it('2.4 应该正确显示房间租金', async () => {
      houseApi.getHouseDetail.mockResolvedValue({
        data: mockSharedHouseDetail
      })

      const wrapper = createWrapper()
      await flushPromises()

      // 验证房间租金
      const rooms = wrapper.vm.houseData.rooms
      expect(rooms[0].rent_price).toBe(5000.0)
      expect(rooms[1].rent_price).toBe(3800.0)
      expect(rooms[2].rent_price).toBe(3500.0)

      wrapper.unmount()
    })

    it('2.5 应该正确显示房间面积', async () => {
      houseApi.getHouseDetail.mockResolvedValue({
        data: mockSharedHouseDetail
      })

      const wrapper = createWrapper()
      await flushPromises()

      // 验证房间面积
      const rooms = wrapper.vm.houseData.rooms
      expect(rooms[0].area).toBe(25.0)
      expect(rooms[1].area).toBe(18.0)
      expect(rooms[2].area).toBe(16.0)

      wrapper.unmount()
    })

    it('2.6 应该正确显示房间朝向', async () => {
      houseApi.getHouseDetail.mockResolvedValue({
        data: mockSharedHouseDetail
      })

      const wrapper = createWrapper()
      await flushPromises()

      // 验证房间朝向
      const rooms = wrapper.vm.houseData.rooms
      expect(rooms[0].orientation).toBe('south')
      expect(rooms[1].orientation).toBe('north')
      expect(rooms[2].orientation).toBe('east')

      wrapper.unmount()
    })

    it('2.7 应该正确显示主卧标识', async () => {
      houseApi.getHouseDetail.mockResolvedValue({
        data: mockSharedHouseDetail
      })

      const wrapper = createWrapper()
      await flushPromises()

      // 验证主卧标识
      const rooms = wrapper.vm.houseData.rooms
      expect(rooms[0].is_master).toBe(true)
      expect(rooms[1].is_master).toBe(false)
      expect(rooms[2].is_master).toBe(false)

      wrapper.unmount()
    })

    it('2.8 空房间列表时应该正常显示', async () => {
      const houseWithEmptyRooms = {
        ...mockSharedHouseDetail,
        rooms: []
      }

      houseApi.getHouseDetail.mockResolvedValue({
        data: houseWithEmptyRooms
      })

      const wrapper = createWrapper()
      await flushPromises()

      // 验证空房间列表
      expect(wrapper.vm.houseData.rooms).toHaveLength(0)

      wrapper.unmount()
    })
  })

  // ============================================
  // 3. 测试房间管理（新增、编辑、删除）
  // ============================================
  describe('3. 房间管理', () => {
    it('3.1 点击编辑房间按钮应该触发编辑事件', async () => {
      houseApi.getHouseDetail.mockResolvedValue({
        data: mockSharedHouseDetail
      })

      const wrapper = createWrapper()
      await flushPromises()

      // 模拟编辑房间
      const room = mockSharedHouseDetail.rooms[0]
      wrapper.vm.handleEditRoom(room)

      // 验证提示信息
      expect(ElMessage.info).toHaveBeenCalledWith('房间编辑功能待实现')

      wrapper.unmount()
    })

    it('3.2 点击删除房间按钮应该触发删除事件', async () => {
      houseApi.getHouseDetail.mockResolvedValue({
        data: mockSharedHouseDetail
      })

      const wrapper = createWrapper()
      await flushPromises()

      // 模拟删除房间
      const room = mockSharedHouseDetail.rooms[0]
      wrapper.vm.handleDeleteRoom(room)

      // 验证提示信息
      expect(ElMessage.info).toHaveBeenCalledWith('房间删除功能待实现')

      wrapper.unmount()
    })

    it('3.3 点击查看房间按钮应该触发查看事件', async () => {
      houseApi.getHouseDetail.mockResolvedValue({
        data: mockSharedHouseDetail
      })

      const wrapper = createWrapper()
      await flushPromises()

      // 模拟查看房间
      const room = mockSharedHouseDetail.rooms[0]
      wrapper.vm.handleViewRoom(room)

      // 验证提示信息
      expect(ElMessage.info).toHaveBeenCalledWith('房间详情功能待实现')

      wrapper.unmount()
    })

    it('3.4 管理员应该有房间编辑权限', async () => {
      houseApi.getHouseDetail.mockResolvedValue({
        data: mockSharedHouseDetail
      })

      const wrapper = createWrapper()
      await flushPromises()

      // 验证权限
      expect(wrapper.vm.hasPermission('edit')).toBe(true)

      wrapper.unmount()
    })

    it('3.5 管理员应该有房间删除权限', async () => {
      houseApi.getHouseDetail.mockResolvedValue({
        data: mockSharedHouseDetail
      })

      const wrapper = createWrapper()
      await flushPromises()

      // 验证权限
      expect(wrapper.vm.hasPermission('delete')).toBe(true)

      wrapper.unmount()
    })

    it('3.6 房东应该有房间编辑权限', async () => {
      const pinia = createPinia()
      setActivePinia(pinia)

      const userStore = useUserStore()
      userStore.setUserInfo({
        id: 2,
        username: 'landlord',
        role: 'landlord',
        user_type: 'landlord'
      })

      houseApi.getHouseDetail.mockResolvedValue({
        data: mockSharedHouseDetail
      })

      const wrapper = mount(HouseDetail, {
        global: {
          plugins: [pinia],
          mocks: {
            $router: mockRouter,
            $route: {
              path: '/houses/2',
              params: { id: '2' },
              query: {}
            }
          },
          stubs: {
            HouseForm: {
              name: 'HouseForm',
              template: '<div class="mock-house-form"><slot /></div>',
              props: ['modelValue', 'isEdit', 'submitLoading']
            },
            RoomList: {
              name: 'RoomList',
              template: '<div class="mock-room-list"><slot /></div>',
              props: ['modelValue', 'showAddButton', 'showEditButton', 'showDeleteButton', 'loading']
            },
            RouterLink: true,
            RouterView: true
          }
        }
      })

      await flushPromises()

      // 验证权限
      expect(wrapper.vm.hasPermission('edit')).toBe(true)

      wrapper.unmount()
    })

    it('3.7 房东不应该有房间删除权限', async () => {
      const pinia = createPinia()
      setActivePinia(pinia)

      const userStore = useUserStore()
      userStore.setUserInfo({
        id: 2,
        username: 'landlord',
        role: 'landlord',
        user_type: 'landlord'
      })

      houseApi.getHouseDetail.mockResolvedValue({
        data: mockSharedHouseDetail
      })

      const wrapper = mount(HouseDetail, {
        global: {
          plugins: [pinia],
          mocks: {
            $router: mockRouter,
            $route: {
              path: '/houses/2',
              params: { id: '2' },
              query: {}
            }
          },
          stubs: {
            HouseForm: {
              name: 'HouseForm',
              template: '<div class="mock-house-form"><slot /></div>',
              props: ['modelValue', 'isEdit', 'submitLoading']
            },
            RoomList: {
              name: 'RoomList',
              template: '<div class="mock-room-list"><slot /></div>',
              props: ['modelValue', 'showAddButton', 'showEditButton', 'showDeleteButton', 'loading']
            },
            RouterLink: true,
            RouterView: true
          }
        }
      })

      await flushPromises()

      // 验证权限
      expect(wrapper.vm.hasPermission('delete')).toBe(false)

      wrapper.unmount()
    })
  })

  // ============================================
  // 4. 测试媒体文件管理
  // ============================================
  describe('4. 媒体文件管理', () => {
    it('4.1 应该正确显示图片列表', async () => {
      houseApi.getHouseDetail.mockResolvedValue({
        data: mockHouseDetail
      })

      const wrapper = createWrapper()
      await flushPromises()

      // 验证图片列表
      expect(wrapper.vm.imageList).toHaveLength(3) // cover_image + 2 images
      expect(wrapper.vm.imageList[0]).toBe('https://example.com/cover1.jpg')
      expect(wrapper.vm.imageList[1]).toBe('https://example.com/image1.jpg')
      expect(wrapper.vm.imageList[2]).toBe('https://example.com/image2.jpg')

      wrapper.unmount()
    })

    it('4.2 应该正确处理封面图片', async () => {
      houseApi.getHouseDetail.mockResolvedValue({
        data: mockHouseDetail
      })

      const wrapper = createWrapper()
      await flushPromises()

      // 验证封面图片在列表第一位
      expect(wrapper.vm.imageList[0]).toBe(mockHouseDetail.cover_image)

      wrapper.unmount()
    })

    it('4.3 应该正确处理重复图片', async () => {
      const houseWithDuplicateImages = {
        ...mockHouseDetail,
        cover_image: 'https://example.com/image1.jpg',
        images: [
          'https://example.com/image1.jpg',
          'https://example.com/image2.jpg',
          'https://example.com/image1.jpg' // 重复
        ]
      }

      houseApi.getHouseDetail.mockResolvedValue({
        data: houseWithDuplicateImages
      })

      const wrapper = createWrapper()
      await flushPromises()

      // 验证去重
      expect(wrapper.vm.imageList).toHaveLength(2)
      expect(wrapper.vm.imageList[0]).toBe('https://example.com/image1.jpg')
      expect(wrapper.vm.imageList[1]).toBe('https://example.com/image2.jpg')

      wrapper.unmount()
    })

    it('4.4 应该正确处理空图片列表', async () => {
      const houseWithNoImages = {
        ...mockHouseDetail,
        cover_image: '',
        images: []
      }

      houseApi.getHouseDetail.mockResolvedValue({
        data: houseWithNoImages
      })

      const wrapper = createWrapper()
      await flushPromises()

      // 验证空图片列表
      expect(wrapper.vm.imageList).toHaveLength(0)

      wrapper.unmount()
    })

    it('4.5 应该正确处理 media 字段（数组格式）', async () => {
      const houseWithMediaArray = {
        ...mockHouseDetail,
        media: [
          'https://example.com/media1.jpg',
          'https://example.com/media2.jpg'
        ]
      }

      houseApi.getHouseDetail.mockResolvedValue({
        data: houseWithMediaArray
      })

      const wrapper = createWrapper()
      await flushPromises()

      // 验证 media 字段被正确处理
      expect(wrapper.vm.imageList).toContain('https://example.com/media1.jpg')
      expect(wrapper.vm.imageList).toContain('https://example.com/media2.jpg')

      wrapper.unmount()
    })

    it('4.6 应该正确处理 media 字段（对象格式）', async () => {
      const houseWithMediaObject = {
        ...mockHouseDetail,
        media: {
          images: [
            'https://example.com/media1.jpg',
            'https://example.com/media2.jpg'
          ]
        }
      }

      houseApi.getHouseDetail.mockResolvedValue({
        data: houseWithMediaObject
      })

      const wrapper = createWrapper()
      await flushPromises()

      // 验证 media 字段被正确处理
      expect(wrapper.vm.imageList).toContain('https://example.com/media1.jpg')
      expect(wrapper.vm.imageList).toContain('https://example.com/media2.jpg')

      wrapper.unmount()
    })

    it('4.7 应该正确处理 media 字段（对象数组格式）', async () => {
      const houseWithMediaObjects = {
        ...mockHouseDetail,
        media: [
          { file_url: 'https://example.com/media1.jpg' },
          { url: 'https://example.com/media2.jpg' },
          { image: 'https://example.com/media3.jpg' }
        ]
      }

      houseApi.getHouseDetail.mockResolvedValue({
        data: houseWithMediaObjects
      })

      const wrapper = createWrapper()
      await flushPromises()

      // 验证 media 字段被正确处理
      expect(wrapper.vm.imageList).toContain('https://example.com/media1.jpg')
      expect(wrapper.vm.imageList).toContain('https://example.com/media2.jpg')
      expect(wrapper.vm.imageList).toContain('https://example.com/media3.jpg')

      wrapper.unmount()
    })

    it('4.8 应该正确处理 media 字段（JSON 字符串格式）', async () => {
      const houseWithMediaString = {
        ...mockHouseDetail,
        media: JSON.stringify([
          'https://example.com/media1.jpg',
          'https://example.com/media2.jpg'
        ])
      }

      houseApi.getHouseDetail.mockResolvedValue({
        data: houseWithMediaString
      })

      const wrapper = createWrapper()
      await flushPromises()

      // 验证 media 字段被正确处理
      expect(wrapper.vm.imageList).toContain('https://example.com/media1.jpg')
      expect(wrapper.vm.imageList).toContain('https://example.com/media2.jpg')

      wrapper.unmount()
    })

    it('4.9 轮播图切换时应该更新当前图片索引', async () => {
      houseApi.getHouseDetail.mockResolvedValue({
        data: mockHouseDetail
      })

      const wrapper = createWrapper()
      await flushPromises()

      // 初始索引为 0
      expect(wrapper.vm.currentImageIndex).toBe(0)

      // 模拟轮播图切换
      wrapper.vm.handleCarouselChange(1)

      // 验证索引更新
      expect(wrapper.vm.currentImageIndex).toBe(1)

      wrapper.unmount()
    })

    it('4.10 点击缩略图应该切换到对应图片', async () => {
      houseApi.getHouseDetail.mockResolvedValue({
        data: mockHouseDetail
      })

      const wrapper = createWrapper()
      await flushPromises()

      // Mock carouselRef
      wrapper.vm.carouselRef = {
        setActiveItem: vi.fn()
      }

      // 初始索引为 0
      expect(wrapper.vm.currentImageIndex).toBe(0)

      // 模拟点击缩略图
      wrapper.vm.handleThumbnailClick(2)

      // 验证索引更新
      expect(wrapper.vm.currentImageIndex).toBe(2)

      wrapper.unmount()
    })

    it('4.11 图片加载错误时应该处理错误', async () => {
      houseApi.getHouseDetail.mockResolvedValue({
        data: mockHouseDetail
      })

      const wrapper = createWrapper()
      await flushPromises()

      // 模拟图片加载错误
      const error = new Error('Image load failed')
      wrapper.vm.handleImageError(error)

      // 验证没有崩溃（console.warn 被调用）
      // 这里只是确保函数不会抛出错误

      wrapper.unmount()
    })

    it('4.12 缩略图加载错误时应该设置默认图片', async () => {
      houseApi.getHouseDetail.mockResolvedValue({
        data: mockHouseDetail
      })

      const wrapper = createWrapper()
      await flushPromises()

      // 模拟缩略图加载错误
      const mockEvent = {
        target: {
          src: 'https://example.com/error.jpg'
        }
      }
      wrapper.vm.handleThumbnailError(mockEvent, 0)

      // 验证设置了默认图片
      expect(mockEvent.target.src).toBe(wrapper.vm.DEFAULT_IMAGE)

      wrapper.unmount()
    })

    it('4.13 图片列表变化时应该重置索引', async () => {
      houseApi.getHouseDetail.mockResolvedValue({
        data: mockHouseDetail
      })

      const wrapper = createWrapper()
      await flushPromises()

      // Mock carouselRef
      wrapper.vm.carouselRef = {
        setActiveItem: vi.fn()
      }

      // 设置索引为超出范围
      wrapper.vm.currentImageIndex = 10

      // 触发图片列表变化（通过更新 houseData）
      wrapper.vm.houseData = {
        ...mockHouseDetail,
        images: ['https://example.com/new1.jpg']
      }
      await flushPromises()

      // 验证索引被重置
      expect(wrapper.vm.currentImageIndex).toBe(0)

      wrapper.unmount()
    })
  })

  // ============================================
  // 5. 测试房源编辑和删除
  // ============================================
  describe('5. 房源编辑和删除', () => {
    it('5.1 点击返回按钮应该返回上一页', async () => {
      houseApi.getHouseDetail.mockResolvedValue({
        data: mockHouseDetail
      })

      const wrapper = createWrapper()
      await flushPromises()

      // 点击返回按钮
      wrapper.vm.handleBack()

      // 验证路由返回
      expect(mockBack).toHaveBeenCalled()

      wrapper.unmount()
    })

    it('5.2 点击编辑按钮应该打开编辑对话框', async () => {
      houseApi.getHouseDetail.mockResolvedValue({
        data: mockHouseDetail
      })

      const wrapper = createWrapper()
      await flushPromises()

      // 点击编辑按钮
      wrapper.vm.handleEdit()

      // 验证对话框状态
      expect(wrapper.vm.dialogVisible).toBe(true)
      expect(wrapper.vm.editData.title).toBe('朝阳区精装两居室')

      wrapper.unmount()
    })

    it('5.3 点击删除按钮应该显示确认对话框', async () => {
      houseApi.getHouseDetail.mockResolvedValue({
        data: mockHouseDetail
      })

      ElMessageBox.confirm.mockResolvedValue('confirm')

      const wrapper = createWrapper()
      await flushPromises()

      // 点击删除按钮
      wrapper.vm.handleDelete()
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

    it('5.4 确认删除应该调用 deleteHouse API', async () => {
      houseApi.getHouseDetail.mockResolvedValue({
        data: mockHouseDetail
      })

      houseApi.deleteHouse.mockResolvedValue({
        success: true
      })

      ElMessageBox.confirm.mockResolvedValue('confirm')

      const wrapper = createWrapper()
      await flushPromises()

      // 确认删除
      await wrapper.vm.handleDelete()
      await flushPromises()

      // 验证 API 被调用
      expect(houseApi.deleteHouse).toHaveBeenCalledWith(1)
      expect(ElMessage.success).toHaveBeenCalledWith('删除成功')
      expect(mockPush).toHaveBeenCalledWith('/houses')

      wrapper.unmount()
    })

    it('5.5 取消删除不应该调用 API', async () => {
      houseApi.getHouseDetail.mockResolvedValue({
        data: mockHouseDetail
      })

      ElMessageBox.confirm.mockRejectedValue(new Error('cancel'))

      const wrapper = createWrapper()
      await flushPromises()

      // 取消删除
      await wrapper.vm.handleDelete()
      await flushPromises()

      // 验证删除 API 没有被调用
      expect(houseApi.deleteHouse).not.toHaveBeenCalled()

      wrapper.unmount()
    })

    it('5.6 删除失败应该显示错误提示', async () => {
      houseApi.getHouseDetail.mockResolvedValue({
        data: mockHouseDetail
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
      await wrapper.vm.handleDelete()
      await flushPromises()

      // 验证错误提示
      expect(ElMessage.error).toHaveBeenCalledWith('该房源有合同关联，无法删除')

      wrapper.unmount()
    })

    it('5.7 提交编辑表单应该调用 editHouse 方法', async () => {
      houseApi.getHouseDetail.mockResolvedValue({
        data: mockHouseDetail
      })

      const wrapper = createWrapper()
      await flushPromises()

      // 打开编辑对话框
      wrapper.vm.handleEdit()
      await flushPromises()

      // 模拟表单提交
      const formData = {
        title: '朝阳区精装两居室（已更新）',
        status: 'available'
      }

      // Mock houseStore.editHouse
      const houseStore = useHouseStore()
      houseStore.editHouse = vi.fn().mockResolvedValue({ id: 1, ...formData })

      await wrapper.vm.handleFormSubmit(formData)
      await flushPromises()

      // 验证成功提示
      expect(ElMessage.success).toHaveBeenCalledWith('编辑成功')
      expect(wrapper.vm.dialogVisible).toBe(false)

      wrapper.unmount()
    })

    it('5.8 编辑失败应该保持对话框打开', async () => {
      houseApi.getHouseDetail.mockResolvedValue({
        data: mockHouseDetail
      })

      const wrapper = createWrapper()
      await flushPromises()

      // 打开编辑对话框
      wrapper.vm.handleEdit()
      await flushPromises()

      // 模拟表单提交失败
      const formData = {
        title: '朝阳区精装两居室',
        status: 'available'
      }

      // Mock houseStore.editHouse 失败
      const houseStore = useHouseStore()
      houseStore.editHouse = vi.fn().mockRejectedValue(new Error('更新失败'))

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
  // 6. 测试权限控制
  // ============================================
  describe('6. 权限控制', () => {
    it('6.1 管理员应该有所有权限', async () => {
      houseApi.getHouseDetail.mockResolvedValue({
        data: mockHouseDetail
      })

      const wrapper = createWrapper()
      await flushPromises()

      // 验证权限
      expect(wrapper.vm.hasPermission('edit')).toBe(true)
      expect(wrapper.vm.hasPermission('delete')).toBe(true)

      wrapper.unmount()
    })

    it('6.2 房东应该有编辑权限', async () => {
      const pinia = createPinia()
      setActivePinia(pinia)

      const userStore = useUserStore()
      userStore.setUserInfo({
        id: 2,
        username: 'landlord',
        role: 'landlord',
        user_type: 'landlord'
      })

      houseApi.getHouseDetail.mockResolvedValue({
        data: mockHouseDetail
      })

      const wrapper = mount(HouseDetail, {
        global: {
          plugins: [pinia],
          mocks: {
            $router: mockRouter,
            $route: {
              path: '/houses/1',
              params: { id: '1' },
              query: {}
            }
          },
          stubs: {
            HouseForm: {
              name: 'HouseForm',
              template: '<div class="mock-house-form"><slot /></div>',
              props: ['modelValue', 'isEdit', 'submitLoading']
            },
            RoomList: {
              name: 'RoomList',
              template: '<div class="mock-room-list"><slot /></div>',
              props: ['modelValue', 'showAddButton', 'showEditButton', 'showDeleteButton', 'loading']
            },
            RouterLink: true,
            RouterView: true
          }
        }
      })

      await flushPromises()

      // 验证权限
      expect(wrapper.vm.hasPermission('edit')).toBe(true)

      wrapper.unmount()
    })

    it('6.3 房东不应该有删除权限', async () => {
      const pinia = createPinia()
      setActivePinia(pinia)

      const userStore = useUserStore()
      userStore.setUserInfo({
        id: 2,
        username: 'landlord',
        role: 'landlord',
        user_type: 'landlord'
      })

      houseApi.getHouseDetail.mockResolvedValue({
        data: mockHouseDetail
      })

      const wrapper = mount(HouseDetail, {
        global: {
          plugins: [pinia],
          mocks: {
            $router: mockRouter,
            $route: {
              path: '/houses/1',
              params: { id: '1' },
              query: {}
            }
          },
          stubs: {
            HouseForm: {
              name: 'HouseForm',
              template: '<div class="mock-house-form"><slot /></div>',
              props: ['modelValue', 'isEdit', 'submitLoading']
            },
            RoomList: {
              name: 'RoomList',
              template: '<div class="mock-room-list"><slot /></div>',
              props: ['modelValue', 'showAddButton', 'showEditButton', 'showDeleteButton', 'loading']
            },
            RouterLink: true,
            RouterView: true
          }
        }
      })

      await flushPromises()

      // 验证权限
      expect(wrapper.vm.hasPermission('delete')).toBe(false)

      wrapper.unmount()
    })
  })
})
