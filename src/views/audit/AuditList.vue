<template>
  <div class="list-page">
    <div class="page-header">
      <div class="header-content">
        <div class="header-left">
          <h1 class="page-title">审计日志</h1>
          <p class="page-subtitle">查看系统操作记录和敏感数据访问日志</p>
        </div>
        <div class="header-right">
          <div class="toggle-wrapper">
            <span class="toggle-label">审计日志开关</span>
            <el-switch
              v-model="auditEnabled"
              :loading="toggleLoading"
              @change="handleToggleChange"
              active-color="#0F766E"
              inactive-color="#D1D5DB"
            />
          </div>
          <el-button type="primary" @click="handleExport" class="export-button" :loading="exportLoading" :disabled="!auditEnabled">
            <el-icon class="btn-icon"><Download /></el-icon>
            导出日志
          </el-button>
        </div>
      </div>
    </div>

    <!-- 禁用提示 -->
    <div v-if="!auditEnabled" class="disabled-notice">
      <el-card class="notice-card">
        <div class="notice-content">
          <el-icon class="notice-icon" :size="48"><Warning /></el-icon>
          <h3 class="notice-title">审计日志功能已禁用</h3>
          <p class="notice-text">请开启开关以查看和记录审计日志</p>
        </div>
      </el-card>
    </div>

    <!-- 审计日志内容 -->
    <template v-else>

    <el-row :gutter="20" class="statistics-row">
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon total">
              <el-icon :size="32"><Document /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ statistics.total_operations || 0 }}</div>
              <div class="stat-label">总操作数</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon success">
              <el-icon :size="32"><CircleCheck /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ statistics.success_count || 0 }}</div>
              <div class="stat-label">成功操作</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon failed">
              <el-icon :size="32"><CircleClose /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ statistics.failed_count || 0 }}</div>
              <div class="stat-label">失败操作</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon rate">
              <el-icon :size="32"><TrendCharts /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ statistics.success_rate ? statistics.success_rate.toFixed(1) : 0 }}%</div>
              <div class="stat-label">成功率</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <div class="filter-section">
      <div class="filter-content">
        <div class="filter-items">
          <div class="filter-item">
            <label class="filter-label">操作用户</label>
            <el-input
              v-model="filterForm.username"
              placeholder="请输入用户名"
              clearable
              @clear="handleSearch"
              @keyup.enter="handleSearch"
              class="filter-input"
            />
          </div>
          <div class="filter-item">
            <label class="filter-label">操作类型</label>
            <el-select v-model="filterForm.operation_type" placeholder="全部类型" clearable class="filter-select">
              <el-option
                v-for="(label, value) in operationTypes"
                :key="value"
                :label="label"
                :value="value"
              />
            </el-select>
          </div>
          <div class="filter-item">
            <label class="filter-label">操作模块</label>
            <el-select v-model="filterForm.model_name" placeholder="全部模块" clearable class="filter-select">
              <el-option label="房东" value="Landlord" />
              <el-option label="租客" value="Tenant" />
              <el-option label="用户" value="User" />
            </el-select>
          </div>
          <div class="filter-item">
            <label class="filter-label">时间范围</label>
            <el-date-picker
              v-model="dateRange"
              type="daterange"
              range-separator="至"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
              :shortcuts="dateShortcuts"
              value-format="YYYY-MM-DD"
              class="filter-daterange"
            />
          </div>
          <div class="filter-item">
            <label class="filter-label">操作状态</label>
            <el-select v-model="filterForm.success" placeholder="全部状态" clearable class="filter-select">
              <el-option label="成功" :value="true" />
              <el-option label="失败" :value="false" />
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
        <el-table
          v-loading="loading"
          :data="auditList"
          class="data-table"
          :header-cell-style="{ background: '#fafafa', fontWeight: '600' }"
          @row-click="handleRowClick"
        >
          <el-table-column prop="id" label="日志ID" min-width="80" align="center" />
          <el-table-column prop="username" label="操作用户" min-width="100">
            <template #default="{ row }">
              <div class="user-info">
                <div class="user-avatar" :style="{ background: getAvatarColor(row.username) }">
                  {{ row.username?.charAt(0)?.toUpperCase() || 'U' }}
                </div>
                <div class="user-details">
                  <div class="user-name">{{ row.username || '-' }}</div>
                  <div class="user-role">{{ row.user_role === 'admin' ? '管理员' : '员工' }}</div>
                </div>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="operation_type" label="操作类型" min-width="90" align="center">
            <template #default="{ row }">
              <span class="operation-badge" :class="row.operation_type">
                {{ operationTypes[row.operation_type] || row.operation_type }}
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="model_name" label="操作模块" min-width="90" align="center">
            <template #default="{ row }">
              <span class="module-badge">{{ getModelName(row.model_name) }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="field_display_name" label="操作字段" min-width="100">
            <template #default="{ row }">
              <span>{{ row.field_display_name || row.field_name || '-' }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="ip_address" label="IP地址" min-width="120" />
          <el-table-column prop="operation_time" label="操作时间" min-width="160">
            <template #default="{ row }">
              {{ formatDate(row.operation_time) }}
            </template>
          </el-table-column>
          <el-table-column prop="success" label="状态" min-width="80" align="center">
            <template #default="{ row }">
              <span class="status-badge" :class="row.success ? 'success' : 'failed'">
                <span class="status-dot"></span>
                {{ row.success ? '成功' : '失败' }}
              </span>
            </template>
          </el-table-column>
          <el-table-column label="操作" min-width="100" fixed="right" align="center">
            <template #default="{ row }">
              <el-button type="primary" size="small" link @click.stop="handleViewDetail(row)">
                <el-icon><View /></el-icon>
                详情
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
      </div>
    </div>
    </template>

    <!-- 详情对话框 -->
    <el-dialog
      v-model="detailVisible"
      title="审计日志详情"
      width="800px"
      :close-on-click-modal="false"
      class="detail-dialog"
    >
      <el-descriptions :column="2" border>
        <el-descriptions-item label="日志ID">
          {{ currentLog?.id }}
        </el-descriptions-item>
        <el-descriptions-item label="操作类型">
          <span class="operation-badge" :class="currentLog?.operation_type">
            {{ operationTypes[currentLog?.operation_type] || currentLog?.operation_type }}
          </span>
        </el-descriptions-item>
        <el-descriptions-item label="操作用户">
          {{ currentLog?.username || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="用户角色">
          {{ currentLog?.user_role === 'admin' ? '管理员' : '员工' }}
        </el-descriptions-item>
        <el-descriptions-item label="操作模块">
          {{ getModelName(currentLog?.model_name) }}
        </el-descriptions-item>
        <el-descriptions-item label="记录ID">
          {{ currentLog?.record_id }}
        </el-descriptions-item>
        <el-descriptions-item label="操作字段">
          {{ currentLog?.field_display_name || currentLog?.field_name || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="操作状态">
          <span class="status-badge" :class="currentLog?.success ? 'success' : 'failed'">
            <span class="status-dot"></span>
            {{ currentLog?.success ? '成功' : '失败' }}
          </span>
        </el-descriptions-item>
        <el-descriptions-item label="IP地址">
          {{ currentLog?.ip_address || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="操作时间">
          {{ formatDate(currentLog?.operation_time) }}
        </el-descriptions-item>
        <el-descriptions-item label="请求路径" :span="2">
          {{ currentLog?.request_path || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="请求方法">
          {{ currentLog?.request_method || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="用户代理" :span="2">
          <div class="user-agent">{{ currentLog?.user_agent || '-' }}</div>
        </el-descriptions-item>
        <el-descriptions-item v-if="!currentLog?.success && currentLog?.error_message" label="错误信息" :span="2">
          <div class="error-message">{{ currentLog?.error_message }}</div>
        </el-descriptions-item>
      </el-descriptions>

      <!-- 数据变更对比 -->
      <div v-if="currentLog?.old_value || currentLog?.new_value" class="change-comparison">
        <h4 class="comparison-title">数据变更对比</h4>
        <el-row :gutter="20">
          <el-col :span="12">
            <div class="change-box old-value">
              <div class="change-label">变更前</div>
              <div class="change-content">{{ currentLog?.old_value || '无' }}</div>
            </div>
          </el-col>
          <el-col :span="12">
            <div class="change-box new-value">
              <div class="change-label">变更后</div>
              <div class="change-content">{{ currentLog?.new_value || '无' }}</div>
            </div>
          </el-col>
        </el-row>
      </div>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="detailVisible = false">关闭</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { Download, Search, Refresh, View, Document, CircleCheck, CircleClose, TrendCharts, Warning } from '@element-plus/icons-vue'
import dayjs from 'dayjs'
import {
  getAuditLogs,
  getAuditLogDetail,
  getAuditStatistics,
  exportAuditLogs,
  getOperationTypes,
  getAuditToggle,
  updateAuditToggle
} from '@/api/audit'

const loading = ref(false)
const exportLoading = ref(false)
const toggleLoading = ref(false)
const auditEnabled = ref(false)
const auditList = ref([])
const detailVisible = ref(false)
const currentLog = ref(null)
const operationTypes = ref({})

const statistics = reactive({
  total_operations: 0,
  success_count: 0,
  failed_count: 0,
  success_rate: 0
})

const filterForm = reactive({
  username: '',
  operation_type: '',
  model_name: '',
  success: null,
  start_date: '',
  end_date: ''
})

const dateRange = ref([])

const pagination = reactive({
  page: 1,
  per_page: 20,
  total: 0
})

const dateShortcuts = [
  {
    text: '今天',
    value: () => {
      const today = dayjs().format('YYYY-MM-DD')
      return [today, today]
    }
  },
  {
    text: '最近7天',
    value: () => {
      const end = dayjs().format('YYYY-MM-DD')
      const start = dayjs().subtract(7, 'day').format('YYYY-MM-DD')
      return [start, end]
    }
  },
  {
    text: '最近30天',
    value: () => {
      const end = dayjs().format('YYYY-MM-DD')
      const start = dayjs().subtract(30, 'day').format('YYYY-MM-DD')
      return [start, end]
    }
  },
  {
    text: '本月',
    value: () => {
      const start = dayjs().startOf('month').format('YYYY-MM-DD')
      const end = dayjs().endOf('month').format('YYYY-MM-DD')
      return [start, end]
    }
  }
]

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

const getModelName = (modelName) => {
  const modelMap = {
    Landlord: '房东',
    Tenant: '租客',
    User: '用户'
  }
  return modelMap[modelName] || modelName || '-'
}

const formatDate = (date) => {
  return date ? dayjs(date).format('YYYY-MM-DD HH:mm:ss') : '-'
}

const fetchOperationTypes = async () => {
  try {
    const res = await getOperationTypes()
    if (res.data && res.data.operation_types) {
      operationTypes.value = res.data.operation_types
    }
  } catch (error) {
    console.error('获取操作类型失败', error)
  }
}

const fetchStatistics = async () => {
  try {
    const params = {}
    if (filterForm.start_date) {
      params.start_date = filterForm.start_date
    }
    if (filterForm.end_date) {
      params.end_date = filterForm.end_date
    }
    
    const res = await getAuditStatistics(params)
    const data = res.data
    statistics.total_operations = data.total_operations || 0
    statistics.success_count = data.success_count || 0
    statistics.failed_count = data.failed_count || 0
    statistics.success_rate = data.success_rate || 0
  } catch (error) {
    console.error('获取统计信息失败', error)
  }
}

const fetchAuditList = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      per_page: pagination.per_page,
      ...filterForm
    }
    
    // 处理时间范围
    if (dateRange.value && dateRange.value.length === 2) {
      params.start_date = dateRange.value[0]
      params.end_date = dateRange.value[1]
    }
    
    const res = await getAuditLogs(params)
    auditList.value = res.data.logs || []
    pagination.total = res.data.pagination.total
  } catch (error) {
    ElMessage.error(error.message || '获取审计日志列表失败')
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  pagination.page = 1
  fetchAuditList()
  fetchStatistics()
}

const handleReset = () => {
  filterForm.username = ''
  filterForm.operation_type = ''
  filterForm.model_name = ''
  filterForm.success = null
  dateRange.value = []
  handleSearch()
}

const handleSizeChange = (size) => {
  pagination.per_page = size
  fetchAuditList()
}

const handlePageChange = (page) => {
  pagination.page = page
  fetchAuditList()
}

const handleRowClick = (row) => {
  handleViewDetail(row)
}

const handleViewDetail = async (row) => {
  try {
    const res = await getAuditLogDetail(row.id)
    currentLog.value = res.data
    detailVisible.value = true
  } catch (error) {
    ElMessage.error(error.message || '获取日志详情失败')
  }
}

const handleExport = async () => {
  exportLoading.value = true
  try {
    const params = {
      format: 'csv',
      ...filterForm
    }
    
    // 处理时间范围
    if (dateRange.value && dateRange.value.length === 2) {
      params.start_date = dateRange.value[0]
      params.end_date = dateRange.value[1]
    }
    
    const res = await exportAuditLogs(params)
    
    // 创建下载链接
    const blob = new Blob([res], { type: 'text/csv;charset=utf-8;' })
    const link = document.createElement('a')
    const url = window.URL.createObjectURL(blob)
    link.href = url
    link.download = `audit_logs_${dayjs().format('YYYYMMDD_HHmmss')}.csv`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    
    ElMessage.success('导出成功')
  } catch (error) {
    ElMessage.error(error.message || '导出失败')
  } finally {
    exportLoading.value = false
  }
}

/**
 * 初始化审计开关状态
 */
const initAuditToggle = async () => {
  // 从 localStorage 读取状态，默认为 false
  const storedEnabled = localStorage.getItem('audit_enabled')
  const localEnabled = storedEnabled === 'true'
  
  try {
    // 从后端同步状态
    const res = await getAuditToggle()
    const serverEnabled = res.data?.enabled ?? false
    
    // 如果本地和服务器状态不一致，以服务器状态为准
    if (localEnabled !== serverEnabled) {
      localStorage.setItem('audit_enabled', String(serverEnabled))
      auditEnabled.value = serverEnabled
    } else {
      auditEnabled.value = localEnabled
    }
  } catch (error) {
    console.error('获取审计开关状态失败', error)
    // 如果请求失败，使用本地状态
    auditEnabled.value = localEnabled
  }
}

/**
 * 处理开关状态变更
 */
const handleToggleChange = async (enabled) => {
  toggleLoading.value = true
  try {
    // 调用 API 更新后端状态
    await updateAuditToggle(enabled)
    
    // 更新 localStorage
    localStorage.setItem('audit_enabled', String(enabled))
    
    ElMessage.success(enabled ? '审计日志功能已启用' : '审计日志功能已禁用')
    
    // 如果启用，加载数据
    if (enabled) {
      fetchAuditList()
      fetchStatistics()
    }
  } catch (error) {
    // 恢复原状态
    auditEnabled.value = !enabled
    ElMessage.error(error.message || '更新审计开关状态失败')
  } finally {
    toggleLoading.value = false
  }
}

onMounted(() => {
  initAuditToggle()
  fetchOperationTypes()
  // 只有启用时才加载数据
  if (auditEnabled.value) {
    fetchAuditList()
    fetchStatistics()
  }
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
  
  .header-right {
    display: flex;
    align-items: center;
    gap: 20px;
  }
  
  .toggle-wrapper {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 8px 16px;
    background: white;
    border-radius: 10px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
    
    .toggle-label {
      font-size: 14px;
      font-weight: 500;
      color: var(--text-primary);
    }
  }
  
  .export-button {
    height: 40px;
    padding: 0 20px;
    border-radius: 10px;
    font-weight: 500;
    background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-primary-dark) 100%);
    border: none;
    box-shadow: 0 4px 12px rgba(15, 118, 110, 0.3);
    transition: all 0.3s ease;
    
    &:hover:not(:disabled) {
      transform: translateY(-2px);
      box-shadow: 0 6px 16px rgba(15, 118, 110, 0.4);
    }
    
    &:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }
    
    .btn-icon {
      margin-right: 6px;
    }
  }
}

.disabled-notice {
  margin-bottom: 24px;
  
  .notice-card {
    border-radius: 16px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
    
    :deep(.el-card__body) {
      padding: 60px 40px;
    }
    
    .notice-content {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      text-align: center;
      
      .notice-icon {
        color: #F59E0B;
        margin-bottom: 20px;
      }
      
      .notice-title {
        font-size: 20px;
        font-weight: 600;
        color: var(--text-primary);
        margin: 0 0 12px 0;
      }
      
      .notice-text {
        font-size: 14px;
        color: var(--text-muted);
        margin: 0;
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
        
        &.success {
          background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        }
        
        &.failed {
          background: linear-gradient(135deg, #eb3349 0%, #f45c43 100%);
        }
        
        &.rate {
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
      width: 160px;
    }
    
    .filter-daterange {
      width: 260px;
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
  
  .data-table {
    width: 100%;
    
    :deep(.el-table__header th) {
      background: #fafafa !important;
      font-weight: 600;
      color: var(--text-primary);
      font-size: 13px;
    }
    
    :deep(.el-table__row) {
      cursor: pointer;
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
    
    .user-details {
      .user-name {
        font-weight: 500;
        color: var(--text-primary);
      }
      
      .user-role {
        font-size: 12px;
        color: var(--text-muted);
      }
    }
  }
  
  .operation-badge {
    display: inline-flex;
    align-items: center;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 500;
    
    &.view {
      background: rgba(59, 130, 246, 0.1);
      color: #3B82F6;
    }
    
    &.modify {
      background: rgba(245, 158, 11, 0.1);
      color: #F59E0B;
    }
    
    &.delete {
      background: rgba(239, 68, 68, 0.1);
      color: #EF4444;
    }
    
    &.export {
      background: rgba(16, 185, 129, 0.1);
      color: #10B981;
    }
  }
  
  .module-badge {
    display: inline-flex;
    align-items: center;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 500;
    background: rgba(15, 118, 110, 0.1);
    color: #0F766E;
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
    
    &.success {
      background: rgba(16, 185, 129, 0.1);
      color: #10B981;
      
      .status-dot {
        background: #10B981;
      }
    }
    
    &.failed {
      background: rgba(239, 68, 68, 0.1);
      color: #EF4444;
      
      .status-dot {
        background: #EF4444;
      }
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
  
  :deep(.el-descriptions__label) {
    font-weight: 500;
    width: 120px;
  }
  
  .user-agent {
    font-size: 12px;
    color: var(--text-muted);
    word-break: break-all;
  }
  
  .error-message {
    color: #EF4444;
    font-size: 13px;
  }
  
  .change-comparison {
    margin-top: 24px;
    
    .comparison-title {
      font-size: 16px;
      font-weight: 600;
      color: var(--text-primary);
      margin-bottom: 16px;
    }
    
    .change-box {
      border-radius: 8px;
      padding: 16px;
      
      &.old-value {
        background: rgba(239, 68, 68, 0.05);
        border: 1px solid rgba(239, 68, 68, 0.2);
        
        .change-label {
          color: #EF4444;
        }
      }
      
      &.new-value {
        background: rgba(16, 185, 129, 0.05);
        border: 1px solid rgba(16, 185, 129, 0.2);
        
        .change-label {
          color: #10B981;
        }
      }
      
      .change-label {
        font-size: 13px;
        font-weight: 600;
        margin-bottom: 8px;
      }
      
      .change-content {
        font-size: 13px;
        color: var(--text-primary);
        word-break: break-all;
        white-space: pre-wrap;
      }
    }
  }
  
  .dialog-footer {
    display: flex;
    justify-content: flex-end;
    gap: 12px;
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
      
      .export-button {
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
        .filter-select,
        .filter-daterange {
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
  }
}
</style>
