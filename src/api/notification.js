import request from './request'

/**
 * 获取通知列表
 * @param {Object} params 查询参数
 * @returns {Promise}
 */
export function getNotificationList(params) {
  return request.get('/notifications', { params })
}

/**
 * 发送通知
 * @param {Object} data 通知数据
 * @returns {Promise}
 */
export function sendNotification(data) {
  return request.post('/notifications', data)
}

/**
 * 批量发送通知
 * @param {Object} data 批量发送数据
 * @param {Array} data.tenant_ids 租客ID列表
 * @param {string} data.title 通知标题
 * @param {string} data.content 通知内容
 * @param {string} data.type 通知类型
 * @returns {Promise}
 */
export function batchSend(data) {
  return request.post('/notifications/batch-send', data)
}

/**
 * 标记通知为已读
 * @param {number} id 通知 ID
 * @returns {Promise}
 */
export function markAsRead(id) {
  return request.put(`/notifications/${id}/read`)
}

/**
 * 删除通知
 * @param {number} id 通知 ID
 * @returns {Promise}
 */
export function deleteNotification(id) {
  return request.delete(`/notifications/${id}`)
}
