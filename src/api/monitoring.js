import request from './request'

/**
 * 系统监控模块 API
 */

// ==================== 健康检查接口 ====================

/**
 * 系统健康检查
 * @returns {Promise}
 */
export function healthCheck() {
  return request.get('/monitoring/health')
}

/**
 * 数据库健康检查
 * @returns {Promise}
 */
export function dbHealthCheck() {
  return request.get('/monitoring/health/db')
}

/**
 * Redis 健康检查
 * @returns {Promise}
 */
export function redisHealthCheck() {
  return request.get('/monitoring/health/redis')
}

/**
 * 系统资源健康检查
 * @returns {Promise}
 */
export function systemHealthCheck() {
  return request.get('/monitoring/health/system')
}

// ==================== Prometheus 指标接口 ====================

/**
 * 获取 Prometheus 指标
 * @returns {Promise}
 */
export function getMetrics() {
  return request.get('/monitoring/metrics')
}

// ==================== 性能监控接口 ====================

/**
 * 获取性能概览
 * @returns {Promise}
 */
export function getPerformanceOverview() {
  return request.get('/monitoring/performance')
}

/**
 * 获取 QPS 统计
 * @returns {Promise}
 */
export function getQPSStats() {
  return request.get('/monitoring/performance/qps')
}

/**
 * 获取响应时间统计
 * @returns {Promise}
 */
export function getResponseTimeStats() {
  return request.get('/monitoring/performance/response-time')
}

/**
 * 获取错误率统计
 * @returns {Promise}
 */
export function getErrorRateStats() {
  return request.get('/monitoring/performance/error-rate')
}

/**
 * 获取资源使用统计
 * @returns {Promise}
 */
export function getResourceStats() {
  return request.get('/monitoring/performance/resources')
}

// ==================== 告警管理接口 ====================

/**
 * 获取告警列表
 * @param {Object} params 查询参数
 * @returns {Promise}
 */
export function getAlerts(params) {
  return request.get('/monitoring/alerts', { params })
}

/**
 * 获取告警历史
 * @param {Object} params 查询参数
 * @returns {Promise}
 */
export function getAlertHistory(params) {
  return request.get('/monitoring/alerts/history', { params })
}

/**
 * 解决告警
 * @param {number} id 告警 ID
 * @param {Object} data 解决信息
 * @returns {Promise}
 */
export function resolveAlert(id, data) {
  return request.post(`/monitoring/alerts/${id}/resolve`, data)
}

/**
 * 清除已解决的告警
 * @returns {Promise}
 */
export function clearResolvedAlerts() {
  return request.post('/monitoring/alerts/clear-resolved')
}

// ==================== 监控仪表盘接口 ====================

/**
 * 获取监控仪表盘数据
 * @returns {Promise}
 */
export function getDashboard() {
  return request.get('/monitoring/dashboard')
}

// ==================== 监控数据管理接口 ====================

/**
 * 重置监控数据
 * @returns {Promise}
 */
export function resetMonitoringData() {
  return request.post('/monitoring/reset')
}
