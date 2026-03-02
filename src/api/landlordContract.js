import request from './request'

/**
 * 获取承包合同列表
 * @param {Object} params 查询参数
 * @param {number} [params.page=1] 页码
 * @param {number} [params.per_page=10] 每页数量
 * @param {string} [params.keyword] 搜索关键词
 * @param {string} [params.status] 合同状态筛选
 * @returns {Promise}
 */
export function getLandlordContractList(params) {
  return request.get('/landlord_contracts', { params })
}

/**
 * 获取承包合同详情
 * @param {number} id 合同 ID
 * @returns {Promise}
 */
export function getLandlordContractDetail(id) {
  return request.get(`/landlord_contracts/${id}`)
}

/**
 * 创建承包合同
 * @param {Object} data 合同数据
 * @param {string} data.title 合同标题
 * @param {number} data.landlord_id 房东 ID
 * @param {number[]} data.house_ids 房源 ID 列表
 * @param {string} data.start_date 合同开始日期
 * @param {string} data.end_date 合同结束日期
 * @param {number} data.contract_amount 合同金额
 * @param {number} data.service_fee_rate 服务费率
 * @param {number} [data.minimum_fee] 最低服务费
 * @param {number} [data.payment_cycle] 付款周期
 * @param {string} [data.remark] 备注
 * @returns {Promise}
 */
export function createLandlordContract(data) {
  return request.post('/landlord_contracts', data)
}

/**
 * 更新承包合同
 * @param {number} id 合同 ID
 * @param {Object} data 合同数据
 * @param {string} [data.title] 合同标题
 * @param {number} [data.contract_amount] 合同金额
 * @param {number} [data.service_fee_rate] 服务费率
 * @param {number} [data.minimum_fee] 最低服务费
 * @param {number} [data.payment_cycle] 付款周期
 * @param {string} [data.remark] 备注
 * @returns {Promise}
 */
export function updateLandlordContract(id, data) {
  return request.put(`/landlord_contracts/${id}`, data)
}

/**
 * 删除承包合同
 * @param {number} id 合同 ID
 * @returns {Promise}
 */
export function deleteLandlordContract(id) {
  return request.delete(`/landlord_contracts/${id}`)
}

/**
 * 激活承包合同
 * @param {number} id 合同 ID
 * @returns {Promise}
 */
export function activateLandlordContract(id) {
  return request.post(`/landlord_contracts/${id}/activate`)
}

/**
 * 终止承包合同
 * @param {number} id 合同 ID
 * @param {Object} data 终止数据
 * @param {string} data.terminate_date 终止日期
 * @param {string} data.reason 终止原因
 * @param {number} [data.settlement_amount] 结算金额（可选）
 * @param {string} [data.remark] 备注
 * @returns {Promise}
 */
export function terminateLandlordContract(id, data) {
  return request.post(`/landlord_contracts/${id}/terminate`, data)
}

/**
 * 续签承包合同
 * @param {number} id 合同 ID
 * @param {Object} data 续签数据
 * @param {string} data.end_date 新结束日期
 * @param {number} [data.contract_amount] 新合同金额
 * @param {number} [data.service_fee_rate] 新服务费率
 * @param {string} [data.remark] 备注
 * @returns {Promise}
 */
export function renewLandlordContract(id, data) {
  return request.post(`/landlord_contracts/${id}/renew`, data)
}

/**
 * 获取即将到期的合同
 * @param {Object} params 查询参数
 * @param {number} [params.days=30] 天数范围
 * @param {boolean} [params.include_expired] 是否包含已过期合同
 * @returns {Promise}
 */
export function getExpiringContracts(params) {
  return request.get('/landlord_contracts/expiring', { params })
}

/**
 * 获取承包合同统计信息
 * @param {Object} params 统计参数
 * @param {number} [params.landlord_id] 房东 ID
 * @returns {Promise}
 */
export function getLandlordContractStats(params) {
  return request.get('/landlord_contracts/stats', { params })
}
