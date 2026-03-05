import { defineStore } from 'pinia'
import { ref } from 'vue'
import {
  getOverviewStatistics,
  getHouseStatistics,
  getIncomeStatistics,
  getTenantStatistics,
  getContractStatistics,
  exportExcel as exportExcelApi,
  exportPdf as exportPdfApi
} from '@/api/statistics'

export const useStatisticsStore = defineStore('statistics', () => {
  // 概览统计数据状态
  const overviewData = ref(null)
  const loading = ref(false)

  // 各模块统计状态
  const houseStats = ref(null)
  const incomeStats = ref(null)
  const tenantStats = ref(null)
  const contractStats = ref(null)

  // 各模块加载状态
  const houseStatsLoading = ref(false)
  const incomeStatsLoading = ref(false)
  const tenantStatsLoading = ref(false)
  const contractStatsLoading = ref(false)

  /**
   * 获取概览统计
   * @param {Object} params 查询参数
   * @returns {Promise}
   */
  async function fetchOverview(params = {}) {
    loading.value = true
    try {
      const res = await getOverviewStatistics(params)
      overviewData.value = res.data
      return res.data
    } catch (error) {
      console.error('获取概览统计失败:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  /**
   * 获取房源统计
   * @param {Object} params 查询参数
   * @returns {Promise}
   */
  async function fetchHouseStats(params = {}) {
    houseStatsLoading.value = true
    try {
      const res = await getHouseStatistics(params)
      houseStats.value = res.data
      return res.data
    } catch (error) {
      console.error('获取房源统计失败:', error)
      throw error
    } finally {
      houseStatsLoading.value = false
    }
  }

  /**
   * 获取收入统计
   * @param {Object} params 查询参数
   * @returns {Promise}
   */
  async function fetchIncomeStats(params = {}) {
    incomeStatsLoading.value = true
    try {
      const res = await getIncomeStatistics(params)
      incomeStats.value = res.data
      return res.data
    } catch (error) {
      console.error('获取收入统计失败:', error)
      throw error
    } finally {
      incomeStatsLoading.value = false
    }
  }

  /**
   * 获取租客统计
   * @param {Object} params 查询参数
   * @returns {Promise}
   */
  async function fetchTenantStats(params = {}) {
    tenantStatsLoading.value = true
    try {
      const res = await getTenantStatistics(params)
      tenantStats.value = res.data
      return res.data
    } catch (error) {
      console.error('获取租客统计失败:', error)
      throw error
    } finally {
      tenantStatsLoading.value = false
    }
  }

  /**
   * 获取合同统计
   * @param {Object} params 查询参数
   * @returns {Promise}
   */
  async function fetchContractStats(params = {}) {
    contractStatsLoading.value = true
    try {
      const res = await getContractStatistics(params)
      contractStats.value = res.data
      return res.data
    } catch (error) {
      console.error('获取合同统计失败:', error)
      throw error
    } finally {
      contractStatsLoading.value = false
    }
  }

  /**
   * 导出Excel报表
   * @param {Object} params 查询参数
   * @param {String} filename 文件名
   * @returns {Promise}
   */
  async function exportExcel(params = {}, filename = 'statistics-report.xlsx') {
    try {
      const res = await exportExcelApi(params)
      // 创建下载链接
      const blob = new Blob([res], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = filename
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
      return true
    } catch (error) {
      console.error('导出Excel失败:', error)
      throw error
    }
  }

  /**
   * 导出PDF报表
   * @param {Object} params 查询参数
   * @param {String} filename 文件名
   * @returns {Promise}
   */
  async function exportPDF(params = {}, filename = 'statistics-report.pdf') {
    try {
      const res = await exportPdfApi(params)
      // 创建下载链接
      const blob = new Blob([res], { type: 'application/pdf' })
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = filename
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
      return true
    } catch (error) {
      console.error('导出PDF失败:', error)
      throw error
    }
  }

  /**
   * 刷新所有统计数据
   * @param {Object} params 查询参数
   * @returns {Promise}
   */
  async function refreshAllStats(params = {}) {
    try {
      // 并行请求所有统计数据
      const [overview, house, income, tenant, contract] = await Promise.all([
        fetchOverview(params),
        fetchHouseStats(params),
        fetchIncomeStats(params),
        fetchTenantStats(params),
        fetchContractStats(params)
      ])
      
      return {
        overview,
        house,
        income,
        tenant,
        contract
      }
    } catch (error) {
      console.error('刷新所有统计失败:', error)
      throw error
    }
  }

  /**
   * 清空所有统计数据
   */
  function clearAllStats() {
    overviewData.value = null
    houseStats.value = null
    incomeStats.value = null
    tenantStats.value = null
    contractStats.value = null
  }

  return {
    // 概览统计状态
    overviewData,
    loading,
    
    // 各模块统计状态
    houseStats,
    incomeStats,
    tenantStats,
    contractStats,
    
    // 各模块加载状态
    houseStatsLoading,
    incomeStatsLoading,
    tenantStatsLoading,
    contractStatsLoading,
    
    // 方法
    fetchOverview,
    fetchHouseStats,
    fetchIncomeStats,
    fetchTenantStats,
    fetchContractStats,
    exportExcel,
    exportPDF,
    refreshAllStats,
    clearAllStats
  }
})
