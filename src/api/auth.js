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
 * 刷新 Token
 * @returns {Promise}
 */
export function refreshToken() {
  return request.post('/auth/refresh')
}

/**
 * 验证 Token
 * @returns {Promise}
 */
export function verifyToken() {
  return request.post('/auth/verify-token')
}

/**
 * 检查密码强度
 * @param {string} password 密码
 * @returns {Promise}
 */
export function checkPasswordStrength(password) {
  return request.post('/auth/password/strength', { password })
}

/**
 * 获取密码过期信息
 * @returns {Promise}
 */
export function getPasswordExpiry() {
  return request.get('/auth/password/expiry')
}

/**
 * 请求密码重置
 * @param {string} email 邮箱地址
 * @returns {Promise}
 */
export function requestPasswordReset(email) {
  return request.post('/auth/password/reset-request', { email })
}

/**
 * 重置密码
 * @param {Object} data { token, new_password }
 * @returns {Promise}
 */
export function resetPassword(data) {
  return request.post('/auth/password/reset', data)
}

/**
 * 获取密码建议
 * @returns {Promise}
 */
export function getPasswordSuggestions() {
  return request.get('/auth/password/suggestions')
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
