<template>
  <div class="tenant-list-page">
    <el-card class="page-header">
      <div class="header-content">
        <h2>租客管理</h2>
        <div class="header-buttons">
          <el-button type="primary" @click="handleAdd">
            <el-icon><Plus /></el-icon>
            新增租客
          </el-button>
          <el-button type="primary" @click="handleBatchNotify" :disabled="selectedTenants.length === 0">
            <el-icon><Bell /></el-icon>
            批量发送通知
          </el-button>
        </div>
      </div>
    </el-card>

    <el-row :gutter="20" class="statistics-row">
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon total">
              <el-icon :size="32"><User /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ statistics.total || 0 }}</div>
              <div class="stat-label">总租客数</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon pending">
              <el-icon :size="32"><Clock /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ statistics.pending || 0 }}</div>
              <div class="stat-label">待租租客</div>
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
              <div class="stat-label">在租租客</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon expired">
              <el-icon :size="32"><CircleClose /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ statistics.expired || 0 }}</div>
              <div class="stat-label">已退租</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon blacklisted">
              <el-icon :size="32"><Warning /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ statistics.blacklisted || 0 }}</div>
              <div class="stat-label">黑名单</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-card class="filter-card">
      <el-form :inline="true" :model="searchForm" class="filter-form">
        <el-form-item label="关键词">
          <el-input
            v-model="searchForm.keyword"
            placeholder="姓名/手机号/身份证号"
            clearable
            @clear="handleSearch"
            @keyup.enter="handleSearch"
          />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="searchForm.status" placeholder="全部状态" clearable>
            <el-option label="待租" value="pending" />
            <el-option label="在租" value="active" />
            <el-option label="已退租" value="expired" />
            <el-option label="黑名单" value="blacklisted" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">
            <el-icon><Search /></el-icon>
            搜索
          </el-button>
          <el-button @click="handleReset">
            <el-icon><Refresh /></el-icon>
            重置
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card class="table-card">
      <el-table
        v-loading="loading"
        :data="tenantList"
        stripe
        style="width: 100%"
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="55" />
        <el-table-column prop="id" label="ID" min-width="60" />
        <el-table-column prop="name" label="姓名" min-width="80" />
        <el-table-column prop="phone" label="手机号" min-width="120" />
        <el-table-column prop="status" label="状态" min-width="70">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" size="small">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="credit_score" label="信用分" min-width="100">
          <template #default="{ row }">
            <div v-if="row.credit_score !== undefined && row.credit_score !== null" class="credit-score-cell">
              <span class="score-value" :style="{ color: getCreditColor(row.credit_score) }">
                {{ row.credit_score }}
              </span>
              <el-tag :type="getCreditTagType(row.credit_score)" size="small" style="margin-left: 8px;">
                {{ getCreditLevel(row.credit_score) }}
              </el-tag>
            </div>
            <span v-else class="no-score">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="occupation" label="职业" min-width="80" />
        <el-table-column label="操作" min-width="280" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="handleView(row)" link>
              详情
            </el-button>
            <el-button type="primary" size="small" @click="handleEdit(row)" link>
              编辑
            </el-button>
            <el-dropdown @command="(cmd) => handleChangeStatus(cmd, row)">
              <el-button type="warning" size="small" link>
                状态<el-icon class="el-icon--right"><ArrowDown /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="pending" :disabled="row.status === 'pending'">
                    设为待租
                  </el-dropdown-item>
                  <el-dropdown-item command="active" :disabled="row.status === 'active'">
                    设为在租
                  </el-dropdown-item>
                  <el-dropdown-item command="expired" :disabled="row.status === 'expired'">
                    设为已退租
                  </el-dropdown-item>
                  <el-dropdown-item command="blacklisted" :disabled="row.status === 'blacklisted'" divided>
                    加入黑名单
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
            <el-button type="danger" size="small" @click="handleDelete(row)" link>
              删除
            </el-button>
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
    </el-card>

    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="700px"
      :close-on-click-modal="false"
      destroy-on-close
    >
      <el-form
        ref="tenantFormRef"
        :model="tenantForm"
        :rules="formRules"
        label-width="120px"
      >
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="姓名" prop="name">
              <el-input v-model="tenantForm.name" placeholder="请输入姓名" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="身份证号" prop="id_card">
              <el-input v-model="tenantForm.id_card" placeholder="请输入身份证号" maxlength="18" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="24">
            <el-form-item label="个人照片" prop="photo">
              <el-upload
                class="avatar-uploader"
                action="#"
                :http-request="handlePhotoUpload"
                :show-file-list="false"
                :before-upload="beforePhotoUpload"
                accept="image/*"
              >
                <img v-if="tenantForm.photo" :src="tenantForm.photo" class="avatar" />
                <el-icon v-else class="avatar-uploader-icon"><Plus /></el-icon>
              </el-upload>
              <el-button 
                v-if="tenantForm.photo" 
                type="danger" 
                size="small" 
                @click="handlePhotoDelete"
                style="margin-top: 10px"
              >
                删除照片
              </el-button>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="手机号" prop="phone">
              <el-input v-model="tenantForm.phone" placeholder="请输入手机号" maxlength="11" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="邮箱" prop="email">
              <el-input v-model="tenantForm.email" placeholder="请输入邮箱" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-divider content-position="left">紧急联系人信息</el-divider>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="紧急联系人" prop="emergency_contact">
              <el-input v-model="tenantForm.emergency_contact" placeholder="请输入紧急联系人" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="紧急联系电话" prop="emergency_phone">
              <el-input v-model="tenantForm.emergency_phone" placeholder="请输入紧急联系电话" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="与联系人关系" prop="emergency_relation">
              <el-input v-model="tenantForm.emergency_relation" placeholder="如：配偶、父母等" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-divider content-position="left">其他信息</el-divider>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="职业" prop="occupation">
              <el-input v-model="tenantForm.occupation" placeholder="请输入职业" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="工作单位" prop="company">
              <el-input v-model="tenantForm.company" placeholder="请输入工作单位" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="备注" prop="remark">
          <el-input
            v-model="tenantForm.remark"
            type="textarea"
            placeholder="请输入备注信息"
            :rows="3"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="handleSubmit">
          确定
        </el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="detailVisible"
      title="租客详情"
      width="800px"
      destroy-on-close
    >
      <div class="tenant-header">
        <div class="tenant-photo">
          <el-avatar 
            v-if="currentTenant.photo" 
            :src="currentTenant.photo" 
            :size="100"
            fit="cover"
          />
          <el-avatar v-else :size="100" class="avatar-placeholder">
            {{ currentTenant.name?.charAt(0) || '?' }}
          </el-avatar>
        </div>
        <div class="tenant-basic">
          <h3 class="tenant-name">{{ currentTenant.name }}</h3>
          <el-tag :type="getStatusType(currentTenant.status)" style="margin-top: 8px;">
            {{ getStatusText(currentTenant.status) }}
          </el-tag>
        </div>
        <div class="tenant-credit" v-if="currentTenant.credit_score !== undefined && currentTenant.credit_score !== null">
          <div class="credit-score-display">
            <div class="credit-label">信用分</div>
            <div class="credit-value" :style="{ color: getCreditColor(currentTenant.credit_score) }">
              {{ currentTenant.credit_score }}
            </div>
            <el-tag :type="getCreditTagType(currentTenant.credit_score)" size="small">
              {{ getCreditLevel(currentTenant.credit_score) }}
            </el-tag>
          </div>
        </div>
      </div>
      
      <el-descriptions :column="2" border>
        <el-descriptions-item label="身份证号">
          {{ maskIdCard(currentTenant.id_card) }}
        </el-descriptions-item>
        <el-descriptions-item label="手机号">
          {{ currentTenant.phone || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="邮箱">
          {{ currentTenant.email || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="职业">
          {{ currentTenant.occupation || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="工作单位">
          {{ currentTenant.company || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="合同数">
          <el-link type="primary" @click="handleViewContracts(currentTenant)">
            {{ currentTenant.contracts_count || 0 }} 份合同
          </el-link>
        </el-descriptions-item>
        <el-descriptions-item label="创建时间">
          {{ formatDate(currentTenant.created_at) }}
        </el-descriptions-item>
      </el-descriptions>
      
      <el-descriptions title="紧急联系人信息" :column="2" border style="margin-top: 20px;">
        <el-descriptions-item label="紧急联系人">
          {{ currentTenant.emergency_contact || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="紧急联系电话">
          {{ currentTenant.emergency_phone || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="与联系人关系">
          {{ currentTenant.emergency_relation || '-' }}
        </el-descriptions-item>
      </el-descriptions>
      
      <el-descriptions style="margin-top: 20px;" :column="1" border>
        <el-descriptions-item label="备注">
          {{ currentTenant.remark || '-' }}
        </el-descriptions-item>
      </el-descriptions>

      <div v-if="creditRecords.length > 0" class="credit-records-section">
        <el-divider content-position="left">信用记录</el-divider>
        <el-timeline>
          <el-timeline-item
            v-for="record in creditRecords"
            :key="record.id"
            :timestamp="formatDate(record.created_at)"
            placement="top"
            :type="record.score_change > 0 ? 'success' : 'danger'"
          >
            <el-card class="credit-record-card">
              <div class="record-header">
                <span class="record-type">{{ getCreditEventType(record.event_type) }}</span>
                <span class="score-change" :style="{ color: record.score_change > 0 ? '#67C23A' : '#F56C6C' }">
                  {{ record.score_change > 0 ? '+' : '' }}{{ record.score_change }}分
                </span>
              </div>
              <div class="record-description">{{ record.description || '-' }}</div>
            </el-card>
          </el-timeline-item>
        </el-timeline>
      </div>
      <template #footer>
        <div style="display: flex; justify-content: flex-end; gap: 12px;">
          <el-button @click="detailVisible = false">关闭</el-button>
          <el-button type="primary" @click="handleEditFromDetail">编辑</el-button>
        </div>
      </template>
    </el-dialog>

    <el-dialog
      v-model="contractsVisible"
      title="租客合同列表"
      width="800px"
      destroy-on-close
    >
      <el-table :data="tenantContracts" v-loading="contractsLoading">
        <el-table-column prop="contract_no" label="合同编号" width="150" />
        <el-table-column prop="house_name" label="房源" width="150" />
        <el-table-column prop="start_date" label="开始日期" width="120" />
        <el-table-column prop="end_date" label="结束日期" width="120" />
        <el-table-column prop="monthly_rent" label="月租金" width="100">
          <template #default="{ row }">
            ¥{{ row.monthly_rent }}
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getContractStatusType(row.status)">
              {{ getContractStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>

    <el-dialog
      v-model="notifyDialogVisible"
      title="批量发送通知"
      width="600px"
      :close-on-click-modal="false"
      destroy-on-close
    >
      <el-alert
        title="通知信息"
        type="info"
        :closable="false"
        show-icon
        style="margin-bottom: 20px"
      >
        将向选中的 {{ selectedTenants.length }} 位租客发送通知
      </el-alert>
      
      <el-form
        ref="notifyFormRef"
        :model="notifyForm"
        :rules="notifyFormRules"
        label-width="100px"
        label-position="right"
      >
        <el-form-item label="通知标题" prop="title">
          <el-input
            v-model="notifyForm.title"
            placeholder="请输入通知标题"
            maxlength="100"
            show-word-limit
          />
        </el-form-item>
        
        <el-form-item label="通知类型" prop="type">
          <el-select v-model="notifyForm.type" placeholder="请选择通知类型" style="width: 100%">
            <el-option label="系统通知" value="system" />
            <el-option label="缴费提醒" value="payment" />
            <el-option label="合同提醒" value="contract" />
            <el-option label="其他" value="other" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="通知内容" prop="content">
          <el-input
            v-model="notifyForm.content"
            type="textarea"
            :rows="5"
            placeholder="请输入通知内容"
            maxlength="500"
            show-word-limit
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="notifyDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleNotifySubmit" :loading="notifySubmitLoading">
            发送通知
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, Refresh, User, CircleCheck, CircleClose, Warning, ArrowDown, Clock, Bell } from '@element-plus/icons-vue'
import dayjs from 'dayjs'
import { getTenantList, getTenantDetail, createTenant, updateTenant, deleteTenant, getTenantStats, getTenantContracts } from '@/api/tenant'
import { batchSend } from '@/api/notification'
import { uploadImage } from '@/api/upload'

const loading = ref(false)
const tenantList = ref([])
const selectedTenants = ref([])
const dialogVisible = ref(false)
const dialogTitle = ref('新增租客')
const detailVisible = ref(false)
const submitLoading = ref(false)
const tenantFormRef = ref(null)
const currentTenant = ref({})
const contractsVisible = ref(false)
const contractsLoading = ref(false)
const tenantContracts = ref([])
const notifyDialogVisible = ref(false)
const notifySubmitLoading = ref(false)
const notifyFormRef = ref(null)
const creditRecords = ref([])

const statistics = reactive({
  total: 0,
  pending: 0,
  active: 0,
  expired: 0,
  blacklisted: 0
})

const searchForm = reactive({
  keyword: '',
  status: ''
})

const pagination = reactive({
  page: 1,
  per_page: 20,
  total: 0
})

const tenantForm = reactive({
  name: '',
  id_card: '',
  phone: '',
  email: '',
  emergency_contact: '',
  emergency_phone: '',
  emergency_relation: '',
  occupation: '',
  company: '',
  remark: '',
  photo: ''
})

const notifyForm = reactive({
  title: '',
  type: 'system',
  content: ''
})

const formRules = {
  name: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
  id_card: [
    { pattern: /(^\d{15}$)|(^\d{18}$)|(^\d{17}(\d|X|x)$)/, message: '请输入正确的身份证号', trigger: 'blur' }
  ],
  phone: [
    { required: true, message: '请输入手机号', trigger: 'blur' },
    { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号', trigger: 'blur' }
  ],
  email: [
    { type: 'email', message: '请输入正确的邮箱地址', trigger: 'blur' }
  ],
  emergency_contact: [],
  emergency_phone: [
    { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号', trigger: 'blur' }
  ],
  emergency_relation: []
}

const notifyFormRules = {
  title: [{ required: true, message: '请输入通知标题', trigger: 'blur' }],
  type: [{ required: true, message: '请选择通知类型', trigger: 'change' }],
  content: [{ required: true, message: '请输入通知内容', trigger: 'blur' }]
}

const getStatusType = (status) => {
  const types = {
    pending: 'warning',
    active: 'success',
    expired: 'info',
    blacklisted: 'danger'
  }
  return types[status] || 'info'
}

const getStatusText = (status) => {
  const texts = {
    pending: '待租',
    active: '在租',
    expired: '已退租',
    blacklisted: '黑名单'
  }
  return texts[status] || status
}

const getContractStatusType = (status) => {
  const types = {
    active: 'success',
    expired: 'info',
    terminated: 'danger'
  }
  return types[status] || 'info'
}

const getContractStatusText = (status) => {
  const texts = {
    active: '生效中',
    expired: '已到期',
    terminated: '已终止'
  }
  return texts[status] || status
}

const getCreditLevel = (score) => {
  if (score >= 90) return '优秀'
  if (score >= 80) return '良好'
  if (score >= 60) return '中等'
  if (score >= 40) return '一般'
  return '较差'
}

const getCreditColor = (score) => {
  if (score >= 90) return '#67C23A'
  if (score >= 80) return '#409EFF'
  if (score >= 60) return '#E6A23C'
  if (score >= 40) return '#F56C6C'
  return '#F56C6C'
}

const getCreditTagType = (score) => {
  if (score >= 90) return 'success'
  if (score >= 80) return ''
  if (score >= 60) return 'warning'
  return 'danger'
}

const maskIdCard = (idCard) => {
  if (!idCard) return '-'
  
  // 转换为字符串并去除空格
  const idCardStr = String(idCard).trim()
  
  // 验证身份证号长度(15位或18位)
  if (idCardStr.length !== 15 && idCardStr.length !== 18) {
    return idCardStr // 长度不符合要求,返回原值
  }
  
  // 验证是否只包含数字和X(最后一位可以是X)
  const validPattern = idCardStr.length === 15 
    ? /^\d{15}$/ 
    : /^\d{17}[\dXx]$/
  
  if (!validPattern.test(idCardStr)) {
    return idCardStr // 格式不符合要求,返回原值
  }
  
  // 脱敏处理:保留前6位和后4位,中间用*代替
  return idCardStr.replace(/^(.{6}).*(.{4})$/, '$1********$2')
}

const formatDate = (date) => {
  return date ? dayjs(date).format('YYYY-MM-DD HH:mm') : '-'
}

const fetchStatistics = async () => {
  try {
    const res = await getTenantStats()
    const data = res.data
    statistics.total = data.total || 0
    statistics.pending = data.by_status?.pending || 0
    statistics.active = data.by_status?.active || 0
    statistics.expired = data.by_status?.expired || 0
    statistics.blacklisted = data.by_status?.blacklisted || 0
  } catch (error) {
    console.error('获取统计信息失败', error)
  }
}

const loadTenantList = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      per_page: pagination.per_page,
      ...searchForm
    }
    const res = await getTenantList(params)
    tenantList.value = res.data?.items || []
    pagination.total = res.data?.pagination?.total || 0
  } catch (error) {
    ElMessage.error('加载租客列表失败')
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  pagination.page = 1
  loadTenantList()
}

const handleReset = () => {
  searchForm.keyword = ''
  searchForm.status = ''
  handleSearch()
}

const handleSizeChange = (size) => {
  pagination.per_page = size
  loadTenantList()
}

const handlePageChange = (page) => {
  pagination.page = page
  loadTenantList()
}

const resetForm = () => {
  Object.assign(tenantForm, {
    name: '',
    id_card: '',
    phone: '',
    email: '',
    emergency_contact: '',
    emergency_phone: '',
    emergency_relation: '',
    occupation: '',
    company: '',
    remark: '',
    photo: ''
  })
}

const handleAdd = () => {
  dialogTitle.value = '新增租客'
  resetForm()
  currentTenant.value = {}
  dialogVisible.value = true
}

const handleView = async (row) => {
  try {
    const res = await getTenantDetail(row.id)
    currentTenant.value = res.data || row
    detailVisible.value = true
    loadCreditRecords(row.id)
  } catch (error) {
    currentTenant.value = { ...row }
    detailVisible.value = true
  }
}

const loadCreditRecords = async (tenantId) => {
  try {
    const res = await getTenantCreditRecords(tenantId, { limit: 10 })
    creditRecords.value = res.data?.items || []
  } catch (error) {
    console.error('获取信用记录失败', error)
    creditRecords.value = []
  }
}

const getCreditEventType = (eventType) => {
  const types = {
    payment_on_time: '按时付款',
    payment_late: '逾期付款',
    contract_complete: '合同完成',
    contract_terminated: '合同终止',
    damage_property: '损坏财产',
    good_behavior: '良好行为',
    bad_behavior: '不良行为',
    manual_adjust: '人工调整'
  }
  return types[eventType] || eventType
}

const handleEdit = (row) => {
  dialogTitle.value = '编辑租客'
  currentTenant.value = { ...row }
  Object.assign(tenantForm, {
    name: row.name || '',
    id_card: row.id_card || '',
    phone: row.phone || '',
    email: row.email || '',
    emergency_contact: row.emergency_contact || '',
    emergency_phone: row.emergency_phone || '',
    emergency_relation: row.emergency_relation || '',
    occupation: row.occupation || '',
    company: row.company || '',
    remark: row.remark || '',
    photo: row.photo || ''
  })
  dialogVisible.value = true
}

const handleEditFromDetail = () => {
  detailVisible.value = false
  handleEdit(currentTenant.value)
}

const handleSubmit = async () => {
  if (!tenantFormRef.value) return
  
  await tenantFormRef.value.validate(async (valid) => {
    if (!valid) return
    
    submitLoading.value = true
    try {
      const data = { ...tenantForm }
      if (currentTenant.value?.id) {
        await updateTenant(currentTenant.value.id, data)
        ElMessage.success('编辑成功')
      } else {
        await createTenant(data)
        ElMessage.success('创建成功')
      }
      dialogVisible.value = false
      loadTenantList()
      fetchStatistics()
    } catch (error) {
      ElMessage.error(error.message || '操作失败')
    } finally {
      submitLoading.value = false
    }
  })
}

const handleChangeStatus = async (status, row) => {
  const statusTexts = {
    pending: '待租',
    active: '在租',
    expired: '已退租',
    blacklisted: '黑名单'
  }
  
  try {
    await ElMessageBox.confirm(`确定要将"${row.name}"的状态改为${statusTexts[status]}吗？`, '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    await updateTenant(row.id, { status })
    ElMessage.success('状态修改成功')
    loadTenantList()
    fetchStatistics()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('修改状态失败')
    }
  }
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm('确定要删除该租客吗？删除后不可恢复！', '警告', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    await deleteTenant(row.id)
    ElMessage.success('删除成功')
    loadTenantList()
    fetchStatistics()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const handleViewContracts = async (row) => {
  contractsVisible.value = true
  contractsLoading.value = true
  try {
    const res = await getTenantContracts(row.id)
    tenantContracts.value = res.data || []
  } catch (error) {
    ElMessage.error('获取合同列表失败')
    tenantContracts.value = []
  } finally {
    contractsLoading.value = false
  }
}

// 照片上传前验证
const beforePhotoUpload = (file) => {
  const isJPG = file.type === 'image/jpeg' || file.type === 'image/png' || file.type === 'image/webp'
  const isLt2M = file.size / 1024 / 1024 < 2

  if (!isJPG) {
    ElMessage.error('只能上传 JPG、PNG 或 WebP 格式的图片!')
    return false
  }
  if (!isLt2M) {
    ElMessage.error('图片大小不能超过 2MB!')
    return false
  }
  return true
}

// 处理照片上传
const handlePhotoUpload = async (options) => {
  const { file, onSuccess, onError } = options
  try {
    const response = await uploadImage(file)
    tenantForm.photo = response.data.files?.[0]?.file_url
    ElMessage.success('照片上传成功')
    onSuccess(response)
  } catch (error) {
    console.error('照片上传失败:', error)
    ElMessage.error('照片上传失败，请重试')
    onError(error)
  }
}

// 处理照片删除
const handlePhotoDelete = () => {
  tenantForm.photo = ''
  ElMessage.success('照片已删除')
}

// 选择变化处理
const handleSelectionChange = (selection) => {
  selectedTenants.value = selection
}

// 批量发送通知
const handleBatchNotify = () => {
  if (selectedTenants.value.length === 0) {
    ElMessage.warning('请先选择要发送通知的租客')
    return
  }
  
  notifyForm.title = ''
  notifyForm.type = 'system'
  notifyForm.content = ''
  notifyDialogVisible.value = true
}

// 提交批量通知
const handleNotifySubmit = async () => {
  if (!notifyFormRef.value) return
  
  try {
    await notifyFormRef.value.validate()
  } catch (error) {
    return
  }
  
  notifySubmitLoading.value = true
  try {
    const tenantIds = selectedTenants.value.map(item => item.id)
    const data = {
      tenant_ids: tenantIds,
      title: notifyForm.title,
      type: notifyForm.type,
      content: notifyForm.content
    }
    
    await batchSend(data)
    ElMessage.success(`成功向 ${tenantIds.length} 位租客发送通知`)
    notifyDialogVisible.value = false
    selectedTenants.value = []
  } catch (error) {
    console.error('发送通知失败:', error)
    ElMessage.error('发送通知失败：' + (error.message || '请稍后重试'))
  } finally {
    notifySubmitLoading.value = false
  }
}

onMounted(() => {
  loadTenantList()
  fetchStatistics()
})
</script>

<style lang="scss" scoped>
.tenant-list-page {
  .page-header {
    margin-bottom: 20px;
    
    .header-content {
      display: flex;
      justify-content: space-between;
      align-items: center;
      
      h2 {
        margin: 0;
        font-size: 20px;
        font-weight: 600;
      }
      
      .header-buttons {
        display: flex;
        gap: 10px;
      }
    }
  }
  
  .tenant-header {
    display: flex;
    align-items: center;
    gap: 20px;
    margin-bottom: 20px;
    padding: 20px;
    background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
    border-radius: 8px;
    
    .tenant-photo {
      .avatar-placeholder {
        background-color: rgba(255, 255, 255, 0.2);
        color: #fff;
        font-size: 36px;
        font-weight: bold;
      }
    }
    
    .tenant-basic {
      flex: 1;
      
      .tenant-name {
        margin: 0;
        font-size: 24px;
        font-weight: bold;
        color: #fff;
      }
    }

    .tenant-credit {
      .credit-score-display {
        background: rgba(255, 255, 255, 0.2);
        padding: 16px 24px;
        border-radius: 8px;
        text-align: center;
        
        .credit-label {
          font-size: 14px;
          color: rgba(255, 255, 255, 0.9);
          margin-bottom: 8px;
        }
        
        .credit-value {
          font-size: 36px;
          font-weight: bold;
          color: #fff;
          margin-bottom: 8px;
        }
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
          
          &.pending {
            background: linear-gradient(135deg, #f6d365 0%, #fda085 100%);
          }
          
          &.active {
            background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
          }
          
          &.expired {
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
          }
          
          &.blacklisted {
            background: linear-gradient(135deg, #eb3349 0%, #f45c43 100%);
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
  
  .filter-card {
    margin-bottom: 20px;
    
    .filter-form {
      display: flex;
      flex-wrap: wrap;
      
      .el-form-item {
        margin-bottom: 0;
        margin-right: 20px;
      }
    }
  }
  
  .table-card {
    .pagination-container {
      margin-top: 20px;
      display: flex;
      justify-content: flex-end;
    }
  }

  .avatar-uploader {
    border: 1px dashed #d9d9d9;
    border-radius: 6px;
    cursor: pointer;
    position: relative;
    overflow: hidden;
    transition: all 0.3s;
    
    &:hover {
      border-color: #409eff;
    }

    .avatar {
      width: 120px;
      height: 120px;
      display: block;
      object-fit: cover;
    }

    .avatar-uploader-icon {
      font-size: 28px;
      color: #909399;
      width: 120px;
      height: 120px;
      display: flex;
      align-items: center;
      justify-content: center;
      background-color: #f5f7fa;
    }
  }

  .credit-score-cell {
    display: flex;
    align-items: center;
    
    .score-value {
      font-size: 16px;
      font-weight: 600;
    }
  }

  .credit-records-section {
    margin-top: 20px;
    
    .credit-record-card {
      .record-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;
        
        .record-type {
          font-weight: 600;
          color: #303133;
        }
        
        .score-change {
          font-size: 16px;
          font-weight: 600;
        }
      }
      
      .record-description {
        color: #606266;
        font-size: 14px;
      }
    }
  }
}
</style>
