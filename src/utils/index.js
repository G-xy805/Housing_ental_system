/**
 * 工具函数导出
 */

// 格式化工具
export * from './business'

// 通用工具
export { formatDate, formatMoney, formatNumber, calculateArea } from './business'
export { validatePhone, validateEmail, validateIdCard } from './business'
export { generateRandomString, deepClone, debounce, throttle } from './business'

// 权限工具
export * from './permission'