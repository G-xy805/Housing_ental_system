import request from './request'

/**
 * 获取房东列表
 * @param {Object} params 查询参数
 * @param {number} [params.page=1] 页码
 * @param {number} [params.page_size=10] 每页数量
 * @param {string} [params.search] 搜索关键词（姓名、手机号）
 * @param {string} [params.status] 筛选状态（active、inactive）
 * @returns {Promise}
 */
export function getLandlordList(params) {
  return request.get('/landlords', { params })
}

/**
 * 获取房东详情
 * @param {number} id 房东 ID
 * @returns {Promise}
 */
export function getLandlordDetail(id) {
  return request.get(`/landlords/${id}`)
}

/**
 * 创建房东
 * @param {Object} data 房东数据
 * @param {string} data.name 房东姓名
 * @param {string} data.phone 手机号
 * @param {string} [data.email] 邮箱
 * @param {string} [data.id_card] 身份证号
 * @param {string} [data.remark] 备注
 * @returns {Promise}
 */
export function createLandlord(data) {
  return request.post('/landlords', data)
}

/**
 * 更新房东
 * @param {number} id 房东 ID
 * @param {Object} data 房东数据
 * @param {string} [data.name] 房东姓名
 * @param {string} [data.phone] 手机号
 * @param {string} [data.email] 邮箱
 * @param {string} [data.id_card] 身份证号
 * @param {string} [data.remark] 备注
 * @param {string} [data.status] 状态（active、inactive）
 * @returns {Promise}
 */
export function updateLandlord(id, data) {
  return request.put(`/landlords/${id}`, data)
}

/**
 * 删除房东
 * @param {number} id 房东 ID
 * @returns {Promise}
 */
export function deleteLandlord(id) {
  return request.delete(`/landlords/${id}`)
}

/**
 * 获取房东的房源列表
 * @param {number} landlordId 房东 ID
 * @param {Object} params 查询参数
 * @param {number} [params.page=1] 页码
 * @param {number} [params.page_size=10] 每页数量
 * @param {string} [params.status] 房源状态筛选
 * @returns {Promise}
 */
export function getLandlordHouses(landlordId, params) {
  return request.get(`/landlords/${landlordId}/houses`, { params })
}

/**
 * 获取房东的合同列表
 * @param {number} landlordId 房东 ID
 * @param {Object} params 查询参数
 * @param {number} [params.page=1] 页码
 * @param {number} [params.page_size=10] 每页数量
 * @param {string} [params.status] 合同状态筛选
 * @returns {Promise}
 */
export function getLandlordContracts(landlordId, params) {
  return request.get(`/landlords/${landlordId}/contracts`, { params })
}

/**
 * 获取房东统计信息
 * @returns {Promise}
 */
export function getLandlordStats() {
  return request.get('/landlords/stats')
}

/**
 * 搜索房东
 * @param {Object} params 查询参数
 * @param {string} params.q 搜索关键词（姓名/电话）
 * @returns {Promise}
 */
export function searchLandlords(params) {
  return request.get('/landlords/search', { params })
}
