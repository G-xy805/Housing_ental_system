import request from './request'

/**
 * 获取租客列表
 * @param {Object} params 查询参数
 * @returns {Promise}
 */
export function getTenantList(params) {
  return request.get('/tenants', { params })
}

/**
 * 获取租客详情
 * @param {number} id 租客 ID
 * @returns {Promise}
 */
export function getTenantDetail(id) {
  return request.get(`/tenants/${id}`)
}

/**
 * 创建租客
 * @param {Object} data 租客数据
 * @returns {Promise}
 */
export function createTenant(data) {
  return request.post('/tenants', data)
}

/**
 * 更新租客
 * @param {number} id 租客 ID
 * @param {Object} data 租客数据
 * @returns {Promise}
 */
export function updateTenant(id, data) {
  return request.put(`/tenants/${id}`, data)
}

/**
 * 删除租客
 * @param {number} id 租客 ID
 * @returns {Promise}
 */
export function deleteTenant(id) {
  return request.delete(`/tenants/${id}`)
}

/**
 * 获取租客统计信息
 * @returns {Promise}
 */
export function getTenantStats() {
  return request.get('/tenants/stats')
}

/**
 * 获取租客合同列表
 * @param {number} id 租客 ID
 * @returns {Promise}
 */
export function getTenantContracts(id) {
  return request.get(`/tenants/${id}/contracts`)
}

/**
 * 上传租客证件照
 * @param {FormData} formData 图片文件
 * @returns {Promise}
 */
export function uploadTenantPhoto(formData) {
  return request.post('/tenants/upload-photo', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}
