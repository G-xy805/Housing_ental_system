import request from './request'

/**
 * 通用文件上传
 * @param {File} file - 要上传的文件
 * @returns {Promise}
 */
export function uploadFile(file) {
  const formData = new FormData()
  formData.append('files', file)
  
  return request.post('/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

/**
 * 上传图片
 * @param {File} file - 图片文件
 * @returns {Promise}
 */
export function uploadImage(file) {
  const formData = new FormData()
  formData.append('files', file)
  
  return request.post('/upload/image', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

/**
 * 上传视频
 * @param {File} file - 视频文件
 * @returns {Promise}
 */
export function uploadVideo(file) {
  const formData = new FormData()
  formData.append('files', file)
  
  return request.post('/upload/video', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

/**
 * 上传房源媒体文件
 * @param {number} houseId - 房源ID
 * @param {File} file - 媒体文件
 * @param {Object} options - 可选参数
 * @param {string} options.description - 文件描述
 * @param {boolean} options.is_cover - 是否设为封面
 * @param {number} options.sort_order - 排序顺序
 * @returns {Promise}
 */
export function uploadHouseMedia(houseId, file, options = {}) {
  const formData = new FormData()
  formData.append('files', file)
  
  if (options.description) {
    formData.append('description', options.description)
  }
  if (options.is_cover !== undefined) {
    formData.append('is_cover', options.is_cover)
  }
  if (options.sort_order !== undefined) {
    formData.append('sort_order', options.sort_order)
  }
  
  return request.post(`/upload/house/${houseId}`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

/**
 * 删除媒体文件
 * @param {number} mediaId - 媒体文件ID
 * @returns {Promise}
 */
export function deleteMedia(mediaId) {
  return request.delete(`/upload/${mediaId}`)
}

/**
 * 设置封面图片
 * @param {number} mediaId - 媒体ID
 * @param {boolean} isCover - 是否设为封面，默认为true
 * @returns {Promise}
 */
export function setCoverImage(mediaId, isCover = true) {
  return request.put(`/upload/${mediaId}/cover`, { is_cover: isCover })
}

/**
 * 获取房源媒体列表
 * @param {number} houseId - 房源ID
 * @returns {Promise}
 */
export function getHouseMediaList(houseId) {
  return request.get(`/upload/house/${houseId}/media`)
}
