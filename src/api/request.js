import axios from 'axios'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/store/user'
import router from '@/router'

// 创建 axios 实例
const request = axios.create({
  baseURL: '/api',
  timeout: 30000
})

// 存储所有活跃的请求控制器
const pendingRequests = new Map()

/**
 * 生成请求的唯一键
 * @param {Object} config 请求配置
 * @returns {string} 请求唯一键
 */
const generateRequestKey = (config) => {
  const { method, url, params, data } = config
  // 对于 FormData（文件上传），不参与唯一键生成，避免取消并发上传
  // 添加时间戳确保每次上传请求都是唯一的
  const dataKey = data instanceof FormData ? `formData_${Date.now()}` : JSON.stringify(data)
  return [method, url, JSON.stringify(params), dataKey].join('&')
}

/**
 * 添加请求到待处理列表
 * @param {Object} config 请求配置
 * @returns {AbortController} AbortController 实例
 */
const addPendingRequest = (config) => {
  // 如果配置中已经提供了 signal,则不创建新的 AbortController
  if (config.signal) {
    return null
  }

  const requestKey = generateRequestKey(config)
  
  // 如果存在相同的请求,取消之前的请求
  if (pendingRequests.has(requestKey)) {
    const controller = pendingRequests.get(requestKey)
    controller.abort()
    pendingRequests.delete(requestKey)
  }

  // 创建新的 AbortController
  const controller = new AbortController()
  config.signal = controller.signal
  pendingRequests.set(requestKey, controller)

  return controller
}

/**
 * 从待处理列表中移除请求
 * @param {Object} config 请求配置
 */
const removePendingRequest = (config) => {
  const requestKey = generateRequestKey(config)
  
  if (pendingRequests.has(requestKey)) {
    pendingRequests.delete(requestKey)
  }
}

/**
 * 取消所有待处理的请求
 */
export const cancelAllRequests = () => {
  pendingRequests.forEach((controller, key) => {
    controller.abort()
  })
  pendingRequests.clear()
}

/**
 * 取消特定请求
 * @param {string} url 请求 URL
 * @param {string} method 请求方法
 */
export const cancelRequest = (url, method = 'get') => {
  const requestKey = `${method.toLowerCase()}&${url}`
  
  pendingRequests.forEach((controller, key) => {
    if (key.includes(requestKey)) {
      controller.abort()
      pendingRequests.delete(key)
    }
  })
}

// 请求拦截器
request.interceptors.request.use(
  config => {
    // 添加请求取消支持
    addPendingRequest(config)

    // 动态获取 userStore(避免循环依赖)
    const userStore = useUserStore()
    
    if (userStore.token) {
      config.headers.Authorization = `Bearer ${userStore.token}`
    }
    
    // 设置默认 Content-Type 为 JSON,除非是 FormData
    if (!config.headers['Content-Type'] && !(config.data instanceof FormData)) {
      config.headers['Content-Type'] = 'application/json'
    }
    
    // 添加请求时间戳(可选,用于防止缓存)
    if (config.method === 'get') {
      config.params = {
        ...config.params,
        _t: Date.now()
      }
    }
    
    return config
  },
  error => {
    console.error('请求拦截器错误:', error)
    ElMessage.error('网络错误,请稍后重试')
    return Promise.reject(error)
  }
)

// 响应拦截器
request.interceptors.response.use(
  response => {
    // 请求完成后从待处理列表中移除
    removePendingRequest(response.config)

    // 如果响应的是二进制数据(如下载),直接返回
    if (response.config.responseType === 'blob') {
      return response
    }
    
    const res = response.data
    
    // 根据后端返回的状态码判断(这里假设成功状态码为 200 或 0)
    // 如果后端直接返回数据,没有 code 字段,也视为成功
    // 特殊处理:如果有 success 字段,不管值是什么,都返回原始响应,让前端自己处理
    if (res.success !== undefined) {
      return res
    }
    if (res.code === undefined || res.code === 200 || res.code === 0) {
      return res
    }
    
    // 业务错误
    ElMessage.error(res.message || '请求失败')
    return Promise.reject(new Error(res.message || '请求失败'))
  },
  error => {
    // 请求完成后从待处理列表中移除
    if (error.config) {
      removePendingRequest(error.config)
    }

    console.error('响应错误:', error.message)
    
    // 处理请求被取消的情况
    if (error.name === 'CanceledError' || error.code === 'ERR_CANCELED') {
      console.log('请求已取消:', error.config?.url)
      return Promise.reject(error)
    }
    
    // 处理网络错误
    if (error.message === 'Network Error') {
      ElMessage.error('网络连接失败,请检查网络设置')
      return Promise.reject(error)
    }
    
    // 处理超时错误
    if (error.code === 'ECONNABORTED' || error.message.includes('timeout')) {
      ElMessage.error('请求超时,请稍后重试')
      return Promise.reject(error)
    }
    
    // 处理 HTTP 错误状态码
    if (error.response) {
      const { status, data } = error.response
      
      // 获取错误信息
      let errorMsg = data?.message || getHttpErrorMessage(status)
      
      // 处理422错误的详细信息
      if (status === 422 && data?.error) {
        if (typeof data.error === 'string') {
          errorMsg = data.error
        } else if (typeof data.error === 'object') {
          // 提取错误对象中的信息
          const errorMessages = []
          for (const [key, value] of Object.entries(data.error)) {
            if (Array.isArray(value)) {
              errorMessages.push(`${key}: ${value.join(', ')}`)
            } else {
              errorMessages.push(`${key}: ${value}`)
            }
          }
          errorMsg = errorMessages.join('; ')
        }
      }
      
      switch (status) {
        case 400:
          ElMessage.error(errorMsg)
          break
          
        case 401:
          ElMessage.error('登录已过期,请重新登录')
          // 清除用户信息并跳转登录页
          handleUnauthorized()
          break
          
        case 403:
          ElMessage.error(errorMsg || '拒绝访问')
          // 可选:跳转到 403 页面
          // router.push('/403')
          break
          
        case 404:
          ElMessage.error(errorMsg || '请求的资源不存在')
          break
          
        case 408:
          ElMessage.error('请求超时')
          break
          
        case 422:
          // 表单验证错误
          ElMessage.error(errorMsg || '参数验证失败')
          break
          
        case 429:
          ElMessage.error('请求过于频繁,请稍后再试')
          break
          
        case 500:
          ElMessage.error(errorMsg || '服务器错误')
          break
          
        case 502:
          ElMessage.error('网关错误')
          break
          
        case 503:
          ElMessage.error('服务不可用')
          break
          
        case 504:
          ElMessage.error('网关超时')
          break
          
        default:
          ElMessage.error(errorMsg || `请求失败 (${status})`)
      }
    } else {
      // 没有响应的情况
      ElMessage.error('网络错误,请检查网络连接')
    }
    
    return Promise.reject(error)
  }
)

/**
 * 获取 HTTP 状态码对应的错误信息
 * @param {number} status HTTP 状态码
 * @returns {string}
 */
function getHttpErrorMessage(status) {
  const errorMessages = {
    400: '请求参数错误',
    401: '未授权，请重新登录',
    403: '拒绝访问',
    404: '请求的资源不存在',
    408: '请求超时',
    422: '参数验证失败',
    429: '请求过于频繁',
    500: '服务器内部错误',
    502: '网关错误',
    503: '服务不可用',
    504: '网关超时'
  }
  return errorMessages[status] || '请求失败'
}

/**
 * 处理未授权情况
 */
function handleUnauthorized() {
  const userStore = useUserStore()
  userStore.clearStorage()
  
  // 取消所有待处理的请求
  cancelAllRequests()
  
  // 如果当前不在登录页,跳转到登录页
  if (router.currentRoute.value.path !== '/login') {
    router.push({
      path: '/login',
      query: {
        redirect: router.currentRoute.value.fullPath
      }
    })
  }
}

export default request
