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
export function uploadHouseImage(formData, houseId) {
  return request.post(`/upload/house/${houseId}`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

/**
 * 获取房源统计信息
 * @returns {Promise}
 */
export function getHouseStats() {
  return request.get('/houses/stats')
}
