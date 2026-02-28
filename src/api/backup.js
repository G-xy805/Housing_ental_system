import request from './request'

/**
 * 获取备份列表
 * @param {Object} params 查询参数
 * @returns {Promise}
 */
export function getBackupList(params) {
  return request.get('/backup/list', { params })
}

/**
 * 创建备份
 * @param {Object} data 备份数据
 * @returns {Promise}
 */
export function createBackup(data) {
  return request.post('/backup/create', data)
}

/**
 * 下载备份
 * @param {string} filename 备份文件名
 * @returns {Promise}
 */
export function downloadBackup(filename) {
  return request.get(`/backup/download/${filename}`, {
    responseType: 'blob'
  })
}

/**
 * 恢复备份
 * @param {Object} data 恢复数据
 * @returns {Promise}
 */
export function restoreBackup(data) {
  return request.post('/backup/restore', data)
}

/**
 * 删除备份
 * @param {string} filename 备份文件名
 * @returns {Promise}
 */
export function deleteBackup(filename) {
  return request.delete(`/backup/${filename}`)
}

/**
 * 获取备份设置
 * @returns {Promise}
 */
export function getBackupSettings() {
  return request.get('/backup/settings')
}

/**
 * 更新备份设置
 * @param {Object} data 备份设置
 * @returns {Promise}
 */
export function updateBackupSettings(data) {
  return request.put('/backup/settings', data)
}
