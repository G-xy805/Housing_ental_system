import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import {
  getEmployeeList,
  getEmployeeDetail,
  createEmployee,
  updateEmployee,
  updateEmployeeStatus,
  deleteEmployee,
  resetEmployeePassword,
  batchActionEmployees,
  getEmployeeStats
} from '@/api/employee'

export const useEmployeeStore = defineStore('employee', () => {
  // ==================== 状态 ====================
  // 员工列表状态
  const employeeList = ref([])
  const loading = ref(false)
  const pagination = ref({
    page: 1,
    per_page: 20,
    total: 0
  })

  // 员工详情缓存
  const currentEmployee = ref(null)
  const detailLoading = ref(false)

  // 员工统计状态
  const employeeStats = ref(null)

  // ==================== 计算属性 ====================
  const total = computed(() => pagination.value.total)
  const currentPage = computed(() => pagination.value.page)
  const pageSize = computed(() => pagination.value.per_page)

  // ==================== 方法 ====================

  /**
   * 获取员工列表
   * @param {Object} params 查询参数
   * @returns {Promise}
   */
  async function fetchEmployeeList(params = {}) {
    loading.value = true
    try {
      const res = await getEmployeeList(params)
      employeeList.value = res.data?.items || []
      pagination.value = {
        page: res.data?.page || 1,
        per_page: res.data?.per_page || 20,
        total: res.data?.total || 0
      }
      return res.data
    } catch (error) {
      console.error('获取员工列表失败:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  /**
   * 获取员工详情
   * @param {number} id 员工ID
   * @returns {Promise}
   */
  async function fetchEmployeeDetail(id) {
    detailLoading.value = true
    try {
      const res = await getEmployeeDetail(id)
      currentEmployee.value = res.data
      return res.data
    } catch (error) {
      console.error('获取员工详情失败:', error)
      throw error
    } finally {
      detailLoading.value = false
    }
  }

  /**
   * 添加员工
   * @param {Object} data 员工数据
   * @returns {Promise}
   */
  async function addEmployee(data) {
    try {
      const res = await createEmployee(data)
      // 刷新列表
      await fetchEmployeeList({ page: pagination.value.page, per_page: pagination.value.per_page })
      return res.data
    } catch (error) {
      console.error('创建员工失败:', error)
      throw error
    }
  }

  /**
   * 编辑员工
   * @param {number} id 员工ID
   * @param {Object} data 员工数据
   * @returns {Promise}
   */
  async function editEmployee(id, data) {
    try {
      const res = await updateEmployee(id, data)
      // 更新当前员工
      if (currentEmployee.value?.id === id) {
        currentEmployee.value = res.data
      }
      // 刷新列表
      await fetchEmployeeList({ page: pagination.value.page, per_page: pagination.value.per_page })
      return res.data
    } catch (error) {
      console.error('更新员工失败:', error)
      throw error
    }
  }

  /**
   * 删除员工
   * @param {number} id 员工ID
   * @returns {Promise}
   */
  async function removeEmployee(id) {
    try {
      await deleteEmployee(id)
      // 从列表中移除
      employeeList.value = employeeList.value.filter(employee => employee.id !== id)
      pagination.value.total -= 1
      // 如果当前详情是该员工，清空
      if (currentEmployee.value?.id === id) {
        currentEmployee.value = null
      }
    } catch (error) {
      console.error('删除员工失败:', error)
      throw error
    }
  }

  /**
   * 更新员工状态
   * @param {number} id 员工ID
   * @param {string} status 状态 (active-在职/resigned-离职/disabled-禁用)
   * @returns {Promise}
   */
  async function updateEmployeeStatusById(id, status) {
    try {
      const res = await updateEmployeeStatus(id, status)
      // 更新当前员工状态
      if (currentEmployee.value?.id === id) {
        currentEmployee.value.status = status
      }
      // 更新列表中的员工状态
      const index = employeeList.value.findIndex(emp => emp.id === id)
      if (index !== -1) {
        employeeList.value[index].status = status
      }
      return res.data
    } catch (error) {
      console.error('更新员工状态失败:', error)
      throw error
    }
  }

  /**
   * 重置员工密码
   * @param {number} id 员工ID
   * @param {string} newPassword 新密码
   * @returns {Promise}
   */
  async function resetPassword(id, newPassword) {
    try {
      const res = await resetEmployeePassword(id, newPassword)
      return res.data
    } catch (error) {
      console.error('重置员工密码失败:', error)
      throw error
    }
  }

  /**
   * 批量操作员工
   * @param {Object} data { user_ids, action }
   * @returns {Promise}
   */
  async function batchAction(data) {
    try {
      const res = await batchActionEmployees(data)
      // 刷新列表
      await fetchEmployeeList({ page: pagination.value.page, per_page: pagination.value.per_page })
      return res.data
    } catch (error) {
      console.error('批量操作员工失败:', error)
      throw error
    }
  }

  /**
   * 获取员工统计信息
   * @returns {Promise}
   */
  async function fetchEmployeeStats() {
    try {
      const res = await getEmployeeStats()
      employeeStats.value = res.data
      return res.data
    } catch (error) {
      console.error('获取员工统计信息失败:', error)
      throw error
    }
  }

  /**
   * 设置当前员工
   * @param {Object} employee 员工对象
   */
  function setCurrentEmployee(employee) {
    currentEmployee.value = employee
  }

  /**
   * 清空当前员工
   */
  function clearCurrentEmployee() {
    currentEmployee.value = null
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
    employeeList.value = []
    currentEmployee.value = null
    employeeStats.value = null
    loading.value = false
    detailLoading.value = false
    resetPagination()
  }

  return {
    // 状态
    employeeList,
    loading,
    pagination,
    currentEmployee,
    detailLoading,
    employeeStats,
    // 计算属性
    total,
    currentPage,
    pageSize,
    // 方法
    fetchEmployeeList,
    fetchEmployeeDetail,
    addEmployee,
    editEmployee,
    removeEmployee,
    updateEmployeeStatusById,
    resetPassword,
    batchAction,
    fetchEmployeeStats,
    setCurrentEmployee,
    clearCurrentEmployee,
    resetPagination,
    resetAll
  }
})
