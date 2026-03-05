import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import {
  getLandlordList,
  getLandlordDetail,
  createLandlord,
  updateLandlord,
  deleteLandlord,
  getLandlordHouses,
  getLandlordContracts
} from '@/api/landlord'

export const useLandlordStore = defineStore('landlord', () => {
  // 房东列表状态
  const landlordList = ref([])
  const loading = ref(false)
  const pagination = ref({
    page: 1,
    per_page: 20,
    total: 0
  })

  // 房东详情缓存
  const currentLandlord = ref(null)
  const detailLoading = ref(false)

  // 房东关联数据状态
  const landlordHouses = ref([])
  const landlordContracts = ref([])
  const housesLoading = ref(false)
  const contractsLoading = ref(false)
  const housesPagination = ref({
    page: 1,
    per_page: 20,
    total: 0
  })
  const contractsPagination = ref({
    page: 1,
    per_page: 20,
    total: 0
  })

  // 计算属性
  const total = computed(() => pagination.value.total)
  const currentPage = computed(() => pagination.value.page)
  const pageSize = computed(() => pagination.value.per_page)

  /**
   * 获取房东列表
   * @param {Object} params 查询参数
   * @param {number} [params.page] 页码
   * @param {number} [params.page_size] 每页数量
   * @param {string} [params.search] 搜索关键词（姓名、手机号）
   * @param {string} [params.status] 筛选状态（active、inactive）
   * @returns {Promise}
   */
  async function fetchLandlordList(params = {}) {
    loading.value = true
    try {
      const res = await getLandlordList(params)
      landlordList.value = res.data?.items || []
      pagination.value = {
        page: res.data?.page || 1,
        per_page: res.data?.page_size || 20,
        total: res.data?.total || 0
      }
      return res.data
    } catch (error) {
      console.error('获取房东列表失败:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  /**
   * 获取房东详情
   * @param {number} id 房东 ID
   * @returns {Promise}
   */
  async function fetchLandlordDetail(id) {
    detailLoading.value = true
    try {
      const res = await getLandlordDetail(id)
      currentLandlord.value = res.data
      return res.data
    } catch (error) {
      console.error('获取房东详情失败:', error)
      throw error
    } finally {
      detailLoading.value = false
    }
  }

  /**
   * 添加房东
   * @param {Object} data 房东数据
   * @param {string} data.name 房东姓名
   * @param {string} data.phone 手机号
   * @param {string} [data.email] 邮箱
   * @param {string} [data.id_card] 身份证号
   * @param {string} [data.remark] 备注
   * @returns {Promise}
   */
  async function addLandlord(data) {
    try {
      const res = await createLandlord(data)
      // 刷新列表
      await fetchLandlordList({ page: pagination.value.page, page_size: pagination.value.per_page })
      return res.data
    } catch (error) {
      console.error('创建房东失败:', error)
      throw error
    }
  }

  /**
   * 编辑房东
   * @param {number} id 房东 ID
   * @param {Object} data 房东数据
   * @param {string} [data.name] 房东姓名
   * @param {string} [data.phone] 手机号
   * @param {string} [data.email] 邮箱
   * @param {string} [data.id_card] 身份证号
   * @param {string} [data.remark] 备注
   * @param {string} [data.status] 状态（active、inactive）
   * @returns {Promise}
   */
  async function editLandlord(id, data) {
    try {
      const res = await updateLandlord(id, data)
      // 更新当前房东详情
      if (currentLandlord.value?.id === id) {
        currentLandlord.value = res.data
      }
      // 更新列表中的数据
      const index = landlordList.value.findIndex(item => item.id === id)
      if (index !== -1) {
        landlordList.value[index] = { ...landlordList.value[index], ...res.data }
      }
      return res.data
    } catch (error) {
      console.error('更新房东失败:', error)
      throw error
    }
  }

  /**
   * 删除房东
   * @param {number} id 房东 ID
   * @returns {Promise}
   */
  async function removeLandlord(id) {
    try {
      await deleteLandlord(id)
      // 从列表中移除
      landlordList.value = landlordList.value.filter(item => item.id !== id)
      pagination.value.total -= 1
      // 如果当前详情是该房东，清空
      if (currentLandlord.value?.id === id) {
        currentLandlord.value = null
      }
    } catch (error) {
      console.error('删除房东失败:', error)
      throw error
    }
  }

  /**
   * 获取房东房源
   * @param {number} landlordId 房东 ID
   * @param {Object} params 查询参数
   * @param {number} [params.page] 页码
   * @param {number} [params.page_size] 每页数量
   * @param {string} [params.status] 房源状态筛选
   * @returns {Promise}
   */
  async function fetchLandlordHouses(landlordId, params = {}) {
    housesLoading.value = true
    try {
      const res = await getLandlordHouses(landlordId, params)
      landlordHouses.value = res.data?.items || []
      housesPagination.value = {
        page: res.data?.page || 1,
        per_page: res.data?.page_size || 20,
        total: res.data?.total || 0
      }
      return res.data
    } catch (error) {
      console.error('获取房东房源失败:', error)
      throw error
    } finally {
      housesLoading.value = false
    }
  }

  /**
   * 获取房东合同
   * @param {number} landlordId 房东 ID
   * @param {Object} params 查询参数
   * @param {number} [params.page] 页码
   * @param {number} [params.page_size] 每页数量
   * @param {string} [params.status] 合同状态筛选
   * @returns {Promise}
   */
  async function fetchLandlordContracts(landlordId, params = {}) {
    contractsLoading.value = true
    try {
      const res = await getLandlordContracts(landlordId, params)
      landlordContracts.value = res.data?.items || []
      contractsPagination.value = {
        page: res.data?.page || 1,
        per_page: res.data?.page_size || 20,
        total: res.data?.total || 0
      }
      return res.data
    } catch (error) {
      console.error('获取房东合同失败:', error)
      throw error
    } finally {
      contractsLoading.value = false
    }
  }

  /**
   * 设置当前房东
   * @param {Object} landlord 房东对象
   */
  function setCurrentLandlord(landlord) {
    currentLandlord.value = landlord
  }

  /**
   * 清空当前房东
   */
  function clearCurrentLandlord() {
    currentLandlord.value = null
    landlordHouses.value = []
    landlordContracts.value = []
  }

  /**
   * 重置分页
   */
  function resetPagination() {
    pagination.value = {
      page: 1,
      per_page: 20,
      total: 0
    }
  }

  /**
   * 清空房东关联数据
   */
  function clearLandlordRelations() {
    landlordHouses.value = []
    landlordContracts.value = []
    housesPagination.value = {
      page: 1,
      per_page: 20,
      total: 0
    }
    contractsPagination.value = {
      page: 1,
      per_page: 20,
      total: 0
    }
  }

  return {
    // 房东列表状态
    landlordList,
    loading,
    pagination,
    // 房东详情缓存
    currentLandlord,
    detailLoading,
    // 房东关联数据状态
    landlordHouses,
    landlordContracts,
    housesLoading,
    contractsLoading,
    housesPagination,
    contractsPagination,
    // 计算属性
    total,
    currentPage,
    pageSize,
    // 方法
    fetchLandlordList,
    fetchLandlordDetail,
    addLandlord,
    editLandlord,
    removeLandlord,
    fetchLandlordHouses,
    fetchLandlordContracts,
    setCurrentLandlord,
    clearCurrentLandlord,
    resetPagination,
    clearLandlordRelations
  }
})
