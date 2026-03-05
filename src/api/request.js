import axios from 'axios'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/store/user'
import router from '@/router'

// 创建 axios 实例
const request = axios.create({
  baseURL: '/api',
  timeout: 30000
})

// 请求拦截器
request.interceptors.request.use(
  config => {
    // 动态获取 userStore（避免循环依赖）
    const userStore = useUserStore()
    
    if (userStore.token) {
      config.headers.Authorization = `Bearer ${userStore.token}`
    }
    
    // 设置默认 Content-Type 为 JSON，除非是 FormData
    if (!config.headers['Content-Type'] && !(config.data instanceof FormData)) {
      config.headers['Content-Type'] = 'application/json'
    }
    
    // 添加请求时间戳（可选，用于防止缓存）
    if (config.method === 'get') {
      config.params = {
        ...config.params,
        _t: Date.now()
      }
    }
    
    // 调试：打印 PUT 请求的数据
    if (config.method === 'put' && (config.url.includes('/houses/') || config.url.includes('/payments/'))) {
      console.log('发送 PUT 请求:', config.url)
      console.log('请求数据:', config.data)
      console.log('请求头:', config.headers)
    }
    
    return config
  },
  error => {
    console.error('请求拦截器错误:', error)
    ElMessage.error('网络错误，请稍后重试')
    return Promise.reject(error)
  }
)

// 响应拦截器
request.interceptors.response.use(
  response => {
    // 如果响应的是二进制数据（如下载），直接返回
    if (response.config.responseType === 'blob') {
      return response
    }
    
    const res = response.data
    
    // 根据后端返回的状态码判断（这里假设成功状态码为 200 或 0）
    // 如果后端直接返回数据，没有 code 字段，也视为成功
    // 特殊处理：如果有 success 字段，不管值是什么，都返回原始响应，让前端自己处理
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
    console.error('响应错误:', error)
    console.error('错误详情:', {
      message: error.message,
      code: error.code,
      status: error.response?.status,
      data: error.response?.data,
      config: {
        url: error.config?.url,
        method: error.config?.method,
        baseURL: error.config?.baseURL,
        headers: error.config?.headers
      }
    })
    
    // 处理网络错误
    if (error.message === 'Network Error') {
      ElMessage.error('网络连接失败，请检查网络设置')
      return Promise.reject(error)
    }
    
    // 处理超时错误
    if (error.code === 'ECONNABORTED' || error.message.includes('timeout')) {
      ElMessage.error('请求超时，请稍后重试')
      return Promise.reject(error)
    }
    
    // 处理 HTTP 错误状态码
    if (error.response) {
      const { status, data } = error.response
      
      // 打印详细错误信息
      console.error('响应错误详情:', {
        status,
        data,
        error: data?.error,
        message: data?.message
      })
      
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
          ElMessage.error('登录已过期，请重新登录')
          // 清除用户信息并跳转登录页
          handleUnauthorized()
          break
          
        case 403:
          ElMessage.error(errorMsg || '拒绝访问')
          // 可选：跳转到 403 页面
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
          ElMessage.error('请求过于频繁，请稍后再试')
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
      ElMessage.error('网络错误，请检查网络连接')
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
  
  // 如果当前不在登录页，跳转到登录页
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
