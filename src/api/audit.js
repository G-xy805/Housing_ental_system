import request from './request'

/**
 * 获取审计日志列表
 * @param {Object} params 查询参数
 * @param {number} params.page 页码
 * @param {number} params.per_page 每页数量
 * @param {number} params.user_id 用户 ID
 * @param {string} params.operation_type 操作类型
 * @param {string} params.model_name 模型名称
 * @param {string} params.start_date 开始日期
 * @param {string} params.end_date 结束日期
 * @returns {Promise}
 */
export function getAuditLogs(params) {
  return request.get('/audit/logs', { params })
}

/**
 * 获取审计日志详情
 * @param {number} id 审计日志 ID
 * @returns {Promise}
 */
export function getAuditLogDetail(id) {
  return request.get(`/audit/logs/${id}`)
}

/**
 * 获取用户的审计日志
 * @param {number} userId 用户 ID
 * @param {Object} params 查询参数
 * @param {number} params.page 页码
 * @param {number} params.per_page 每页数量
 * @returns {Promise}
 */
export function getUserAuditLogs(userId, params) {
  return request.get(`/audit/logs/user/${userId}`, { params })
}

/**
 * 获取记录的审计日志
 * @param {string} modelName 模型名称
 * @param {number} recordId 记录 ID
 * @param {Object} params 查询参数
 * @param {number} params.page 页码
 * @param {number} params.per_page 每页数量
 * @returns {Promise}
 */
export function getRecordAuditLogs(modelName, recordId, params) {
  return request.get(`/audit/logs/record/${modelName}/${recordId}`, { params })
}

/**
 * 获取审计统计
 * @param {Object} params 查询参数
 * @param {string} params.start_date 开始日期
 * @param {string} params.end_date 结束日期
 * @returns {Promise}
 */
export function getAuditStatistics(params) {
  return request.get('/audit/statistics', { params })
}

/**
 * 获取用户审计统计
 * @param {number} userId 用户 ID
 * @param {Object} params 查询参数
 * @param {string} params.start_date 开始日期
 * @param {string} params.end_date 结束日期
 * @returns {Promise}
 */
export function getUserAuditStatistics(userId, params) {
  return request.get(`/audit/statistics/user/${userId}`, { params })
}

/**
 * 获取审计告警
 * @param {Object} params 查询参数
 * @param {number} params.page 页码
 * @param {number} params.per_page 每页数量
 * @returns {Promise}
 */
export function getAuditAlerts(params) {
  return request.get('/audit/alerts', { params })
}

/**
 * 导出审计日志
 * @param {Object} params 查询参数
 * @param {string} params.start_date 开始日期
 * @param {string} params.end_date 结束日期
 * @param {string} params.format 导出格式（csv/excel）
 * @returns {Promise}
 */
export function exportAuditLogs(params) {
  return request.get('/audit/export', {
    params,
    responseType: 'blob'
  })
}

/**
 * 导出审计统计
 * @param {Object} params 查询参数
 * @param {string} params.start_date 开始日期
 * @param {string} params.end_date 结束日期
 * @param {string} params.format 导出格式（csv/excel）
 * @returns {Promise}
 */
export function exportAuditStatistics(params) {
  return request.get('/audit/export/statistics', {
    params,
    responseType: 'blob'
  })
}

/**
 * 获取敏感字段列表
 * @returns {Promise}
 */
export function getSensitiveFields() {
  return request.get('/audit/sensitive-fields')
}

/**
 * 获取操作类型列表
 * @returns {Promise}
 */
export function getOperationTypes() {
  return request.get('/audit/operation-types')
}

/**
 * 获取审计日志开关状态
 * @returns {Promise}
 */
export function getAuditToggle() {
  return request.get('/audit/toggle')
}

/**
 * 更新审计日志开关状态
 * @param {boolean} enabled 是否启用
 * @returns {Promise}
 */
export function updateAuditToggle(enabled) {
  return request.put('/audit/toggle', { enabled })
}
