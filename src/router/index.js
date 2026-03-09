import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/store/user'
import Layout from '@/components/Layout.vue'

// 白名单路由（不需要登录即可访问）
const whiteList = ['/login', '/404', '/403']

// 公共路由
const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { title: '登录', public: true }
  },
  {
    path: '/404',
    name: 'NotFound',
    component: () => import('@/views/404.vue'),
    meta: { title: '页面不存在', public: true }
  },
  {
    path: '/403',
    name: 'Forbidden',
    component: () => import('@/views/403.vue'),
    meta: { title: '无权限', public: true }
  },
  // 需要布局的主页面路由
  {
    path: '/',
    name: 'Layout',
    component: Layout,
    redirect: '/dashboard',
    meta: { requiresAuth: true },
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/Dashboard.vue'),
        meta: { title: '仪表盘', icon: 'dashboard', requiresAuth: true, standalone: true }
      },
      {
        path: 'houses',
        name: 'Houses',
        component: () => import('@/views/houses/HouseList.vue'),
        meta: { title: '房源管理', icon: 'houses', requiresAuth: true, group: 'property', groupTitle: '房源管理', groupIcon: 'house' }
      },
      {
        path: 'houses/:id',
        name: 'HouseDetail',
        component: () => import('@/views/houses/HouseDetail.vue'),
        meta: { title: '房源详情', hidden: true, requiresAuth: true }
      },
      {
        path: 'landlords',
        name: 'Landlords',
        component: () => import('@/views/landlords/LandlordList.vue'),
        meta: { title: '房东管理', icon: 'landlords', requiresAuth: true, group: 'customer', groupTitle: '客户管理', groupIcon: 'user' }
      },
      {
        path: 'tenants',
        name: 'Tenants',
        component: () => import('@/views/tenants/TenantList.vue'),
        meta: { title: '租客管理', icon: 'tenants', requiresAuth: true, group: 'customer', groupTitle: '客户管理', groupIcon: 'user' }
      },
      {
        path: 'landlord-contracts',
        name: 'LandlordContracts',
        component: () => import('@/views/landlord-contracts/ContractList.vue'),
        meta: { title: '房东合同管理', icon: 'contracts', requiresAuth: true, group: 'contract', groupTitle: '合同管理', groupIcon: 'document' }
      },
      {
        path: 'contracts',
        name: 'Contracts',
        component: () => import('@/views/contracts/ContractList.vue'),
        meta: { title: '租客合同管理', icon: 'contracts', requiresAuth: true, group: 'contract', groupTitle: '合同管理', groupIcon: 'document' }
      },
      {
        path: 'payments',
        name: 'Payments',
        component: () => import('@/views/payments/PaymentList.vue'),
        meta: { title: '租金管理', icon: 'payments', requiresAuth: true, group: 'finance', groupTitle: '财务管理', groupIcon: 'money' }
      },
      {
        path: 'deposit-refunds',
        name: 'DepositRefunds',
        component: () => import('@/views/deposit-refunds/DepositRefundList.vue'),
        meta: { title: '押金退款管理', icon: 'deposit-refunds', requiresAuth: true, group: 'finance', groupTitle: '财务管理', groupIcon: 'money' }
      },
      {
        path: 'employees',
        name: 'Employees',
        component: () => import('@/views/employees/EmployeeList.vue'),
        meta: { title: '员工管理', icon: 'employees', requiresAuth: true, requiresAdmin: true, group: 'system', groupTitle: '系统管理', groupIcon: 'setting' }
      },
      {
        path: 'backup',
        name: 'Backup',
        component: () => import('@/views/backup/BackupList.vue'),
        meta: { title: '数据备份', icon: 'backup', requiresAuth: true, requiresAdmin: true, group: 'system', groupTitle: '系统管理', groupIcon: 'setting' }
      },
      {
        path: 'audit',
        name: 'Audit',
        component: () => import('@/views/audit/AuditList.vue'),
        meta: { title: '审计日志', icon: 'audit', requiresAuth: true, requiresAdmin: true, group: 'system', groupTitle: '系统管理', groupIcon: 'setting' }
      },
      {
        path: 'monitoring',
        name: 'Monitoring',
        component: () => import('@/views/monitoring/MonitoringDashboard.vue'),
        meta: { title: '系统监控', icon: 'monitoring', requiresAuth: true, requiresAdmin: true, group: 'system', groupTitle: '系统管理', groupIcon: 'setting' }
      },
      {
        path: 'profile',
        name: 'Profile',
        component: () => import('@/views/profile/Profile.vue'),
        meta: { title: '个人中心', hidden: true, requiresAuth: true }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

/**
 * 全局前置守卫
 * 功能：
 * 1. 设置页面标题
 * 2. 检查Token是否存在
 * 3. 检查Token是否过期，过期则尝试刷新
 * 4. 检查路由是否需要认证
 * 5. 检查路由是否需要管理员权限
 * 6. 未登录用户重定向到登录页
 * 7. 无权限用户重定向到403页面
 */
router.beforeEach(async (to, from, next) => {
  // 设置页面标题
  document.title = to.meta.title ? `${to.meta.title} - 房屋租赁系统` : '房屋租赁系统'
  
  // 获取用户 store
  const userStore = useUserStore()
  const hasToken = userStore.token
  
  // 判断是否在白名单中
  const isInWhiteList = whiteList.includes(to.path) || to.meta.public
  
  // ==================== 未登录处理 ====================
  if (!hasToken) {
    // 如果在白名单中，直接访问
    if (isInWhiteList) {
      next()
    } else {
      // 重定向到登录页，并记录目标路径
      next({
        path: '/login',
        query: { redirect: to.path }
      })
    }
    return
  }
  
  // ==================== 已登录处理 ====================
  
  // 如果访问登录页，重定向到首页
  if (to.path === '/login') {
    next({ name: 'Dashboard' })
    return
  }
  
  // ==================== Token过期处理 ====================
  if (userStore.isTokenExpired()) {
    // Token已过期，尝试刷新
    const refreshed = await userStore.refreshAccessToken()
    if (!refreshed) {
      // 刷新失败，清除状态并跳转登录页
      userStore.clearStorage()
      next({
        path: '/login',
        query: { redirect: to.path }
      })
      return
    }
  } else if (userStore.isTokenExpiringSoon()) {
    // Token即将过期，后台静默刷新
    userStore.refreshAccessToken().catch(err => {
      console.error('后台刷新Token失败:', err)
    })
  }
  
  // ==================== 获取用户信息 ====================
  // 检查是否有完整的用户信息（必须包含 avatar 字段，因为登录响应不包含 avatar）
  const hasCompleteUserInfo = userStore.userInfo && 
    Object.keys(userStore.userInfo).length > 0 && 
    'avatar' in userStore.userInfo
  
  if (!hasCompleteUserInfo) {
    try {
      await userStore.fetchCurrentUser()
    } catch (error) {
      console.error('获取用户信息失败:', error)
      // 获取用户信息失败，清除 token 并跳转到登录页
      userStore.clearStorage()
      next({
        path: '/login',
        query: { redirect: to.path }
      })
      return
    }
  }
  
  // ==================== 权限检查 ====================
  
  // 检查路由是否需要认证
  if (to.meta.requiresAuth) {
    // 检查是否需要管理员权限
    if (to.meta.requiresAdmin) {
      if (!userStore.isAdmin) {
        // 无管理员权限，跳转到 403 页面
        next('/403')
        return
      }
    }
    
    // 兼容旧的 roles 字段
    if (to.meta.roles && to.meta.roles.length > 0) {
      const userRole = userStore.userType
      if (!to.meta.roles.includes(userRole)) {
        // 无权限，跳转到 403 页面
        next('/403')
        return
      }
    }
  }
  
  // 所有检查通过，放行
  next()
})

/**
 * 全局后置钩子
 * 用于处理路由跳转后的操作
 */
router.afterEach((to, from) => {
  // 可以在这里添加页面访问统计等逻辑
  // console.log(`路由跳转: ${from.path} -> ${to.path}`)
})

/**
 * 路由解析错误处理
 */
router.onError((error) => {
  console.error('路由错误:', error)
  
  // 处理动态导入失败的情况
  if (error.message.includes('Failed to fetch dynamically imported module')) {
    // 可以尝试刷新页面或跳转到错误页面
    window.location.reload()
  }
})

export default router
