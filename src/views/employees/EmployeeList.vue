<template>
  <div class="list-page">
    <div class="page-header">
      <div class="header-content">
        <div class="header-left">
          <h1 class="page-title">员工管理</h1>
          <p class="page-subtitle">管理系统员工账户和权限</p>
        </div>
        <div class="header-right">
          <el-button type="primary" @click="handleAdd" class="add-button">
            <el-icon class="btn-icon"><Plus /></el-icon>
            新增员工
          </el-button>
        </div>
      </div>
    </div>

    <el-row :gutter="20" class="statistics-row">
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon total">
              <el-icon :size="32"><UserFilled /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ statistics.total || 0 }}</div>
              <div class="stat-label">总员工数</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon active">
              <el-icon :size="32"><CircleCheck /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ statistics.active || 0 }}</div>
              <div class="stat-label">在职员工</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon disabled">
              <el-icon :size="32"><CircleClose /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ statistics.disabled || 0 }}</div>
              <div class="stat-label">禁用员工</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon new">
              <el-icon :size="32"><TrendCharts /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ statistics.resigned || 0 }}</div>
              <div class="stat-label">离职员工</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <div class="filter-section">
      <div class="filter-content">
        <div class="filter-items">
          <div class="filter-item">
            <label class="filter-label">关键词</label>
            <el-input
              v-model="filterForm.keyword"
              placeholder="姓名/手机号/邮箱"
              clearable
              @clear="handleSearch"
              @keyup.enter="handleSearch"
              class="filter-input"
            />
          </div>
          <div class="filter-item">
            <label class="filter-label">状态</label>
            <el-select v-model="filterForm.status" placeholder="全部状态" clearable class="filter-select">
              <el-option label="在职" value="active" />
              <el-option label="离职" value="resigned" />
              <el-option label="禁用" value="disabled" />
            </el-select>
          </div>
          <div class="filter-item">
            <label class="filter-label">角色</label>
            <el-select v-model="filterForm.role" placeholder="全部角色" clearable class="filter-select">
              <el-option label="管理员" value="admin" />
              <el-option label="员工" value="staff" />
            </el-select>
          </div>
        </div>
        <div class="filter-actions">
          <el-button type="primary" @click="handleSearch" class="search-button">
            <el-icon class="btn-icon"><Search /></el-icon>
            搜索
          </el-button>
          <el-button @click="handleReset" class="reset-button">
            <el-icon class="btn-icon"><Refresh /></el-icon>
            重置
          </el-button>
        </div>
      </div>
    </div>

    <div class="table-section">
      <div class="table-container">
        <div v-if="selectedEmployees.length > 0" class="batch-actions">
          <span class="selected-info">已选择 {{ selectedEmployees.length }} 项</span>
          <el-button type="success" size="small" @click="handleBatchAction('enable')">
            批量启用
          </el-button>
          <el-button type="warning" size="small" @click="handleBatchAction('disable')">
            批量禁用
          </el-button>
          <el-button type="danger" size="small" @click="handleBatchAction('delete')">
            批量删除
          </el-button>
        </div>

        <el-table
          v-loading="loading"
          :data="employeeList"
          class="data-table"
          :header-cell-style="{ background: '#fafafa', fontWeight: '600' }"
          @selection-change="handleSelectionChange"
        >
          <el-table-column type="selection" width="55" />
          <el-table-column prop="id" label="ID" min-width="60" align="center" />
          <el-table-column prop="name" label="姓名" min-width="80">
            <template #default="{ row }">
              <div class="user-info">
                <div class="user-avatar" :style="{ background: getAvatarColor(row.name) }">
                  {{ row.name?.charAt(0) || 'U' }}
                </div>
                <span class="user-name">{{ row.name }}</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="phone" label="手机号" min-width="120" />
          <el-table-column prop="position" label="职位" min-width="90" />
          <el-table-column prop="role" label="角色" min-width="70" align="center">
            <template #default="{ row }">
              <span class="role-badge" :class="row.role">
                {{ row.role === 'admin' ? '管理员' : '员工' }}
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="status" label="状态" min-width="70" align="center">
            <template #default="{ row }">
              <span class="status-badge" :class="row.status">
                <span class="status-dot"></span>
                {{ getStatusText(row.status) }}
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="last_login" label="最后登录" min-width="150">
            <template #default="{ row }">
              {{ formatDate(row.last_login) }}
            </template>
          </el-table-column>
          <el-table-column label="操作" min-width="280" fixed="right" align="center">
            <template #default="{ row }">
              <div class="action-buttons">
                <el-button type="primary" size="small" link @click="handleView(row)">
                  <el-icon><View /></el-icon>
                  详情
                </el-button>
                <el-button type="primary" size="small" link @click="handleEdit(row)">
                  <el-icon><Edit /></el-icon>
                  编辑
                </el-button>
                <el-button
                  :type="row.status === 'active' ? 'warning' : 'success'"
                  size="small"
                  link
                  @click="handleToggleStatus(row)"
                >
                  <el-icon><Switch /></el-icon>
                  {{ row.status === 'active' ? '禁用' : '启用' }}
                </el-button>
                <el-button type="info" size="small" link @click="handleResetPassword(row)">
                  <el-icon><Key /></el-icon>
                  重置密码
                </el-button>
                <el-button
                  type="danger"
                  size="small"
                  link
                  @click="handleDelete(row)"
                  :disabled="row.role === 'admin'"
                >
                  <el-icon><Delete /></el-icon>
                  删除
                </el-button>
              </div>
            </template>
          </el-table-column>
        </el-table>

        <div class="pagination-container">
          <el-pagination
            v-model:current-page="pagination.page"
            v-model:page-size="pagination.per_page"
            :page-sizes="[10, 20, 50, 100]"
            :total="pagination.total"
            layout="total, sizes, prev, pager, next, jumper"
            @size-change="handleSizeChange"
            @current-change="handlePageChange"
          />
        </div>
      </div>
    </div>

    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="560px"
      :close-on-click-modal="false"
      class="form-dialog"
    >
      <el-form
      ref="formRef"
      :model="formData"
      :rules="formRules"
      label-width="100px"
      class="form-content"
    >
      <el-form-item label="用户名" prop="username">
        <el-input
          v-model="formData.username"
          placeholder="请输入用户名"
          :disabled="isEdit"
        />
      </el-form-item>
      <el-form-item v-if="!isEdit" label="密码" prop="password">
        <el-input
          v-model="formData.password"
          type="password"
          placeholder="请输入密码"
          show-password
        />
      </el-form-item>
      <el-form-item label="姓名" prop="name">
        <el-input v-model="formData.name" placeholder="请输入姓名" />
      </el-form-item>
      <el-form-item label="身份证号" prop="id_card">
        <el-input 
          v-model="formData.id_card" 
          placeholder="请输入身份证号" 
          maxlength="18" 
          :disabled="isEdit && hasIdCard"
        />
        <div v-if="isEdit && hasIdCard" class="form-tip">身份证号不可修改，如需更改请联系管理员</div>
      </el-form-item>
      <el-form-item label="手机号" prop="phone">
        <el-input v-model="formData.phone" placeholder="请输入手机号" />
      </el-form-item>
      <el-form-item label="邮箱" prop="email">
        <el-input v-model="formData.email" placeholder="请输入邮箱" />
      </el-form-item>
      <el-form-item label="职位" prop="position">
        <el-input v-model="formData.position" placeholder="请输入职位" />
      </el-form-item>
      <el-form-item label="角色" prop="role">
        <el-select v-model="formData.role" placeholder="请选择角色">
          <el-option label="管理员" value="admin" />
          <el-option label="员工" value="staff" />
        </el-select>
      </el-form-item>
      <el-form-item label="头像" prop="avatar">
        <div class="upload-container">
          <el-upload
            class="avatar-uploader"
            action="#"
            :http-request="handlePhotoUpload"
            :show-file-list="false"
            :before-upload="beforePhotoUpload"
          >
            <img v-if="formData.avatar" :src="formData.avatar" class="avatar" />
            <el-icon v-else class="avatar-uploader-icon"><Plus /></el-icon>
          </el-upload>
          <el-button
            v-if="formData.avatar"
            type="text"
            size="small"
            class="delete-photo-btn"
            @click="handlePhotoDelete"
          >
            <el-icon><Delete /></el-icon>
            删除头像
          </el-button>
        </div>
      </el-form-item>
      <el-form-item v-if="isEdit" label="状态" prop="status">
        <el-select v-model="formData.status" placeholder="请选择状态">
          <el-option label="在职" value="active" />
          <el-option label="离职" value="resigned" />
          <el-option label="禁用" value="disabled" />
        </el-select>
      </el-form-item>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="dialogVisible = false" class="cancel-btn">取消</el-button>
          <el-button type="primary" :loading="submitLoading" @click="handleSubmit" class="submit-btn">
            确定
          </el-button>
        </div>
      </template>
    </el-dialog>

    <el-dialog v-model="passwordDialogVisible" title="重置密码" width="420px" class="form-dialog">
      <el-form :model="passwordForm" label-width="80px" class="form-content">
        <el-form-item label="员工">
          <el-input :value="currentEmployee?.name" disabled />
        </el-form-item>
        <el-form-item label="新密码">
          <el-input
            v-model="passwordForm.newPassword"
            type="password"
            placeholder="请输入新密码"
            show-password
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="passwordDialogVisible = false" class="cancel-btn">取消</el-button>
          <el-button type="primary" :loading="passwordLoading" @click="confirmResetPassword" class="submit-btn">
            确定
          </el-button>
        </div>
      </template>
    </el-dialog>

    <el-dialog v-model="detailVisible" title="员工详情" width="800px" class="detail-dialog">
      <div class="detail-header">
        <div class="detail-avatar">
          <img v-if="currentEmployee?.avatar" :src="currentEmployee.avatar" alt="头像" class="avatar-image" />
          <div v-else class="avatar-placeholder" :style="{ background: getAvatarColor(currentEmployee?.name) }">
            {{ currentEmployee?.name?.charAt(0) || 'U' }}
          </div>
        </div>
        <div class="detail-basic-info">
          <h3 class="detail-name">{{ currentEmployee?.name }}</h3>
          <p class="detail-position">{{ currentEmployee?.position || '暂无职位' }}</p>
          <span class="role-badge" :class="currentEmployee?.role">
            {{ roleMap[currentEmployee?.role] || '-' }}
          </span>
        </div>
      </div>
      <el-descriptions :column="2" border class="detail-descriptions">
        <el-descriptions-item label="ID">
          {{ currentEmployee?.id }}
        </el-descriptions-item>
        <el-descriptions-item label="用户名">
          {{ currentEmployee?.username }}
        </el-descriptions-item>
        <el-descriptions-item label="手机号">
          {{ currentEmployee?.phone }}
        </el-descriptions-item>
        <el-descriptions-item label="邮箱">
          {{ currentEmployee?.email || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="身份证号">
          {{ maskIdCard(currentEmployee?.id_card) }}
        </el-descriptions-item>
        <el-descriptions-item label="状态">
          <span class="status-badge" :class="currentEmployee?.status">
            <span class="status-dot"></span>
            {{ statusMap[currentEmployee?.status] || '-' }}
          </span>
        </el-descriptions-item>
        <el-descriptions-item label="创建时间">
          {{ formatDate(currentEmployee?.created_at) }}
        </el-descriptions-item>
        <el-descriptions-item label="更新时间">
          {{ formatDate(currentEmployee?.updated_at) }}
        </el-descriptions-item>
      </el-descriptions>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="detailVisible = false">关闭</el-button>
          <el-button type="primary" @click="handleEdit(currentEmployee)">编辑</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, Refresh, Edit, Delete, Key, Switch, View, UserFilled, CircleCheck, CircleClose, TrendCharts } from '@element-plus/icons-vue'
import dayjs from 'dayjs'
import request from '@/api/request'
import {
  getEmployeeList,
  createEmployee,
  updateEmployee,
  updateEmployeeStatus,
  deleteEmployee,
  resetEmployeePassword,
  getEmployeeStats,
  batchActionEmployees
} from '@/api/employee'
import { useUserStore } from '@/store/user'

const userStore = useUserStore()

const loading = ref(false)
const employeeList = ref([])
const selectedEmployees = ref([])
const dialogVisible = ref(false)
const detailVisible = ref(false)
const dialogTitle = ref('新增员工')
const isEdit = ref(false)
const submitLoading = ref(false)
const formRef = ref(null)
const currentEmployee = ref(null)
const hasIdCard = ref(false)

const statistics = reactive({
  total: 0,
  active: 0,
  disabled: 0,
  resigned: 0
})

const filterForm = reactive({
  keyword: '',
  status: '',
  role: ''
})

const pagination = reactive({
  page: 1,
  per_page: 20,
  total: 0
})

const formData = reactive({
  username: '',
  password: '',
  name: '',
  id_card: '',
  phone: '',
  email: '',
  position: '',
  role: 'staff',
  status: 'active',
  avatar: ''
})

// 动态表单验证规则
const formRules = computed(() => ({
  username: isEdit.value
    ? [{ min: 3, max: 50, message: '用户名长度在 3 到 50 个字符', trigger: 'blur' }]
    : [
        { required: true, message: '请输入用户名', trigger: 'blur' },
        { min: 3, max: 50, message: '用户名长度在 3 到 50 个字符', trigger: 'blur' }
      ],
  password: isEdit.value
    ? []
    : [
        { required: true, message: '请输入密码', trigger: 'blur' },
        { min: 6, message: '密码长度不能少于 6 个字符', trigger: 'blur' }
      ],
  name: [],
  id_card: (isEdit.value && hasIdCard.value)
    ? []
    : [
        { pattern: /^[1-9]\d{5}(18|19|20)\d{2}(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])\d{3}[\dXx]$/, message: '请输入正确的18位身份证号', trigger: 'blur' }
      ],
  phone: [
    { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号', trigger: 'blur' }
  ],
  email: [
    { type: 'email', message: '请输入正确的邮箱地址', trigger: 'blur' }
  ],
  role: []
}))

const passwordDialogVisible = ref(false)
const passwordLoading = ref(false)
const passwordForm = reactive({
  newPassword: ''
})

const roleMap = {
  admin: '管理员',
  staff: '员工'
}

const statusMap = {
  active: '在职',
  resigned: '离职',
  disabled: '禁用'
}

const avatarColors = [
  'linear-gradient(135deg, #0F766E 0%, #14B8A6 100%)',
  'linear-gradient(135deg, #0369A1 0%, #0EA5E9 100%)',
  'linear-gradient(135deg, #7C3AED 0%, #A78BFA 100%)',
  'linear-gradient(135deg, #DC2626 0%, #F87171 100%)',
  'linear-gradient(135deg, #EA580C 0%, #FB923C 100%)',
  'linear-gradient(135deg, #0D9488 0%, #5EEAD4 100%)'
]

const getAvatarColor = (name) => {
  const index = name ? name.charCodeAt(0) % avatarColors.length : 0
  return avatarColors[index]
}

const getStatusType = (status) => {
  const types = {
    active: 'success',
    resigned: 'info',
    disabled: 'danger'
  }
  return types[status] || 'info'
}

const getStatusText = (status) => {
  const texts = {
    active: '在职',
    resigned: '离职',
    disabled: '禁用'
  }
  return texts[status] || '未知'
}

const formatDate = (date) => {
  return date ? dayjs(date).format('YYYY-MM-DD HH:mm') : '-'
}

const maskIdCard = (idCard) => {
  if (!idCard) return '-'
  // 身份证号脱敏：保留前3位和后4位，中间用*代替
  if (idCard.length >= 8) {
    return idCard.substring(0, 3) + '***********' + idCard.substring(idCard.length - 4)
  }
  return idCard
}

const fetchStatistics = async () => {
  try {
    const res = await getEmployeeStats()
    const data = res.data
    statistics.total = data.total || 0
    statistics.active = data.by_status?.active || 0
    statistics.disabled = data.by_status?.disabled || 0
    statistics.resigned = data.by_status?.resigned || 0
  } catch (error) {
    console.error('获取统计信息失败', error)
  }
}

const fetchEmployeeList = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      per_page: pagination.per_page,
      ...filterForm
    }
    const res = await getEmployeeList(params)
    employeeList.value = res.data.items || []
    pagination.total = res.data.pagination.total
  } catch (error) {
    ElMessage.error(error.message || '获取员工列表失败')
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  pagination.page = 1
  fetchEmployeeList()
}

const handleReset = () => {
  filterForm.keyword = ''
  filterForm.status = ''
  filterForm.role = ''
  handleSearch()
}

const handleSizeChange = (size) => {
  pagination.per_page = size
  fetchEmployeeList()
}

const handlePageChange = (page) => {
  pagination.page = page
  fetchEmployeeList()
}

const handleSelectionChange = (selection) => {
  selectedEmployees.value = selection
}

const resetForm = () => {
  formData.username = ''
  formData.password = ''
  formData.name = ''
  formData.id_card = ''
  formData.phone = ''
  formData.email = ''
  formData.position = ''
  formData.role = 'staff'
  formData.status = 'active'
  formData.avatar = ''
}

const beforePhotoUpload = (file) => {
  const isJPG = file.type === 'image/jpeg' || file.type === 'image/png'
  const isLt2M = file.size / 1024 / 1024 < 2

  if (!isJPG) {
    ElMessage.error('只能上传 JPG 或 PNG 格式的图片!')
  }
  if (!isLt2M) {
    ElMessage.error('图片大小不能超过 2MB!')
  }

  return isJPG && isLt2M
}

const handlePhotoUpload = async (options) => {
  const { file, onSuccess, onError } = options
  
  try {
    const uploadFormData = new FormData()
    uploadFormData.append('files', file)
    uploadFormData.append('file_type', 'image')
    
    const res = await request({
      url: '/upload',
      method: 'post',
      data: uploadFormData
    })
    
    if (res.success) {
      formData.avatar = res.data?.files?.[0]?.file_url || res.data?.uploaded_files?.[0]?.file_url
      ElMessage.success('头像上传成功')
      onSuccess(res)
    } else {
      ElMessage.error(res.message || '头像上传失败')
      onError(res)
    }
  } catch (error) {
    console.error('头像上传失败:', error)
    ElMessage.error('头像上传失败')
    onError(error)
  }
}

const handlePhotoDelete = () => {
  formData.avatar = ''
  ElMessage.success('头像已删除')
}

const handleAdd = () => {
  isEdit.value = false
  dialogTitle.value = '新增员工'
  resetForm()
  dialogVisible.value = true
}

const handleView = (row) => {
  currentEmployee.value = row
  detailVisible.value = true
}

const handleEdit = (row) => {
  isEdit.value = true
  dialogTitle.value = '编辑员工'
  hasIdCard.value = !!(row.id_card && row.id_card.length > 0)
  Object.assign(formData, {
    id: row.id,
    username: row.username,
    name: row.name,
    id_card: row.id_card || '',
    phone: row.phone,
    email: row.email,
    position: row.position,
    role: row.role,
    status: row.status,
    avatar: row.avatar || ''
  })
  dialogVisible.value = true
}

const handleSubmit = async () => {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    
    submitLoading.value = true
    try {
      if (isEdit.value) {
        await updateEmployee(formData.id, formData)
        ElMessage.success('更新成功')
        
        if (userStore.userInfo.id === formData.id) {
          userStore.updateUserInfo({ avatar: formData.avatar })
        }
      } else {
        await createEmployee(formData)
        ElMessage.success('创建成功')
      }
      dialogVisible.value = false
      fetchEmployeeList()
      fetchStatistics()
    } catch (error) {
      ElMessage.error(error.message || '操作失败')
    } finally {
      submitLoading.value = false
    }
  })
}

const handleToggleStatus = async (row) => {
  const newStatus = row.status === 'active' ? 'disabled' : 'active'
  const actionText = newStatus === 'active' ? '启用' : '禁用'
  
  try {
    await ElMessageBox.confirm(`确定要${actionText}该员工吗？`, '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    await updateEmployeeStatus(row.id, newStatus)
    ElMessage.success(`${actionText}成功`)
    fetchEmployeeList()
    fetchStatistics()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.message || `${actionText}失败`)
    }
  }
}

const handleResetPassword = (row) => {
  currentEmployee.value = row
  passwordForm.newPassword = ''
  passwordDialogVisible.value = true
}

const confirmResetPassword = async () => {
  if (!passwordForm.newPassword) {
    ElMessage.warning('请输入新密码')
    return
  }
  
  if (passwordForm.newPassword.length < 6) {
    ElMessage.warning('密码长度不能少于 6 个字符')
    return
  }
  
  passwordLoading.value = true
  try {
    await resetEmployeePassword(currentEmployee.value.id, passwordForm.newPassword)
    ElMessage.success('密码重置成功')
    passwordDialogVisible.value = false
  } catch (error) {
    ElMessage.error(error.message || '密码重置失败')
  } finally {
    passwordLoading.value = false
  }
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm('确定要删除该员工吗？此操作不可恢复！', '警告', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    await deleteEmployee(row.id)
    ElMessage.success('删除成功')
    fetchEmployeeList()
    fetchStatistics()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.message || '删除失败')
    }
  }
}

const handleBatchAction = async (action) => {
  const actionTexts = {
    enable: '启用',
    disable: '禁用',
    delete: '删除'
  }
  
  try {
    await ElMessageBox.confirm(`确定要批量${actionTexts[action]}选中的员工吗？`, '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    const userIds = selectedEmployees.value.map(employee => employee.id)
    await batchActionEmployees({ user_ids: userIds, action })
    ElMessage.success(`批量${actionTexts[action]}成功`)
    selectedEmployees.value = []
    fetchEmployeeList()
    fetchStatistics()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.message || `批量${actionTexts[action]}失败`)
    }
  }
}

onMounted(() => {
  fetchEmployeeList()
  fetchStatistics()
})
</script>

<style lang="scss" scoped>
.list-page {
  padding: 24px;
  background: var(--bg-secondary);
  min-height: calc(100vh - 60px);
}

.page-header {
  margin-bottom: 24px;
  
  .header-content {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
  }
  
  .header-left {
    .page-title {
      font-size: 24px;
      font-weight: 700;
      color: var(--text-primary);
      margin: 0 0 4px 0;
    }
    
    .page-subtitle {
      font-size: 14px;
      color: var(--text-muted);
      margin: 0;
    }
  }
  
  .add-button {
    height: 40px;
    padding: 0 20px;
    border-radius: 10px;
    font-weight: 500;
    background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-primary-dark) 100%);
    border: none;
    box-shadow: 0 4px 12px rgba(15, 118, 110, 0.3);
    transition: all 0.3s ease;
    
    &:hover {
      transform: translateY(-2px);
      box-shadow: 0 6px 16px rgba(15, 118, 110, 0.4);
    }
    
    .btn-icon {
      margin-right: 6px;
    }
  }
}

.statistics-row {
  margin-bottom: 20px;
  
  .stat-card {
    .stat-content {
      display: flex;
      align-items: center;
      gap: 16px;
      
      .stat-icon {
        width: 64px;
        height: 64px;
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: #fff;
        
        &.total {
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }
        
        &.active {
          background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        }
        
        &.disabled {
          background: linear-gradient(135deg, #eb3349 0%, #f45c43 100%);
        }
        
        &.new {
          background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        }
      }
      
      .stat-info {
        .stat-value {
          font-size: 28px;
          font-weight: 600;
          color: #303133;
        }
        
        .stat-label {
          font-size: 14px;
          color: #909399;
          margin-top: 4px;
        }
      }
    }
  }
}

.filter-section {
  background: white;
  border-radius: 16px;
  padding: 20px 24px;
  margin-bottom: 20px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  
  .filter-content {
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
    gap: 20px;
    flex-wrap: wrap;
  }
  
  .filter-items {
    display: flex;
    gap: 20px;
    flex-wrap: wrap;
    flex: 1;
  }
  
  .filter-item {
    display: flex;
    flex-direction: column;
    gap: 8px;
    
    .filter-label {
      font-size: 13px;
      font-weight: 500;
      color: var(--text-regular);
    }
    
    .filter-input,
    .filter-select {
      width: 180px;
    }
  }
  
  .filter-actions {
    display: flex;
    gap: 10px;
    
    .search-button,
    .reset-button {
      height: 36px;
      padding: 0 16px;
      border-radius: 8px;
      font-weight: 500;
      
      .btn-icon {
        margin-right: 4px;
      }
    }
    
    .search-button {
      background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-primary-dark) 100%);
      border: none;
    }
  }
}

.table-section {
  background: white;
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  
  .batch-actions {
    margin-bottom: 16px;
    padding: 10px 16px;
    background-color: #f4f4f5;
    border-radius: 4px;
    display: flex;
    align-items: center;
    gap: 12px;
    
    .selected-info {
      color: #606266;
      font-size: 14px;
    }
  }
  
  .data-table {
    width: 100%;
    
    :deep(.el-table__header th) {
      background: #fafafa !important;
      font-weight: 600;
      color: var(--text-primary);
      font-size: 13px;
    }
    
    :deep(.el-table__row) {
      transition: all 0.2s ease;
      
      &:hover {
        background: #f8fafc !important;
      }
    }
    
    :deep(.el-table__cell) {
      padding: 14px 0;
    }
  }
  
  .user-info {
    display: flex;
    align-items: center;
    gap: 10px;
    
    .user-avatar {
      width: 32px;
      height: 32px;
      border-radius: 8px;
      display: flex;
      align-items: center;
      justify-content: center;
      color: white;
      font-size: 14px;
      font-weight: 600;
      flex-shrink: 0;
    }
    
    .user-name {
      font-weight: 500;
      color: var(--text-primary);
    }
  }
  
  .email-text {
    color: var(--text-regular);
    font-size: 13px;
  }
  
  .role-badge {
    display: inline-flex;
    align-items: center;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 500;
    
    &.admin {
      background: rgba(220, 38, 38, 0.1);
      color: #DC2626;
    }
    
    &.staff {
      background: rgba(15, 118, 110, 0.1);
      color: #0F766E;
    }
  }
  
  .status-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 500;
    
    .status-dot {
      width: 6px;
      height: 6px;
      border-radius: 50%;
    }
    
    &.active {
      background: rgba(16, 185, 129, 0.1);
      color: #10B981;
      
      .status-dot {
        background: #10B981;
      }
    }
    
    &.resigned {
      background: rgba(107, 114, 128, 0.1);
      color: #6B7280;
      
      .status-dot {
        background: #6B7280;
      }
    }
    
    &.disabled {
      background: rgba(239, 68, 68, 0.1);
      color: #EF4444;
      
      .status-dot {
        background: #EF4444;
      }
    }
  }
  
  .date-text {
    color: var(--text-muted);
    font-size: 13px;
  }
  
  .action-buttons {
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 8px;
    flex-wrap: nowrap;
    white-space: nowrap;
    
    .el-button {
      padding: 4px 6px;
      font-size: 12px;
      flex-shrink: 0;
      
      .el-icon {
        margin-right: 2px;
      }
    }
  }
}

.detail-dialog {
  :deep(.el-dialog) {
    border-radius: 16px;
    overflow: hidden;
  }
  
  :deep(.el-dialog__header) {
    padding: 20px 24px;
    border-bottom: 1px solid var(--border-secondary);
    margin: 0;
    
    .el-dialog__title {
      font-size: 18px;
      font-weight: 600;
      color: var(--text-primary);
    }
  }
  
  :deep(.el-dialog__body) {
    padding: 24px;
  }
  
  :deep(.el-dialog__footer) {
    padding: 16px 24px;
    border-top: 1px solid var(--border-secondary);
  }
  
  .detail-header {
    display: flex;
    align-items: center;
    gap: 20px;
    padding: 20px;
    background: linear-gradient(135deg, rgba(15, 118, 110, 0.05) 0%, rgba(20, 184, 166, 0.05) 100%);
    border-radius: 12px;
    margin-bottom: 20px;
    
    .detail-avatar {
      flex-shrink: 0;
      
      .avatar-image {
        width: 80px;
        height: 80px;
        border-radius: 12px;
        object-fit: cover;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
      }
      
      .avatar-placeholder {
        width: 80px;
        height: 80px;
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-size: 32px;
        font-weight: 600;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
      }
    }
    
    .detail-basic-info {
      flex: 1;
      
      .detail-name {
        font-size: 20px;
        font-weight: 600;
        color: var(--text-primary);
        margin: 0 0 4px 0;
      }
      
      .detail-position {
        font-size: 14px;
        color: var(--text-muted);
        margin: 0 0 8px 0;
      }
      
      .role-badge {
        display: inline-flex;
        align-items: center;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 500;
        
        &.admin {
          background: rgba(220, 38, 38, 0.1);
          color: #DC2626;
        }
        
        &.staff {
          background: rgba(15, 118, 110, 0.1);
          color: #0F766E;
        }
      }
    }
  }
  
  .detail-descriptions {
    :deep(.el-descriptions__label) {
      font-weight: 500;
      width: 120px;
    }
  }
  
  .dialog-footer {
    display: flex;
    justify-content: flex-end;
    gap: 12px;
    
    .cancel-btn,
    .el-button--primary {
      min-width: 80px;
      border-radius: 8px;
      font-weight: 500;
    }
    
    .el-button--primary {
      background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-primary-dark) 100%);
      border: none;
    }
  }
}

.pagination-container {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid var(--border-secondary);
  
  :deep(.el-pagination) {
    .el-pagination__total,
    .el-pagination__sizes,
    .el-pagination__jump {
      font-size: 13px;
    }
    
    .btn-prev,
    .btn-next,
    .el-pager li {
      border-radius: 6px;
      min-width: 32px;
      height: 32px;
      line-height: 32px;
    }
    
    .el-pager li.is-active {
      background: var(--color-primary);
      color: white;
    }
  }
}

.form-dialog {
  :deep(.el-dialog) {
    border-radius: 16px;
    overflow: hidden;
  }
  
  :deep(.el-dialog__header) {
    padding: 20px 24px;
    border-bottom: 1px solid var(--border-secondary);
    margin: 0;
    
    .el-dialog__title {
      font-size: 18px;
      font-weight: 600;
      color: var(--text-primary);
    }
  }
  
  :deep(.el-dialog__body) {
    padding: 24px;
  }
  
  :deep(.el-dialog__footer) {
    padding: 16px 24px;
    border-top: 1px solid var(--border-secondary);
  }
  
  .form-content {
  :deep(.el-form-item) {
    margin-bottom: 20px;
    
    .el-form-item__label {
      font-weight: 500;
      color: var(--text-regular);
    }
  }
  
  .upload-container {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }
  
  .form-tip {
    font-size: 12px;
    color: var(--text-secondary, #909399);
    margin-top: 4px;
  }
  
  .avatar-uploader {
    border: 1px dashed var(--border-secondary);
    border-radius: 8px;
    padding: 20px;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    transition: all 0.3s ease;
    
    &:hover {
      border-color: var(--color-primary);
      background-color: rgba(15, 118, 110, 0.05);
    }
  }
  
  .avatar {
    width: 120px;
    height: 120px;
    border-radius: 8px;
    object-fit: cover;
  }
  
  .avatar-uploader-icon {
    font-size: 32px;
    color: var(--text-muted);
  }
  
  .delete-photo-btn {
    width: 120px;
    margin-top: 4px;
    color: var(--color-danger);
    
    &:hover {
      color: var(--color-danger-dark);
    }
  }
}
  
  .dialog-footer {
    display: flex;
    justify-content: flex-end;
    gap: 12px;
    
    .cancel-btn,
    .submit-btn {
      min-width: 80px;
      border-radius: 8px;
      font-weight: 500;
    }
    
    .submit-btn {
      background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-primary-dark) 100%);
      border: none;
    }
  }
}

@media screen and (max-width: 768px) {
  .list-page {
    padding: 16px;
  }
  
  .page-header {
    .header-content {
      flex-direction: column;
      gap: 16px;
    }
    
    .header-right {
      width: 100%;
      
      .add-button {
        width: 100%;
      }
    }
  }
  
  .statistics-row {
    .stat-card {
      margin-bottom: 16px;
    }
  }
  
  .filter-section {
    .filter-content {
      flex-direction: column;
      align-items: stretch;
    }
    
    .filter-items {
      flex-direction: column;
      
      .filter-item {
        .filter-input,
        .filter-select {
          width: 100%;
        }
      }
    }
    
    .filter-actions {
      width: 100%;
      
      .search-button,
      .reset-button {
        flex: 1;
      }
    }
  }
  
  .table-section {
    padding: 16px;
    overflow-x: auto;
    
    .batch-actions {
      flex-direction: column;
      align-items: stretch;
      gap: 8px;
      
      .el-button {
        width: 100%;
      }
    }
  }
}
</style>
