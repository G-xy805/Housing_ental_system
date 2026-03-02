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
    meta: {},
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/Dashboard.vue'),
        meta: { title: '仪表盘', icon: 'dashboard' }
      },
      {
        path: 'houses',
        name: 'Houses',
        component: () => import('@/views/houses/HouseList.vue'),
        meta: { title: '房源管理', icon: 'houses' }
      },
      {
        path: 'houses/:id',
        name: 'HouseDetail',
        component: () => import('@/views/houses/HouseDetail.vue'),
        meta: { title: '房源详情', hidden: true }
      },
      {
        path: 'contracts',
        name: 'Contracts',
        component: () => import('@/views/contracts/ContractList.vue'),
        meta: { title: '合同管理', icon: 'contracts' }
      },
      {
        path: 'payments',
        name: 'Payments',
        component: () => import('@/views/payments/PaymentList.vue'),
        meta: { title: '租金管理', icon: 'payments' }
      },
      {
        path: 'employees',
        name: 'Employees',
        component: () => import('@/views/employees/EmployeeList.vue'),
        meta: { title: '员工管理', icon: 'employees', roles: ['admin'] }
      },
      {
        path: 'tenants',
        name: 'Tenants',
        component: () => import('@/views/tenants/TenantList.vue'),
        meta: { title: '租客管理', icon: 'tenants' }
      },
      {
        path: 'landlords',
        name: 'Landlords',
        component: () => import('@/views/landlords/LandlordList.vue'),
        meta: { title: '房东管理', icon: 'landlords' }
      },
      {
        path: 'landlord-contracts',
        name: 'LandlordContracts',
        component: () => import('@/views/landlord-contracts/ContractList.vue'),
        meta: { title: '房东合同管理', icon: 'contracts' }
      },
      {
        path: 'backup',
        name: 'Backup',
        component: () => import('@/views/backup/BackupList.vue'),
        meta: { title: '数据备份', icon: 'backup', roles: ['admin'] }
      },
      {
        path: 'profile',
        name: 'Profile',
        component: () => import('@/views/profile/Profile.vue'),
        meta: { title: '个人中心', hidden: true }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach(async (to, from, next) => {
  // 设置页面标题
  document.title = to.meta.title ? `${to.meta.title} - 房屋租赁系统` : '房屋租赁系统'
  
  // 获取用户 store
  const userStore = useUserStore()
  const hasToken = userStore.token
  
  // 判断是否在白名单中
  const isInWhiteList = whiteList.includes(to.path) || to.meta.public
  
  if (hasToken) {
    // 已登录
    
    // 如果访问登录页，重定向到首页
    if (to.path === '/login') {
      next({ name: 'Dashboard' })
      return
    }
    
    // 检查是否需要获取用户信息
    if (!userStore.userInfo.username) {
      try {
        await userStore.fetchCurrentUser()
      } catch (error) {
        // 获取用户信息失败，清除 token 并跳转到登录页
        userStore.logout()
        next(`/login?redirect=${to.path}`)
        return
      }
    }
    
    // 检查角色权限
    if (to.meta.roles && to.meta.roles.length > 0) {
      const userRole = userStore.userType
      if (!to.meta.roles.includes(userRole)) {
        // 无权限，跳转到 403 页面
        next('/403')
        return
      }
    }
    
    next()
  } else {
    // 未登录
    
    // 如果在白名单中，直接访问
    if (isInWhiteList) {
      next()
    } else {
      // 重定向到登录页
      next(`/login?redirect=${to.path}`)
    }
  }
})

// 路由解析错误处理
router.onError((error) => {
  console.error('路由错误:', error)
})

export default router
