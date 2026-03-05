import request from './request'

/**
 * 获取合同列表
 * @param {Object} params 查询参数
 * @returns {Promise}
 */
export function getContractList(params) {
  return request.get('/contracts', { params })
}

/**
 * 获取合同详情
 * @param {number} id 合同 ID
 * @returns {Promise}
 */
export function getContractDetail(id) {
  return request.get(`/contracts/${id}`)
}

/**
 * 创建合同
 * @param {Object} data 合同数据
 * @returns {Promise}
 */
export function createContract(data) {
  return request.post('/contracts', data)
}

/**
 * 更新合同
 * @param {number} id 合同 ID
 * @param {Object} data 合同数据
 * @returns {Promise}
 */
export function updateContract(id, data) {
  return request.put(`/contracts/${id}`, data)
}

/**
 * 删除合同
 * @param {number} id 合同 ID
 * @returns {Promise}
 */
export function deleteContract(id) {
  return request.delete(`/contracts/${id}`)
}

/**
 * 激活合同
 * @param {number} id 合同 ID
 * @returns {Promise}
 */
export function activateContract(id) {
  return request.post(`/contracts/${id}/activate`)
}

/**
 * 终止合同
 * @param {number} id 合同 ID
 * @param {Object} data 终止数据
 * @returns {Promise}
 */
export function terminateContract(id, data) {
  return request.post(`/contracts/${id}/terminate`, data)
}

/**
 * 续签合同
 * @param {number} id 合同 ID
 * @param {Object} data 续签数据
 * @returns {Promise}
 */
export function renewContract(id, data) {
  return request.post(`/contracts/${id}/renew`, data)
}

/**
 * 下载合同文件
 * @param {number} id 合同 ID
 * @returns {Promise}
 */
export function downloadContractFile(id) {
  return request.get(`/contracts/${id}/download`, {
    responseType: 'blob'
  })
}

/**
 * 获取合同统计信息
 * @returns {Promise}
 */
export function getContractStats() {
  return request.get('/contracts/stats')
}

/**
 * 获取即将到期的合同
 * @param {Object} params 查询参数
 * @param {number} [params.days=30] 查询多少天内到期的合同
 * @returns {Promise}
 */
export function getExpiringContracts(params) {
  return request.get('/contracts/expiring', { params })
}

/**
 * 获取合同的支付记录
 * @param {number} id 合同 ID
 * @param {Object} params 查询参数
 * @returns {Promise}
 */
export function getContractPayments(id, params) {
  return request.get(`/contracts/${id}/payments`, { params })
}


