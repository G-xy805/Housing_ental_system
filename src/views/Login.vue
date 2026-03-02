<template>
  <div class="login-container">
    <!-- 背景装饰 -->
    <div class="background-decoration">
      <div class="shape shape-1"></div>
      <div class="shape shape-2"></div>
      <div class="shape shape-3"></div>
      <div class="shape shape-4"></div>
    </div>
    
    <!-- 左侧品牌区域 -->
    <div class="brand-section">
      <div class="brand-content">
        <div class="brand-logo">
          <svg viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
            <rect width="48" height="48" rx="12" fill="white" fill-opacity="0.2"/>
            <path d="M12 24L24 12L36 24V36H27V27H21V36H12V24Z" fill="white"/>
          </svg>
        </div>
        <h1 class="brand-title">房屋租赁管理系统</h1>
        <p class="brand-description">
          高效、智能、安全的房屋租赁管理平台<br/>
          助您轻松管理房源、租客与合同
        </p>
        
        <div class="features">
          <div class="feature-item">
            <div class="feature-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>
                <polyline points="9,22 9,12 15,12 15,22"/>
              </svg>
            </div>
            <span>房源管理</span>
          </div>
          <div class="feature-item">
            <div class="feature-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
                <circle cx="9" cy="7" r="4"/>
                <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
                <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
              </svg>
            </div>
            <span>租客管理</span>
          </div>
          <div class="feature-item">
            <div class="feature-icon">
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
          <div class="feature-item">
            <div class="feature-icon">
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
          <h2 class="login-title">欢迎回来</h2>
          <p class="login-subtitle">请登录您的账号以继续</p>
        </div>
        
        <el-form
          ref="loginFormRef"
          :model="loginForm"
          :rules="loginRules"
          class="login-form"
          size="large"
        >
          <el-form-item prop="username">
            <div class="input-wrapper">
              <label class="input-label">用户名</label>
              <el-input
                v-model="loginForm.username"
                placeholder="请输入用户名"
                :prefix-icon="User"
                clearable
              />
            </div>
          </el-form-item>
          
          <el-form-item prop="password">
            <div class="input-wrapper">
              <label class="input-label">密码</label>
              <el-input
                v-model="loginForm.password"
                type="password"
                placeholder="请输入密码"
                :prefix-icon="Lock"
                show-password
                @keyup.enter="handleLogin"
              />
            </div>
          </el-form-item>
          
          <el-form-item>
            <div class="login-options">
              <el-checkbox v-model="rememberMe">
                <span class="remember-text">记住我</span>
              </el-checkbox>
              <el-link type="primary" :underline="false" class="forgot-link">
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
            >
              <span v-if="!loading">登 录</span>
              <span v-else>登录中...</span>
            </el-button>
          </el-form-item>
        </el-form>
        
        <div class="login-footer">
          <div class="divider">
            <span>或</span>
          </div>
          <p class="demo-account">
            演示账号：<code>admin</code> / <code>Admin123!</code>
          </p>
        </div>
      </div>
      
      <!-- 版权信息 -->
      <div class="copyright">
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
.login-container {
  width: 100%;
  min-height: 100vh;
  display: flex;
  background: linear-gradient(135deg, #0F766E 0%, #0D9488 50%, #14B8A6 100%);
  position: relative;
  overflow: hidden;
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
    background: rgba(255, 255, 255, 0.1);
    animation: float 20s infinite ease-in-out;
  }
  
  .shape-1 {
    width: 400px;
    height: 400px;
    top: -100px;
    left: -100px;
    animation-delay: 0s;
  }
  
  .shape-2 {
    width: 300px;
    height: 300px;
    top: 50%;
    left: 30%;
    animation-delay: -5s;
  }
  
  .shape-3 {
    width: 200px;
    height: 200px;
    bottom: 10%;
    left: 10%;
    animation-delay: -10s;
  }
  
  .shape-4 {
    width: 150px;
    height: 150px;
    top: 20%;
    left: 45%;
    animation-delay: -15s;
  }
}

@keyframes float {
  0%, 100% {
    transform: translate(0, 0) rotate(0deg);
  }
  25% {
    transform: translate(20px, -20px) rotate(5deg);
  }
  50% {
    transform: translate(-10px, 20px) rotate(-5deg);
  }
  75% {
    transform: translate(-20px, -10px) rotate(3deg);
  }
}

.brand-section {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px;
  position: relative;
  z-index: 1;
  
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
  
  svg {
    width: 100%;
    height: 100%;
    filter: drop-shadow(0 4px 20px rgba(0, 0, 0, 0.2));
  }
}

.brand-title {
  font-size: 42px;
  font-weight: 700;
  margin-bottom: 16px;
  line-height: 1.2;
  text-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

.brand-description {
  font-size: 18px;
  line-height: 1.6;
  opacity: 0.9;
  margin-bottom: 48px;
}

.features {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 24px;
}

.feature-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 20px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  backdrop-filter: blur(10px);
  transition: all 0.3s ease;
  
  &:hover {
    background: rgba(255, 255, 255, 0.2);
    transform: translateY(-2px);
  }
  
  .feature-icon {
    width: 40px;
    height: 40px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: rgba(255, 255, 255, 0.2);
    border-radius: 10px;
    
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

.login-section {
  width: 480px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: 40px;
  position: relative;
  z-index: 1;
  
  @media (max-width: 968px) {
    width: 100%;
    max-width: 480px;
    margin: 0 auto;
  }
  
  @media (max-width: 480px) {
    padding: 24px;
  }
}

.login-box {
  background: white;
  border-radius: 24px;
  padding: 48px 40px;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
  animation: scaleIn 0.5s ease-out;
  
  @media (max-width: 480px) {
    padding: 32px 24px;
    border-radius: 20px;
  }
}

@keyframes scaleIn {
  from {
    opacity: 0;
    transform: scale(0.95);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

.login-header {
  text-align: center;
  margin-bottom: 36px;
}

.login-title {
  font-size: 28px;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 8px;
}

.login-subtitle {
  font-size: 15px;
  color: var(--text-muted);
  margin: 0;
}

.login-form {
  .el-form-item {
    margin-bottom: 24px;
  }
  
  .input-wrapper {
    width: 100%;
  }
  
  .input-label {
    display: block;
    font-size: 14px;
    font-weight: 500;
    color: var(--text-regular);
    margin-bottom: 8px;
  }
  
  :deep(.el-input__wrapper) {
    padding: 4px 16px;
    height: 48px;
    border-radius: 12px;
    box-shadow: 0 0 0 1px var(--border-secondary);
    transition: all 0.2s ease;
    
    &:hover {
      box-shadow: 0 0 0 1px var(--color-primary-light);
    }
    
    &.is-focus {
      box-shadow: 0 0 0 2px var(--color-primary);
    }
  }
  
  :deep(.el-input__inner) {
    font-size: 15px;
    
    &::placeholder {
      color: var(--text-placeholder);
    }
  }
  
  .login-options {
    display: flex;
    justify-content: space-between;
    align-items: center;
    width: 100%;
    
    .remember-text {
      font-size: 14px;
      color: var(--text-regular);
    }
    
    .forgot-link {
      font-size: 14px;
      font-weight: 500;
    }
  }
  
  .login-button {
    width: 100%;
    height: 52px;
    font-size: 16px;
    font-weight: 600;
    border-radius: 12px;
    background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-primary-dark) 100%);
    border: none;
    box-shadow: 0 4px 14px rgba(15, 118, 110, 0.4);
    transition: all 0.3s ease;
    
    &:hover:not(:disabled) {
      transform: translateY(-2px);
      box-shadow: 0 6px 20px rgba(15, 118, 110, 0.5);
    }
    
    &:active:not(:disabled) {
      transform: translateY(0);
    }
  }
}

.login-footer {
  margin-top: 24px;
  
  .divider {
    display: flex;
    align-items: center;
    margin-bottom: 20px;
    
    &::before,
    &::after {
      content: '';
      flex: 1;
      height: 1px;
      background: var(--border-secondary);
    }
    
    span {
      padding: 0 16px;
      font-size: 13px;
      color: var(--text-muted);
    }
  }
  
  .demo-account {
    text-align: center;
    font-size: 13px;
    color: var(--text-muted);
    margin: 0;
    padding: 12px 16px;
    background: var(--bg-tertiary);
    border-radius: 8px;
    
    code {
      background: var(--color-primary-light-9);
      color: var(--color-primary);
      padding: 2px 8px;
      border-radius: 4px;
      font-family: 'JetBrains Mono', monospace;
      font-size: 12px;
    }
  }
}

.copyright {
  text-align: center;
  margin-top: 24px;
  
  p {
    font-size: 12px;
    color: rgba(255, 255, 255, 0.7);
    margin: 0;
  }
}
</style>
