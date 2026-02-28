import request from './request'

/**
 * 获取概览统计
 * @param {Object} params 查询参数
 * @returns {Promise}
 */
export function getOverviewStatistics(params) {
  return request.get('/statistics/overview', { params })
}

/**
 * 获取房源统计
 * @param {Object} params 查询参数
 * @returns {Promise}
 */
export function getHouseStatistics(params) {
  return request.get('/statistics/houses', { params })
}

/**
 * 获取收入统计
 * @param {Object} params 查询参数
 * @returns {Promise}
 */
export function getIncomeStatistics(params) {
  return request.get('/statistics/income', { params })
}

/**
 * 获取租客统计
 * @param {Object} params 查询参数
 * @returns {Promise}
 */
export function getTenantStatistics(params) {
  return request.get('/statistics/tenants', { params })
}

/**
 * 获取合同统计
 * @param {Object} params 查询参数
 * @returns {Promise}
 */
export function getContractStatistics(params) {
  return request.get('/statistics/contracts', { params })
}

/**
 * 导出 Excel 报表
 * @param {Object} params 查询参数
 * @returns {Promise}
 */
export function exportExcel(params) {
  return request.get('/statistics/export/excel', {
    params,
    responseType: 'blob'
  })
}

/**
 * 导出 PDF 报表
 * @param {Object} params 查询参数
 * @returns {Promise}
 */
export function exportPdf(params) {
  return request.get('/statistics/export/pdf', {
    params,
    responseType: 'blob'
  })
}
