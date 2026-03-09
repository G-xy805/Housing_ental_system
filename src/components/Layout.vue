<template>
  <div class="layout-container">
    <!-- 跳过导航链接 (无障碍访问) -->
    <a href="#main-content" class="skip-link">
      跳过导航菜单，直接访问主要内容
    </a>
    
    <!-- 移动端遮罩 -->
    <transition name="fade">
      <div 
        v-if="isMobile && !isCollapse" 
        class="sidebar-overlay"
        @click="isCollapse = true"
        aria-hidden="true"
      />
    </transition>
    
    <!-- 侧边栏 -->
    <el-aside 
      width="200px" 
      class="sidebar"
      :class="{ 'sidebar-mobile': isMobile }"
      role="navigation"
      aria-label="主导航菜单"
    >
      <!-- Logo -->
      <div class="logo" role="banner">
        <div class="logo-icon" aria-hidden="true">
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
          role="menubar"
          aria-label="系统导航菜单"
        >
          <template v-for="item in groupedMenuItems" :key="item.key">
            <!-- 独立菜单项（仪表盘） -->
            <el-menu-item
              v-if="item.type === 'standalone'"
              :index="item.route.path"
              class="menu-item"
              role="menuitem"
              :aria-label="item.route.meta && item.route.meta.title || ''"
            >
              <el-icon class="menu-icon" aria-hidden="true">
                <component :is="getMenuIcon(item.route.meta && item.route.meta.icon)" />
              </el-icon>
              <template #title>
                <span class="menu-title">{{ item.route.meta && item.route.meta.title || '' }}</span>
              </template>
            </el-menu-item>
            
            <!-- 分组菜单 -->
            <el-sub-menu
              v-else-if="item.type === 'group'"
              :index="item.groupKey"
              class="sub-menu"
              role="menuitem"
              :aria-label="item.groupTitle"
              :aria-expanded="false"
            >
              <template #title>
                <el-icon class="menu-icon" aria-hidden="true">
                  <component :is="getMenuIcon(item.groupIcon)" />
                </el-icon>
                <span class="menu-title">{{ item.groupTitle }}</span>
              </template>
              <el-menu-item
                v-for="route in item.routes"
                :key="route.path"
                :index="route.path"
                class="sub-menu-item"
                role="menuitem"
                :aria-label="route.meta && route.meta.title || ''"
              >
                <span class="menu-title">{{ route.meta && route.meta.title || '' }}</span>
              </el-menu-item>
            </el-sub-menu>
          </template>
        </el-menu>
      </el-scrollbar>
    </el-aside>
    
    <!-- 主内容区 -->
    <el-container class="main-container">
      <!-- 顶部导航栏 -->
      <el-header class="header" role="banner">
        <div class="header-left">
          <!-- 移动端菜单按钮 -->
          <el-icon 
            v-if="isMobile" 
            class="menu-btn" 
            @click="isCollapse = !isCollapse"
            role="button"
            :aria-label="isCollapse ? '展开导航菜单' : '收起导航菜单'"
            :aria-expanded="!isCollapse"
            tabindex="0"
            @keydown.enter="isCollapse = !isCollapse"
            @keydown.space.prevent="isCollapse = !isCollapse"
          >
            <Fold v-if="isCollapse" />
            <Expand v-else />
          </el-icon>
          
          <!-- 面包屑 -->
          <el-breadcrumb separator="/" class="breadcrumb" role="navigation" aria-label="面包屑导航">
            <el-breadcrumb-item :to="{ path: '/' }">
              <el-icon aria-hidden="true"><HomeFilled /></el-icon>
              <span>首页</span>
            </el-breadcrumb-item>
            <el-breadcrumb-item v-if="currentRoute && currentRoute.meta && currentRoute.meta.title" aria-current="page">
              {{ currentRoute.meta.title }}
            </el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        
        <div class="header-right">
          <!-- 搜索按钮 -->
          <el-tooltip content="搜索" placement="bottom">
            <div 
              class="header-action-btn" 
              @click="handleSearch"
              role="button"
              aria-label="搜索"
              tabindex="0"
              @keydown.enter="handleSearch"
              @keydown.space.prevent="handleSearch"
            >
              <el-icon :size="20" aria-hidden="true"><Search /></el-icon>
            </div>
          </el-tooltip>
          
          <!-- 全屏按钮 -->
          <el-tooltip :content="isFullscreen ? '退出全屏' : '全屏'" placement="bottom">
            <div 
              class="header-action-btn" 
              @click="toggleFullscreen"
              role="button"
              :aria-label="isFullscreen ? '退出全屏' : '进入全屏'"
              :aria-pressed="isFullscreen"
              tabindex="0"
              @keydown.enter="toggleFullscreen"
              @keydown.space.prevent="toggleFullscreen"
            >
              <el-icon :size="20" aria-hidden="true">
                <FullScreen v-if="!isFullscreen" />
                <Close v-else />
              </el-icon>
            </div>
          </el-tooltip>
          
          <!-- 通知 -->
          <el-tooltip content="通知" placement="bottom">
            <el-badge :value="notificationCount" :hidden="notificationCount === 0" class="notification-badge">
              <div 
                class="header-action-btn" 
                @click="handleNotification"
                role="button"
                aria-label="查看通知"
                :aria-label="notificationCount > 0 ? `有 ${notificationCount} 条未读通知` : '暂无通知'"
                tabindex="0"
                @keydown.enter="handleNotification"
                @keydown.space.prevent="handleNotification"
              >
                <el-icon :size="20" aria-hidden="true"><Bell /></el-icon>
              </div>
            </el-badge>
          </el-tooltip>
          
          <!-- 用户信息下拉 -->
          <el-dropdown class="user-dropdown" trigger="click" @command="handleCommand">
            <div 
              class="user-info"
              role="button"
              aria-label="用户菜单"
              aria-haspopup="true"
              tabindex="0"
            >
              <el-avatar 
                :size="36" 
                :src="userStore.avatar" 
                class="user-avatar"
                :alt="`${userStore.username || '用户'}的头像`"
              >
                <el-icon :size="20" aria-hidden="true"><UserFilled /></el-icon>
              </el-avatar>
              <div class="user-detail">
                <span class="username">{{ userStore.username || '用户' }}</span>
                <span class="user-role">{{ getRoleName(userStore.role) }}</span>
              </div>
              <el-icon class="dropdown-arrow" aria-hidden="true"><ArrowDown /></el-icon>
            </div>
            <template #dropdown>
              <el-dropdown-menu role="menu" aria-label="用户菜单">
                <el-dropdown-item command="profile" role="menuitem">
                  <el-icon aria-hidden="true"><User /></el-icon>
                  <span>个人中心</span>
                </el-dropdown-item>
                <el-dropdown-item divided command="logout" role="menuitem">
                  <el-icon class="logout-icon" aria-hidden="true"><SwitchButton /></el-icon>
                  <span>退出登录</span>
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>
      
      <!-- 主内容 -->
      <el-main class="main-content" id="main-content" role="main" aria-label="主要内容区域">
        <router-view v-slot="{ Component }">
          <transition name="fade-slide" mode="out-in">
            <keep-alive :include="cachedViews">
              <component :is="Component" :key="routeKey" />
            </keep-alive>
          </transition>
        </router-view>
      </el-main>
      
      <!-- 页脚 -->
      <el-footer class="footer" height="auto" role="contentinfo">
        <div class="footer-content">
          <span>房屋租赁管理系统</span>
          <span class="divider" aria-hidden="true">|</span>
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
  DataAnalysis,
  Setting,
  Wallet
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

const groupedMenuItems = computed(() => {
  const items = []
  const groupMap = new Map()
  
  menuRoutes.value.forEach(child => {
    if (!child.meta) return
    
    const meta = child.meta
    
    if (meta.standalone) {
      items.push({
        type: 'standalone',
        key: child.path,
        route: {
          path: '/' + child.path,
          meta: meta
        }
      })
    } else if (meta.group) {
      if (!groupMap.has(meta.group)) {
        groupMap.set(meta.group, {
          type: 'group',
          key: meta.group,
          groupKey: 'group-' + meta.group,
          groupTitle: meta.groupTitle || '',
          groupIcon: meta.groupIcon || 'folder',
          routes: []
        })
      }
      
      const group = groupMap.get(meta.group)
      const requiresAdmin = meta.requiresAdmin
      const isAdmin = userStore.isAdmin
      
      if (!requiresAdmin || isAdmin) {
        group.routes.push({
          path: '/' + child.path,
          meta: meta
        })
      }
    }
  })
  
  const groupOrder = ['property', 'customer', 'contract', 'finance', 'system']
  const sortedGroups = groupOrder
    .map(key => groupMap.get(key))
    .filter(group => group && group.routes.length > 0)
  
  return [...items, ...sortedGroups]
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
    'house': House,
    'user': User,
    'document': Document,
    'money': Wallet,
    'setting': Setting,
    'Odometer': Odometer,
    'House': House,
    'Document': Document,
    'UserFilled': UserFilled,
    'User': User,
    'Money': Money,
    'Cloudy': Cloudy,
    'DataAnalysis': DataAnalysis,
    'FolderOpened': FolderOpened,
    'Tickets': Tickets,
    'Setting': Setting,
    'Wallet': Wallet
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

// ==================== 无障碍访问样式 ====================
// 跳过导航链接
.skip-link {
  position: absolute;
  top: -100%;
  left: 50%;
  transform: translateX(-50%);
  z-index: 9999;
  padding: var(--spacing-3) var(--spacing-5);
  background: var(--color-primary);
  color: var(--color-white);
  font-weight: var(--font-weight-semibold);
  text-decoration: none;
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-lg);
  transition: top var(--transition-fast);
  
  &:focus {
    top: var(--spacing-4);
    outline: none;
    box-shadow: 0 0 0 3px rgba(15, 118, 110, 0.3), var(--shadow-lg);
  }
}

// ==================== 移动端遮罩层优化 ====================
.sidebar-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(15, 23, 42, 0.6);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  z-index: 999;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

// ==================== 侧边栏优化 ====================
.sidebar {
  width: 200px;
  background: linear-gradient(180deg, #1E293B 0%, #0F172A 100%);
  display: flex;
  flex-direction: column;
  position: relative;
  z-index: 1000;
  overflow: visible;
  flex-shrink: 0;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  
  // 移动端侧边栏抽屉效果
  &.sidebar-mobile {
    position: fixed;
    left: 0;
    top: 0;
    height: 100%;
    transform: translateX(0);
    transition: transform 0.35s cubic-bezier(0.32, 0.72, 0, 1);
    box-shadow: 
      4px 0 24px rgba(0, 0, 0, 0.3),
      8px 0 48px rgba(0, 0, 0, 0.15);
    
    // 抽屉滑出动画
    animation: slideInLeft 0.35s cubic-bezier(0.32, 0.72, 0, 1);
  }
}

// 抽屉滑入动画
@keyframes slideInLeft {
  from {
    transform: translateX(-100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

// Logo 区域
.logo {
  height: 56px;
  min-height: 56px;
  display: flex;
  align-items: center;
  padding: 0 12px;
  gap: 10px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  overflow: hidden;
  transition: all 0.3s ease;
  
  .logo-icon {
    width: 32px;
    height: 32px;
    flex-shrink: 0;
    transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
    
    svg {
      width: 100%;
      height: 100%;
    }
    
    &:hover {
      transform: scale(1.08) rotate(-3deg);
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

// 菜单滚动容器
.menu-scrollbar {
  flex: 1;
  overflow: hidden;
  min-height: 0;
  
  :deep(.el-scrollbar__wrap) {
    overflow-x: hidden;
  }
  
  :deep(.el-scrollbar__bar) {
    opacity: 0.2;
    transition: opacity 0.25s ease;
    
    &:hover {
      opacity: 0.5;
    }
  }
}

// ==================== 菜单项优化 ====================
.sidebar-menu {
  border-right: none;
  background: transparent;
  padding: 8px;
  
  :deep(.el-menu-item),
  :deep(.el-sub-menu__title) {
    height: 44px;
    line-height: 44px;
    margin: 3px 0;
    border-radius: 12px;
    color: rgba(255, 255, 255, 0.85);
    transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
    font-weight: 500;
    box-sizing: border-box;
    padding: 0 12px !important;
    position: relative;
    overflow: hidden;
    
    // 悬停效果增强
    &::before {
      content: '';
      position: absolute;
      left: 0;
      top: 0;
      right: 0;
      bottom: 0;
      background: rgba(255, 255, 255, 0.08);
      border-radius: 12px;
      opacity: 0;
      transition: opacity 0.25s ease;
      pointer-events: none;
    }
    
    &:hover {
      color: #ffffff;
      transform: translateX(4px);
      
      &::before {
        opacity: 1;
      }
      
      .menu-icon {
        color: #5EEAD4 !important;
        transform: scale(1.1);
      }
    }
    
    // 焦点可见样式（无障碍访问）
    &:focus-visible {
      outline: 2px solid #5EEAD4;
      outline-offset: 2px;
      background: rgba(255, 255, 255, 0.12);
      
      &::before {
        opacity: 1;
        background: rgba(94, 234, 212, 0.15);
      }
    }
  }
  
  // 激活状态优化
  :deep(.el-menu-item.is-active) {
    background: linear-gradient(135deg, #0F766E 0%, #0D9488 100%);
    color: #ffffff !important;
    box-shadow: 
      0 4px 16px rgba(15, 118, 110, 0.35),
      inset 0 1px 0 rgba(255, 255, 255, 0.1);
    transform: translateX(4px);
    
    // 左侧激活指示器
    &::after {
      content: '';
      position: absolute;
      left: 0;
      top: 50%;
      transform: translateY(-50%);
      width: 3px;
      height: 60%;
      background: #5EEAD4;
      border-radius: 0 3px 3px 0;
      box-shadow: 0 0 8px rgba(94, 234, 212, 0.6);
    }
    
    .menu-icon {
      color: #ffffff !important;
      transform: scale(1.05);
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
  
  // 子菜单项优化
  :deep(.el-sub-menu .el-menu-item) {
    padding-left: 48px !important;
    height: 40px;
    line-height: 40px;
    font-size: 13px;
    color: rgba(255, 255, 255, 0.85) !important;
    box-sizing: border-box;
    background-color: transparent !important;
    position: relative;
    
    // 子菜单项悬停效果
    &::before {
      content: '';
      position: absolute;
      left: 24px;
      top: 50%;
      transform: translateY(-50%);
      width: 6px;
      height: 6px;
      border-radius: 50%;
      background: rgba(255, 255, 255, 0.3);
      transition: all 0.25s ease;
    }
    
    &:hover {
      background: rgba(255, 255, 255, 0.08) !important;
      color: #ffffff !important;
      transform: translateX(4px);
      
      &::before {
        background: #5EEAD4;
        box-shadow: 0 0 8px rgba(94, 234, 212, 0.5);
      }
    }
    
    &.is-active {
      background: rgba(15, 118, 110, 0.2) !important;
      color: #ffffff !important;
      
      &::before {
        background: #5EEAD4;
        box-shadow: 0 0 8px rgba(94, 234, 212, 0.6);
      }
    }
  }
  
  // 菜单图标优化
  .menu-icon {
    font-size: 17px;
    margin-right: 10px;
    color: rgba(255, 255, 255, 0.75);
    transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
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
    letter-spacing: 0.3px;
  }
  
  // 子菜单展开动画优化
  :deep(.el-sub-menu) {
    .el-sub-menu__title {
      color: rgba(255, 255, 255, 0.9) !important;
      
      &:hover {
        background: rgba(255, 255, 255, 0.08) !important;
        color: #ffffff !important;
      }
    }
    
    > .el-menu {
      background-color: rgba(0, 0, 0, 0.12) !important;
      border-radius: 12px;
      margin: 4px 0;
      padding: 4px 0;
      
      .el-menu-item {
        margin: 2px 6px;
        background-color: transparent !important;
        border-radius: 10px;
      }
    }
    
    // 子菜单展开动画
    .el-sub-menu__icon-arrow {
      transition: transform 0.25s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    &.is-opened .el-sub-menu__icon-arrow {
      transform: rotate(180deg);
    }
  }
}

// ==================== 主容器 ====================
.main-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-width: 0;
}

// ==================== 顶部导航栏优化 ====================
.header {
  height: 56px;
  min-height: 56px;
  background: #fff;
  box-shadow: 
    0 1px 3px rgba(0, 0, 0, 0.04),
    0 4px 12px rgba(0, 0, 0, 0.03);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  position: relative;
  z-index: 100;
  transition: box-shadow 0.3s ease;
  
  .header-left {
    display: flex;
    align-items: center;
    gap: 12px;
    
    // 移动端菜单按钮
    .menu-btn {
      font-size: 22px;
      color: var(--text-regular);
      cursor: pointer;
      padding: 8px;
      border-radius: 10px;
      transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
      position: relative;
      
      &::before {
        content: '';
        position: absolute;
        inset: 0;
        border-radius: 10px;
        background: var(--color-primary);
        opacity: 0;
        transition: opacity 0.25s ease;
      }
      
      &:hover {
        color: var(--color-primary);
        transform: scale(1.05);
        
        &::before {
          opacity: 0.08;
        }
      }
      
      &:active {
        transform: scale(0.95);
      }
    }
    
    // 面包屑导航优化
    .breadcrumb {
      :deep(.el-breadcrumb__item) {
        // 面包屑项入场动画
        animation: breadcrumbFadeIn 0.3s ease forwards;
        
        @keyframes breadcrumbFadeIn {
          from {
            opacity: 0;
            transform: translateX(-8px);
          }
          to {
            opacity: 1;
            transform: translateX(0);
          }
        }
        
        .el-breadcrumb__inner {
          display: flex;
          align-items: center;
          gap: 6px;
          color: var(--text-muted);
          font-weight: 500;
          font-size: 13px;
          padding: 4px 8px;
          border-radius: 8px;
          transition: all 0.25s ease;
          
          .el-icon {
            font-size: 14px;
            transition: transform 0.25s ease;
          }
          
          &:hover {
            color: var(--color-primary);
            background: rgba(15, 118, 110, 0.06);
            
            .el-icon {
              transform: scale(1.15);
            }
          }
          
          &.is-link {
            font-weight: 500;
          }
        }
        
        // 分隔符样式优化
        .el-breadcrumb__separator {
          color: var(--border-secondary);
          font-weight: 400;
          margin: 0 4px;
          transition: all 0.25s ease;
        }
        
        &:last-child .el-breadcrumb__inner {
          color: var(--text-primary);
          font-weight: 600;
          background: rgba(15, 118, 110, 0.08);
        }
        
        // 悬停时分隔符效果
        &:hover .el-breadcrumb__separator {
          color: var(--color-primary);
        }
      }
    }
  }
  
  .header-right {
    display: flex;
    align-items: center;
    gap: 8px;
  }
  
  // 操作按钮优化
  .header-action-btn {
    width: 36px;
    height: 36px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 10px;
    color: var(--text-regular);
    cursor: pointer;
    transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
    position: relative;
    overflow: hidden;
    
    // 涟漪效果
    &::after {
      content: '';
      position: absolute;
      inset: 0;
      background: var(--color-primary);
      border-radius: 50%;
      opacity: 0;
      transform: scale(0);
      transition: all 0.4s ease;
    }
    
    &:hover {
      background: rgba(15, 118, 110, 0.08);
      color: var(--color-primary);
      transform: translateY(-1px);
      
      .el-icon {
        animation: iconBounce 0.4s ease;
      }
    }
    
    // 焦点可见样式（无障碍访问）
    &:focus-visible {
      outline: 2px solid var(--color-primary);
      outline-offset: 2px;
      background: rgba(15, 118, 110, 0.08);
      
      .el-icon {
        animation: iconBounce 0.4s ease;
      }
    }
    
    &:active {
      transform: translateY(0);
      
      &::after {
        opacity: 0.15;
        transform: scale(2.5);
        transition: all 0s;
      }
    }
  }
  
  // 通知徽章优化
  .notification-badge {
    :deep(.el-badge__content) {
      border: 2px solid #fff;
      font-size: 10px;
      height: 18px;
      line-height: 14px;
      padding: 0 5px;
      font-weight: 600;
      box-shadow: 0 2px 8px rgba(239, 68, 68, 0.4);
      animation: badgePulse 2s ease-in-out infinite;
    }
  }
  
  // 用户下拉菜单优化
  .user-dropdown {
    margin-left: 8px;
    cursor: pointer;
    
    .user-info {
      display: flex;
      align-items: center;
      gap: 10px;
      padding: 6px 12px 6px 6px;
      border-radius: 14px;
      transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
      background: transparent;
      
      &:hover {
        background: rgba(15, 118, 110, 0.06);
        
        .user-avatar {
          transform: scale(1.08);
          box-shadow: 0 4px 12px rgba(15, 118, 110, 0.3);
        }
        
        .user-detail .username {
          color: var(--color-primary);
        }
      }
    }
    
    .user-avatar {
      background: linear-gradient(135deg, #0F766E 0%, #0D9488 100%);
      color: #fff;
      transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
      box-shadow: 0 2px 8px rgba(15, 118, 110, 0.2);
    }
    
    .user-detail {
      display: flex;
      flex-direction: column;
      align-items: flex-start;
      
      .username {
        font-size: 13px;
        font-weight: 600;
        color: var(--text-primary);
        line-height: 1.3;
        transition: color 0.25s ease;
      }
      
      .user-role {
        font-size: 11px;
        color: var(--text-muted);
        line-height: 1.3;
        margin-top: 1px;
      }
    }
    
    .dropdown-arrow {
      color: var(--text-muted);
      transition: transform 0.25s cubic-bezier(0.4, 0, 0.2, 1);
      font-size: 12px;
    }
    
    &:hover .dropdown-arrow {
      transform: rotate(180deg);
      color: var(--color-primary);
    }
  }
  
  // 下拉菜单项优化
  :deep(.el-dropdown-menu__item) {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 12px 18px;
    font-size: 13px;
    transition: all 0.2s ease;
    
    .el-icon {
      font-size: 16px;
      transition: transform 0.2s ease;
    }
    
    &:hover {
      background: rgba(15, 118, 110, 0.06);
      color: var(--color-primary);
      
      .el-icon {
        transform: scale(1.15);
      }
    }
    
    &.logout-icon {
      color: var(--color-danger);
      
      &:hover {
        background: rgba(239, 68, 68, 0.06);
        color: var(--color-danger);
      }
    }
  }
}

// 图标弹跳动画
@keyframes iconBounce {
  0%, 100% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.2);
  }
}

// 徽章脉冲动画
@keyframes badgePulse {
  0%, 100% {
    transform: scale(1);
    opacity: 1;
  }
  50% {
    transform: scale(1.1);
    opacity: 0.9;
  }
}

// ==================== 主内容区 ====================
.main-content {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 20px;
  background: var(--bg-primary);
  min-width: 0;
  
  // 平滑滚动
  scroll-behavior: smooth;
  
  // 自定义滚动条
  &::-webkit-scrollbar {
    width: 6px;
  }
  
  &::-webkit-scrollbar-track {
    background: transparent;
  }
  
  &::-webkit-scrollbar-thumb {
    background: rgba(0, 0, 0, 0.15);
    border-radius: 3px;
    transition: background 0.2s ease;
    
    &:hover {
      background: rgba(0, 0, 0, 0.25);
    }
  }
}

// ==================== 页脚 ====================
.footer {
  height: auto;
  padding: 12px 20px;
  background: #fff;
  border-top: 1px solid var(--border-secondary);
  transition: all 0.3s ease;
  
  .footer-content {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 10px;
    font-size: 12px;
    color: var(--text-muted);
    
    .divider {
      color: var(--border-secondary);
      opacity: 0.5;
    }
  }
}

// ==================== 过渡动画优化 ====================
// 页面切换动画
.fade-slide-enter-active,
.fade-slide-leave-active {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.fade-slide-enter-from {
  opacity: 0;
  transform: translateY(12px);
}

.fade-slide-leave-to {
  opacity: 0;
  transform: translateY(-12px);
}

// 滑动淡入动画
.slide-fade-enter-active,
.slide-fade-leave-active {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.slide-fade-enter-from,
.slide-fade-leave-to {
  opacity: 0;
  transform: translateX(-12px);
}

// 淡入淡出动画
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

// ==================== 响应式设计 ====================

// ----------------------------------------
// 桌面端布局优化（≥1200px）
// ----------------------------------------
@media screen and (min-width: 1200px) {
  .layout-container {
    // 确保侧边栏完整显示
    .sidebar {
      width: 200px;
      flex-shrink: 0;
    }
  }
  
  // 内容区域最大宽度 1400px
  .main-container {
    flex: 1;
    max-width: calc(100% - 200px);
  }
  
  .main-content {
    padding: 24px;
    max-width: 1400px;
    margin: 0 auto;
    width: 100%;
  }
  
  // 多列布局优化
  .header {
    padding: 0 24px;
    
    .header-right {
      gap: 10px;
    }
  }
  
  // 页脚优化
  .footer {
    padding: 14px 24px;
  }
}

// 超大屏幕优化（≥1920px）
@media screen and (min-width: 1920px) {
  .main-content {
    padding: 32px;
    max-width: 1600px;
  }
  
  .header {
    padding: 0 32px;
  }
  
  .footer {
    padding: 16px 32px;
  }
}

// ----------------------------------------
// 平板端布局优化（768px - 1199px）
// ----------------------------------------
@media screen and (min-width: 768px) and (max-width: 1199px) {
  .layout-container {
    // 侧边栏可折叠
    .sidebar {
      width: 180px;
      flex-shrink: 0;
    }
  }
  
  .main-container {
    flex: 1;
    max-width: calc(100% - 180px);
  }
  
  .main-content {
    padding: 20px;
  }
  
  .header {
    padding: 0 20px;
    
    .header-right {
      gap: 8px;
    }
  }
  
  .footer {
    padding: 12px 20px;
  }
  
  // 表格支持横向滚动
  .main-content {
    overflow-x: hidden;
    
    .el-table {
      font-size: 13px;
      
      th, td {
        padding: 10px 12px;
      }
    }
  }
}

// ----------------------------------------
// 移动端布局优化（<768px）
// ----------------------------------------
@media screen and (max-width: 767px) {
  .layout-container {
    flex-direction: column;
  }
  
  // 侧边栏隐藏为抽屉式
  .sidebar {
    position: fixed;
    left: -200px;
    top: 0;
    height: 100vh;
    width: 200px;
    z-index: 1001;
    transform: translateX(0);
    transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    
    &.sidebar-mobile {
      left: 0;
      transform: translateX(0);
    }
  }
  
  // 主容器全宽
  .main-container {
    width: 100%;
    max-width: 100%;
    margin-left: 0;
  }
  
  .header {
    padding: 0 16px;
    height: 56px;
    min-height: 56px;
    
    .header-left {
      .breadcrumb {
        display: none;
      }
      
      .menu-btn {
        display: flex;
        min-width: 44px;
        min-height: 44px;
      }
    }
    
    .header-right {
      gap: 6px;
      
      .header-action-btn {
        width: 40px;
        height: 40px;
        min-width: 44px;
        min-height: 44px;
      }
      
      .user-dropdown {
        .user-detail {
          display: none;
        }
        
        .dropdown-arrow {
          display: none;
        }
        
        .user-info {
          padding: 6px;
          border-radius: 12px;
          min-width: 44px;
          min-height: 44px;
        }
        
        .user-avatar {
          width: 36px;
          height: 36px;
        }
      }
    }
  }
  
  .main-content {
    padding: 16px;
    padding-bottom: 80px; // 为底部导航留出空间
    
    // 表格转为卡片列表
    .el-table {
      display: block;
      
      .el-table__header-wrapper {
        display: none;
      }
      
      .el-table__body-wrapper {
        display: block;
        
        .el-table__body {
          display: block;
          
          tbody {
            display: block;
            
            tr {
              display: block;
              margin-bottom: 12px;
              border: 1px solid var(--border-secondary);
              border-radius: 12px;
              background: var(--bg-card);
              box-shadow: var(--shadow-sm);
              overflow: hidden;
              
              &:hover {
                background: var(--bg-card);
              }
              
              td {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 12px 16px;
                border-bottom: 1px solid var(--border-light);
                font-size: 13px;
                
                &:last-child {
                  border-bottom: none;
                }
                
                &::before {
                  content: attr(data-label);
                  font-weight: 600;
                  color: var(--text-secondary);
                  margin-right: 12px;
                  flex-shrink: 0;
                }
              }
            }
          }
        }
      }
    }
    
    // 表单字段垂直排列
    .el-form {
      .el-form-item {
        display: block;
        margin-bottom: 16px;
        
        .el-form-item__label {
          display: block;
          text-align: left;
          padding-bottom: 8px;
          margin-bottom: 0;
          float: none;
        }
        
        .el-form-item__content {
          margin-left: 0 !important;
          line-height: 44px;
        }
      }
      
      .el-form-item__content {
        .el-input,
        .el-select,
        .el-textarea {
          width: 100%;
        }
        
        .el-button {
          min-height: 44px;
          padding: 12px 20px;
        }
      }
    }
    
    // 卡片网格单列
    .el-row {
      flex-direction: column;
      
      .el-col {
        width: 100% !important;
        max-width: 100% !important;
        margin-bottom: 16px;
      }
    }
  }
  
  // 页脚固定在底部
  .footer {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    padding: 10px 16px;
    background: #fff;
    border-top: 1px solid var(--border-secondary);
    box-shadow: 0 -2px 8px rgba(0, 0, 0, 0.05);
    z-index: 100;
    
    .footer-content {
      font-size: 11px;
      justify-content: center;
    }
  }
}

// ----------------------------------------
// 小屏幕移动端优化（<480px）
// ----------------------------------------
@media screen and (max-width: 479px) {
  .header {
    padding: 0 12px;
    
    .header-right {
      gap: 4px;
      
      // 隐藏部分操作按钮，保留核心功能
      .header-action-btn:not(:nth-last-child(-n+2)) {
        display: none;
      }
      
      .header-action-btn {
        width: 36px;
        height: 36px;
        min-width: 44px;
        min-height: 44px;
      }
    }
  }
  
  .main-content {
    padding: 12px;
    padding-bottom: 72px;
    
    // 更紧凑的卡片列表
    .el-table {
      .el-table__body-wrapper {
        .el-table__body {
          tbody {
            tr {
              margin-bottom: 10px;
              
              td {
                padding: 10px 12px;
                font-size: 12px;
              }
            }
          }
        }
      }
    }
  }
  
  .footer {
    padding: 8px 12px;
    
    .footer-content {
      font-size: 10px;
      gap: 6px;
    }
  }
}

// ----------------------------------------
// 超小屏幕优化（<375px）
// ----------------------------------------
@media screen and (max-width: 374px) {
  .header {
    padding: 0 8px;
    
    .header-right {
      gap: 2px;
    }
  }
  
  .main-content {
    padding: 8px;
    padding-bottom: 68px;
  }
  
  .footer {
    padding: 6px 8px;
  }
}
</style>
