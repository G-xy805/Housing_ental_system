import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { 
  getCurrentUser, 
  logout as logoutApi,
  changePassword as changePasswordApi,
  updateUser
} from '@/api/user'
import { 
  refreshToken as refreshTokenApi,
  getPasswordExpiry,
  verifyToken
} from '@/api/auth'
import router from '@/router'
import { ElMessage } from 'element-plus'

// Token刷新状态
let isRefreshing = false
let refreshSubscribers = []

// 订阅Token刷新
function subscribeTokenRefresh(cb) {
  refreshSubscribers.push(cb)
}

// 通知所有订阅者
function onRefreshed(token) {
  refreshSubscribers.forEach(cb => cb(token))
  refreshSubscribers = []
}

// 刷新失败
function onRefreshFailed() {
  refreshSubscribers = []
}

export const useUserStore = defineStore('user', () => {
  // ==================== 状态 ====================
  const token = ref(localStorage.getItem('token') || '')
  const refreshTokenValue = ref(localStorage.getItem('refreshToken') || '')
  const tokenExpiry = ref(localStorage.getItem('tokenExpiry') || '')
  const userInfo = ref(JSON.parse(localStorage.getItem('userInfo') || '{}'))
  const userPreferences = ref(JSON.parse(localStorage.getItem('userPreferences') || '{}'))
  const isLoading = ref(false)
  
  // ==================== 计算属性 ====================
  
  // 基础信息
  const isLoggedIn = computed(() => !!token.value)
  const userId = computed(() => userInfo.value.id || null)
  const username = computed(() => userInfo.value.username || '')
  const email = computed(() => userInfo.value.email || '')
  const phone = computed(() => userInfo.value.phone || '')
  const avatar = computed(() => userInfo.value.avatar || '')
  const role = computed(() => userInfo.value.role || userInfo.value.user_type || '')
  const status = computed(() => userInfo.value.status || 'active')
  const createdAt = computed(() => userInfo.value.created_at || '')
  const updatedAt = computed(() => userInfo.value.updated_at || '')
  
  // 用户类型判断（兼容旧字段）
  const userType = computed(() => userInfo.value.user_type || userInfo.value.role || '')
  
  // 角色判断
  const isAdmin = computed(() => {
    const type = userType.value.toLowerCase()
    return type === 'admin' || type === 'administrator'
  })
  
  const isEmployee = computed(() => {
    const type = userType.value.toLowerCase()
    return type === 'employee' || type === 'staff'
  })
  
  const isLandlord = computed(() => {
    const type = userType.value.toLowerCase()
    return type === 'landlord'
  })
  
  const isTenant = computed(() => {
    const type = userType.value.toLowerCase()
    return type === 'tenant'
  })
  
  // 状态判断
  const isActive = computed(() => status.value === 'active')
  const isInactive = computed(() => status.value === 'inactive')
  const isSuspended = computed(() => status.value === 'suspended')
  
  // ==================== 权限管理 ====================
  
  /**
   * 检查是否有特定操作权限
   * @param {string} action 操作类型: 'view', 'create', 'edit', 'delete'
   * @returns {boolean}
   */
  function hasPermission(action) {
    // 管理员拥有所有权限
    if (isAdmin.value) {
      return true
    }
    
    // 普通员工权限：查看、创建、编辑（无删除）
    if (isEmployee.value) {
      const employeePermissions = ['view', 'create', 'add', 'edit', 'update']
      return employeePermissions.includes(action)
    }
    
    // 房东权限：管理自己的房源和合同
    if (isLandlord.value) {
      const landlordPermissions = ['view', 'create', 'add', 'edit', 'update']
      return landlordPermissions.includes(action)
    }
    
    // 租客权限：仅查看
    if (isTenant.value) {
      return action === 'view'
    }
    
    return false
  }
  
  /**
   * 检查是否有多个权限中的任意一个
   * @param {string[]} actions 操作类型数组
   * @returns {boolean}
   */
  function hasAnyPermission(actions) {
    return actions.some(action => hasPermission(action))
  }
  
  /**
   * 检查是否有所有权限
   * @param {string[]} actions 操作类型数组
   * @returns {boolean}
   */
  function hasAllPermissions(actions) {
    return actions.every(action => hasPermission(action))
  }
  
  /**
   * 获取用户所有权限列表
   * @returns {string[]}
   */
  function getPermissions() {
    if (isAdmin.value) {
      return ['view', 'create', 'edit', 'delete']
    }
    
    if (isEmployee.value || isLandlord.value) {
      return ['view', 'create', 'edit']
    }
    
    if (isTenant.value) {
      return ['view']
    }
    
    return []
  }
  
  // ==================== Token管理 ====================
  
  /**
   * 设置Token
   * @param {string} newToken 访问令牌
   * @param {string} newRefreshToken 刷新令牌
   * @param {number} expiresIn 过期时间（秒）
   */
  function setToken(newToken, newRefreshToken = null, expiresIn = null) {
    token.value = newToken
    localStorage.setItem('token', newToken)
    
    if (newRefreshToken) {
      refreshTokenValue.value = newRefreshToken
      localStorage.setItem('refreshToken', newRefreshToken)
    }
    
    if (expiresIn) {
      const expiryTime = Date.now() + expiresIn * 1000
      tokenExpiry.value = expiryTime.toString()
      localStorage.setItem('tokenExpiry', expiryTime.toString())
    }
  }
  
  /**
   * 检查Token是否即将过期（提前5分钟）
   * @returns {boolean}
   */
  function isTokenExpiringSoon() {
    if (!tokenExpiry.value) {
      return false
    }
    
    const expiryTime = parseInt(tokenExpiry.value)
    const now = Date.now()
    const bufferTime = 5 * 60 * 1000 // 5分钟缓冲
    
    return now >= (expiryTime - bufferTime)
  }
  
  /**
   * 检查Token是否已过期
   * @returns {boolean}
   */
  function isTokenExpired() {
    if (!tokenExpiry.value) {
      return false
    }
    
    const expiryTime = parseInt(tokenExpiry.value)
    return Date.now() >= expiryTime
  }
  
  /**
   * 刷新Token
   * @returns {Promise<boolean>}
   */
  async function refreshAccessToken() {
    // 如果正在刷新，等待刷新完成
    if (isRefreshing) {
      return new Promise((resolve, reject) => {
        subscribeTokenRefresh(token => {
          if (token) {
            resolve(true)
          } else {
            reject(new Error('Token刷新失败'))
          }
        })
      })
    }
    
    // 如果没有refreshToken，直接返回失败
    if (!refreshTokenValue.value) {
      return false
    }
    
    isRefreshing = true
    
    try {
      const res = await refreshTokenApi()
      const newToken = res.data.access_token || res.data.token
      const newRefreshToken = res.data.refresh_token
      const expiresIn = res.data.expires_in
      
      setToken(newToken, newRefreshToken, expiresIn)
      onRefreshed(newToken)
      
      return true
    } catch (error) {
      console.error('Token刷新失败:', error)
      onRefreshFailed()
      clearStorage()
      router.push('/login')
      return false
    } finally {
      isRefreshing = false
    }
  }
  
  /**
   * 验证Token有效性
   * @returns {Promise<boolean>}
   */
  async function verifyAccessToken() {
    if (!token.value) {
      return false
    }
    
    try {
      await verifyToken()
      return true
    } catch (error) {
      console.error('Token验证失败:', error)
      return false
    }
  }
  
  // ==================== 用户信息管理 ====================
  
  /**
   * 设置用户信息
   * @param {Object} info 用户信息
   */
  function setUserInfo(info) {
    userInfo.value = info
    localStorage.setItem('userInfo', JSON.stringify(info))
  }
  
  /**
   * 设置用户偏好
   * @param {Object} preferences 偏好设置
   */
  function setUserPreferences(preferences) {
    userPreferences.value = { ...userPreferences.value, ...preferences }
    localStorage.setItem('userPreferences', JSON.stringify(userPreferences.value))
  }
  
  /**
   * 获取用户偏好
   * @param {string} key 偏好键名
   * @param {*} defaultValue 默认值
   * @returns {*}
   */
  function getPreference(key, defaultValue = null) {
    return userPreferences.value[key] ?? defaultValue
  }
  
  /**
   * 清除存储
   */
  function clearStorage() {
    token.value = ''
    refreshTokenValue.value = ''
    tokenExpiry.value = ''
    userInfo.value = {}
    userPreferences.value = {}
    
    localStorage.removeItem('token')
    localStorage.removeItem('refreshToken')
    localStorage.removeItem('tokenExpiry')
    localStorage.removeItem('userInfo')
    localStorage.removeItem('userPreferences')
    localStorage.removeItem('rememberMe')
  }
  
  // ==================== 登录/登出 ====================
  
  /**
   * 登录
   * @param {Object} userData 登录数据
   */
  function login(userData) {
    const accessToken = userData.access_token || userData.token
    const refreshToken = userData.refresh_token
    const expiresIn = userData.expires_in
    
    setToken(accessToken, refreshToken, expiresIn)
    
    // 只保存基本用户信息，完整信息由 fetchCurrentUser 获取
    const basicUserInfo = userData.user || userData
    if (basicUserInfo.avatar !== undefined) {
      // 如果登录响应包含完整用户信息（包括 avatar），直接保存
      setUserInfo(basicUserInfo)
    }
    // 否则不保存，让路由守卫触发 fetchCurrentUser 获取完整信息
  }
  
  /**
   * 登出
   */
  async function logout() {
    try {
      if (token.value) {
        await logoutApi().catch(() => {})
      }
    } finally {
      clearStorage()
      router.push('/login')
    }
  }
  
  /**
   * 获取当前用户信息
   */
  async function fetchCurrentUser() {
    if (!token.value) {
      return null
    }
    
    isLoading.value = true
    try {
      const res = await getCurrentUser()
      setUserInfo(res.data || res)
      return res.data || res
    } catch (error) {
      console.error('获取用户信息失败:', error)
      clearStorage()
      return null
    } finally {
      isLoading.value = false
    }
  }
  
  /**
   * 更新用户信息
   * @param {Object} info 用户信息
   */
  function updateUserInfo(info) {
    setUserInfo({ ...userInfo.value, ...info })
  }
  
  /**
   * 检查认证状态
   */
  async function checkAuth() {
    if (token.value && (!userInfo.value.username || Object.keys(userInfo.value).length === 0)) {
      await fetchCurrentUser()
    }
    return isLoggedIn.value
  }
  
  // ==================== 新增功能 ====================
  
  /**
   * 修改密码
   * @param {string} oldPassword 旧密码
   * @param {string} newPassword 新密码
   * @returns {Promise}
   */
  async function changePassword(oldPassword, newPassword) {
    try {
      const res = await changePasswordApi({
        old_password: oldPassword,
        new_password: newPassword
      })
      ElMessage.success('密码修改成功')
      return res
    } catch (error) {
      console.error('修改密码失败:', error)
      throw error
    }
  }
  
  /**
   * 更新头像
   * @param {string} avatarUrl 头像URL
   * @returns {Promise}
   */
  async function updateAvatar(avatarUrl) {
    try {
      const res = await updateUser(userId.value, { avatar: avatarUrl })
      updateUserInfo({ avatar: avatarUrl })
      ElMessage.success('头像更新成功')
      return res
    } catch (error) {
      console.error('更新头像失败:', error)
      throw error
    }
  }
  
  /**
   * 检查密码过期状态
   * @returns {Promise<Object>}
   */
  async function checkPasswordExpiry() {
    try {
      const res = await getPasswordExpiry()
      return {
        isExpired: res.data?.is_expired || false,
        daysUntilExpiry: res.data?.days_until_expiry || null,
        lastChangedAt: res.data?.last_changed_at || null,
        warningMessage: res.data?.warning_message || ''
      }
    } catch (error) {
      console.error('检查密码过期状态失败:', error)
      return {
        isExpired: false,
        daysUntilExpiry: null,
        lastChangedAt: null,
        warningMessage: ''
      }
    }
  }
  
  /**
   * 更新用户偏好设置
   * @param {string} key 偏好键名
   * @param {*} value 偏好值
   */
  function updatePreference(key, value) {
    setUserPreferences({ [key]: value })
  }
  
  /**
   * 重置用户偏好设置
   */
  function resetPreferences() {
    userPreferences.value = {}
    localStorage.removeItem('userPreferences')
  }
  
  // ==================== 导出 ====================
  
  return {
    // 状态
    token,
    refreshTokenValue,
    tokenExpiry,
    userInfo,
    userPreferences,
    isLoading,
    
    // 计算属性 - 基础信息
    isLoggedIn,
    userId,
    username,
    email,
    phone,
    avatar,
    role,
    status,
    createdAt,
    updatedAt,
    userType,
    
    // 计算属性 - 角色判断
    isAdmin,
    isEmployee,
    isLandlord,
    isTenant,
    
    // 计算属性 - 状态判断
    isActive,
    isInactive,
    isSuspended,
    
    // 权限管理
    hasPermission,
    hasAnyPermission,
    hasAllPermissions,
    getPermissions,
    
    // Token管理
    setToken,
    isTokenExpiringSoon,
    isTokenExpired,
    refreshAccessToken,
    verifyAccessToken,
    
    // 用户信息管理
    setUserInfo,
    setUserPreferences,
    getPreference,
    clearStorage,
    
    // 登录/登出
    login,
    logout,
    fetchCurrentUser,
    updateUserInfo,
    checkAuth,
    
    // 新增功能
    changePassword,
    updateAvatar,
    checkPasswordExpiry,
    updatePreference,
    resetPreferences
  }
})
