import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import {
  getTenantList,
  getTenantDetail,
  createTenant,
  updateTenant,
  deleteTenant,
  uploadTenantPhoto
} from '@/api/tenant'

export const useTenantStore = defineStore('tenant', () => {
  // 状态
  const tenantList = ref([])
  const currentTenant = ref(null)
  const loading = ref(false)
  const detailLoading = ref(false)
  const pagination = ref({
    page: 1,
    per_page: 20,
    total: 0
  })
  const searchParams = ref({})

  // 计算属性
  const total = computed(() => pagination.value.total)
  const currentPage = computed(() => pagination.value.page)
  const pageSize = computed(() => pagination.value.per_page)

  // 方法
  /**
   * 获取租客列表
   * @param {Object} params 查询参数
   * @returns {Promise}
   */
  async function fetchTenantList(params = {}) {
    loading.value = true
    try {
      // 合并搜索参数
      const queryParams = { ...searchParams.value, ...params }
      const res = await getTenantList(queryParams)
      tenantList.value = res.data?.items || []
      pagination.value = {
        page: res.data?.page || 1,
        per_page: res.data?.per_page || 20,
        total: res.data?.total || 0
      }
      return res.data
    } catch (error) {
      console.error('获取租客列表失败:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  /**
   * 获取租客详情
   * @param {number} id 租客 ID
   * @returns {Promise}
   */
  async function fetchTenantDetail(id) {
    detailLoading.value = true
    try {
      const res = await getTenantDetail(id)
      currentTenant.value = res.data
      return res.data
    } catch (error) {
      console.error('获取租客详情失败:', error)
      throw error
    } finally {
      detailLoading.value = false
    }
  }

  /**
   * 添加租客
   * @param {Object} data 租客数据
   * @returns {Promise}
   */
  async function addTenant(data) {
    try {
      const res = await createTenant(data)
      // 刷新列表
      await fetchTenantList({ page: pagination.value.page, per_page: pagination.value.per_page })
      return res.data
    } catch (error) {
      console.error('创建租客失败:', error)
      throw error
    }
  }

  /**
   * 编辑租客
   * @param {number} id 租客 ID
   * @param {Object} data 租客数据
   * @returns {Promise}
   */
  async function editTenant(id, data) {
    try {
      const res = await updateTenant(id, data)
      // 更新当前租客
      if (currentTenant.value?.id === id) {
        currentTenant.value = res.data
      }
      // 刷新列表
      await fetchTenantList({ page: pagination.value.page, per_page: pagination.value.per_page })
      return res.data
    } catch (error) {
      console.error('更新租客失败:', error)
      throw error
    }
  }

  /**
   * 删除租客
   * @param {number} id 租客 ID
   * @returns {Promise}
   */
  async function removeTenant(id) {
    try {
      await deleteTenant(id)
      // 从列表中移除
      tenantList.value = tenantList.value.filter(tenant => tenant.id !== id)
      pagination.value.total -= 1
      // 如果当前详情是该租客，清空
      if (currentTenant.value?.id === id) {
        currentTenant.value = null
      }
    } catch (error) {
      console.error('删除租客失败:', error)
      throw error
    }
  }

  /**
   * 搜索租客
   * @param {Object} params 搜索参数
   * @returns {Promise}
   */
  async function searchTenants(params = {}) {
    // 保存搜索参数
    searchParams.value = params
    // 重置到第一页
    pagination.value.page = 1
    // 执行搜索
    return await fetchTenantList({ page: 1, per_page: pagination.value.per_page })
  }

  /**
   * 上传租客证件照
   * @param {FormData} formData 图片文件
   * @returns {Promise}
   */
  async function uploadPhoto(formData) {
    try {
      const res = await uploadTenantPhoto(formData)
      return res.data
    } catch (error) {
      console.error('上传证件照失败:', error)
      throw error
    }
  }

  /**
   * 设置当前租客
   * @param {Object} tenant 租客对象
   */
  function setCurrentTenant(tenant) {
    currentTenant.value = tenant
  }

  /**
   * 清空当前租客
   */
  function clearCurrentTenant() {
    currentTenant.value = null
  }

  /**
   * 清空搜索参数
   */
  function clearSearchParams() {
    searchParams.value = {}
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
   * 重置所有状态
   */
  function resetAll() {
    tenantList.value = []
    currentTenant.value = null
    searchParams.value = {}
    resetPagination()
  }

  return {
    // 状态
    tenantList,
    currentTenant,
    loading,
    detailLoading,
    pagination,
    searchParams,
    // 计算属性
    total,
    currentPage,
    pageSize,
    // 方法
    fetchTenantList,
    fetchTenantDetail,
    addTenant,
    editTenant,
    removeTenant,
    searchTenants,
    uploadPhoto,
    setCurrentTenant,
    clearCurrentTenant,
    clearSearchParams,
    resetPagination,
    resetAll
  }
})
