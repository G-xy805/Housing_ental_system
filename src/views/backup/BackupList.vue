<template>
  <div class="backup-list-page">
    <div class="page-header">
      <h2>数据备份管理</h2>
      <div class="header-actions">
        <el-button type="primary" @click="handleCreateBackup">
          <el-icon><Plus /></el-icon>
          手动备份
        </el-button>
        <el-button @click="handleSettings">
          <el-icon><Setting /></el-icon>
          自动备份设置
        </el-button>
      </div>
    </div>

    <!-- 备份列表 -->
    <el-card class="table-card" shadow="hover">
      <el-table
        :data="backupList"
        style="width: 100%"
        v-loading="loading"
        :default-sort="{ prop: 'created_at', order: 'descending' }"
      >
        <el-table-column prop="filename" label="备份文件名" min-width="200">
          <template #default="scope">
            <span class="filename-text">{{ scope.row.filename }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="备份时间" width="180" sortable>
          <template #default="scope">
            {{ formatDate(scope.row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column prop="file_size" label="文件大小" width="120">
          <template #default="scope">
            {{ formatFileSize(scope.row.file_size) }}
          </template>
        </el-table-column>
        <el-table-column prop="backup_type" label="备份类型" width="120">
          <template #default="scope">
            <el-tag :type="scope.row.backup_type === 'full' ? 'primary' : 'success'">
              {{ scope.row.backup_type === 'full' ? '完整备份' : '增量备份' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="operator" label="操作人" width="120" />
        <el-table-column prop="remark" label="备注" min-width="150" show-overflow-tooltip />
        <el-table-column label="操作" width="280" fixed="right">
          <template #default="scope">
            <el-button link type="primary" @click="handleDownload(scope.row)">
              <el-icon><Download /></el-icon>
              下载
            </el-button>
            <el-button link type="warning" @click="handleRestore(scope.row)">
              <el-icon><RefreshLeft /></el-icon>
              恢复
            </el-button>
            <el-button link type="danger" @click="handleDelete(scope.row)">
              <el-icon><Delete /></el-icon>
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      <template #empty>
        <el-empty description="暂无备份数据">
          <el-button type="primary" @click="handleCreateBackup">
            创建备份
          </el-button>
        </el-empty>
      </template>
    </el-card>

    <!-- 分页 -->
    <el-card class="pagination-card" v-if="backupList.length > 0">
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.per_page"
        :total="pagination.total"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleSizeChange"
        @current-change="handlePageChange"
      />
    </el-card>

    <!-- 创建备份对话框 -->
    <el-dialog
      v-model="createDialogVisible"
      title="创建备份"
      width="500px"
      :close-on-click-modal="false"
      destroy-on-close
    >
      <el-form
        ref="createBackupFormRef"
        :model="createBackupForm"
        :rules="createBackupRules"
        label-width="100px"
      >
        <el-form-item label="备份类型" prop="backup_type">
          <el-select v-model="createBackupForm.backup_type" placeholder="请选择备份类型" style="width: 100%">
            <el-option
              label="完整备份"
              value="full"
              description="备份所有数据，文件较大，耗时较长"
            />
            <el-option
              label="增量备份"
              value="incremental"
              description="仅备份变更数据，文件较小，速度快"
            />
          </el-select>
          <el-alert
            v-if="createBackupForm.backup_type === 'incremental'"
            type="info"
            description="增量备份需要至少存在一个完整备份"
            show-icon
            style="margin-top: 10px"
          />
        </el-form-item>
        <el-form-item label="备注" prop="remark">
          <el-input
            v-model="createBackupForm.remark"
            type="textarea"
            placeholder="请输入备份备注（可选）"
            :rows="3"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="createDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleSubmitCreate" :loading="createLoading">
            确定
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 数据恢复对话框 -->
    <el-dialog
      v-model="restoreDialogVisible"
      title="数据恢复"
      width="550px"
      :close-on-click-modal="false"
      destroy-on-close
    >
      <el-alert
        title="警告：数据恢复操作"
        type="error"
        description="数据恢复将覆盖当前系统的所有数据，此操作不可逆！请确保已备份当前重要数据后再进行恢复操作。"
        show-icon
        :closable="false"
        style="margin-bottom: 20px"
      />
      
      <el-form label-width="120px">
        <el-form-item label="备份文件">
          <span class="info-text">{{ currentBackup.filename }}</span>
        </el-form-item>
        <el-form-item label="备份时间">
          <span class="info-text">{{ formatDate(currentBackup.created_at) }}</span>
        </el-form-item>
        <el-form-item label="备份类型">
          <el-tag :type="currentBackup.backup_type === 'full' ? 'primary' : 'success'">
            {{ currentBackup.backup_type === 'full' ? '完整备份' : '增量备份' }}
          </el-tag>
        </el-form-item>
        <el-form-item label="文件大小">
          <span class="info-text">{{ formatFileSize(currentBackup.file_size) }}</span>
        </el-form-item>
        <el-form-item label="备注">
          <span class="info-text">{{ currentBackup.remark || '无' }}</span>
        </el-form-item>
        <el-form-item label="确认操作">
          <el-checkbox v-model="restoreConfirm">
            我已了解风险，确认要恢复到此备份
          </el-checkbox>
        </el-form-item>
      </el-form>

      <!-- 恢复进度 -->
      <div v-if="restoring" class="progress-section">
        <el-progress
          :percentage="restoreProgress"
          :status="restoreStatus"
          :stroke-width="20"
        />
        <p class="progress-text">{{ restoreText }}</p>
      </div>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="restoreDialogVisible = false" :disabled="restoring">取消</el-button>
          <el-button
            type="danger"
            @click="handleSubmitRestore"
            :loading="restoring"
            :disabled="!restoreConfirm || restoring"
          >
            确认恢复
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 自动备份设置对话框 -->
    <el-dialog
      v-model="settingsDialogVisible"
      title="自动备份设置"
      width="550px"
      :close-on-click-modal="false"
      destroy-on-close
    >
      <el-form
        ref="settingsFormRef"
        :model="settingsForm"
        :rules="settingsRules"
        label-width="120px"
      >
        <el-form-item label="启用自动备份">
          <el-switch
            v-model="settingsForm.enabled"
            active-text="开启"
            inactive-text="关闭"
          />
        </el-form-item>
        
        <template v-if="settingsForm.enabled">
          <el-form-item label="备份频率" prop="frequency">
            <el-select v-model="settingsForm.frequency" placeholder="请选择备份频率" style="width: 100%">
              <el-option label="每天" value="daily" />
              <el-option label="每周" value="weekly" />
              <el-option label="每月" value="monthly" />
            </el-select>
          </el-form-item>

          <el-form-item label="备份时间" prop="backup_time">
            <el-time-picker
              v-model="settingsForm.backup_time"
              format="HH:mm"
              value-format="HH:mm"
              placeholder="选择时间"
              style="width: 100%"
            />
            <el-alert
              type="info"
              description="建议在系统使用低峰期进行自动备份"
              show-icon
              style="margin-top: 10px"
            />
          </el-form-item>

          <el-form-item label="每周备份日" prop="weekday" v-if="settingsForm.frequency === 'weekly'">
            <el-select v-model="settingsForm.weekday" placeholder="请选择星期" style="width: 100%">
              <el-option label="星期一" :value="1" />
              <el-option label="星期二" :value="2" />
              <el-option label="星期三" :value="3" />
              <el-option label="星期四" :value="4" />
              <el-option label="星期五" :value="5" />
              <el-option label="星期六" :value="6" />
              <el-option label="星期日" :value="0" />
            </el-select>
          </el-form-item>

          <el-form-item label="每月备份日" prop="day_of_month" v-if="settingsForm.frequency === 'monthly'">
            <el-select v-model="settingsForm.day_of_month" placeholder="请选择日期" style="width: 100%">
              <el-option
                v-for="day in 31"
                :key="day"
                :label="`${day}日`"
                :value="day"
              />
            </el-select>
          </el-form-item>

          <el-form-item label="保留数量" prop="keep_count">
            <el-input-number
              v-model="settingsForm.keep_count"
              :min="1"
              :max="100"
              :step="1"
              style="width: 150px"
            />
            <span class="form-tip">个（超出数量的旧备份将自动删除）</span>
          </el-form-item>

          <el-form-item label="备份类型">
            <el-radio-group v-model="settingsForm.backup_type">
              <el-radio label="full">完整备份</el-radio>
              <el-radio label="incremental">增量备份</el-radio>
            </el-radio-group>
            <el-alert
              type="warning"
              description="建议选择增量备份以减少存储空间占用"
              show-icon
              style="margin-top: 10px"
            />
          </el-form-item>
        </template>
      </el-form>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="settingsDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleSubmitSettings" :loading="settingsLoading">
            保存设置
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 下载进度对话框 -->
    <el-dialog
      v-model="downloadDialogVisible"
      title="下载备份"
      width="400px"
      :close-on-click-modal="false"
      :show-close="false"
    >
      <div class="download-progress">
        <p class="download-filename">{{ downloadingFile.filename }}</p>
        <el-progress
          :percentage="downloadProgress"
          :status="downloadStatus"
          :stroke-width="20"
        />
        <p class="progress-text">{{ downloadText }}</p>
      </div>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="handleCancelDownload" :disabled="downloadStatus === 'success'">
            {{ downloadStatus === 'success' ? '关闭' : '取消' }}
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Plus,
  Setting,
  Download,
  RefreshLeft,
  Delete,
  View
} from '@element-plus/icons-vue'
import {
  getBackupList,
  createBackup,
  downloadBackup,
  restoreBackup,
  deleteBackup,
  getBackupSettings,
  updateBackupSettings
} from '@/api/backup'
import dayjs from 'dayjs'

// 加载状态
const loading = ref(false)
const createLoading = ref(false)
const settingsLoading = ref(false)
const restoring = ref(false)

// 备份列表
const backupList = ref([])

// 分页
const pagination = reactive({
  page: 1,
  per_page: 10,
  total: 0
})

// 创建备份对话框
const createDialogVisible = ref(false)
const createBackupFormRef = ref(null)
const createBackupForm = reactive({
  backup_type: 'full',
  remark: ''
})

const createBackupRules = {
  backup_type: [
    { required: true, message: '请选择备份类型', trigger: 'change' }
  ]
}

// 恢复备份对话框
const restoreDialogVisible = ref(false)
const currentBackup = ref({})
const restoreConfirm = ref(false)
const restoreProgress = ref(0)
const restoreStatus = ref('')
const restoreText = ref('')

// 设置对话框
const settingsDialogVisible = ref(false)
const settingsFormRef = ref(null)
const settingsForm = reactive({
  enabled: false,
  frequency: 'daily',
  backup_time: '',
  weekday: 1,
  day_of_month: 1,
  keep_count: 10,
  backup_type: 'incremental'
})

const settingsRules = {
  frequency: [
    { required: true, message: '请选择备份频率', trigger: 'change' }
  ],
  backup_time: [
    { required: true, message: '请选择备份时间', trigger: 'change' }
  ],
  keep_count: [
    { required: true, message: '请输入保留数量', trigger: 'blur' }
  ]
}

// 下载进度对话框
const downloadDialogVisible = ref(false)
const downloadingFile = ref({})
const downloadProgress = ref(0)
const downloadStatus = ref('')
const downloadText = ref('')
let downloadController = null

// 格式化日期
const formatDate = (date) => {
  if (!date) return '-'
  return dayjs(date).format('YYYY-MM-DD HH:mm:ss')
}

// 格式化文件大小
const formatFileSize = (bytes) => {
  if (!bytes && bytes !== 0) return '-'
  const units = ['B', 'KB', 'MB', 'GB', 'TB']
  let i = 0
  let size = bytes
  while (size >= 1024 && i < units.length - 1) {
    size /= 1024
    i++
  }
  return `${size.toFixed(2)} ${units[i]}`
}

// 加载备份列表
const loadBackupList = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      per_page: pagination.per_page
    }
    const res = await getBackupList(params)
    backupList.value = res.data?.items || []
    pagination.total = res.data?.pagination?.total || 0
  } catch (error) {
    console.error('加载备份列表失败:', error)
    ElMessage.error('加载备份列表失败')
  } finally {
    loading.value = false
  }
}

// 手动备份
const handleCreateBackup = () => {
  createDialogVisible.value = true
}

const handleSubmitCreate = async () => {
  if (!createBackupFormRef.value) return
  
  try {
    await createBackupFormRef.value.validate()
  } catch (error) {
    return
  }

  createLoading.value = true
  try {
    const data = {
      backup_type: createBackupForm.backup_type,
      remark: createBackupForm.remark
    }
    await createBackup(data)
    ElMessage.success('备份创建成功')
    createDialogVisible.value = false
    loadBackupList()
  } catch (error) {
    console.error('创建备份失败:', error)
    ElMessage.error('创建备份失败：' + (error.message || '请稍后重试'))
  } finally {
    createLoading.value = false
  }
}

// 下载备份
const handleDownload = (row) => {
  downloadingFile.value = {
    filename: row.filename,
    size: row.file_size
  }
  downloadDialogVisible.value = true
  downloadProgress.value = 0
  downloadStatus.value = ''
  downloadText.value = '准备下载...'
  
  downloadBackupFile(row.filename)
}

const downloadBackupFile = async (filename) => {
  try {
    // 模拟下载进度
    let progress = 0
    const interval = setInterval(() => {
      progress += Math.random() * 20
      if (progress >= 95) {
        progress = 95
        clearInterval(interval)
      }
      downloadProgress.value = Math.floor(progress)
      downloadText.value = '下载中...'
    }, 200)

    const response = await downloadBackup(filename)
    
    clearInterval(interval)
    downloadProgress.value = 100
    downloadStatus.value = 'success'
    downloadText.value = '下载完成'
    
    // 创建下载链接
    const blob = new Blob([response.data], { type: 'application/octet-stream' })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = filename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    
    ElMessage.success('备份下载成功')
  } catch (error) {
    console.error('下载备份失败:', error)
    downloadStatus.value = 'exception'
    downloadText.value = '下载失败'
    ElMessage.error('下载备份失败')
  }
}

const handleCancelDownload = () => {
  if (downloadStatus.value === 'success') {
    downloadDialogVisible.value = false
  } else {
    // 取消下载逻辑（如果后端支持）
    downloadDialogVisible.value = false
    ElMessage.info('已取消下载')
  }
}

// 恢复备份
const handleRestore = (row) => {
  currentBackup.value = { ...row }
  restoreConfirm.value = false
  restoreProgress.value = 0
  restoreStatus.value = ''
  restoreText.value = ''
  restoreDialogVisible.value = true
}

const handleSubmitRestore = async () => {
  if (!restoreConfirm.value) {
    ElMessage.warning('请确认风险后再进行恢复操作')
    return
  }

  restoring.value = true
  restoreProgress.value = 0
  restoreStatus.value = ''
  restoreText.value = '准备恢复...'

  try {
    // 模拟恢复进度
    const simulateProgress = () => {
      return new Promise((resolve) => {
        let progress = 0
        const interval = setInterval(() => {
          progress += Math.random() * 15
          if (progress >= 100) {
            progress = 100
            clearInterval(interval)
            resolve()
          } else {
            restoreProgress.value = Math.floor(progress)
            restoreText.value = '数据恢复中...'
          }
        }, 300)
      })
    }

    // 开始恢复
    const restorePromise = restoreBackup({
      filename: currentBackup.value.filename,
      confirm: true
    })

    await Promise.all([
      restorePromise,
      simulateProgress()
    ])

    restoreProgress.value = 100
    restoreStatus.value = 'success'
    restoreText.value = '恢复成功'
    
    ElMessage.success('数据恢复成功，系统将重启')
    
    setTimeout(() => {
      restoreDialogVisible.value = false
      loadBackupList()
    }, 1500)
  } catch (error) {
    console.error('恢复备份失败:', error)
    restoreStatus.value = 'exception'
    restoreText.value = '恢复失败'
    ElMessage.error('恢复备份失败：' + (error.message || '请稍后重试'))
  } finally {
    restoring.value = false
  }
}

// 删除备份
const handleDelete = (row) => {
  ElMessageBox.confirm(
    `确定要删除备份文件"${row.filename}"吗？删除后不可恢复！`,
    '删除确认',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(async () => {
    try {
      await deleteBackup(row.filename)
      ElMessage.success('删除成功')
      loadBackupList()
    } catch (error) {
      console.error('删除备份失败:', error)
      ElMessage.error('删除备份失败')
    }
  }).catch(() => {})
}

// 自动备份设置
const handleSettings = async () => {
  settingsDialogVisible.value = true
  await loadSettings()
}

const loadSettings = async () => {
  try {
    const res = await getBackupSettings()
    const settings = res.data || {}
    Object.assign(settingsForm, {
      enabled: settings.enabled || false,
      frequency: settings.frequency || 'daily',
      backup_time: settings.backup_time || '',
      weekday: settings.weekday || 1,
      day_of_month: settings.day_of_month || 1,
      keep_count: settings.keep_count || 10,
      backup_type: settings.backup_type || 'incremental'
    })
  } catch (error) {
    console.error('加载备份设置失败:', error)
  }
}

const handleSubmitSettings = async () => {
  if (!settingsFormRef.value) return
  
  try {
    await settingsFormRef.value.validate()
  } catch (error) {
    return
  }

  settingsLoading.value = true
  try {
    const data = {
      enabled: settingsForm.enabled,
      frequency: settingsForm.frequency,
      backup_time: settingsForm.backup_time,
      weekday: settingsForm.enabled && settingsForm.frequency === 'weekly' ? settingsForm.weekday : undefined,
      day_of_month: settingsForm.enabled && settingsForm.frequency === 'monthly' ? settingsForm.day_of_month : undefined,
      keep_count: settingsForm.keep_count,
      backup_type: settingsForm.backup_type
    }
    
    await updateBackupSettings(data)
    ElMessage.success('保存成功')
    settingsDialogVisible.value = false
  } catch (error) {
    console.error('保存设置失败:', error)
    ElMessage.error('保存设置失败')
  } finally {
    settingsLoading.value = false
  }
}

// 分页处理
const handleSizeChange = (size) => {
  pagination.per_page = size
  pagination.page = 1
  loadBackupList()
}

const handlePageChange = (page) => {
  pagination.page = page
  loadBackupList()
}

// 初始化
onMounted(() => {
  loadBackupList()
})
</script>

<style lang="scss" scoped>
.backup-list-page {
  padding: 20px;

  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;

    h2 {
      margin: 0;
      color: #333;
      font-size: 24px;
    }

    .header-actions {
      display: flex;
      gap: 10px;
    }
  }

  .table-card {
    margin-bottom: 20px;

    .filename-text {
      font-family: 'Consolas', 'Monaco', monospace;
      font-size: 13px;
    }
  }

  .pagination-card {
    .el-pagination {
      display: flex;
      justify-content: flex-end;
    }
  }

  .info-text {
    color: #606266;
  }

  .form-tip {
    margin-left: 10px;
    color: #909399;
    font-size: 13px;
  }

  .progress-section {
    margin-top: 20px;
    padding: 20px;
    background-color: #f5f7fa;
    border-radius: 4px;

    .progress-text {
      margin-top: 10px;
      text-align: center;
      color: #606266;
      font-size: 14px;
    }
  }

  .download-progress {
    padding: 20px 0;

    .download-filename {
      font-family: 'Consolas', 'Monaco', monospace;
      font-size: 13px;
      color: #606266;
      margin-bottom: 20px;
      word-break: break-all;
    }

    .progress-text {
      margin-top: 10px;
      text-align: center;
      color: #606266;
      font-size: 14px;
    }
  }
}
</style>
