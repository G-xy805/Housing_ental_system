/**
 * 权限工具函数
 * 提供权限检查、角色判断和Vue自定义指令
 */

import { useUserStore } from '@/store/user'

// ==================== 权限规则配置 ====================

/**
 * 角色权限映射表
 * 定义每个角色允许的操作类型
 */
const ROLE_PERMISSIONS = {
  admin: ['view', 'create', 'edit', 'delete'],
  staff: ['view', 'create', 'edit'],
  employee: ['view', 'create', 'edit'],
  landlord: ['view', 'create', 'edit'],
  tenant: ['view']
}

/**
 * 支持的操作类型
 */
export const PERMISSION_ACTIONS = {
  VIEW: 'view',
  CREATE: 'create',
  EDIT: 'edit',
  DELETE: 'delete'
}

// ==================== 权限检查函数 ====================

/**
 * 检查指定角色是否有特定操作权限
 * @param {string} role - 用户角色 (admin, staff, employee, landlord, tenant)
 * @param {string} action - 操作类型 (view, create, edit, delete)
 * @returns {boolean} 是否有权限
 * 
 * @example
 * checkPermission('admin', 'delete') // true
 * checkPermission('tenant', 'edit') // false
 * checkPermission('staff', 'view') // true
 */
export function checkPermission(role, action) {
  if (!role || !action) {
    console.warn('checkPermission: role 和 action 参数不能为空')
    return false
  }

  // 标准化角色名称（转小写）
  const normalizedRole = role.toLowerCase()
  
  // 获取该角色的权限列表
  const permissions = ROLE_PERMISSIONS[normalizedRole]
  
  if (!permissions) {
    console.warn(`checkPermission: 未知角色 "${role}"`)
    return false
  }

  return permissions.includes(action)
}

/**
 * 检查当前用户是否有特定操作权限
 * @param {string} action - 操作类型 (view, create, edit, delete)
 * @returns {boolean} 是否有权限
 */
export function hasActionPermission(action) {
  const userStore = useUserStore()
  const role = userStore.userType || userStore.role
  return checkPermission(role, action)
}

/**
 * 检查当前用户是否有特定操作权限（别名）
 * @param {string} action - 操作类型 (view, create, edit, delete)
 * @returns {boolean} 是否有权限
 */
export function hasPermission(action) {
  return hasActionPermission(action)
}

/**
 * 检查当前用户是否有多个权限中的任意一个
 * @param {string[]} actions - 操作类型数组
 * @returns {boolean} 是否有任意一个权限
 */
export function hasAnyActionPermission(actions) {
  return actions.some(action => hasActionPermission(action))
}

/**
 * 检查当前用户是否有所有指定权限
 * @param {string[]} actions - 操作类型数组
 * @returns {boolean} 是否拥有所有权限
 */
export function hasAllActionPermissions(actions) {
  return actions.every(action => hasActionPermission(action))
}

/**
 * 获取指定角色的所有权限
 * @param {string} role - 用户角色
 * @returns {string[]} 权限列表
 */
export function getRolePermissions(role) {
  const normalizedRole = role?.toLowerCase()
  return ROLE_PERMISSIONS[normalizedRole] || []
}

/**
 * 获取当前用户的所有权限
 * @returns {string[]} 权限列表
 */
export function getCurrentUserPermissions() {
  const userStore = useUserStore()
  const role = userStore.userType || userStore.role
  return getRolePermissions(role)
}

// ==================== 角色判断函数 ====================

/**
 * 判断当前用户是否为管理员
 * @returns {boolean}
 */
export function isAdmin() {
  const userStore = useUserStore()
  return userStore.isAdmin
}

/**
 * 判断当前用户是否为普通员工
 * @returns {boolean}
 */
export function isEmployee() {
  const userStore = useUserStore()
  return userStore.isEmployee
}

/**
 * 判断当前用户是否为房东
 * @returns {boolean}
 */
export function isLandlord() {
  const userStore = useUserStore()
  return userStore.isLandlord
}

/**
 * 判断当前用户是否为租客
 * @returns {boolean}
 */
export function isTenant() {
  const userStore = useUserStore()
  return userStore.isTenant
}

/**
 * 判断当前用户是否为指定角色
 * @param {string|string[]} roles - 角色或角色数组
 * @returns {boolean}
 */
export function isRole(roles) {
  const userStore = useUserStore()
  const currentRole = (userStore.userType || userStore.role).toLowerCase()
  const roleList = Array.isArray(roles) 
    ? roles.map(r => r.toLowerCase()) 
    : [roles.toLowerCase()]
  
  return roleList.includes(currentRole)
}

/**
 * 获取当前用户角色
 * @returns {string} 当前用户角色
 */
export function getCurrentRole() {
  const userStore = useUserStore()
  return userStore.userType || userStore.role || ''
}

// ==================== Vue 自定义指令 ====================

/**
 * v-permission 指令
 * 用于按钮级别权限控制
 * 
 * 用法：
 * - v-permission="'delete'" - 需要delete权限
 * - v-permission="['edit', 'delete']" - 需要edit或delete权限
 * 
 * @example
 * <el-button v-permission="'delete'">删除</el-button>
 * <el-button v-permission="['edit', 'delete']">操作</el-button>
 */
export const permissionDirective = {
  mounted(el, binding) {
    const { value } = binding
    
    if (value === undefined || value === null) {
      console.warn('v-permission 指令需要提供权限参数')
      return
    }

    // 标准化权限为数组
    const permissions = Array.isArray(value) ? value : [value]
    
    // 检查是否有任意一个权限
    const hasPermission = hasAnyActionPermission(permissions)
    
    if (!hasPermission) {
      // 没有权限，移除元素
      el.parentNode?.removeChild(el)
    }
  }
}

/**
 * v-role 指令
 * 基于角色控制元素显示
 * 
 * 用法：
 * - v-role="'admin'" - 仅管理员可见
 * - v-role="['admin', 'landlord']" - 管理员或房东可见
 * 
 * @example
 * <div v-role="'admin'">仅管理员可见</div>
 * <div v-role="['admin', 'staff']">管理员和员工可见</div>
 */
export const roleDirective = {
  mounted(el, binding) {
    const { value } = binding
    
    if (value === undefined || value === null) {
      console.warn('v-role 指令需要提供角色参数')
      return
    }

    // 标准化角色为数组
    const roles = Array.isArray(value) ? value : [value]
    
    // 检查是否有对应角色
    const hasRole = isRole(roles)
    
    if (!hasRole) {
      // 没有对应角色，移除元素
      el.parentNode?.removeChild(el)
    }
  }
}

/**
 * v-admin 指令
 * 仅管理员可见
 */
export const adminDirective = {
  mounted(el) {
    if (!isAdmin()) {
      el.parentNode?.removeChild(el)
    }
  }
}

/**
 * v-employee 指令
 * 仅普通员工可见
 */
export const employeeDirective = {
  mounted(el) {
    if (!isEmployee()) {
      el.parentNode?.removeChild(el)
    }
  }
}

/**
 * v-landlord 指令
 * 仅房东可见
 */
export const landlordDirective = {
  mounted(el) {
    if (!isLandlord()) {
      el.parentNode?.removeChild(el)
    }
  }
}

/**
 * v-tenant 指令
 * 仅租客可见
 */
export const tenantDirective = {
  mounted(el) {
    if (!isTenant()) {
      el.parentNode?.removeChild(el)
    }
  }
}

// ==================== 指令注册 ====================

/**
 * 注册所有权限相关指令
 * @param {Object} app - Vue 应用实例
 */
export function setupPermissionDirectives(app) {
  app.directive('permission', permissionDirective)
  app.directive('role', roleDirective)
  app.directive('admin', adminDirective)
  app.directive('employee', employeeDirective)
  app.directive('landlord', landlordDirective)
  app.directive('tenant', tenantDirective)
}

// ==================== 默认导出 ====================

export default {
  // 权限检查
  checkPermission,
  hasPermission,
  hasActionPermission,
  hasAnyActionPermission,
  hasAllActionPermissions,
  getRolePermissions,
  getCurrentUserPermissions,
  
  // 角色判断
  isAdmin,
  isEmployee,
  isLandlord,
  isTenant,
  isRole,
  getCurrentRole,
  
  // 指令
  permissionDirective,
  roleDirective,
  adminDirective,
  employeeDirective,
  landlordDirective,
  tenantDirective,
  
  // 指令注册
  setupPermissionDirectives,
  
  // 常量
  PERMISSION_ACTIONS,
  ROLE_PERMISSIONS
}
