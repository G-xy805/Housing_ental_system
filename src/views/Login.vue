<template>
  <div class="login-container" role="main">
    <!-- 背景装饰 -->
    <div class="background-decoration" aria-hidden="true">
      <div class="shape shape-1"></div>
      <div class="shape shape-2"></div>
      <div class="shape shape-3"></div>
      <div class="shape shape-4"></div>
    </div>
    
    <!-- 左侧品牌区域 -->
    <div class="brand-section" aria-labelledby="brand-title">
      <div class="brand-content">
        <div class="brand-logo" aria-hidden="true">
          <svg viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
            <rect width="48" height="48" rx="12" fill="white" fill-opacity="0.2"/>
            <path d="M12 24L24 12L36 24V36H27V27H21V36H12V24Z" fill="white"/>
          </svg>
        </div>
        <h1 class="brand-title" id="brand-title">房屋租赁管理系统</h1>
        <p class="brand-description">
          高效、智能、安全的房屋租赁管理平台<br/>
          助您轻松管理房源、租客与合同
        </p>
        
        <div class="features" role="list" aria-label="系统功能列表">
          <div class="feature-item" role="listitem">
            <div class="feature-icon" aria-hidden="true">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>
                <polyline points="9,22 9,12 15,12 15,22"/>
              </svg>
            </div>
            <span>房源管理</span>
          </div>
          <div class="feature-item" role="listitem">
            <div class="feature-icon" aria-hidden="true">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
                <circle cx="9" cy="7" r="4"/>
                <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
                <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
              </svg>
            </div>
            <span>租客管理</span>
          </div>
          <div class="feature-item" role="listitem">
            <div class="feature-icon" aria-hidden="true">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                <polyline points="14,2 14,8 20,8"/>
                <line x1="16" y1="13" x2="8" y2="13"/>
                <line x1="16" y1="17" x2="8" y2="17"/>
                <polyline points="10,9 9,9 8,9"/>
              </svg>
            </div>
            <span>合同管理</span>
          </div>
          <div class="feature-item" role="listitem">
            <div class="feature-icon" aria-hidden="true">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="12" y1="1" x2="12" y2="23"/>
                <path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>
              </svg>
            </div>
            <span>财务管理</span>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 右侧登录表单 -->
    <div class="login-section">
      <div class="login-box">
        <div class="login-header">
          <h2 class="login-title" id="login-title">欢迎回来</h2>
          <p class="login-subtitle">请登录您的账号以继续</p>
        </div>
        
        <el-form
          ref="loginFormRef"
          :model="loginForm"
          :rules="loginRules"
          class="login-form"
          size="large"
          aria-labelledby="login-title"
          @submit.prevent="handleLogin"
        >
          <el-form-item prop="username">
            <div class="input-wrapper">
              <label class="input-label" for="username">用户名</label>
              <el-input
                id="username"
                v-model="loginForm.username"
                placeholder="请输入用户名"
                :prefix-icon="User"
                clearable
                aria-required="true"
                autocomplete="username"
              />
            </div>
          </el-form-item>
          
          <el-form-item prop="password">
            <div class="input-wrapper">
              <label class="input-label" for="password">密码</label>
              <el-input
                id="password"
                v-model="loginForm.password"
                type="password"
                placeholder="请输入密码"
                :prefix-icon="Lock"
                show-password
                aria-required="true"
                autocomplete="current-password"
                @keyup.enter="handleLogin"
              />
            </div>
          </el-form-item>
          
          <el-form-item>
            <div class="login-options">
              <el-checkbox 
                v-model="rememberMe"
                aria-describedby="remember-hint"
              >
                <span class="remember-text">记住我</span>
              </el-checkbox>
              <span id="remember-hint" class="sr-only">勾选后将保持登录状态</span>
              <el-link 
                type="primary" 
                :underline="false" 
                class="forgot-link"
                aria-label="忘记密码？点击找回"
              >
                忘记密码？
              </el-link>
            </div>
          </el-form-item>
          
          <el-form-item>
            <el-button
              type="primary"
              size="large"
              :loading="loading"
              class="login-button"
              @click="handleLogin"
              :aria-busy="loading"
              :aria-disabled="loading"
            >
              <span v-if="!loading">登 录</span>
              <span v-else>登录中...</span>
            </el-button>
          </el-form-item>
        </el-form>
        
        <div class="login-footer">
          <div class="divider" role="separator" aria-hidden="true">
            <span>或</span>
          </div>
          <p v-if="showDemoAccount" class="demo-account" role="note">
            演示账号：<code>admin</code> / <code>Admin123!</code>
          </p>
        </div>
      </div>
      
      <!-- 版权信息 -->
      <div class="copyright" role="contentinfo">
        <p>© 2024 房屋租赁管理系统 · All Rights Reserved</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock } from '@element-plus/icons-vue'
import { useUserStore } from '@/store/user'
import { login } from '@/api/user'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

// 环境变量控制是否显示演示账号
const showDemoAccount = import.meta.env.VITE_SHOW_DEMO_ACCOUNT === 'true'

const loginFormRef = ref(null)
const loading = ref(false)
const rememberMe = ref(false)

const loginForm = reactive({
  username: '',
  password: ''
})

const loginRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度在 3 到 20 个字符', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 20, message: '密码长度在 6 到 20 个字符', trigger: 'blur' }
  ]
}

const handleLogin = async () => {
  if (!loginFormRef.value) return
  
  await loginFormRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true
      try {
        const res = await login(loginForm)
        
        userStore.login(res.data)
        
        if (rememberMe.value) {
          localStorage.setItem('rememberMe', 'true')
        } else {
          localStorage.removeItem('rememberMe')
        }
        
        await userStore.fetchCurrentUser()
        
        ElMessage.success('登录成功')
        
        const redirect = route.query.redirect || '/dashboard'
        router.push(redirect)
      } catch (error) {
        console.error('登录失败:', error)
        // 处理账号锁定的错误
        if (error.response && error.response.status === 403) {
          const errorMsg = error.response.data?.message || '账号已被锁定，请联系管理员'
          ElMessage.error(errorMsg)
        } else if (error.response && error.response.status === 401) {
          const errorMsg = error.response.data?.message || '用户名或密码错误'
          ElMessage.error(errorMsg)
        } else {
          ElMessage.error('登录失败，请稍后重试')
        }
      } finally {
        loading.value = false
      }
    }
  })
}
</script>

<style lang="scss" scoped>
// ============================================
// SubTask 4.1: 增强背景动画效果
// ============================================

.login-container {
  width: 100%;
  min-height: 100vh;
  display: flex;
  // 动态渐变背景 - 多层渐变叠加
  background:
    radial-gradient(ellipse at 20% 80%, rgba(20, 184, 166, 0.4) 0%, transparent 50%),
    radial-gradient(ellipse at 80% 20%, rgba(6, 182, 212, 0.3) 0%, transparent 50%),
    radial-gradient(ellipse at 50% 50%, rgba(13, 148, 136, 0.2) 0%, transparent 70%),
    linear-gradient(135deg, #0F766E 0%, #0D9488 35%, #14B8A6 65%, #06B6D4 100%);
  background-size: 200% 200%, 200% 200%, 200% 200%, 100% 100%;
  animation: gradientShift 15s ease infinite;
  position: relative;
  overflow: hidden;
}

// 动态渐变动画
@keyframes gradientShift {
  0%, 100% {
    background-position:
      0% 100%,
      100% 0%,
      50% 50%,
      0% 0%;
  }
  25% {
    background-position:
      50% 50%,
      50% 50%,
      25% 75%,
      0% 0%;
  }
  50% {
    background-position:
      100% 0%,
      0% 100%,
      50% 50%,
      0% 0%;
  }
  75% {
    background-position:
      50% 50%,
      50% 50%,
      75% 25%,
      0% 0%;
  }
}

.background-decoration {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  overflow: hidden;
  pointer-events: none;

  .shape {
    position: absolute;
    border-radius: 50%;
    background: rgba(255, 255, 255, 0.08);
    backdrop-filter: blur(2px);
    animation: float 20s infinite ease-in-out;
    // 添加内部光晕效果
    box-shadow:
      inset 0 0 60px rgba(255, 255, 255, 0.1),
      0 0 40px rgba(255, 255, 255, 0.05);
  }

  .shape-1 {
    width: 500px;
    height: 500px;
    top: -150px;
    left: -150px;
    animation-delay: 0s;
    background: radial-gradient(circle, rgba(255, 255, 255, 0.12) 0%, rgba(255, 255, 255, 0.05) 70%, transparent 100%);
  }

  .shape-2 {
    width: 350px;
    height: 350px;
    top: 40%;
    left: 25%;
    animation-delay: -5s;
    background: radial-gradient(circle, rgba(6, 182, 212, 0.15) 0%, rgba(6, 182, 212, 0.05) 70%, transparent 100%);
  }

  .shape-3 {
    width: 250px;
    height: 250px;
    bottom: 5%;
    left: 5%;
    animation-delay: -10s;
    background: radial-gradient(circle, rgba(255, 255, 255, 0.1) 0%, rgba(255, 255, 255, 0.03) 70%, transparent 100%);
  }

  .shape-4 {
    width: 180px;
    height: 180px;
    top: 15%;
    left: 40%;
    animation-delay: -15s;
    background: radial-gradient(circle, rgba(20, 184, 166, 0.15) 0%, rgba(20, 184, 166, 0.05) 70%, transparent 100%);
  }
}

// 增强的浮动动画 - 更流畅的轨迹
@keyframes float {
  0%, 100% {
    transform: translate(0, 0) rotate(0deg) scale(1);
  }
  25% {
    transform: translate(30px, -30px) rotate(5deg) scale(1.02);
  }
  50% {
    transform: translate(-15px, 25px) rotate(-5deg) scale(0.98);
  }
  75% {
    transform: translate(-25px, -15px) rotate(3deg) scale(1.01);
  }
}

// ============================================
// 品牌区域样式
// ============================================

.brand-section {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px;
  position: relative;
  z-index: 1;

  @media (max-width: 1024px) {
    padding: 32px;
  }

  @media (max-width: 968px) {
    display: none;
  }
}

.brand-content {
  max-width: 480px;
  color: white;
  animation: fadeInUp 0.8s ease-out;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.brand-logo {
  width: 80px;
  height: 80px;
  margin-bottom: 32px;
  animation: logoFloat 4s ease-in-out infinite;

  svg {
    width: 100%;
    height: 100%;
    filter: drop-shadow(0 4px 20px rgba(0, 0, 0, 0.2));
  }
}

@keyframes logoFloat {
  0%, 100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-8px);
  }
}

.brand-title {
  font-size: 42px;
  font-weight: 700;
  margin-bottom: 16px;
  line-height: 1.2;
  text-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);

  @media (max-width: 1024px) {
    font-size: 36px;
  }
}

.brand-description {
  font-size: 18px;
  line-height: 1.6;
  opacity: 0.9;
  margin-bottom: 48px;

  @media (max-width: 1024px) {
    font-size: 16px;
    margin-bottom: 36px;
  }
}

.features {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
}

.feature-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 20px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  cursor: default;

  &:hover {
    background: rgba(255, 255, 255, 0.18);
    transform: translateY(-3px) scale(1.02);
    border-color: rgba(255, 255, 255, 0.2);
    box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);

    .feature-icon {
      transform: scale(1.1) rotate(5deg);
      background: rgba(255, 255, 255, 0.3);
    }
  }

  .feature-icon {
    width: 40px;
    height: 40px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: rgba(255, 255, 255, 0.2);
    border-radius: 12px;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);

    svg {
      width: 20px;
      height: 20px;
    }
  }

  span {
    font-size: 15px;
    font-weight: 500;
  }
}

// ============================================
// SubTask 4.4: 优化响应式布局 - 登录区域
// ============================================

.login-section {
  width: 480px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: 40px;
  position: relative;
  z-index: 1;

  // 平板端适配
  @media (max-width: 1024px) {
    width: 420px;
    padding: 32px;
  }

  // 小屏幕适配
  @media (max-width: 968px) {
    width: 100%;
    max-width: 480px;
    margin: 0 auto;
    padding: 24px;
  }

  // 移动端适配
  @media (max-width: 480px) {
    padding: 16px;
    justify-content: flex-start;
    padding-top: 40px;
  }

  // 超小屏幕
  @media (max-width: 360px) {
    padding: 12px;
    padding-top: 24px;
  }
}

.login-box {
  background: white;
  border-radius: 24px;
  padding: 48px 40px;
  box-shadow:
    0 25px 50px -12px rgba(0, 0, 0, 0.25),
    0 0 0 1px rgba(255, 255, 255, 0.1);
  animation: scaleIn 0.5s ease-out;
  position: relative;
  overflow: hidden;

  // 顶部装饰光效
  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 4px;
    background: linear-gradient(90deg, var(--color-primary), var(--color-primary-light), var(--color-primary));
    background-size: 200% 100%;
    animation: shimmer 3s ease-in-out infinite;
  }

  // 平板端
  @media (max-width: 1024px) {
    padding: 40px 32px;
    border-radius: 20px;
  }

  // 移动端
  @media (max-width: 480px) {
    padding: 28px 20px;
    border-radius: 16px;
    box-shadow:
      0 15px 35px -10px rgba(0, 0, 0, 0.2),
      0 0 0 1px rgba(255, 255, 255, 0.1);
  }

  // 超小屏幕
  @media (max-width: 360px) {
    padding: 24px 16px;
    border-radius: 12px;
  }
}

@keyframes shimmer {
  0%, 100% {
    background-position: 200% 0;
  }
  50% {
    background-position: 0% 0;
  }
}

@keyframes scaleIn {
  from {
    opacity: 0;
    transform: scale(0.95) translateY(10px);
  }
  to {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}

.login-header {
  text-align: center;
  margin-bottom: 36px;

  @media (max-width: 480px) {
    margin-bottom: 28px;
  }

  @media (max-width: 360px) {
    margin-bottom: 24px;
  }
}

.login-title {
  font-size: 28px;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 8px;

  @media (max-width: 480px) {
    font-size: 24px;
  }

  @media (max-width: 360px) {
    font-size: 22px;
  }
}

.login-subtitle {
  font-size: 15px;
  color: var(--text-muted);
  margin: 0;

  @media (max-width: 480px) {
    font-size: 14px;
  }
}

// ============================================
// SubTask 4.2: 优化表单输入交互
// ============================================

.login-form {
  .el-form-item {
    margin-bottom: 24px;

    @media (max-width: 480px) {
      margin-bottom: 20px;
    }

    @media (max-width: 360px) {
      margin-bottom: 16px;
    }
  }

  .input-wrapper {
    width: 100%;
    position: relative;
  }

  .input-label {
    display: block;
    font-size: 14px;
    font-weight: 500;
    color: var(--text-regular);
    margin-bottom: 8px;
    transition: all 0.2s ease;

    @media (max-width: 480px) {
      font-size: 13px;
      margin-bottom: 6px;
    }
  }

  // 输入框聚焦时标签颜色变化
  .input-wrapper:focus-within .input-label {
    color: var(--color-primary);
  }

  :deep(.el-input__wrapper) {
    padding: 4px 16px;
    height: 48px;
    border-radius: 12px;
    box-shadow: 0 0 0 1px var(--border-secondary);
    transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
    background: var(--bg-primary);

    @media (max-width: 480px) {
      height: 44px;
      border-radius: 10px;
      padding: 4px 12px;
    }

    @media (max-width: 360px) {
      height: 42px;
      border-radius: 8px;
    }

    &:hover {
      box-shadow: 0 0 0 1px var(--color-primary-light);
      background: var(--bg-primary);
    }

    &.is-focus {
      box-shadow:
        0 0 0 2px var(--color-primary),
        0 4px 12px rgba(15, 118, 110, 0.15);
      transform: translateY(-1px);
    }

    // 焦点可见样式（无障碍访问）
    &:focus-within {
      box-shadow: 0 0 0 2px var(--color-primary), 0 0 0 4px rgba(15, 118, 110, 0.1);
    }
  }

  // 输入框图标动画
  :deep(.el-input__prefix) {
    transition: all 0.25s ease;

    .el-icon {
      font-size: 18px;
      color: var(--text-muted);
      transition: all 0.25s ease;
    }
  }

  :deep(.el-input__wrapper.is-focus) {
    .el-input__prefix .el-icon {
      color: var(--color-primary);
      transform: scale(1.1);
    }
  }

  :deep(.el-input__inner) {
    font-size: 15px;

    @media (max-width: 480px) {
      font-size: 14px;
    }

    &::placeholder {
      color: var(--text-placeholder);
      transition: all 0.2s ease;
    }

    // 焦点可见样式
    &:focus-visible {
      outline: none;
    }
  }

  // 输入框聚焦时占位符上浮效果
  :deep(.el-input__wrapper.is-focus .el-input__inner::placeholder) {
    opacity: 0.6;
  }

  // 清除按钮和密码显示按钮动画
  :deep(.el-input__suffix) {
    .el-input__clear,
    .el-input__password {
      transition: all 0.2s ease;

      &:hover {
        color: var(--color-primary);
        transform: scale(1.1);
      }
    }
  }

  .login-options {
    display: flex;
    justify-content: space-between;
    align-items: center;
    width: 100%;

    @media (max-width: 360px) {
      flex-direction: column;
      align-items: flex-start;
      gap: 8px;
    }

    .remember-text {
      font-size: 14px;
      color: var(--text-regular);

      @media (max-width: 480px) {
        font-size: 13px;
      }
    }

    .forgot-link {
      font-size: 14px;
      font-weight: 500;
      transition: all 0.2s ease;

      @media (max-width: 480px) {
        font-size: 13px;
      }

      &:hover {
        transform: translateX(2px);
      }

      // 焦点可见样式（无障碍访问）
      &:focus-visible {
        outline: 2px solid var(--color-primary);
        outline-offset: 2px;
        border-radius: var(--radius-sm);
      }
    }
  }

  // ============================================
  // SubTask 4.3: 添加登录按钮加载动画
  // ============================================

  .login-button {
    width: 100%;
    height: 52px;
    font-size: 16px;
    font-weight: 600;
    border-radius: 12px;
    background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-primary-dark) 100%);
    border: none;
    box-shadow:
      0 4px 14px rgba(15, 118, 110, 0.4),
      inset 0 1px 0 rgba(255, 255, 255, 0.1);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    position: relative;
    overflow: hidden;

    @media (max-width: 480px) {
      height: 48px;
      font-size: 15px;
      border-radius: 10px;
    }

    @media (max-width: 360px) {
      height: 44px;
      font-size: 14px;
      border-radius: 8px;
    }

    // 按钮光泽效果
    &::before {
      content: '';
      position: absolute;
      top: 0;
      left: -100%;
      width: 100%;
      height: 100%;
      background: linear-gradient(
        90deg,
        transparent,
        rgba(255, 255, 255, 0.2),
        transparent
      );
      transition: left 0.5s ease;
    }

    &:hover:not(:disabled) {
      transform: translateY(-2px);
      box-shadow:
        0 8px 25px rgba(15, 118, 110, 0.5),
        inset 0 1px 0 rgba(255, 255, 255, 0.15);
      background: linear-gradient(135deg, var(--color-primary-dark) 0%, var(--color-primary) 100%);

      &::before {
        left: 100%;
      }
    }

    &:active:not(:disabled) {
      transform: translateY(0) scale(0.98);
      box-shadow:
        0 2px 8px rgba(15, 118, 110, 0.4),
        inset 0 1px 0 rgba(255, 255, 255, 0.1);
    }

    // 焦点可见样式（无障碍访问）
    &:focus-visible {
      outline: 2px solid var(--color-white);
      outline-offset: 2px;
      box-shadow: 0 0 0 4px rgba(15, 118, 110, 0.3), 0 4px 14px rgba(15, 118, 110, 0.4);
    }

    // 加载状态动画
    &.is-loading {
      pointer-events: none;

      &::after {
        content: '';
        position: absolute;
        width: 20px;
        height: 20px;
        border: 2px solid rgba(255, 255, 255, 0.3);
        border-top-color: white;
        border-radius: 50%;
        animation: buttonSpin 0.8s linear infinite;
      }
    }
  }
}

// 按钮加载旋转动画
@keyframes buttonSpin {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}

// ============================================
// 登录底部区域
// ============================================

.login-footer {
  margin-top: 24px;

  @media (max-width: 480px) {
    margin-top: 20px;
  }

  .divider {
    display: flex;
    align-items: center;
    margin-bottom: 20px;

    @media (max-width: 480px) {
      margin-bottom: 16px;
    }

    &::before,
    &::after {
      content: '';
      flex: 1;
      height: 1px;
      background: linear-gradient(
        90deg,
        transparent,
        var(--border-secondary),
        transparent
      );
    }

    span {
      padding: 0 16px;
      font-size: 13px;
      color: var(--text-muted);

      @media (max-width: 480px) {
        font-size: 12px;
        padding: 0 12px;
      }
    }
  }

  .demo-account {
    text-align: center;
    font-size: 13px;
    color: var(--text-muted);
    margin: 0;
    padding: 12px 16px;
    background: var(--bg-tertiary);
    border-radius: 10px;
    border: 1px solid var(--border-secondary);
    transition: all 0.2s ease;

    @media (max-width: 480px) {
      font-size: 12px;
      padding: 10px 12px;
      border-radius: 8px;
    }

    &:hover {
      background: var(--bg-secondary);
      border-color: var(--color-primary-light);
    }

    code {
      background: var(--color-primary-light-9);
      color: var(--color-primary);
      padding: 2px 8px;
      border-radius: 4px;
      font-family: 'JetBrains Mono', monospace;
      font-size: 12px;
      transition: all 0.2s ease;

      @media (max-width: 480px) {
        font-size: 11px;
        padding: 2px 6px;
      }
    }
  }
}

// ============================================
// 版权信息
// ============================================

.copyright {
  text-align: center;
  margin-top: 24px;

  @media (max-width: 480px) {
    margin-top: 16px;
  }

  p {
    font-size: 12px;
    color: rgba(255, 255, 255, 0.7);
    margin: 0;
    text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);

    @media (max-width: 480px) {
      font-size: 11px;
    }
  }
}

// ============================================
// SubTask 4.4: 额外的响应式优化
// ============================================

// 横屏模式下的移动端适配
@media (max-width: 896px) and (orientation: landscape) {
  .login-container {
    min-height: auto;
    padding: 20px 0;
  }

  .login-section {
    justify-content: center;
    padding: 16px;
  }

  .login-box {
    padding: 24px 32px;
  }

  .login-header {
    margin-bottom: 20px;
  }

  .login-form .el-form-item {
    margin-bottom: 16px;
  }
}

// 高分辨率屏幕优化
@media (min-width: 1440px) {
  .brand-section {
    padding: 60px;
  }

  .brand-content {
    max-width: 560px;
  }

  .brand-title {
    font-size: 48px;
  }

  .brand-description {
    font-size: 20px;
  }

  .login-section {
    width: 520px;
    padding: 60px;
  }

  .login-box {
    padding: 56px 48px;
  }
}

// 打印样式优化
@media print {
  .login-container {
    background: white;
  }

  .background-decoration {
    display: none;
  }

  .brand-section {
    display: none;
  }

  .login-section {
    width: 100%;
    max-width: none;
  }

  .login-box {
    box-shadow: none;
    border: 1px solid #ddd;
  }
}

// 减少动画偏好设置
@media (prefers-reduced-motion: reduce) {
  .login-container {
    animation: none;
  }

  .background-decoration .shape {
    animation: none;
  }

  .brand-logo {
    animation: none;
  }

  .login-box {
    animation: none;

    &::before {
      animation: none;
    }
  }

  .login-form .login-button::before {
    display: none;
  }

  * {
    transition-duration: 0.01ms !important;
    animation-duration: 0.01ms !important;
  }
}
</style>
