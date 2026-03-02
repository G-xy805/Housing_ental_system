import request from './request'

/**
 * 获取房源列表
 * @param {Object} params 查询参数
 * @returns {Promise}
 */
export function getHouseList(params) {
  return request.get('/houses', { params })
}

/**
 * 获取房源详情
 * @param {number} id 房源 ID
 * @returns {Promise}
 */
export function getHouseDetail(id) {
  return request.get(`/houses/${id}`)
}

/**
 * 创建房源
 * @param {Object} data 房源数据
 * @returns {Promise}
 */
export function createHouse(data) {
  return request.post('/houses', data)
}

/**
 * 更新房源
 * @param {number} id 房源 ID
 * @param {Object} data 房源数据
 * @returns {Promise}
 */
export function updateHouse(id, data) {
  return request.put(`/houses/${id}`, data)
}

/**
 * 删除房源
 * @param {number} id 房源 ID
 * @returns {Promise}
 */
export function deleteHouse(id) {
  return request.delete(`/houses/${id}`)
}

/**
 * 上传房源图片
 * @param {FormData} formData 图片文件
 * @param {number} houseId 房源 ID
 * @returns {Promise}
 */
export function uploadHouseImage(formData, houseId, isCover = false) {
  formData.append('is_cover', isCover)
  return request.post(`/upload/house/${houseId}`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

/**
 * 通用图片上传（不依赖房源 ID）
 * @param {FormData} formData 图片文件
 * @returns {Promise}
 */
export function uploadImage(formData) {
  return request.post('/upload/image', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

/**
 * 删除媒体文件
 * @param {number} id 媒体文件 ID
 * @returns {Promise}
 */
export function deleteMedia(id) {
  return request.delete(`/upload/${id}`)
}

/**
 * 设置封面图片
 * @param {number} mediaId 媒体 ID
 * @param {boolean} isCover 是否设为封面
 * @returns {Promise}
 */
export function setCoverImage(mediaId, isCover = true) {
  return request.put(`/upload/${mediaId}/cover`, { is_cover: isCover })
}

/**
 * 获取房源统计信息
 * @returns {Promise}
 */
export function getHouseStats() {
  return request.get('/houses/stats')
}

// ============================================================================
// 房间管理相关方法（合租房源）
// ============================================================================

/**
 * 获取房间列表
 * @param {number} houseId 房源 ID
 * @param {Object} params 查询参数 { status: 'available' }
 * @returns {Promise}
 */
export function getRoomList(houseId, params) {
  return request.get(`/houses/${houseId}/rooms`, { params })
}

/**
 * 创建房间
 * @param {number} houseId 房源 ID
 * @param {Object} data 房间数据
 * @returns {Promise}
 */
export function createRoom(houseId, data) {
  return request.post(`/houses/${houseId}/rooms`, data)
}

/**
 * 更新房间
 * @param {number} roomId 房间 ID
 * @param {Object} data 房间数据
 * @returns {Promise}
 */
export function updateRoom(roomId, data) {
  return request.put(`/houses/rooms/${roomId}`, data)
}

/**
 * 删除房间
 * @param {number} roomId 房间 ID
 * @returns {Promise}
 */
export function deleteRoom(roomId) {
  return request.delete(`/houses/rooms/${roomId}`)
}

/**
 * 更新房源状态
 * @param {number} houseId 房源 ID
 * @param {Object} data 状态数据 { status: 'available' }
 * @returns {Promise}
 */
export function updateHouseStatus(houseId, data) {
  return request.put(`/houses/${houseId}/status`, data)
}

/**
 * 重新计算房源状态（基于房间状态）
 * @param {number} houseId 房源 ID
 * @returns {Promise}
 */
export function recalculateHouseStatus(houseId) {
  return request.post(`/houses/${houseId}/auto-status`)
}
