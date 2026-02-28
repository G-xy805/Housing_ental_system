import request from './request'

/**
 * 获取支付记录列表
 * @param {Object} params 查询参数
 * @returns {Promise}
 */
export function getPaymentList(params) {
  return request.get('/payments', { params })
}

/**
 * 获取支付记录详情
 * @param {number} id 支付记录 ID
 * @returns {Promise}
 */
export function getPaymentDetail(id) {
  return request.get(`/payments/${id}`)
}

/**
 * 创建支付记录
 * @param {Object} data 支付记录数据
 * @returns {Promise}
 */
export function createPayment(data) {
  return request.post('/payments', data)
}

/**
 * 更新支付记录
 * @param {number} id 支付记录 ID
 * @param {Object} data 支付记录数据
 * @returns {Promise}
 */
export function updatePayment(id, data) {
  return request.put(`/payments/${id}`, data)
}

/**
 * 删除支付记录
 * @param {number} id 支付记录 ID
 * @returns {Promise}
 */
export function deletePayment(id) {
  return request.delete(`/payments/${id}`)
}

/**
 * 确认收款
 * @param {number} id 支付记录 ID
 * @param {Object} data 收款数据
 * @returns {Promise}
 */
export function verifyPayment(id, data) {
  return request.post(`/payments/${id}/verify`, data)
}

/**
 * 获取逾期支付记录
 * @param {Object} params 查询参数
 * @returns {Promise}
 */
export function getOverduePayments(params) {
  return request.get('/payments/overdue', { params })
}

/**
 * 获取合同的还款计划
 * @param {number} contractId 合同 ID
 * @returns {Promise}
 */
export function getContractPaymentPlan(contractId) {
  return request.get(`/payments/contracts/${contractId}/payment-plan`)
}

/**
 * 获取支付统计信息
 * @param {Object} params 查询参数
 * @returns {Promise}
 */
export function getPaymentStats(params) {
  return request.get('/payments/stats', { params })
}

/**
 * 批量更新滞纳金
 * @returns {Promise}
 */
export function updateLateFees() {
  return request.post('/payments/update-late-fees')
}
