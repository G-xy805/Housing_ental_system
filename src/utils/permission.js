/**
 * 权限控制指令
 * 用于根据用户角色控制元素显示/隐藏
 */

import { useUserStore } from '@/store/user'

/**
 * 检查用户是否有指定权限
 * @param {string} permission 权限类型 ('view', 'create', 'edit', 'delete')
 * @returns {boolean} 是否有权限
 */
export function hasPermission(permission) {
  const userStore = useUserStore()
  const userType = userStore.userType
  
  // 管理员拥有所有权限
  if (userType === 'admin') {
    return true
  }
  // 普通员工有查看、创建、编辑权限，无删除权限
  else if (userType === 'staff') {
    return permission !== 'delete'
  }
  // 其他角色无权限
  return false
}

/**
 * v-permission 指令
 * 用法：v-permission="['admin']" 或 v-permission="['admin', 'landlord']"
 * 只有当用户角色在指定角色列表中时才显示元素
 */
export const permission = {
  mounted(el, binding) {
    const { value } = binding
    
    if (value && Array.isArray(value) && value.length > 0) {
      const userStore = useUserStore()
      const userType = userStore.userType
      const permissions = value
      
      // 检查用户角色是否在权限列表中
      const hasPermission = permissions.includes(userType)
      
      if (!hasPermission) {
        // 没有权限，移除元素
        el.parentNode && el.parentNode.removeChild(el)
      }
    } else {
      console.warn('v-permission 指令需要提供角色数组，如 v-permission="[\'admin\']"')
    }
  }
}

/**
 * v-admin 指令
 * 用法：v-admin
 * 仅管理员可见的元素
 */
export const admin = {
  mounted(el) {
    const userStore = useUserStore()
    
    if (!userStore.isAdmin) {
      // 不是管理员，移除元素
      el.parentNode && el.parentNode.removeChild(el)
    }
  }
}

/**
 * v-landlord 指令
 * 用法：v-landlord
 * 仅房东可见的元素
 */
export const landlord = {
  mounted(el) {
    const userStore = useUserStore()
    
    if (!userStore.isLandlord) {
      // 不是房东，移除元素
      el.parentNode && el.parentNode.removeChild(el)
    }
  }
}

/**
 * v-tenant 指令
 * 用法：v-tenant
 * 仅租客可见的元素
 */
export const tenant = {
  mounted(el) {
    const userStore = useUserStore()
    
    if (!userStore.isTenant) {
      // 不是租客，移除元素
      el.parentNode && el.parentNode.removeChild(el)
    }
  }
}

/**
 * v-role 指令
 * 用法：v-role="'admin'" 或 v-role="['admin', 'landlord']"
 * 更灵活的角色控制指令
 */
export const role = {
  mounted(el, binding) {
    const { value } = binding
    
    if (!value) {
      console.warn('v-role 指令需要提供角色字符串或数组')
      return
    }
    
    const userStore = useUserStore()
    const userType = userStore.userType
    
    // 支持字符串或数组
    const roles = Array.isArray(value) ? value : [value]
    const hasRole = roles.includes(userType)
    
    if (!hasRole) {
      // 没有对应角色，移除元素
      el.parentNode && el.parentNode.removeChild(el)
    }
  }
}

/**
 * 注册所有权限指令
 * @param {Object} app Vue 应用实例
 */
export function setupPermissionDirectives(app) {
  app.directive('permission', permission)
  app.directive('admin', admin)
  app.directive('landlord', landlord)
  app.directive('tenant', tenant)
  app.directive('role', role)
}

export default {
  permission,
  admin,
  landlord,
  tenant,
  role,
  setupPermissionDirectives
}
