import request from './request'

/**
 * 获取员工列表
 * @param {Object} params 查询参数
 * @returns {Promise}
 */
export function getEmployeeList(params) {
  return request.get('/employees', { params })
}

/**
 * 获取员工详情
 * @param {number} id 员工 ID
 * @returns {Promise}
 */
export function getEmployeeDetail(id) {
  return request.get(`/employees/${id}`)
}

/**
 * 创建员工
 * @param {Object} data 员工数据
 * @returns {Promise}
 */
export function createEmployee(data) {
  return request.post('/employees', data)
}

/**
 * 更新员工信息
 * @param {number} id 员工 ID
 * @param {Object} data 员工数据
 * @returns {Promise}
 */
export function updateEmployee(id, data) {
  return request.put(`/employees/${id}`, data)
}

/**
 * 更新员工状态
 * @param {number} id 员工 ID
 * @param {string} status 状态
 * @returns {Promise}
 */
export function updateEmployeeStatus(id, status) {
  return request.patch(`/employees/${id}/status`, { status })
}

/**
 * 删除员工
 * @param {number} id 员工 ID
 * @returns {Promise}
 */
export function deleteEmployee(id) {
  return request.delete(`/employees/${id}`)
}

/**
 * 重置员工密码
 * @param {number} id 员工 ID
 * @param {string} newPassword 新密码
 * @returns {Promise}
 */
export function resetEmployeePassword(id, newPassword) {
  return request.post(`/employees/${id}/reset-password`, { new_password: newPassword })
}

/**
 * 批量操作员工
 * @param {Object} data { user_ids, action }
 * @returns {Promise}
 */
export function batchActionEmployees(data) {
  return request.post('/employees/batch-action', data)
}

/**
 * 获取员工统计信息
 * @returns {Promise}
 */
export function getEmployeeStats() {
  return request.get('/employees/stats')
}
