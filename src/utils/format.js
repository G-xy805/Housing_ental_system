/**
 * 格式化工具函数
 * 提供各种数据格式化功能
 */

/**
 * 金额格式化
 * @param {number|string} amount 金额
 * @param {Object} options 配置选项
 * @param {boolean} options.showSymbol 是否显示货币符号，默认 true
 * @param {number} options.decimals 小数位数，默认 2
 * @param {string} options.symbol 货币符号，默认 '¥'
 * @param {string} options.thousandsSeparator 千分位分隔符，默认 ','
 * @param {string} options.decimalSeparator 小数点分隔符，默认 '.'
 * @returns {string} 格式化后的金额字符串
 */
export function formatMoney(amount, options = {}) {
  const {
    showSymbol = true,
    decimals = 2,
    symbol = '¥',
    thousandsSeparator = ',',
    decimalSeparator = '.'
  } = options

  // 处理空值
  if (amount === null || amount === undefined || amount === '') {
    const zeroValue = '0'.padEnd(decimals + 1, '.0').slice(0, decimals + 1)
    return showSymbol ? `${symbol}${zeroValue}` : zeroValue
  }

  // 转换为数字
  const num = parseFloat(amount)
  if (isNaN(num)) {
    const zeroValue = '0'.padEnd(decimals + 1, '.0').slice(0, decimals + 1)
    return showSymbol ? `${symbol}${zeroValue}` : zeroValue
  }

  // 处理负数
  const isNegative = num < 0
  const absNum = Math.abs(num)

  // 格式化小数部分
  const fixedNum = absNum.toFixed(decimals)
  const [integerPart, decimalPart] = fixedNum.split('.')

  // 添加千分位分隔符
  const formattedInteger = integerPart.replace(/\B(?=(\d{3})+(?!\d))/g, thousandsSeparator)

  // 组合结果
  let result = formattedInteger
  if (decimals > 0 && decimalPart) {
    result += decimalSeparator + decimalPart
  }

  // 添加负号和货币符号
  if (isNegative) {
    result = '-' + result
  }
  if (showSymbol) {
    result = symbol + result
  }

  return result
}

/**
 * 日期格式化
 * @param {Date|string|number} date 日期
 * @param {string} format 格式字符串，支持：
 *   - YYYY: 四位年份
 *   - YY: 两位年份
 *   - MM: 两位月份
 *   - M: 月份
 *   - DD: 两位日期
 *   - D: 日期
 *   - HH: 两位小时（24小时制）
 *   - H: 小时（24小时制）
 *   - hh: 两位小时（12小时制）
 *   - h: 小时（12小时制）
 *   - mm: 两位分钟
 *   - m: 分钟
 *   - ss: 两位秒
 *   - s: 秒
 *   - A: AM/PM
 *   - a: am/pm
 * @returns {string} 格式化后的日期字符串
 */
export function formatDate(date, format = 'YYYY-MM-DD') {
  if (!date) return ''

  const d = new Date(date)
  if (isNaN(d.getTime())) return ''

  const year = d.getFullYear()
  const month = d.getMonth() + 1
  const day = d.getDate()
  const hours = d.getHours()
  const minutes = d.getMinutes()
  const seconds = d.getSeconds()
  const hour12 = hours % 12 || 12

  const formatMap = {
    YYYY: String(year),
    YY: String(year).slice(-2),
    MM: String(month).padStart(2, '0'),
    M: String(month),
    DD: String(day).padStart(2, '0'),
    D: String(day),
    HH: String(hours).padStart(2, '0'),
    H: String(hours),
    hh: String(hour12).padStart(2, '0'),
    h: String(hour12),
    mm: String(minutes).padStart(2, '0'),
    m: String(minutes),
    ss: String(seconds).padStart(2, '0'),
    s: String(seconds),
    A: hours < 12 ? 'AM' : 'PM',
    a: hours < 12 ? 'am' : 'pm'
  }

  // 按照长度从长到短排序替换，避免部分匹配问题
  const sortedKeys = Object.keys(formatMap).sort((a, b) => b.length - a.length)
  let result = format

  sortedKeys.forEach(key => {
    result = result.replace(new RegExp(key, 'g'), formatMap[key])
  })

  return result
}

/**
 * 状态格式化映射表
 * 根据数据库模型定义的状态
 */
const statusMaps = {
  // 房源状态
  house: {
    available: '空闲',
    rented: '已租',
    maintenance: '维护中',
    partially_rented: '部分出租',
    reserved: '已预订',
    cancelled: '已取消'
  },
  // 房源类型
  houseType: {
    whole: '整租',
    shared: '合租'
  },
  // 租客状态
  tenant: {
    pending: '待租',
    active: '在租',
    expired: '已退租',
    blacklisted: '黑名单'
  },
  // 合同状态
  contract: {
    draft: '草稿',
    pending: '待签约',
    active: '履行中',
    expired: '已到期',
    terminated: '已终止',
    breached: '已违约',
    renewed: '已续签',
    cancelled: '已取消'
  },
  // 支付状态
  payment: {
    pending: '待支付',
    paid: '已支付',
    overdue: '逾期',
    partial: '部分支付',
    refunded: '已退款',
    cancelled: '已取消'
  },
  // 支付方式
  paymentMethod: {
    cash: '现金',
    bank: '银行转账',
    wechat: '微信支付',
    alipay: '支付宝',
    credit_card: '信用卡'
  },
  // 支付类型
  paymentType: {
    rent: '租金',
    deposit: '押金',
    utility: '水电煤',
    other: '其他'
  },
  // 员工状态
  employee: {
    active: '在职',
    resigned: '已离职',
    disabled: '已禁用'
  },
  // 房东状态
  landlord: {
    active: '正常',
    inactive: '停用',
    blacklisted: '黑名单'
  },
  // 房间状态
  room: {
    available: '空闲',
    rented: '已租',
    maintenance: '维护中'
  }
}

/**
 * 状态格式化
 * @param {string} type 状态类型（house/tenant/contract/payment/paymentMethod/paymentType/employee/landlord/room）
 * @param {string} status 状态值
 * @returns {string} 状态的中文文本
 */
export function formatStatus(type, status) {
  if (!type || !status) return status || ''

  const map = statusMaps[type]
  if (!map) return status

  return map[status] || status
}

/**
 * 获取状态配置（包含文本和类型，用于 Element Plus Tag 组件）
 * @param {string} type 状态类型
 * @param {string} status 状态值
 * @returns {Object} 状态配置 { text, type }
 */
export function getStatusConfig(type, status) {
  const text = formatStatus(type, status)

  // 状态颜色映射
  const colorMap = {
    // 房源状态颜色
    available: 'success',
    rented: 'info',
    maintenance: 'warning',
    partially_rented: 'warning',
    reserved: 'primary',
    // 租客状态颜色
    pending: 'warning',
    active: 'success',
    expired: 'info',
    blacklisted: 'danger',
    // 合同状态颜色
    draft: 'info',
    pending: 'warning',
    active: 'success',
    expired: 'info',
    terminated: 'danger',
    breached: 'danger',
    renewed: 'primary',
    // 支付状态颜色
    pending: 'warning',
    paid: 'success',
    overdue: 'danger',
    partial: 'warning',
    refunded: 'info',
    // 员工状态颜色
    resigned: 'danger',
    disabled: 'warning'
  }

  return {
    text,
    type: colorMap[status] || 'default'
  }
}

/**
 * 文件大小格式化
 * @param {number} bytes 字节数
 * @param {number} decimals 小数位数，默认 2
 * @returns {string} 格式化后的文件大小
 */
export function formatFileSize(bytes, decimals = 2) {
  if (bytes === null || bytes === undefined || bytes === 0) return '0 B'

  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))

  return parseFloat((bytes / Math.pow(k, i)).toFixed(decimals)) + ' ' + sizes[i]
}

/**
 * 手机号格式化（隐藏中间4位）
 * @param {string} phone 手机号
 * @param {string} separator 分隔符，默认空格
 * @returns {string} 格式化后的手机号
 */
export function formatPhoneNumber(phone, separator = ' ') {
  if (!phone) return ''

  // 移除所有非数字字符
  const cleaned = String(phone).replace(/\D/g, '')

  // 验证手机号长度
  if (cleaned.length !== 11) return phone

  // 格式化为：138 1234 5678 或 138****5678
  return `${cleaned.slice(0, 3)}${separator}${cleaned.slice(3, 7)}${separator}${cleaned.slice(7)}`
}

/**
 * 手机号脱敏（隐藏中间4位）
 * @param {string} phone 手机号
 * @returns {string} 脱敏后的手机号
 */
export function maskPhoneNumber(phone) {
  if (!phone) return ''

  const cleaned = String(phone).replace(/\D/g, '')
  if (cleaned.length !== 11) return phone

  return cleaned.replace(/(\d{3})\d{4}(\d{4})/, '$1****$2')
}

/**
 * 身份证号脱敏
 * @param {string} idCard 身份证号
 * @returns {string} 脱敏后的身份证号
 */
export function maskIdCardNumber(idCard) {
  if (!idCard) return ''

  const cleaned = String(idCard).replace(/\s/g, '')
  if (cleaned.length !== 15 && cleaned.length !== 18) return idCard

  // 显示前6位和后4位
  return cleaned.replace(/(\d{6})\d+(\d{4})/, '$1********$2')
}

/**
 * 银行卡号格式化
 * @param {string} cardNo 银行卡号
 * @param {string} separator 分隔符，默认空格
 * @returns {string} 格式化后的银行卡号
 */
export function formatBankCard(cardNo, separator = ' ') {
  if (!cardNo) return ''

  const cleaned = String(cardNo).replace(/\D/g, '')
  if (cleaned.length < 16) return cardNo

  // 每4位一组
  return cleaned.replace(/(.{4})/g, `$1${separator}`).trim()
}

/**
 * 银行卡号脱敏
 * @param {string} cardNo 银行卡号
 * @returns {string} 脱敏后的银行卡号
 */
export function maskBankCard(cardNo) {
  if (!cardNo) return ''

  const cleaned = String(cardNo).replace(/\D/g, '')
  if (cleaned.length < 16) return cardNo

  // 显示前4位和后4位
  return cleaned.replace(/(\d{4})\d+(\d{4})/, '$1 **** **** $2')
}

/**
 * 百分比格式化
 * @param {number} value 数值
 * @param {number} decimals 小数位数，默认 2
 * @returns {string} 格式化后的百分比
 */
export function formatPercent(value, decimals = 2) {
  if (value === null || value === undefined || value === '') return '0%'

  const num = parseFloat(value)
  if (isNaN(num)) return '0%'

  return num.toFixed(decimals) + '%'
}

/**
 * 数字格式化（千分位）
 * @param {number|string} num 数字
 * @param {number} decimals 小数位数，默认不限制
 * @returns {string} 格式化后的数字
 */
export function formatNumber(num, decimals) {
  if (num === null || num === undefined || num === '') return '0'

  const n = parseFloat(num)
  if (isNaN(n)) return '0'

  let formatted
  if (decimals !== undefined) {
    formatted = n.toFixed(decimals)
  } else {
    formatted = String(n)
  }

  const [integerPart, decimalPart] = formatted.split('.')
  const formattedInteger = integerPart.replace(/\B(?=(\d{3})+(?!\d))/g, ',')

  return decimalPart ? `${formattedInteger}.${decimalPart}` : formattedInteger
}

/**
 * 面积格式化
 * @param {number} area 面积（平方米）
 * @param {number} decimals 小数位数，默认 2
 * @returns {string} 格式化后的面积
 */
export function formatArea(area, decimals = 2) {
  if (area === null || area === undefined || area === '') return '0㎡'

  const num = parseFloat(area)
  if (isNaN(num)) return '0㎡'

  return num.toFixed(decimals) + '㎡'
}

/**
 * 楼层格式化
 * @param {number|string} floor 楼层
 * @param {number|string} totalFloors 总楼层
 * @returns {string} 格式化后的楼层信息
 */
export function formatFloor(floor, totalFloors) {
  if (!floor) return ''

  if (!totalFloors) return `第${floor}层`

  return `${floor}/${totalFloors}层`
}

/**
 * 租期格式化
 * @param {string} startDate 开始日期
 * @param {string} endDate 结束日期
 * @returns {string} 格式化后的租期
 */
export function formatLeasePeriod(startDate, endDate) {
  if (!startDate || !endDate) return ''

  const start = new Date(startDate)
  const end = new Date(endDate)

  if (isNaN(start.getTime()) || isNaN(end.getTime())) return ''

  const years = end.getFullYear() - start.getFullYear()
  const months = end.getMonth() - start.getMonth()
  const days = end.getDate() - start.getDate()

  let result = ''

  if (years > 0) {
    result += `${years}年`
  }

  if (months > 0 || years > 0) {
    result += `${months}个月`
  }

  if (days > 0 && years === 0) {
    result += `${days}天`
  }

  return result || '不足1个月'
}

/**
 * 相对时间格式化
 * @param {Date|string|number} date 日期
 * @returns {string} 相对时间描述
 */
export function formatRelativeTime(date) {
  if (!date) return ''

  const d = new Date(date)
  if (isNaN(d.getTime())) return ''

  const now = new Date()
  const diff = now.getTime() - d.getTime()

  const seconds = Math.floor(diff / 1000)
  const minutes = Math.floor(seconds / 60)
  const hours = Math.floor(minutes / 60)
  const days = Math.floor(hours / 24)
  const months = Math.floor(days / 30)
  const years = Math.floor(days / 365)

  if (seconds < 60) return '刚刚'
  if (minutes < 60) return `${minutes}分钟前`
  if (hours < 24) return `${hours}小时前`
  if (days < 30) return `${days}天前`
  if (months < 12) return `${months}个月前`
  return `${years}年前`
}
