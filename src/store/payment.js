import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import {
  getPaymentList,
  getPaymentDetail,
  createPayment,
  updatePayment,
  deletePayment,
  verifyPayment,
  getOverduePayments,
  getPaymentStats,
  updateLateFees
} from '@/api/payment'

export const usePaymentStore = defineStore('payment', () => {
  // ==================== 状态 ====================
  // 支付记录列表
  const paymentList = ref([])
  // 当前支付详情
  const currentPayment = ref(null)
  // 加载状态
  const loading = ref(false)
  const detailLoading = ref(false)
  // 分页信息
  const pagination = ref({
    page: 1,
    per_page: 20,
    total: 0
  })

  // 支付统计数据
  const paymentStats = ref({
    total_amount: 0,           // 总金额
    paid_amount: 0,            // 已支付金额
    pending_amount: 0,         // 待支付金额
    overdue_amount: 0,         // 逾期金额
    total_count: 0,            // 总记录数
    paid_count: 0,             // 已支付数量
    pending_count: 0,          // 待支付数量
    overdue_count: 0           // 逾期数量
  })

  // 逾期支付列表
  const overduePayments = ref([])
  const overdueLoading = ref(false)

  // ==================== 计算属性 ====================
  const total = computed(() => pagination.value.total)
  const currentPage = computed(() => pagination.value.page)
  const pageSize = computed(() => pagination.value.per_page)

  // ==================== 方法 ====================
  /**
   * 获取支付记录列表
   * @param {Object} params 查询参数
   * @returns {Promise}
   */
  async function fetchPaymentList(params = {}) {
    loading.value = true
    try {
      const res = await getPaymentList(params)
      paymentList.value = res.data?.items || []
      pagination.value = {
        page: res.data?.page || 1,
        per_page: res.data?.per_page || 20,
        total: res.data?.total || 0
      }
      return res.data
    } catch (error) {
      console.error('获取支付记录列表失败:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  /**
   * 获取支付详情
   * @param {number} id 支付记录 ID
   * @returns {Promise}
   */
  async function fetchPaymentDetail(id) {
    detailLoading.value = true
    try {
      const res = await getPaymentDetail(id)
      currentPayment.value = res.data
      return res.data
    } catch (error) {
      console.error('获取支付详情失败:', error)
      throw error
    } finally {
      detailLoading.value = false
    }
  }

  /**
   * 添加支付记录
   * @param {Object} data 支付记录数据
   * @returns {Promise}
   */
  async function addPayment(data) {
    try {
      const res = await createPayment(data)
      // 刷新列表
      await fetchPaymentList({ page: pagination.value.page, per_page: pagination.value.per_page })
      return res.data
    } catch (error) {
      console.error('创建支付记录失败:', error)
      throw error
    }
  }

  /**
   * 编辑支付记录
   * @param {number} id 支付记录 ID
   * @param {Object} data 支付记录数据
   * @returns {Promise}
   */
  async function editPayment(id, data) {
    try {
      const res = await updatePayment(id, data)
      // 更新当前支付记录
      if (currentPayment.value?.id === id) {
        currentPayment.value = res.data
      }
      // 刷新列表
      await fetchPaymentList({ page: pagination.value.page, per_page: pagination.value.per_page })
      return res.data
    } catch (error) {
      console.error('更新支付记录失败:', error)
      throw error
    }
  }

  /**
   * 删除支付记录
   * @param {number} id 支付记录 ID
   * @returns {Promise}
   */
  async function removePayment(id) {
    try {
      await deletePayment(id)
      // 从列表中移除
      paymentList.value = paymentList.value.filter(payment => payment.id !== id)
      pagination.value.total -= 1
      // 如果当前详情是该支付记录，清空
      if (currentPayment.value?.id === id) {
        currentPayment.value = null
      }
    } catch (error) {
      console.error('删除支付记录失败:', error)
      throw error
    }
  }

  /**
   * 确认支付
   * @param {number} id 支付记录 ID
   * @param {Object} data 确认数据（paid_amount, payment_date, payment_method等）
   * @returns {Promise}
   */
  async function confirmPayment(id, data) {
    try {
      const res = await verifyPayment(id, data)
      // 更新当前支付记录
      if (currentPayment.value?.id === id) {
        currentPayment.value = res.data
      }
      // 更新列表中的对应记录
      const index = paymentList.value.findIndex(p => p.id === id)
      if (index !== -1) {
        paymentList.value[index] = res.data
      }
      // 刷新统计数据
      await fetchPaymentStats()
      return res.data
    } catch (error) {
      console.error('确认支付失败:', error)
      throw error
    }
  }

  /**
   * 获取逾期支付列表
   * @param {Object} params 查询参数
   * @returns {Promise}
   */
  async function fetchOverduePayments(params = {}) {
    overdueLoading.value = true
    try {
      const res = await getOverduePayments(params)
      overduePayments.value = res.data?.items || []
      return res.data
    } catch (error) {
      console.error('获取逾期支付列表失败:', error)
      throw error
    } finally {
      overdueLoading.value = false
    }
  }

  /**
   * 获取支付统计
   * @param {Object} params 查询参数
   * @returns {Promise}
   */
  async function fetchPaymentStats(params = {}) {
    try {
      const res = await getPaymentStats(params)
      paymentStats.value = res.data || {
        total_amount: 0,
        paid_amount: 0,
        pending_amount: 0,
        overdue_amount: 0,
        total_count: 0,
        paid_count: 0,
        pending_count: 0,
        overdue_count: 0
      }
      return res.data
    } catch (error) {
      console.error('获取支付统计失败:', error)
      throw error
    }
  }

  /**
   * 更新滞纳金
   * @returns {Promise}
   */
  async function updateLateFeesBatch() {
    try {
      const res = await updateLateFees()
      // 刷新逾期列表和统计数据
      await Promise.all([
        fetchOverduePayments(),
        fetchPaymentStats()
      ])
      return res.data
    } catch (error) {
      console.error('更新滞纳金失败:', error)
      throw error
    }
  }

  /**
   * 设置当前支付记录
   * @param {Object} payment 支付记录
   */
  function setCurrentPayment(payment) {
    currentPayment.value = payment
  }

  /**
   * 清空当前支付记录
   */
  function clearCurrentPayment() {
    currentPayment.value = null
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
   * 重置统计数据
   */
  function resetStats() {
    paymentStats.value = {
      total_amount: 0,
      paid_amount: 0,
      pending_amount: 0,
      overdue_amount: 0,
      total_count: 0,
      paid_count: 0,
      pending_count: 0,
      overdue_count: 0
    }
  }

  /**
   * 清空逾期支付列表
   */
  function clearOverduePayments() {
    overduePayments.value = []
  }

  return {
    // 状态
    paymentList,
    currentPayment,
    loading,
    detailLoading,
    pagination,
    paymentStats,
    overduePayments,
    overdueLoading,
    // 计算属性
    total,
    currentPage,
    pageSize,
    // 方法
    fetchPaymentList,
    fetchPaymentDetail,
    addPayment,
    editPayment,
    removePayment,
    confirmPayment,
    fetchOverduePayments,
    fetchPaymentStats,
    updateLateFeesBatch,
    setCurrentPayment,
    clearCurrentPayment,
    resetPagination,
    resetStats,
    clearOverduePayments
  }
})
