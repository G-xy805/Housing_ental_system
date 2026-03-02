<template>
  <div class="layout-container">
    <!-- 移动端遮罩 -->
    <transition name="fade">
      <div 
        v-if="isMobile && !isCollapse" 
        class="sidebar-overlay"
        @click="isCollapse = true"
      />
    </transition>
    
    <!-- 侧边栏 -->
    <el-aside 
      width="200px" 
      class="sidebar"
      :class="{ 'sidebar-mobile': isMobile }"
    >
      <!-- Logo -->
      <div class="logo">
        <div class="logo-icon">
          <svg viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
            <rect width="32" height="32" rx="8" fill="url(#logo-gradient)"/>
            <path d="M8 16L16 8L24 16V24H18V18H14V24H8V16Z" fill="white"/>
            <defs>
              <linearGradient id="logo-gradient" x1="0" y1="0" x2="32" y2="32" gradientUnits="userSpaceOnUse">
                <stop stop-color="#0F766E"/>
                <stop offset="1" stop-color="#0D9488"/>
              </linearGradient>
            </defs>
          </svg>
        </div>
        <span class="logo-text">房屋租赁系统</span>
      </div>
      
      <!-- 菜单 -->
      <el-scrollbar class="menu-scrollbar">
        <el-menu
          :default-active="activeMenu"
          :collapse="false"
          :collapse-transition="false"
          :unique-opened="true"
          router
          class="sidebar-menu"
        >
          <template v-for="route in menuRoutes" :key="route.path">
            <!-- 单级菜单 -->
            <el-menu-item
              v-if="!route.children && !(route.meta && route.meta.hidden)"
              :index="route.path"
              class="menu-item"
            >
              <el-icon class="menu-icon">
                <component :is="getMenuIcon(route.meta && route.meta.icon)" />
              </el-icon>
              <template #title>
                <span class="menu-title">{{ route.meta && route.meta.title || '' }}</span>
              </template>
            </el-menu-item>
            
            <!-- 多级菜单 -->
            <el-sub-menu 
              v-else-if="route.children && route.children.length > 0" 
              :index="route.path"
              class="sub-menu"
            >
              <template #title>
                <el-icon class="menu-icon">
                  <component :is="getMenuIcon(route.meta && route.meta.icon)" />
                </el-icon>
                <span class="menu-title">{{ route.meta && route.meta.title || '' }}</span>
              </template>
              <template v-for="child in route.children" :key="child.path">
                <el-menu-item
                  v-if="!(child.meta && child.meta.hidden)"
                  :index="child.path"
                  class="sub-menu-item"
                >
                  <span class="menu-title">{{ child.meta && child.meta.title || '' }}</span>
                </el-menu-item>
              </template>
            </el-sub-menu>
          </template>
        </el-menu>
      </el-scrollbar>
    </el-aside>
    
    <!-- 主内容区 -->
    <el-container class="main-container">
      <!-- 顶部导航栏 -->
      <el-header class="header">
        <div class="header-left">
          <!-- 移动端菜单按钮 -->
          <el-icon 
            v-if="isMobile" 
            class="menu-btn" 
            @click="isCollapse = !isCollapse"
          >
            <Fold v-if="isCollapse" />
            <Expand v-else />
          </el-icon>
          
          <!-- 面包屑 -->
          <el-breadcrumb separator="/" class="breadcrumb">
            <el-breadcrumb-item :to="{ path: '/' }">
              <el-icon><HomeFilled /></el-icon>
              <span>首页</span>
            </el-breadcrumb-item>
            <el-breadcrumb-item v-if="currentRoute && currentRoute.meta && currentRoute.meta.title">
              {{ currentRoute.meta.title }}
            </el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        
        <div class="header-right">
          <!-- 搜索按钮 -->
          <el-tooltip content="搜索" placement="bottom">
            <div class="header-action-btn" @click="handleSearch">
              <el-icon :size="20"><Search /></el-icon>
            </div>
          </el-tooltip>
          
          <!-- 全屏按钮 -->
          <el-tooltip :content="isFullscreen ? '退出全屏' : '全屏'" placement="bottom">
            <div class="header-action-btn" @click="toggleFullscreen">
              <el-icon :size="20">
                <FullScreen v-if="!isFullscreen" />
                <Close v-else />
              </el-icon>
            </div>
          </el-tooltip>
          
          <!-- 通知 -->
          <el-tooltip content="通知" placement="bottom">
            <el-badge :value="notificationCount" :hidden="notificationCount === 0" class="notification-badge">
              <div class="header-action-btn" @click="handleNotification">
                <el-icon :size="20"><Bell /></el-icon>
              </div>
            </el-badge>
          </el-tooltip>
          
          <!-- 用户信息下拉 -->
          <el-dropdown class="user-dropdown" trigger="click" @command="handleCommand">
            <div class="user-info">
              <el-avatar 
                :size="36" 
                :src="userStore.avatar" 
                class="user-avatar"
              >
                <el-icon :size="20"><UserFilled /></el-icon>
              </el-avatar>
              <div class="user-detail">
                <span class="username">{{ userStore.username || '用户' }}</span>
                <span class="user-role">{{ getRoleName(userStore.role) }}</span>
              </div>
              <el-icon class="dropdown-arrow"><ArrowDown /></el-icon>
            </div>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile">
                  <el-icon><User /></el-icon>
                  <span>个人中心</span>
                </el-dropdown-item>
                <el-dropdown-item command="settings">
                  <el-icon><Setting /></el-icon>
                  <span>账号设置</span>
                </el-dropdown-item>
                <el-dropdown-item divided command="logout">
                  <el-icon class="logout-icon"><SwitchButton /></el-icon>
                  <span>退出登录</span>
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>
      
      <!-- 主内容 -->
      <el-main class="main-content">
        <router-view v-slot="{ Component }">
          <transition name="fade-slide" mode="out-in">
            <keep-alive :include="cachedViews">
              <component :is="Component" :key="routeKey" />
            </keep-alive>
          </transition>
        </router-view>
      </el-main>
      
      <!-- 页脚 -->
      <el-footer class="footer" height="auto">
        <div class="footer-content">
          <span>房屋租赁管理系统</span>
          <span class="divider">|</span>
          <span>Version 1.0.0</span>
        </div>
      </el-footer>
    </el-container>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessageBox, ElMessage } from 'element-plus'
import {
  Bell,
  ArrowDown,
  User,
  Setting,
  SwitchButton,
  Odometer,
  Document,
  UserFilled,
  Money,
  Cloudy,
  Search,
  FullScreen,
  Close,
  HomeFilled,
  House,
  Tickets,
  FolderOpened,
  DataAnalysis
} from '@element-plus/icons-vue'
import { useUserStore } from '@/store/user'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const isMobile = ref(false)
const isCollapse = ref(false)
const isFullscreen = ref(false)
const notificationCount = ref(3)
const cachedViews = ref(['Dashboard'])

const activeMenu = computed(() => route.path)
const currentRoute = computed(() => route)
const routeKey = computed(() => route.fullPath)

const menuRoutes = computed(() => {
  const routes = router.options.routes || []
  // 找到Layout路由，返回其children
  const layoutRoute = routes.find(route => route.name === 'Layout')
  if (layoutRoute && layoutRoute.children) {
    return layoutRoute.children.filter(child => {
      if (!child) return false
      if (!child.meta) return true
      return !child.meta.hidden
    })
  }
  return []
})

const getMenuIcon = (iconName) => {
  const iconMap = {
    'dashboard': Odometer,
    'houses': House,
    'contracts': Document,
    'users': UserFilled,
    'employees': UserFilled,
    'tenants': User,
    'landlords': UserFilled,
    'payments': Money,
    'backup': Cloudy,
    'finance': DataAnalysis,
    'reports': FolderOpened,
    'contracts-manage': Tickets,
    'Odometer': Odometer,
    'House': House,
    'Document': Document,
    'UserFilled': UserFilled,
    'User': User,
    'Money': Money,
    'Cloudy': Cloudy,
    'DataAnalysis': DataAnalysis,
    'FolderOpened': FolderOpened,
    'Tickets': Tickets
  }
  return iconMap[iconName] || House
}

const getRoleName = (role) => {
  const roleMap = {
    'admin': '系统管理员',
    'staff': '员工'
  }
  return roleMap[role] || '用户'
}

const toggleFullscreen = () => {
  if (!document.fullscreenElement) {
    document.documentElement.requestFullscreen()
    isFullscreen.value = true
  } else {
    document.exitFullscreen()
    isFullscreen.value = false
  }
}

const handleSearch = () => {
  ElMessage.info('搜索功能开发中...')
}

const handleNotification = () => {
  ElMessage.info('通知功能开发中...')
}

const handleCommand = (command) => {
  switch (command) {
    case 'profile':
      router.push('/profile')
      break
    case 'settings':
      router.push('/profile')
      break
    case 'logout':
      handleLogout()
      break
  }
}

const handleLogout = async () => {
  try {
    await ElMessageBox.confirm('确定要退出登录吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    await userStore.logout()
    ElMessage.success('已退出登录')
  } catch {
    // 取消退出
  }
}

const handleResize = () => {
  isMobile.value = window.innerWidth < 768
}

onMounted(() => {
  handleResize()
  window.addEventListener('resize', handleResize)
  document.addEventListener('fullscreenchange', () => {
    isFullscreen.value = !!document.fullscreenElement
  })
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  document.removeEventListener('fullscreenchange', () => {
    isFullscreen.value = !!document.fullscreenElement
  })
})
</script>

<style lang="scss" scoped>
.layout-container {
  width: 100%;
  height: 100vh;
  display: flex;
  background: var(--bg-primary);
  overflow: hidden;
}

.sidebar-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(4px);
  z-index: 999;
}

.sidebar {
  width: 200px;
  background: linear-gradient(180deg, #1E293B 0%, #0F172A 100%);
  display: flex;
  flex-direction: column;
  position: relative;
  z-index: 1000;
  overflow: visible;
  flex-shrink: 0;
  
  &.sidebar-mobile {
    position: fixed;
    left: 0;
    top: 0;
    height: 100%;
    transform: translateX(0);
    transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    box-shadow: 4px 0 24px rgba(0, 0, 0, 0.3);
  }
}

.logo {
    height: 56px;
    min-height: 56px;
    display: flex;
    align-items: center;
    padding: 0 12px;
    gap: 10px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
    overflow: hidden;
    
    .logo-icon {
      width: 32px;
      height: 32px;
      flex-shrink: 0;
      
      svg {
        width: 100%;
        height: 100%;
      }
    }
    
    .logo-text {
      font-size: 14px;
      font-weight: 600;
      color: #ffffff;
      white-space: nowrap;
      letter-spacing: 0.5px;
    }
  }

.menu-scrollbar {
  flex: 1;
  overflow: hidden;
  min-height: 0;
  
  :deep(.el-scrollbar__wrap) {
    overflow-x: hidden;
  }
  
  :deep(.el-scrollbar__bar) {
    opacity: 0.3;
    transition: opacity 0.2s;
    
    &:hover {
      opacity: 0.6;
    }
  }
}

.sidebar-menu {
  border-right: none;
  background: transparent;
  padding: 8px;
  
  :deep(.el-menu-item),
  :deep(.el-sub-menu__title) {
    height: 44px;
    line-height: 44px;
    margin: 3px 0;
    border-radius: 6px;
    color: rgba(255, 255, 255, 0.85);
    transition: all 0.2s ease;
    font-weight: 500;
    box-sizing: border-box;
    padding: 0 10px !important;
    
    &:hover {
      background: rgba(255, 255, 255, 0.1);
      color: #ffffff;
    }
  }
  
  :deep(.el-menu-item.is-active) {
    background: linear-gradient(135deg, #0F766E 0%, #0D9488 100%);
    color: #ffffff !important;
    box-shadow: 0 4px 12px rgba(15, 118, 110, 0.4);
    
    .menu-icon {
      color: #ffffff !important;
    }
  }
  
  :deep(.el-sub-menu.is-active) {
    > .el-sub-menu__title {
      color: #ffffff !important;
      
      .menu-icon {
        color: #5EEAD4 !important;
      }
    }
  }
  
  :deep(.el-sub-menu .el-menu-item) {
    padding-left: 44px !important;
    height: 40px;
    line-height: 40px;
    font-size: 13px;
    color: rgba(255, 255, 255, 0.9) !important;
    box-sizing: border-box;
    background-color: transparent !important;
    
    &:hover {
      background: rgba(255, 255, 255, 0.1) !important;
      color: #ffffff !important;
    }
    
    &.is-active {
      background: rgba(15, 118, 110, 0.25) !important;
      color: #ffffff !important;
    }
  }
  
  .menu-icon {
    font-size: 17px;
    margin-right: 8px;
    color: rgba(255, 255, 255, 0.75);
    transition: color 0.2s ease;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
  }
  
  .menu-title {
    font-size: 13px;
    font-weight: 500;
    color: inherit;
    display: inline-block;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  
  // 确保子菜单展开时可见
  :deep(.el-sub-menu) {
    .el-sub-menu__title {
      color: rgba(255, 255, 255, 0.9) !important;
      
      &:hover {
        background: rgba(255, 255, 255, 0.1) !important;
        color: #ffffff !important;
      }
    }
    
    > .el-menu {
      background-color: rgba(0, 0, 0, 0.15) !important;
      border-radius: 8px;
      margin: 2px 0;
      
      .el-menu-item {
        margin: 2px 8px;
        background-color: transparent !important;
      }
    }
  }
}

.main-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-width: 0;
}

.header {
  height: 56px;
  min-height: 56px;
  background: #fff;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  position: relative;
  z-index: 100;
  
  .header-left {
    display: flex;
    align-items: center;
    gap: 12px;
    
    .menu-btn {
      font-size: 22px;
      color: var(--text-regular);
      cursor: pointer;
      padding: 8px;
      border-radius: 8px;
      transition: all 0.2s ease;
      
      &:hover {
        background: var(--bg-hover);
        color: var(--color-primary);
      }
    }
    
    .breadcrumb {
      :deep(.el-breadcrumb__item) {
        .el-breadcrumb__inner {
          display: flex;
          align-items: center;
          gap: 4px;
          color: var(--text-muted);
          font-weight: 500;
          
          &:hover {
            color: var(--color-primary);
          }
          
          &.is-link {
            font-weight: 500;
          }
        }
        
        &:last-child .el-breadcrumb__inner {
          color: var(--text-primary);
        }
      }
    }
  }
  
  .header-right {
    display: flex;
    align-items: center;
    gap: 6px;
  }
  
  .header-action-btn {
    width: 36px;
    height: 36px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 8px;
    color: var(--text-regular);
    cursor: pointer;
    transition: all 0.2s ease;
    
    &:hover {
      background: var(--bg-hover);
      color: var(--color-primary);
    }
  }
  
  .notification-badge {
    :deep(.el-badge__content) {
      border: none;
      font-size: 10px;
      height: 16px;
      line-height: 16px;
      padding: 0 5px;
    }
  }
  
  .user-dropdown {
    margin-left: 6px;
    cursor: pointer;
    
    .user-info {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 4px 8px 4px 4px;
      border-radius: 10px;
      transition: all 0.2s ease;
    }
    
    .user-avatar {
      background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-primary-dark) 100%);
      color: #fff;
    }
    
    .user-detail {
      display: flex;
      flex-direction: column;
      align-items: flex-start;
      
      .username {
        font-size: 13px;
        font-weight: 600;
        color: var(--text-primary);
        line-height: 1.2;
      }
      
      .user-role {
        font-size: 11px;
        color: var(--text-muted);
        line-height: 1.2;
      }
    }
    
    .dropdown-arrow {
      color: var(--text-muted);
      transition: transform 0.2s ease;
    }
    
    &:hover .dropdown-arrow {
      transform: rotate(180deg);
    }
  }
  
  :deep(.el-dropdown-menu__item) {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 10px 16px;
    
    .el-icon {
      font-size: 16px;
    }
    
    &.logout-icon {
      color: var(--color-danger);
    }
  }
}

.main-content {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 16px;
  background: var(--bg-primary);
  min-width: 0;
}

.footer {
  height: auto;
  padding: 10px 16px;
  background: #fff;
  border-top: 1px solid var(--border-secondary);
  
  .footer-content {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    font-size: 12px;
    color: var(--text-muted);
    
    .divider {
      color: var(--border-secondary);
    }
  }
}

.fade-slide-enter-active,
.fade-slide-leave-active {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.fade-slide-enter-from {
  opacity: 0;
  transform: translateY(10px);
}

.fade-slide-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

.slide-fade-enter-active,
.slide-fade-leave-active {
  transition: all 0.3s ease;
}

.slide-fade-enter-from,
.slide-fade-leave-to {
  opacity: 0;
  transform: translateX(-10px);
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

@media screen and (max-width: 768px) {
  .header {
    padding: 0 16px;
    
    .header-left {
      .breadcrumb {
        display: none;
      }
    }
    
    .header-right {
      gap: 4px;
      
      .header-action-btn {
        width: 36px;
        height: 36px;
      }
      
      .user-dropdown {
        .user-detail {
          display: none;
        }
        
        .dropdown-arrow {
          display: none;
        }
      }
    }
  }
  
  .main-content {
    padding: 16px;
  }
  
  .footer {
    padding: 10px 16px;
  }
}

@media screen and (max-width: 480px) {
  .header {
    .header-right {
      .header-action-btn:not(:last-of-type) {
        display: none;
      }
    }
  }
}
</style>
