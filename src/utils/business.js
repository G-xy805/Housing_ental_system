/**
 * 业务工具函数
 * 包含状态映射、数据格式化等业务相关工具函数
 */

/**
 * 房源状态映射
 */
export const houseStatusMap = {
  available: { text: '空闲', type: 'success' },
  rented: { text: '已租', type: 'info' },
  maintenance: { text: '维护中', type: 'warning' },
  partially_rented: { text: '部分出租', type: 'warning' },
  reserved: { text: '已预订', type: 'primary' },
  cancelled: { text: '已取消', type: 'danger' }
}

/**
 * 房源类型映射
 */
export const houseTypeMap = {
  whole: { text: '整租', type: 'primary' },
  shared: { text: '合租', type: 'info' }
}

/**
 * 租客状态映射
 */
export const tenantStatusMap = {
  pending: { text: '待租', type: 'warning' },
  active: { text: '在租', type: 'success' },
  expired: { text: '已退租', type: 'info' },
  blacklisted: { text: '黑名单', type: 'danger' }
}

/**
 * 合同状态映射
 */
export const contractStatusMap = {
  draft: { text: '草稿', type: 'info' },
  pending: { text: '待签约', type: 'warning' },
  active: { text: '履行中', type: 'success' },
  expired: { text: '已到期', type: 'info' },
  terminated: { text: '已终止', type: 'danger' },
  breached: { text: '已违约', type: 'danger' },
  renewed: { text: '已续签', type: 'primary' },
  cancelled: { text: '已取消', type: 'danger' }
}

/**
 * 支付状态映射
 */
export const paymentStatusMap = {
  pending: { text: '待支付', type: 'warning' },
  paid: { text: '已支付', type: 'success' },
  overdue: { text: '逾期', type: 'danger' },
  partial: { text: '部分支付', type: 'warning' },
  refunded: { text: '已退款', type: 'info' },
  cancelled: { text: '已取消', type: 'danger' }
}

/**
 * 支付方式映射
 */
export const paymentMethodMap = {
  cash: { text: '现金', icon: 'money-bill' },
  bank: { text: '银行转账', icon: 'bank' },
  wechat: { text: '微信支付', icon: 'wechat' },
  alipay: { text: '支付宝', icon: 'alipay' },
  credit_card: { text: '信用卡', icon: 'credit-card' }
}

/**
 * 支付类型映射
 */
export const paymentTypeMap = {
  rent: { text: '租金', type: 'primary' },
  deposit: { text: '押金', type: 'info' },
  utility: { text: '水电煤', type: 'warning' },
  other: { text: '其他', type: 'default' }
}

/**
 * 付款方式映射（合同）
 */
export const paymentCycleMap = {
  press_one_pay_one: { text: '押一付一', months: 1 },
  press_one_pay_three: { text: '押一付三', months: 3 },
  press_one_pay_six: { text: '押一付六', months: 6 },
  press_one_pay_twelve: { text: '押一付十二', months: 12 },
  '月付': { text: '月付', months: 1 },
  '季付': { text: '季付', months: 3 },
  '半年付': { text: '半年付', months: 6 },
  '年付': { text: '年付', months: 12 }
}

/**
 * 员工状态映射
 */
export const employeeStatusMap = {
  active: { text: '在职', type: 'success' },
  resigned: { text: '已离职', type: 'danger' },
  disabled: { text: '已禁用', type: 'warning' }
}

/**
 * 状态颜色类型映射
 */
export const statusColorMap = {
  success: 'success',
  warning: 'warning',
  danger: 'danger',
  info: 'info',
  primary: 'primary',
  default: 'default'
}

/**
 * 获取状态配置
 * @param {Object} statusMap 状态映射对象
 * @param {string} status 状态值
 * @returns {Object} 状态配置
 */
export function getStatusConfig(statusMap, status) {
  return statusMap[status] || { text: status, type: 'default' }
}

/**
 * 格式化日期时间
 * @param {Date|string|number} date 日期
 * @param {string} format 格式
 * @returns {string}
 */
export function formatDateTime(date, format = 'YYYY-MM-DD HH:mm:ss') {
  if (!date) return ''
  
  const d = new Date(date)
  if (isNaN(d.getTime())) return ''
  
  const year = d.getFullYear()
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  const hours = String(d.getHours()).padStart(2, '0')
  const minutes = String(d.getMinutes()).padStart(2, '0')
  const seconds = String(d.getSeconds()).padStart(2, '0')
  
  return format
    .replace('YYYY', year)
    .replace('MM', month)
    .replace('DD', day)
    .replace('HH', hours)
    .replace('mm', minutes)
    .replace('ss', seconds)
}

/**
 * 格式化日期
 * @param {Date|string|number} date 日期
 * @param {string} format 格式
 * @returns {string}
 */
export function formatDate(date, format = 'YYYY-MM-DD') {
  return formatDateTime(date, format)
}

/**
 * 格式化时间
 * @param {Date|string|number} date 时间
 * @param {string} format 格式
 * @returns {string}
 */
export function formatTime(date, format = 'HH:mm:ss') {
  return formatDateTime(date, format)
}

/**
 * 格式化金额
 * @param {number|string} amount 金额
 * @param {boolean} showSymbol 是否显示货币符号
 * @returns {string}
 */
export function formatMoney(amount, showSymbol = true) {
  if (amount === null || amount === undefined || amount === '') return showSymbol ? '¥0.00' : '0.00'
  
  const num = parseFloat(amount)
  if (isNaN(num)) return showSymbol ? '¥0.00' : '0.00'
  
  const formatted = num.toFixed(2).replace(/\d(?=(\d{3})+\.)/g, '$&,')
  return showSymbol ? `¥${formatted}` : formatted
}

/**
 * 格式化数字（千分位）
 * @param {number|string} num 数字
 * @returns {string}
 */
export function formatNumber(num) {
  if (num === null || num === undefined || num === '') return '0'
  return String(num).replace(/\B(?=(\d{3})+(?!\d))/g, ',')
}

/**
 * 计算面积
 * @param {number} length 长度
 * @param {number} width 宽度
 * @returns {string}
 */
export function calculateArea(length, width) {
  const area = parseFloat((length * width).toFixed(2))
  return `${area}㎡`
}

/**
 * 验证手机号
 * @param {string} phone 手机号
 * @returns {boolean}
 */
export function validatePhone(phone) {
  return /^1[3-9]\d{9}$/.test(phone)
}

/**
 * 验证邮箱
 * @param {string} email 邮箱
 * @returns {boolean}
 */
export function validateEmail(email) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)
}

/**
 * 验证身份证号
 * @param {string} idCard 身份证号
 * @returns {boolean}
 */
export function validateIdCard(idCard) {
  return /(^\d{15}$)|(^\d{18}$)|(^\d{17}(\d|X|x)$)/.test(idCard)
}

/**
 * 手机号脱敏（显示前3位和后4位）
 * @param {string} phone 手机号
 * @returns {string}
 */
export function maskPhone(phone) {
  if (!phone || phone.length !== 11) return phone
  return phone.replace(/(\d{3})\d{4}(\d{4})/, '$1****$2')
}

/**
 * 身份证号脱敏（显示前6位和后4位）
 * @param {string} idCard 身份证号
 * @returns {string}
 */
export function maskIdCard(idCard) {
  if (!idCard || idCard.length < 10) return idCard
  return idCard.replace(/(\d{6})\d{8,10}(\d{4})/, '$1**********$2')
}

/**
 * 生成合同编号
 * @param {string} prefix 前缀
 * @returns {string}
 */
export function generateContractNo(prefix = 'HT') {
  const timestamp = Date.now()
  const random = Math.floor(Math.random() * 10000).toString().padStart(4, '0')
  return `${prefix}${timestamp}${random}`
}

/**
 * 生成随机字符串
 * @param {number} length 长度
 * @returns {string}
 */
export function generateRandomString(length = 8) {
  const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
  let result = ''
  for (let i = 0; i < length; i++) {
    result += chars.charAt(Math.floor(Math.random() * chars.length))
  }
  return result
}

/**
 * 深拷贝
 * @param {*} obj 要拷贝的对象
 * @returns {*}
 */
export function deepClone(obj) {
  if (obj === null || typeof obj !== 'object') return obj
  if (obj instanceof Date) return new Date(obj)
  if (obj instanceof Array) return obj.map(item => deepClone(item))
  if (obj instanceof Object) {
    const copy = {}
    Object.keys(obj).forEach(key => {
      copy[key] = deepClone(obj[key])
    })
    return copy
  }
  return obj
}

/**
 * 防抖函数
 * @param {Function} func 函数
 * @param {number} wait 等待时间（毫秒）
 * @returns {Function}
 */
export function debounce(func, wait = 500) {
  let timeout
  return function (...args) {
    clearTimeout(timeout)
    timeout = setTimeout(() => {
      func.apply(this, args)
    }, wait)
  }
}

/**
 * 节流函数
 * @param {Function} func 函数
 * @param {number} wait 等待时间（毫秒）
 * @returns {Function}
 */
export function throttle(func, wait = 500) {
  let lastTime = 0
  return function (...args) {
    const now = Date.now()
    if (now - lastTime >= wait) {
      lastTime = now
      func.apply(this, args)
    }
  }
}

/**
 * 计算两个日期之间的天数差
 * @param {Date|string} startDate 开始日期
 * @param {Date|string} endDate 结束日期
 * @returns {number}
 */
export function getDaysBetween(startDate, endDate) {
  const start = new Date(startDate)
  const end = new Date(endDate)
  const diffTime = Math.abs(end - start)
  return Math.ceil(diffTime / (1000 * 60 * 60 * 24))
}

/**
 * 计算月租金（按年计算）
 * @param {number} annualRent 年租金
 * @returns {number}
 */
export function calculateMonthlyRent(annualRent) {
  return parseFloat((annualRent / 12).toFixed(2))
}

/**
 * 计算押金（通常是月租金的倍数）
 * @param {number} monthlyRent 月租金
 * @param {number} months 倍数（如 2 表示押二付三）
 * @returns {number}
 */
export function calculateDeposit(monthlyRent, months = 2) {
  return parseFloat((monthlyRent * months).toFixed(2))
}

/**
 * 计算滞纳金
 * @param {number} amount 金额
 * @param {number} days 迟交天数
 * @param {number} rate 滞纳金率（百分比）
 * @returns {number}
 */
export function calculateLateFee(amount, days, rate = 0.05) {
  return parseFloat((amount * rate * days).toFixed(2))
}

/**
 * 判断日期是否已过期
 * @param {Date|string} date 日期
 * @returns {boolean}
 */
export function isExpired(date) {
  if (!date) return false
  return new Date(date) < new Date()
}

/**
 * 判断日期是否即将到期（30天内）
 * @param {Date|string} date 日期
 * @returns {boolean}
 */
export function isExpiringSoon(date) {
  if (!date) return false
  const today = new Date()
  const targetDate = new Date(date)
  const diffTime = targetDate - today
  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))
  return diffDays > 0 && diffDays <= 30
}

/**
 * 获取合同租期
 * @param {string} startDate 开始日期
 * @param {string} endDate 结束日期
 * @returns {string}
 */
export function getContractPeriod(startDate, endDate) {
  const start = new Date(startDate)
  const end = new Date(endDate)
  const years = end.getFullYear() - start.getFullYear()
  const months = end.getMonth() - start.getMonth()
  
  if (years > 0) {
    return `${years}年${months > 0 ? months + '个月' : ''}`
  }
  return `${months}个月`
}

/**
 * 格式化房间方向
 * @param {string} direction 方向
 * @returns {string}
 */
export function formatDirection(direction) {
  const directionMap = {
    north: '北',
    south: '南',
    east: '东',
    west: '西',
    northeast: '东北',
    northwest: '西北',
    southeast: '东南',
    southwest: '西南'
  }
  return directionMap[direction.toLowerCase()] || direction
}

/**
 * 格式化楼层
 * @param {number} floor 楼层
 * @param {number} totalFloors 总楼层
 * @returns {string}
 */
export function formatFloor(floor, totalFloors) {
  if (!floor) return ''
  if (!totalFloors) return `第${floor}层`
  
  let floorText = ''
  if (floor === 1) floorText = '一层'
  else if (floor === 2) floorText = '二层'
  else if (floor === 3) floorText = '三层'
  else floorText = `${floor}层`
  
  return `${floorText}（共${totalFloors}层）`
}
