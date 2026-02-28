<template>
  <div class="forbidden-page">
    <div class="error-content">
      <h1 class="error-code">403</h1>
      <h2 class="error-title">无权限访问</h2>
      <p class="error-message">抱歉，您没有权限访问该页面</p>
      <el-button type="primary" @click="handleBack">返回首页</el-button>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()

const handleBack = () => {
  router.push('/')
}
</script>

<style lang="scss" scoped>
.forbidden-page {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background: #f5f7fa;

  .error-content {
    text-align: center;
    padding: 60px 20px;

    .error-code {
      font-size: 120px;
      font-weight: bold;
      color: #f56c6c;
      margin: 0;
      line-height: 1;
    }

    .error-title {
      font-size: 32px;
      color: #333;
      margin: 20px 0;
    }

    .error-message {
      font-size: 16px;
      color: #909399;
      margin-bottom: 30px;
    }
  }
}
</style>
