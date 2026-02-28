import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { getCurrentUser, logout as logoutApi } from '@/api/user'
import router from '@/router'

export const useUserStore = defineStore('user', () => {
  // 状态
  const token = ref(localStorage.getItem('token') || '')
  const userInfo = ref(JSON.parse(localStorage.getItem('userInfo') || '{}'))
  const isLoading = ref(false)
  
  // 计算属性
  const isLoggedIn = computed(() => !!token.value)
  const userType = computed(() => userInfo.value.user_type || '')
  const username = computed(() => userInfo.value.username || '')
  const email = computed(() => userInfo.value.email || '')
  const phone = computed(() => userInfo.value.phone || '')
  const avatar = computed(() => userInfo.value.avatar || '')
  const isAdmin = computed(() => userType.value === 'admin')
  const isLandlord = computed(() => userType.value === 'landlord')
  const isTenant = computed(() => userType.value === 'tenant')
  
  // 方法
  function setToken(newToken) {
    token.value = newToken
    localStorage.setItem('token', newToken)
  }
  
  function setUserInfo(info) {
    userInfo.value = info
    localStorage.setItem('userInfo', JSON.stringify(info))
  }
  
  function clearStorage() {
    token.value = ''
    userInfo.value = {}
    localStorage.removeItem('token')
    localStorage.removeItem('userInfo')
    localStorage.removeItem('rememberMe')
  }
  
  // 登录
  function login(userData) {
    // 后端返回的是 access_token，前端期望的是 token
    setToken(userData.access_token || userData.token)
    setUserInfo(userData.user)
  }
  
  // 登出
  async function logout() {
    try {
      // 调用 API 登出（可选，用于服务端失效 token）
      if (token.value) {
        await logoutApi().catch(() => {})
      }
    } finally {
      // 清除本地数据
      clearStorage()
      // 跳转到登录页
      router.push('/login')
    }
  }
  
  // 获取当前用户信息
  async function fetchCurrentUser() {
    if (!token.value) {
      return null
    }
    
    isLoading.value = true
    try {
      const res = await getCurrentUser()
      setUserInfo(res.data)
      return res.data
    } catch (error) {
      console.error('获取用户信息失败:', error)
      // 如果获取失败，清除登录状态
      clearStorage()
      return null
    } finally {
      isLoading.value = false
    }
  }
  
  // 更新用户信息
  function updateUserInfo(info) {
    setUserInfo({ ...userInfo.value, ...info })
  }
  
  // 检查是否需要刷新用户信息
  async function checkAuth() {
    if (token.value && (!userInfo.value.username || Object.keys(userInfo.value).length === 0)) {
      await fetchCurrentUser()
    }
    return isLoggedIn.value
  }
  
  return {
    // 状态
    token,
    userInfo,
    isLoading,
    // 计算属性
    isLoggedIn,
    userType,
    username,
    email,
    phone,
    avatar,
    isAdmin,
    isLandlord,
    isTenant,
    // 方法
    setToken,
    setUserInfo,
    clearStorage,
    login,
    logout,
    fetchCurrentUser,
    updateUserInfo,
    checkAuth
  }
})
