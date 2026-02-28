<template>
  <div class="profile-page">
    <el-row :gutter="20">
      <el-col :span="8">
        <el-card class="profile-card">
          <template #header>
            <div class="card-header">
              <span>个人信息</span>
            </div>
          </template>
          <div class="profile-content">
            <div class="avatar-section">
              <el-avatar :size="100" :src="userStore.avatar || defaultAvatar" />
              <el-upload
                class="avatar-upload"
                action="#"
                :show-file-list="false"
                :before-upload="beforeAvatarUpload"
              >
                <el-button type="primary" size="small">更换头像</el-button>
              </el-upload>
            </div>
            <div class="info-section">
              <div class="info-item">
                <span class="label">用户名：</span>
                <span class="value">{{ userStore.username }}</span>
              </div>
              <div class="info-item">
                <span class="label">姓名：</span>
                <span class="value">{{ userInfo.name || '-' }}</span>
              </div>
              <div class="info-item">
                <span class="label">手机号：</span>
                <span class="value">{{ userInfo.phone || '-' }}</span>
              </div>
              <div class="info-item">
                <span class="label">邮箱：</span>
                <span class="value">{{ userInfo.email || '-' }}</span>
              </div>
              <div class="info-item">
                <span class="label">角色：</span>
                <el-tag :type="userStore.userType === 'admin' ? 'danger' : 'primary'">
                  {{ userStore.userType === 'admin' ? '管理员' : '员工' }}
                </el-tag>
              </div>
              <div class="info-item">
                <span class="label">职位：</span>
                <span class="value">{{ userInfo.position || '-' }}</span>
              </div>
              <div class="info-item">
                <span class="label">最后登录：</span>
                <span class="value">{{ formatDate(userInfo.last_login) }}</span>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="16">
        <el-card class="settings-card">
          <el-tabs v-model="activeTab">
            <el-tab-pane label="基本信息" name="info">
              <el-form
                ref="infoFormRef"
                :model="infoForm"
                :rules="infoRules"
                label-width="100px"
                class="info-form"
              >
                <el-form-item label="姓名" prop="name">
                  <el-input v-model="infoForm.name" placeholder="请输入姓名" />
                </el-form-item>
                <el-form-item label="手机号" prop="phone">
                  <el-input v-model="infoForm.phone" placeholder="请输入手机号" />
                </el-form-item>
                <el-form-item label="邮箱" prop="email">
                  <el-input v-model="infoForm.email" placeholder="请输入邮箱" />
                </el-form-item>
                <el-form-item label="职位" prop="position">
                  <el-input v-model="infoForm.position" placeholder="请输入职位" disabled />
                </el-form-item>
                <el-form-item>
                  <el-button type="primary" :loading="infoLoading" @click="handleUpdateInfo">
                    保存修改
                  </el-button>
                </el-form-item>
              </el-form>
            </el-tab-pane>

            <el-tab-pane label="修改密码" name="password">
              <el-form
                ref="passwordFormRef"
                :model="passwordForm"
                :rules="passwordRules"
                label-width="100px"
                class="password-form"
              >
                <el-form-item label="当前密码" prop="old_password">
                  <el-input
                    v-model="passwordForm.old_password"
                    type="password"
                    placeholder="请输入当前密码"
                    show-password
                  />
                </el-form-item>
                <el-form-item label="新密码" prop="new_password">
                  <el-input
                    v-model="passwordForm.new_password"
                    type="password"
                    placeholder="至少 6 位字符"
                    show-password
                  />
                </el-form-item>
                <el-form-item label="确认密码" prop="confirm_password">
                  <el-input
                    v-model="passwordForm.confirm_password"
                    type="password"
                    placeholder="请再次输入新密码"
                    show-password
                  />
                </el-form-item>
                <el-form-item>
                  <el-button type="primary" :loading="passwordLoading" @click="handleChangePassword">
                    修改密码
                  </el-button>
                  <el-button @click="resetPasswordForm">重置</el-button>
                </el-form-item>
              </el-form>
            </el-tab-pane>

            <el-tab-pane label="账号设置" name="settings">
              <div class="settings-section">
                <h4>账号安全</h4>
                <div class="setting-item">
                  <div class="setting-info">
                    <span class="setting-label">登录失败锁定</span>
                    <span class="setting-desc">连续 5 次登录失败，账号将被锁定 30 分钟</span>
                  </div>
                  <el-tag type="success">已启用</el-tag>
                </div>
                <div class="setting-item">
                  <div class="setting-info">
                    <span class="setting-label">密码强度</span>
                    <span class="setting-desc">密码长度至少 6 个字符</span>
                  </div>
                  <el-tag type="warning">基础</el-tag>
                </div>
              </div>

              <el-divider />

              <div class="settings-section">
                <h4>登录记录</h4>
                <el-table :data="loginRecords" style="width: 100%">
                  <el-table-column prop="login_time" label="登录时间" width="180">
                    <template #default="{ row }">
                      {{ formatDate(row.login_time) }}
                    </template>
                  </el-table-column>
                  <el-table-column prop="ip" label="IP 地址" width="150" />
                  <el-table-column prop="device" label="设备" />
                  <el-table-column prop="status" label="状态" width="100">
                    <template #default="{ row }">
                      <el-tag :type="row.status === 'success' ? 'success' : 'danger'">
                        {{ row.status === 'success' ? '成功' : '失败' }}
                      </el-tag>
                    </template>
                  </el-table-column>
                </el-table>
              </div>
            </el-tab-pane>
          </el-tabs>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import dayjs from 'dayjs'
import { useUserStore } from '@/store/user'
import { getCurrentUser, updateUserInfo, changePassword } from '@/api/user'

const userStore = useUserStore()
const activeTab = ref('info')
const infoFormRef = ref(null)
const passwordFormRef = ref(null)
const infoLoading = ref(false)
const passwordLoading = ref(false)

const defaultAvatar = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAiIGhlaWdodD0iNDAiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PGNpcmNsZSBjeD0iMjAiIGN5PSIyMCIgcj0iMjAiIGZpbGw9IiM0MDlFRkYiLz48Y2lyY2xlIGN4PSIyMCIgY3k9IjE1IiByPSI4IiBmaWxsPSIjZmZmIi8+PHBhdGggZD0iTTEyIDMwYzAtNCA0LTggOC04czggNCA4IDgiIGZpbGw9IiNmZmYiLz48L3N2Zz4='

const userInfo = reactive({
  name: '',
  phone: '',
  email: '',
  position: '',
  last_login: null
})

const infoForm = reactive({
  name: '',
  phone: '',
  email: '',
  position: ''
})

const infoRules = {
  name: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
  phone: [
    { required: true, message: '请输入手机号', trigger: 'blur' },
    { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号', trigger: 'blur' }
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱地址', trigger: 'blur' }
  ]
}

const passwordForm = reactive({
  old_password: '',
  new_password: '',
  confirm_password: ''
})

const validateConfirmPassword = (rule, value, callback) => {
  if (value !== passwordForm.new_password) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const passwordRules = {
  old_password: [
    { required: true, message: '请输入当前密码', trigger: 'blur' }
  ],
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码长度至少 6 位', trigger: 'blur' }
  ],
  confirm_password: [
    { required: true, message: '请再次输入新密码', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: 'blur' }
  ]
}

const loginRecords = ref([
  { login_time: new Date(), ip: '192.168.1.100', device: 'Chrome / Windows', status: 'success' },
  { login_time: new Date(Date.now() - 86400000), ip: '192.168.1.101', device: 'Safari / macOS', status: 'success' },
  { login_time: new Date(Date.now() - 172800000), ip: '192.168.1.102', device: 'Firefox / Linux', status: 'failed' }
])

const formatDate = (date) => {
  return date ? dayjs(date).format('YYYY-MM-DD HH:mm:ss') : '-'
}

const fetchUserInfo = async () => {
  try {
    const res = await getCurrentUser()
    Object.assign(userInfo, res.data)
    Object.assign(infoForm, {
      name: res.data.name || '',
      phone: res.data.phone || '',
      email: res.data.email || '',
      position: res.data.position || ''
    })
  } catch (error) {
    console.error('获取用户信息失败', error)
  }
}

const beforeAvatarUpload = (file) => {
  const isImage = file.type.startsWith('image/')
  const isLt2M = file.size / 1024 / 1024 < 2

  if (!isImage) {
    ElMessage.error('只能上传图片文件!')
    return false
  }
  if (!isLt2M) {
    ElMessage.error('图片大小不能超过 2MB!')
    return false
  }
  
  ElMessage.info('头像上传功能开发中...')
  return false
}

const handleUpdateInfo = async () => {
  if (!infoFormRef.value) return
  
  await infoFormRef.value.validate(async (valid) => {
    if (!valid) return
    
    infoLoading.value = true
    try {
      await updateUserInfo(infoForm)
      Object.assign(userInfo, infoForm)
      ElMessage.success('信息更新成功')
    } catch (error) {
      ElMessage.error(error.message || '更新失败')
    } finally {
      infoLoading.value = false
    }
  })
}

const handleChangePassword = async () => {
  if (!passwordFormRef.value) return
  
  await passwordFormRef.value.validate(async (valid) => {
    if (!valid) return
    
    passwordLoading.value = true
    try {
      await changePassword({
        old_password: passwordForm.old_password,
        new_password: passwordForm.new_password
      })
      ElMessage.success('密码修改成功，请重新登录')
      resetPasswordForm()
      setTimeout(() => {
        userStore.logout()
      }, 1500)
    } catch (error) {
      ElMessage.error(error.message || '密码修改失败')
    } finally {
      passwordLoading.value = false
    }
  })
}

const resetPasswordForm = () => {
  passwordForm.old_password = ''
  passwordForm.new_password = ''
  passwordForm.confirm_password = ''
  if (passwordFormRef.value) {
    passwordFormRef.value.resetFields()
  }
}

onMounted(() => {
  fetchUserInfo()
})
</script>

<style lang="scss" scoped>
.profile-page {
  .profile-card {
    .card-header {
      font-size: 16px;
      font-weight: 600;
    }
    
    .profile-content {
      .avatar-section {
        display: flex;
        flex-direction: column;
        align-items: center;
        padding: 20px 0;
        border-bottom: 1px solid #ebeef5;
        
        .avatar-upload {
          margin-top: 16px;
        }
      }
      
      .info-section {
        padding: 20px 0;
        
        .info-item {
          display: flex;
          align-items: center;
          padding: 12px 0;
          border-bottom: 1px solid #f0f0f0;
          
          &:last-child {
            border-bottom: none;
          }
          
          .label {
            color: #909399;
            width: 80px;
            flex-shrink: 0;
          }
          
          .value {
            color: #303133;
            flex: 1;
          }
        }
      }
    }
  }
  
  .settings-card {
    .info-form,
    .password-form {
      max-width: 500px;
      padding: 20px 0;
    }
    
    .settings-section {
      h4 {
        margin: 0 0 16px 0;
        font-size: 16px;
        font-weight: 600;
        color: #303133;
      }
      
      .setting-item {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 16px;
        background-color: #f5f7fa;
        border-radius: 4px;
        margin-bottom: 12px;
        
        .setting-info {
          .setting-label {
            font-size: 14px;
            font-weight: 500;
            color: #303133;
            display: block;
          }
          
          .setting-desc {
            font-size: 12px;
            color: #909399;
            margin-top: 4px;
            display: block;
          }
        }
      }
    }
  }
}
</style>
