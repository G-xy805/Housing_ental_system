import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import {
  getContractList,
  getContractDetail,
  createContract,
  updateContract,
  deleteContract,
  activateContract,
  terminateContract,
  renewContract
} from '@/api/contract'
import {
  getLandlordContractList,
  getLandlordContractDetail,
  getExpiringContracts
} from '@/api/landlordContract'

export const useContractStore = defineStore('contract', () => {
  // ==================== 租赁合同状态 ====================
  const contractList = ref([])
  const currentContract = ref(null)
  const loading = ref(false)
  const detailLoading = ref(false)
  const pagination = ref({
    page: 1,
    per_page: 20,
    total: 0
  })

  // ==================== 承包合同状态 ====================
  const landlordContractList = ref([])
  const currentLandlordContract = ref(null)
  const landlordContractLoading = ref(false)
  const landlordContractDetailLoading = ref(false)
  const landlordContractPagination = ref({
    page: 1,
    per_page: 20,
    total: 0
  })

  // ==================== 合同到期提醒状态 ====================
  const expiringContracts = ref([])
  const expiringLoading = ref(false)

  // ==================== 计算属性 ====================
  // 租赁合同计算属性
  const total = computed(() => pagination.value.total)
  const currentPage = computed(() => pagination.value.page)
  const pageSize = computed(() => pagination.value.per_page)

  // 承包合同计算属性
  const landlordTotal = computed(() => landlordContractPagination.value.total)
  const landlordCurrentPage = computed(() => landlordContractPagination.value.page)
  const landlordPageSize = computed(() => landlordContractPagination.value.per_page)

  // ==================== 租赁合同方法 ====================
  /**
   * 获取租赁合同列表
   * @param {Object} params 查询参数
   */
  async function fetchContractList(params = {}) {
    loading.value = true
    try {
      const res = await getContractList(params)
      contractList.value = res.data?.items || []
      pagination.value = {
        page: res.data?.page || 1,
        per_page: res.data?.per_page || 20,
        total: res.data?.total || 0
      }
      return res.data
    } catch (error) {
      console.error('获取租赁合同列表失败:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  /**
   * 获取租赁合同详情
   * @param {number} id 合同 ID
   */
  async function fetchContractDetail(id) {
    detailLoading.value = true
    try {
      const res = await getContractDetail(id)
      currentContract.value = res.data
      return res.data
    } catch (error) {
      console.error('获取租赁合同详情失败:', error)
      throw error
    } finally {
      detailLoading.value = false
    }
  }

  /**
   * 添加租赁合同
   * @param {Object} data 合同数据
   */
  async function addContract(data) {
    try {
      const res = await createContract(data)
      await fetchContractList({ page: pagination.value.page, per_page: pagination.value.per_page })
      return res.data
    } catch (error) {
      console.error('创建租赁合同失败:', error)
      throw error
    }
  }

  /**
   * 编辑租赁合同
   * @param {number} id 合同 ID
   * @param {Object} data 合同数据
   */
  async function editContract(id, data) {
    try {
      const res = await updateContract(id, data)
      // 更新当前合同
      if (currentContract.value?.id === id) {
        currentContract.value = res.data
      }
      // 刷新列表
      await fetchContractList({ page: pagination.value.page, per_page: pagination.value.per_page })
      return res.data
    } catch (error) {
      console.error('更新租赁合同失败:', error)
      throw error
    }
  }

  /**
   * 删除租赁合同
   * @param {number} id 合同 ID
   */
  async function removeContract(id) {
    try {
      await deleteContract(id)
      // 从列表中移除
      contractList.value = contractList.value.filter(contract => contract.id !== id)
      pagination.value.total -= 1
      // 如果当前详情是该合同，清空
      if (currentContract.value?.id === id) {
        currentContract.value = null
      }
    } catch (error) {
      console.error('删除租赁合同失败:', error)
      throw error
    }
  }

  /**
   * 激活合同
   * @param {number} id 合同 ID
   */
  async function activateContractAction(id) {
    try {
      const res = await activateContract(id)
      // 更新当前合同
      if (currentContract.value?.id === id) {
        currentContract.value = res.data
      }
      // 更新列表中的合同状态
      const index = contractList.value.findIndex(c => c.id === id)
      if (index !== -1) {
        contractList.value[index] = res.data
      }
      return res.data
    } catch (error) {
      console.error('激活合同失败:', error)
      throw error
    }
  }

  /**
   * 终止合同
   * @param {number} id 合同 ID
   * @param {Object} data 终止数据
   */
  async function terminateContractAction(id, data) {
    try {
      const res = await terminateContract(id, data)
      // 更新当前合同
      if (currentContract.value?.id === id) {
        currentContract.value = res.data
      }
      // 更新列表中的合同状态
      const index = contractList.value.findIndex(c => c.id === id)
      if (index !== -1) {
        contractList.value[index] = res.data
      }
      return res.data
    } catch (error) {
      console.error('终止合同失败:', error)
      throw error
    }
  }

  /**
   * 续签合同
   * @param {number} id 合同 ID
   * @param {Object} data 续签数据
   */
  async function renewContractAction(id, data) {
    try {
      const res = await renewContract(id, data)
      // 更新当前合同
      if (currentContract.value?.id === id) {
        currentContract.value = res.data
      }
      // 更新列表中的合同状态
      const index = contractList.value.findIndex(c => c.id === id)
      if (index !== -1) {
        contractList.value[index] = res.data
      }
      return res.data
    } catch (error) {
      console.error('续签合同失败:', error)
      throw error
    }
  }

  // ==================== 承包合同方法 ====================
  /**
   * 获取承包合同列表
   * @param {Object} params 查询参数
   */
  async function fetchLandlordContractList(params = {}) {
    landlordContractLoading.value = true
    try {
      const res = await getLandlordContractList(params)
      landlordContractList.value = res.data?.items || []
      landlordContractPagination.value = {
        page: res.data?.page || 1,
        per_page: res.data?.per_page || 20,
        total: res.data?.total || 0
      }
      return res.data
    } catch (error) {
      console.error('获取承包合同列表失败:', error)
      throw error
    } finally {
      landlordContractLoading.value = false
    }
  }

  /**
   * 获取承包合同详情
   * @param {number} id 合同 ID
   */
  async function fetchLandlordContractDetail(id) {
    landlordContractDetailLoading.value = true
    try {
      const res = await getLandlordContractDetail(id)
      currentLandlordContract.value = res.data
      return res.data
    } catch (error) {
      console.error('获取承包合同详情失败:', error)
      throw error
    } finally {
      landlordContractDetailLoading.value = false
    }
  }

  /**
   * 获取即将到期合同
   * @param {Object} params 查询参数
   */
  async function fetchExpiringContracts(params = {}) {
    expiringLoading.value = true
    try {
      const res = await getExpiringContracts(params)
      expiringContracts.value = res.data?.items || []
      return res.data
    } catch (error) {
      console.error('获取即将到期合同失败:', error)
      throw error
    } finally {
      expiringLoading.value = false
    }
  }

  // ==================== 辅助方法 ====================
  /**
   * 设置当前合同
   * @param {Object} contract 合同对象
   */
  function setCurrentContract(contract) {
    currentContract.value = contract
  }

  /**
   * 清空当前合同
   */
  function clearCurrentContract() {
    currentContract.value = null
  }

  /**
   * 设置当前承包合同
   * @param {Object} contract 承包合同对象
   */
  function setCurrentLandlordContract(contract) {
    currentLandlordContract.value = contract
  }

  /**
   * 清空当前承包合同
   */
  function clearCurrentLandlordContract() {
    currentLandlordContract.value = null
  }

  /**
   * 重置租赁合同分页
   */
  function resetPagination() {
    pagination.value = {
      page: 1,
      per_page: 20,
      total: 0
    }
  }

  /**
   * 重置承包合同分页
   */
  function resetLandlordContractPagination() {
    landlordContractPagination.value = {
      page: 1,
      per_page: 20,
      total: 0
    }
  }

  /**
   * 清空即将到期合同
   */
  function clearExpiringContracts() {
    expiringContracts.value = []
  }

  return {
    // ==================== 租赁合同状态 ====================
    contractList,
    currentContract,
    loading,
    detailLoading,
    pagination,
    // ==================== 承包合同状态 ====================
    landlordContractList,
    currentLandlordContract,
    landlordContractLoading,
    landlordContractDetailLoading,
    landlordContractPagination,
    // ==================== 合同到期提醒状态 ====================
    expiringContracts,
    expiringLoading,
    // ==================== 计算属性 ====================
    total,
    currentPage,
    pageSize,
    landlordTotal,
    landlordCurrentPage,
    landlordPageSize,
    // ==================== 租赁合同方法 ====================
    fetchContractList,
    fetchContractDetail,
    addContract,
    editContract,
    removeContract,
    activateContract: activateContractAction,
    terminateContract: terminateContractAction,
    renewContract: renewContractAction,
    // ==================== 承包合同方法 ====================
    fetchLandlordContractList,
    fetchLandlordContractDetail,
    fetchExpiringContracts,
    // ==================== 辅助方法 ====================
    setCurrentContract,
    clearCurrentContract,
    setCurrentLandlordContract,
    clearCurrentLandlordContract,
    resetPagination,
    resetLandlordContractPagination,
    clearExpiringContracts
  }
})
