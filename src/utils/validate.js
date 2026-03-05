/**
 * 验证工具函数
 * 提供各种数据验证功能
 */

/**
 * 手机号验证
 * 规则：11位数字，1开头
 * @param {string} phone 手机号
 * @returns {Object} 验证结果 { valid: boolean, message: string }
 */
export function validatePhone(phone) {
  if (!phone) {
    return { valid: false, message: '手机号不能为空' }
  }

  const cleaned = String(phone).replace(/\s/g, '')

  if (!/^1\d{10}$/.test(cleaned)) {
    return { valid: false, message: '请输入正确的手机号' }
  }

  // 更严格的验证：第二位应该是 3-9
  if (!/^1[3-9]\d{9}$/.test(cleaned)) {
    return { valid: false, message: '请输入正确的手机号' }
  }

  return { valid: true, message: '' }
}

/**
 * 邮箱验证
 * @param {string} email 邮箱
 * @returns {Object} 验证结果 { valid: boolean, message: string }
 */
export function validateEmail(email) {
  if (!email) {
    return { valid: false, message: '邮箱不能为空' }
  }

  // RFC 5322 标准的简化版本
  const emailRegex = /^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$/

  if (!emailRegex.test(email)) {
    return { valid: false, message: '请输入正确的邮箱地址' }
  }

  return { valid: true, message: '' }
}

/**
 * 身份证号验证
 * 规则：15位或18位，最后一位可以是X
 * @param {string} idCard 身份证号
 * @returns {Object} 验证结果 { valid: boolean, message: string }
 */
export function validateIdCard(idCard) {
  if (!idCard) {
    return { valid: false, message: '身份证号不能为空' }
  }

  const cleaned = String(idCard).replace(/\s/g, '')

  // 基本格式验证
  if (!/(^\d{15}$)|(^\d{17}(\d|X|x)$)/.test(cleaned)) {
    return { valid: false, message: '请输入正确的身份证号' }
  }

  // 18位身份证验证
  if (cleaned.length === 18) {
    // 校验码验证
    const weights = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
    const checkCodes = ['1', '0', 'X', '9', '8', '7', '6', '5', '4', '3', '2']

    let sum = 0
    for (let i = 0; i < 17; i++) {
      sum += parseInt(cleaned[i]) * weights[i]
    }

    const checkCode = checkCodes[sum % 11]
    if (cleaned[17].toUpperCase() !== checkCode) {
      return { valid: false, message: '身份证号校验码错误' }
    }

    // 出生日期验证
    const year = parseInt(cleaned.substring(6, 10))
    const month = parseInt(cleaned.substring(10, 12))
    const day = parseInt(cleaned.substring(12, 14))

    if (!validateBirthDate(year, month, day)) {
      return { valid: false, message: '身份证号中的出生日期无效' }
    }
  }

  // 15位身份证验证
  if (cleaned.length === 15) {
    const year = 1900 + parseInt(cleaned.substring(6, 8))
    const month = parseInt(cleaned.substring(8, 10))
    const day = parseInt(cleaned.substring(10, 12))

    if (!validateBirthDate(year, month, day)) {
      return { valid: false, message: '身份证号中的出生日期无效' }
    }
  }

  return { valid: true, message: '' }
}

/**
 * 验证出生日期是否有效
 * @param {number} year 年
 * @param {number} month 月
 * @param {number} day 日
 * @returns {boolean}
 */
function validateBirthDate(year, month, day) {
  if (month < 1 || month > 12) return false
  if (day < 1 || day > 31) return false

  const date = new Date(year, month - 1, day)
  if (date.getFullYear() !== year || date.getMonth() !== month - 1 || date.getDate() !== day) {
    return false
  }

  // 不能是未来日期
  const now = new Date()
  if (date > now) return false

  return true
}

/**
 * 银行卡号验证
 * 规则：16-19位数字
 * @param {string} cardNo 银行卡号
 * @returns {Object} 验证结果 { valid: boolean, message: string }
 */
export function validateBankCard(cardNo) {
  if (!cardNo) {
    return { valid: false, message: '银行卡号不能为空' }
  }

  const cleaned = String(cardNo).replace(/\s/g, '')

  if (!/^\d{16,19}$/.test(cleaned)) {
    return { valid: false, message: '请输入正确的银行卡号' }
  }

  // Luhn算法验证（银行卡校验算法）
  if (!luhnCheck(cleaned)) {
    return { valid: false, message: '银行卡号校验失败' }
  }

  return { valid: true, message: '' }
}

/**
 * Luhn算法校验
 * @param {string} num 数字字符串
 * @returns {boolean}
 */
function luhnCheck(num) {
  let sum = 0
  let isEven = false

  for (let i = num.length - 1; i >= 0; i--) {
    let digit = parseInt(num[i])

    if (isEven) {
      digit *= 2
      if (digit > 9) {
        digit -= 9
      }
    }

    sum += digit
    isEven = !isEven
  }

  return sum % 10 === 0
}

/**
 * 密码强度验证
 * @param {string} password 密码
 * @param {Object} options 配置选项
 * @param {number} options.minLength 最小长度，默认 6
 * @param {number} options.maxLength 最大长度，默认 20
 * @param {boolean} options.requireLowercase 是否要求小写字母，默认 false
 * @param {boolean} options.requireUppercase 是否要求大写字母，默认 false
 * @param {boolean} options.requireNumber 是否要求数字，默认 false
 * @param {boolean} options.requireSpecial 是否要求特殊字符，默认 false
 * @returns {Object} 验证结果 { valid: boolean, message: string, strength: string, score: number }
 */
export function validatePassword(password, options = {}) {
  const {
    minLength = 6,
    maxLength = 20,
    requireLowercase = false,
    requireUppercase = false,
    requireNumber = false,
    requireSpecial = false
  } = options

  if (!password) {
    return { valid: false, message: '密码不能为空', strength: '无', score: 0 }
  }

  const errors = []

  // 长度验证
  if (password.length < minLength) {
    errors.push(`密码长度不能少于${minLength}位`)
  }
  if (password.length > maxLength) {
    errors.push(`密码长度不能超过${maxLength}位`)
  }

  // 复杂度验证
  if (requireLowercase && !/[a-z]/.test(password)) {
    errors.push('密码必须包含小写字母')
  }
  if (requireUppercase && !/[A-Z]/.test(password)) {
    errors.push('密码必须包含大写字母')
  }
  if (requireNumber && !/\d/.test(password)) {
    errors.push('密码必须包含数字')
  }
  if (requireSpecial && !/[!@#$%^&*(),.?":{}|<>]/.test(password)) {
    errors.push('密码必须包含特殊字符')
  }

  if (errors.length > 0) {
    return { valid: false, message: errors[0], strength: '弱', score: 0 }
  }

  // 计算密码强度
  let score = 0
  const checks = {
    hasLower: /[a-z]/.test(password),
    hasUpper: /[A-Z]/.test(password),
    hasNumber: /\d/.test(password),
    hasSpecial: /[!@#$%^&*(),.?":{}|<>]/.test(password),
    hasLength: password.length >= 8
  }

  if (checks.hasLower) score += 1
  if (checks.hasUpper) score += 1
  if (checks.hasNumber) score += 1
  if (checks.hasSpecial) score += 2
  if (checks.hasLength) score += 1
  if (password.length >= 12) score += 1

  let strength = '弱'
  if (score >= 6) strength = '强'
  else if (score >= 4) strength = '中'

  return {
    valid: true,
    message: '',
    strength,
    score,
    checks
  }
}

/**
 * 用户名验证
 * @param {string} username 用户名
 * @param {Object} options 配置选项
 * @param {number} options.minLength 最小长度，默认 3
 * @param {number} options.maxLength 最大长度，默认 20
 * @returns {Object} 验证结果 { valid: boolean, message: string }
 */
export function validateUsername(username, options = {}) {
  const { minLength = 3, maxLength = 20 } = options

  if (!username) {
    return { valid: false, message: '用户名不能为空' }
  }

  if (username.length < minLength) {
    return { valid: false, message: `用户名长度不能少于${minLength}位` }
  }

  if (username.length > maxLength) {
    return { valid: false, message: `用户名长度不能超过${maxLength}位` }
  }

  // 只允许字母、数字、下划线
  if (!/^[a-zA-Z0-9_]+$/.test(username)) {
    return { valid: false, message: '用户名只能包含字母、数字和下划线' }
  }

  // 不能以数字开头
  if (/^\d/.test(username)) {
    return { valid: false, message: '用户名不能以数字开头' }
  }

  return { valid: true, message: '' }
}

/**
 * 姓名验证
 * @param {string} name 姓名
 * @returns {Object} 验证结果 { valid: boolean, message: string }
 */
export function validateName(name) {
  if (!name) {
    return { valid: false, message: '姓名不能为空' }
  }

  const trimmed = String(name).trim()

  if (trimmed.length < 2) {
    return { valid: false, message: '姓名长度不能少于2位' }
  }

  if (trimmed.length > 20) {
    return { valid: false, message: '姓名长度不能超过20位' }
  }

  // 支持中文、英文、空格
  if (!/^[\u4e00-\u9fa5a-zA-Z\s]+$/.test(trimmed)) {
    return { valid: false, message: '姓名只能包含中文和英文' }
  }

  return { valid: true, message: '' }
}

/**
 * 金额验证
 * @param {number|string} amount 金额
 * @param {Object} options 配置选项
 * @param {number} options.min 最小值
 * @param {number} options.max 最大值
 * @param {number} options.decimals 最大小数位数
 * @returns {Object} 验证结果 { valid: boolean, message: string }
 */
export function validateAmount(amount, options = {}) {
  const { min, max, decimals = 2 } = options

  if (amount === null || amount === undefined || amount === '') {
    return { valid: false, message: '金额不能为空' }
  }

  const num = parseFloat(amount)

  if (isNaN(num)) {
    return { valid: false, message: '请输入有效的金额' }
  }

  if (num < 0) {
    return { valid: false, message: '金额不能为负数' }
  }

  if (min !== undefined && num < min) {
    return { valid: false, message: `金额不能小于${min}` }
  }

  if (max !== undefined && num > max) {
    return { valid: false, message: `金额不能大于${max}` }
  }

  // 验证小数位数
  const decimalPart = String(amount).split('.')[1]
  if (decimalPart && decimalPart.length > decimals) {
    return { valid: false, message: `金额最多保留${decimals}位小数` }
  }

  return { valid: true, message: '' }
}

/**
 * URL验证
 * @param {string} url URL地址
 * @returns {Object} 验证结果 { valid: boolean, message: string }
 */
export function validateUrl(url) {
  if (!url) {
    return { valid: false, message: 'URL不能为空' }
  }

  try {
    new URL(url)
    return { valid: true, message: '' }
  } catch {
    return { valid: false, message: '请输入正确的URL地址' }
  }
}

/**
 * 日期范围验证
 * @param {string|Date} startDate 开始日期
 * @param {string|Date} endDate 结束日期
 * @returns {Object} 验证结果 { valid: boolean, message: string }
 */
export function validateDateRange(startDate, endDate) {
  if (!startDate || !endDate) {
    return { valid: false, message: '日期范围不能为空' }
  }

  const start = new Date(startDate)
  const end = new Date(endDate)

  if (isNaN(start.getTime())) {
    return { valid: false, message: '开始日期格式无效' }
  }

  if (isNaN(end.getTime())) {
    return { valid: false, message: '结束日期格式无效' }
  }

  if (start > end) {
    return { valid: false, message: '开始日期不能晚于结束日期' }
  }

  return { valid: true, message: '' }
}

/**
 * 表单验证器工厂函数
 * 用于 Element Plus 表单验证
 * @param {Function} validateFn 验证函数
 * @returns {Function} Element Plus 表单验证器
 */
export function createValidator(validateFn) {
  return (rule, value, callback) => {
    const result = validateFn(value, rule)
    if (result.valid) {
      callback()
    } else {
      callback(new Error(result.message))
    }
  }
}

/**
 * 批量验证
 * @param {Array} rules 验证规则数组 [{ field, value, validator }]
 * @returns {Object} 验证结果 { valid: boolean, errors: Object }
 */
export function validateAll(rules) {
  const errors = {}

  rules.forEach(({ field, value, validator, ...options }) => {
    const result = validator(value, options)
    if (!result.valid) {
      errors[field] = result.message
    }
  })

  return {
    valid: Object.keys(errors).length === 0,
    errors
  }
}
