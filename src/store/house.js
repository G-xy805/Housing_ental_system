import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import {
  getHouseList,
  getHouseDetail,
  createHouse,
  updateHouse,
  deleteHouse,
  uploadHouseImage
} from '@/api/house'

export const useHouseStore = defineStore('house', () => {
  // 状态
  const houseList = ref([])
  const currentHouse = ref(null)
  const loading = ref(false)
  const detailLoading = ref(false)
  const pagination = ref({
    page: 1,
    per_page: 20,
    total: 0
  })

  // 计算属性
  const total = computed(() => pagination.value.total)
  const currentPage = computed(() => pagination.value.page)
  const pageSize = computed(() => pagination.value.per_page)

  // 方法
  async function fetchHouseList(params = {}) {
    loading.value = true
    try {
      const res = await getHouseList(params)
      houseList.value = res.data?.items || []
      pagination.value = {
        page: res.data?.page || 1,
        per_page: res.data?.per_page || 20,
        total: res.data?.total || 0
      }
      return res.data
    } catch (error) {
      console.error('获取房源列表失败:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  async function fetchHouseDetail(id) {
    detailLoading.value = true
    try {
      const res = await getHouseDetail(id)
      currentHouse.value = res.data
      return res.data
    } catch (error) {
      console.error('获取房源详情失败:', error)
      throw error
    } finally {
      detailLoading.value = false
    }
  }

  async function addHouse(data) {
    try {
      const res = await createHouse(data)
      await fetchHouseList({ page: pagination.value.page, per_page: pagination.value.per_page })
      return res.data
    } catch (error) {
      console.error('创建房源失败:', error)
      throw error
    }
  }

  async function editHouse(id, data) {
    try {
      const res = await updateHouse(id, data)
      // 更新当前房源
      if (currentHouse.value?.id === id) {
        currentHouse.value = res.data
      }
      // 刷新列表
      await fetchHouseList({ page: pagination.value.page, per_page: pagination.value.per_page })
      return res.data
    } catch (error) {
      console.error('更新房源失败:', error)
      throw error
    }
  }

  async function removeHouse(id) {
    try {
      await deleteHouse(id)
      // 从列表中移除
      houseList.value = houseList.value.filter(house => house.id !== id)
      pagination.value.total -= 1
      // 如果当前详情是该房源，清空
      if (currentHouse.value?.id === id) {
        currentHouse.value = null
      }
    } catch (error) {
      console.error('删除房源失败:', error)
      throw error
    }
  }

  async function uploadImage(formData, houseId) {
    try {
      const res = await uploadHouseImage(formData, houseId)
      return res.data
    } catch (error) {
      console.error('上传图片失败:', error)
      throw error
    }
  }

  function setCurrentHouse(house) {
    currentHouse.value = house
  }

  function clearCurrentHouse() {
    currentHouse.value = null
  }

  function resetPagination() {
    pagination.value = {
      page: 1,
      per_page: 20,
      total: 0
    }
  }

  return {
    // 状态
    houseList,
    currentHouse,
    loading,
    detailLoading,
    pagination,
    // 计算属性
    total,
    currentPage,
    pageSize,
    // 方法
    fetchHouseList,
    fetchHouseDetail,
    addHouse,
    editHouse,
    removeHouse,
    uploadImage,
    setCurrentHouse,
    clearCurrentHouse,
    resetPagination
  }
})
