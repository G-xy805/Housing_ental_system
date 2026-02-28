import request from './request'

/**
 * 用户登录
 * @param {Object} data 登录数据 { username, password }
 * @returns {Promise}
 */
export function login(data) {
  return request.post('/auth/login', data)
}

/**
 * 用户登出
 * @returns {Promise}
 */
export function logout() {
  return request.post('/auth/logout')
}

/**
 * 用户注册
 * @param {Object} data 注册数据
 * @returns {Promise}
 */
export function register(data) {
  return request.post('/auth/register', data)
}

/**
 * 获取当前用户信息
 * @returns {Promise}
 */
export function getCurrentUser() {
  return request.get('/auth/me')
}

/**
 * 更新用户信息
 * @param {Object} data 用户信息
 * @returns {Promise}
 */
export function updateUserInfo(data) {
  return request.put('/auth/me', data)
}

/**
 * 修改密码
 * @param {Object} data { old_password, new_password }
 * @returns {Promise}
 */
export function changePassword(data) {
  return request.post('/auth/change-password', data)
}

/**
 * 获取用户列表
 * @param {Object} params 查询参数
 * @returns {Promise}
 */
export function getUserList(params) {
  return request.get('/users', { params })
}

/**
 * 获取用户详情
 * @param {number} id 用户 ID
 * @returns {Promise}
 */
export function getUserDetail(id) {
  return request.get(`/users/${id}`)
}

/**
 * 创建用户
 * @param {Object} data 用户数据
 * @returns {Promise}
 */
export function createUser(data) {
  return request.post('/users', data)
}

/**
 * 更新用户
 * @param {number} id 用户 ID
 * @param {Object} data 用户数据
 * @returns {Promise}
 */
export function updateUser(id, data) {
  return request.put(`/users/${id}`, data)
}

/**
 * 删除用户
 * @param {number} id 用户 ID
 * @returns {Promise}
 */
export function deleteUser(id) {
  return request.delete(`/users/${id}`)
}

/**
 * 刷新 Token
 * @returns {Promise}
 */
export function refreshToken() {
  return request.post('/auth/refresh')
}

/**
 * 发送验证码
 * @param {string} email 邮箱
 * @returns {Promise}
 */
export function sendVerifyCode(email) {
  return request.post('/auth/send-code', { email })
}

/**
 * 验证验证码
 * @param {Object} data { email, code }
 * @returns {Promise}
 */
export function verifyCode(data) {
  return request.post('/auth/verify-code', data)
}

/**
 * 重置密码
 * @param {Object} data { email, code, new_password }
 * @returns {Promise}
 */
export function resetPassword(data) {
  return request.post('/auth/reset-password', data)
}

/**
 * 批量操作用户
 * @param {Object} data { user_ids, action }
 * @returns {Promise}
 */
export function batchActionUsers(data) {
  return request.post('/users/batch-action', data)
}

/**
 * 获取用户统计信息
 * @returns {Promise}
 */
export function getUserStatistics() {
  return request.get('/users/stats')
}
