<template>
  <div class="monitoring-dashboard">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <h1 class="page-title">系统监控</h1>
        <p class="page-subtitle">实时监控系统运行状态和性能指标</p>
      </div>
      <div class="header-actions">
        <el-button
          :icon="Refresh"
          @click="handleRefresh"
          :loading="refreshing"
        >
          刷新数据
        </el-button>
        <el-button
          type="danger"
          :icon="Delete"
          @click="handleClearResolved"
          :loading="clearingResolved"
        >
          清除已解决告警
        </el-button>
      </div>
    </div>

    <!-- 系统健康状态 -->
    <div class="health-section">
      <div class="section-header">
        <h2 class="section-title">系统健康状态</h2>
        <el-tag
          :type="overallHealthTag.type"
          :effect="'dark'"
          size="large"
        >
          <el-icon class="status-icon">
            <component :is="overallHealthTag.icon" />
          </el-icon>
          {{ overallHealthTag.text }}
        </el-tag>
      </div>

      <div class="health-grid">
        <!-- 数据库连接状态 -->
        <div class="health-card">
          <div class="health-card-header">
            <div class="health-icon-wrapper" :class="dbHealth.status">
              <el-icon><Coin /></el-icon>
            </div>
            <div class="health-info">
              <h3 class="health-title">数据库连接</h3>
              <el-tag :type="dbHealth.tagType" size="small">
                {{ dbHealth.statusText }}
              </el-tag>
            </div>
          </div>
          <div class="health-details" v-if="dbHealth.details">
            <div class="detail-item">
              <span class="detail-label">响应时间</span>
              <span class="detail-value">{{ dbHealth.details.responseTime }}ms</span>
            </div>
            <div class="detail-item">
              <span class="detail-label">连接池</span>
              <span class="detail-value">{{ dbHealth.details.connections }}/{{ dbHealth.details.maxConnections }}</span>
            </div>
          </div>
        </div>

        <!-- Redis连接状态 -->
        <div class="health-card">
          <div class="health-card-header">
            <div class="health-icon-wrapper" :class="redisHealth.status">
              <el-icon><Cpu /></el-icon>
            </div>
            <div class="health-info">
              <h3 class="health-title">Redis 连接</h3>
              <el-tag :type="redisHealth.tagType" size="small">
                {{ redisHealth.statusText }}
              </el-tag>
            </div>
          </div>
          <div class="health-details" v-if="redisHealth.details">
            <div class="detail-item">
              <span class="detail-label">响应时间</span>
              <span class="detail-value">{{ redisHealth.details.responseTime }}ms</span>
            </div>
            <div class="detail-item">
              <span class="detail-label">内存使用</span>
              <span class="detail-value">{{ redisHealth.details.memoryUsage }}</span>
            </div>
          </div>
        </div>

        <!-- CPU使用率 -->
        <div class="health-card">
          <div class="health-card-header">
            <div class="health-icon-wrapper" :class="systemHealth.cpuStatus">
              <el-icon><Monitor /></el-icon>
            </div>
            <div class="health-info">
              <h3 class="health-title">CPU 使用率</h3>
              <el-tag :type="systemHealth.cpuTagType" size="small">
                {{ systemHealth.cpuUsage }}%
              </el-tag>
            </div>
          </div>
          <div class="health-details">
            <div class="detail-item">
              <span class="detail-label">核心数</span>
              <span class="detail-value">{{ systemHealth.cpuCores }} 核</span>
            </div>
            <div class="detail-item">
              <span class="detail-label">负载</span>
              <span class="detail-value">{{ systemHealth.cpuLoad }}</span>
            </div>
          </div>
        </div>

        <!-- 内存使用率 -->
        <div class="health-card">
          <div class="health-card-header">
            <div class="health-icon-wrapper" :class="systemHealth.memoryStatus">
              <el-icon><Grid /></el-icon>
            </div>
            <div class="health-info">
              <h3 class="health-title">内存使用率</h3>
              <el-tag :type="systemHealth.memoryTagType" size="small">
                {{ systemHealth.memoryUsage }}%
              </el-tag>
            </div>
          </div>
          <div class="health-details">
            <div class="detail-item">
              <span class="detail-label">已使用</span>
              <span class="detail-value">{{ systemHealth.memoryUsed }}</span>
            </div>
            <div class="detail-item">
              <span class="detail-label">总内存</span>
              <span class="detail-value">{{ systemHealth.memoryTotal }}</span>
            </div>
          </div>
        </div>

        <!-- 磁盘使用率 -->
        <div class="health-card">
          <div class="health-card-header">
            <div class="health-icon-wrapper" :class="systemHealth.diskStatus">
              <el-icon><FolderOpened /></el-icon>
            </div>
            <div class="health-info">
              <h3 class="health-title">磁盘使用率</h3>
              <el-tag :type="systemHealth.diskTagType" size="small">
                {{ systemHealth.diskUsage }}%
              </el-tag>
            </div>
          </div>
          <div class="health-details">
            <div class="detail-item">
              <span class="detail-label">已使用</span>
              <span class="detail-value">{{ systemHealth.diskUsed }}</span>
            </div>
            <div class="detail-item">
              <span class="detail-label">总容量</span>
              <span class="detail-value">{{ systemHealth.diskTotal }}</span>
            </div>
          </div>
        </div>

        <!-- 系统运行时间 -->
        <div class="health-card">
          <div class="health-card-header">
            <div class="health-icon-wrapper success">
              <el-icon><Timer /></el-icon>
            </div>
            <div class="health-info">
              <h3 class="health-title">系统运行时间</h3>
              <el-tag type="success" size="small">运行中</el-tag>
            </div>
          </div>
          <div class="health-details">
            <div class="detail-item">
              <span class="detail-label">启动时间</span>
              <span class="detail-value">{{ systemHealth.startTime }}</span>
            </div>
            <div class="detail-item">
              <span class="detail-label">运行时长</span>
              <span class="detail-value">{{ systemHealth.uptime }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 性能指标图表 -->
    <div class="charts-section">
      <div class="section-header">
        <h2 class="section-title">性能指标</h2>
      </div>

      <el-row :gutter="24">
        <!-- QPS统计 -->
        <el-col :xs="24" :lg="12">
          <div class="chart-card">
            <div class="chart-header">
              <h3 class="chart-title">QPS 统计</h3>
              <div class="chart-summary">
                <span class="summary-item">
                  <span class="summary-label">当前</span>
                  <span class="summary-value">{{ performanceData.currentQPS }}</span>
                </span>
                <span class="summary-item">
                  <span class="summary-label">峰值</span>
                  <span class="summary-value">{{ performanceData.maxQPS }}</span>
                </span>
              </div>
            </div>
            <div ref="qpsChartRef" class="chart-container"></div>
          </div>
        </el-col>

        <!-- 响应时间统计 -->
        <el-col :xs="24" :lg="12">
          <div class="chart-card">
            <div class="chart-header">
              <h3 class="chart-title">响应时间统计</h3>
              <div class="chart-summary">
                <span class="summary-item">
                  <span class="summary-label">平均</span>
                  <span class="summary-value">{{ performanceData.avgResponseTime }}ms</span>
                </span>
                <span class="summary-item">
                  <span class="summary-label">P99</span>
                  <span class="summary-value">{{ performanceData.p99ResponseTime }}ms</span>
                </span>
              </div>
            </div>
            <div ref="responseTimeChartRef" class="chart-container"></div>
          </div>
        </el-col>

        <!-- 错误率统计 -->
        <el-col :xs="24" :lg="12">
          <div class="chart-card">
            <div class="chart-header">
              <h3 class="chart-title">错误率统计</h3>
              <div class="chart-summary">
                <span class="summary-item">
                  <span class="summary-label">当前</span>
                  <span class="summary-value error">{{ performanceData.currentErrorRate }}%</span>
                </span>
                <span class="summary-item">
                  <span class="summary-label">总请求</span>
                  <span class="summary-value">{{ performanceData.totalRequests }}</span>
                </span>
              </div>
            </div>
            <div ref="errorRateChartRef" class="chart-container"></div>
          </div>
        </el-col>

        <!-- 资源使用趋势 -->
        <el-col :xs="24" :lg="12">
          <div class="chart-card">
            <div class="chart-header">
              <h3 class="chart-title">资源使用趋势</h3>
              <div class="chart-legend">
                <span class="legend-item cpu">
                  <span class="legend-dot"></span>
                  CPU
                </span>
                <span class="legend-item memory">
                  <span class="legend-dot"></span>
                  内存
                </span>
                <span class="legend-item disk">
                  <span class="legend-dot"></span>
                  磁盘
                </span>
              </div>
            </div>
            <div ref="resourceChartRef" class="chart-container"></div>
          </div>
        </el-col>
      </el-row>
    </div>

    <!-- 告警列表 -->
    <div class="alerts-section">
      <div class="section-header">
        <h2 class="section-title">告警列表</h2>
        <div class="alert-filters">
          <el-select
            v-model="alertFilter.status"
            placeholder="状态筛选"
            clearable
            size="default"
            @change="loadAlerts"
            style="width: 120px"
          >
            <el-option label="全部" value="" />
            <el-option label="未解决" value="active" />
            <el-option label="已解决" value="resolved" />
          </el-select>
          <el-select
            v-model="alertFilter.severity"
            placeholder="级别筛选"
            clearable
            size="default"
            @change="loadAlerts"
            style="width: 120px"
          >
            <el-option label="全部" value="" />
            <el-option label="严重" value="critical" />
            <el-option label="警告" value="warning" />
            <el-option label="信息" value="info" />
          </el-select>
        </div>
      </div>

      <div class="alerts-table-wrapper">
        <el-table
          :data="alerts"
          v-loading="alertsLoading"
          style="width: 100%"
          :row-class-name="getAlertRowClass"
        >
          <el-table-column label="级别" width="100" align="center">
            <template #default="{ row }">
              <el-tag
                :type="getSeverityTagType(row.severity)"
                :effect="'dark'"
                size="small"
              >
                {{ getSeverityText(row.severity) }}
              </el-tag>
            </template>
          </el-table-column>

          <el-table-column label="告警内容" min-width="300">
            <template #default="{ row }">
              <div class="alert-content">
                <div class="alert-title">{{ row.title }}</div>
                <div class="alert-message">{{ row.message }}</div>
              </div>
            </template>
          </el-table-column>

          <el-table-column label="来源" width="120">
            <template #default="{ row }">
              <span class="alert-source">{{ row.source }}</span>
            </template>
          </el-table-column>

          <el-table-column label="触发时间" width="180">
            <template #default="{ row }">
              <span class="alert-time">{{ formatTime(row.triggeredAt) }}</span>
            </template>
          </el-table-column>

          <el-table-column label="状态" width="100" align="center">
            <template #default="{ row }">
              <el-tag
                :type="row.status === 'resolved' ? 'success' : 'danger'"
                size="small"
              >
                {{ row.status === 'resolved' ? '已解决' : '未解决' }}
              </el-tag>
            </template>
          </el-table-column>

          <el-table-column label="操作" width="180" fixed="right">
            <template #default="{ row }">
              <el-button
                v-if="row.status !== 'resolved'"
                type="primary"
                size="small"
                text
                @click="handleResolveAlert(row)"
              >
                解决
              </el-button>
              <el-button
                type="info"
                size="small"
                text
                @click="handleViewAlertDetail(row)"
              >
                详情
              </el-button>
            </template>
          </el-table-column>
        </el-table>

        <Pagination
          v-model:currentPage="alertPagination.page"
          v-model:pageSize="alertPagination.pageSize"
          :total="alertPagination.total"
          @change="loadAlerts"
        />
      </div>
    </div>

    <!-- 告警详情对话框 -->
    <el-dialog
      v-model="alertDetailVisible"
      title="告警详情"
      width="600px"
      :close-on-click-modal="false"
    >
      <div class="alert-detail" v-if="currentAlert">
        <div class="detail-row">
          <span class="detail-label">告警级别：</span>
          <el-tag :type="getSeverityTagType(currentAlert.severity)" effect="dark">
            {{ getSeverityText(currentAlert.severity) }}
          </el-tag>
        </div>
        <div class="detail-row">
          <span class="detail-label">告警标题：</span>
          <span class="detail-text">{{ currentAlert.title }}</span>
        </div>
        <div class="detail-row">
          <span class="detail-label">告警内容：</span>
          <span class="detail-text">{{ currentAlert.message }}</span>
        </div>
        <div class="detail-row">
          <span class="detail-label">告警来源：</span>
          <span class="detail-text">{{ currentAlert.source }}</span>
        </div>
        <div class="detail-row">
          <span class="detail-label">触发时间：</span>
          <span class="detail-text">{{ formatTime(currentAlert.triggeredAt) }}</span>
        </div>
        <div class="detail-row">
          <span class="detail-label">当前状态：</span>
          <el-tag :type="currentAlert.status === 'resolved' ? 'success' : 'danger'">
            {{ currentAlert.status === 'resolved' ? '已解决' : '未解决' }}
          </el-tag>
        </div>
        <div class="detail-row" v-if="currentAlert.resolvedAt">
          <span class="detail-label">解决时间：</span>
          <span class="detail-text">{{ formatTime(currentAlert.resolvedAt) }}</span>
        </div>
        <div class="detail-row" v-if="currentAlert.resolvedBy">
          <span class="detail-label">解决人：</span>
          <span class="detail-text">{{ currentAlert.resolvedBy }}</span>
        </div>
        <div class="detail-row" v-if="currentAlert.resolution">
          <span class="detail-label">解决说明：</span>
          <span class="detail-text">{{ currentAlert.resolution }}</span>
        </div>
      </div>

      <template #footer>
        <el-button @click="alertDetailVisible = false">关闭</el-button>
        <el-button
          v-if="currentAlert && currentAlert.status !== 'resolved'"
          type="primary"
          @click="handleResolveFromDetail"
        >
          解决告警
        </el-button>
      </template>
    </el-dialog>

    <!-- 解决告警对话框 -->
    <el-dialog
      v-model="resolveDialogVisible"
      title="解决告警"
      width="500px"
      :close-on-click-modal="false"
    >
      <el-form
        ref="resolveFormRef"
        :model="resolveForm"
        :rules="resolveRules"
        label-width="100px"
      >
        <el-form-item label="解决说明" prop="resolution">
          <el-input
            v-model="resolveForm.resolution"
            type="textarea"
            :rows="4"
            placeholder="请输入解决说明"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="resolveDialogVisible = false">取消</el-button>
        <el-button
          type="primary"
          @click="confirmResolveAlert"
          :loading="resolving"
        >
          确定
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Refresh,
  Delete,
  Coin,
  Cpu,
  Monitor,
  Grid,
  FolderOpened,
  Timer,
  CircleCheck,
  Warning,
  CircleClose
} from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import dayjs from 'dayjs'
import Pagination from '@/components/common/Pagination.vue'
import {
  healthCheck,
  dbHealthCheck,
  redisHealthCheck,
  systemHealthCheck,
  getQPSStats,
  getResponseTimeStats,
  getErrorRateStats,
  getResourceStats,
  getAlerts,
  resolveAlert,
  clearResolvedAlerts
} from '@/api/monitoring'

// 刷新状态
const refreshing = ref(false)
const clearingResolved = ref(false)

// 系统健康状态
const systemHealth = reactive({
  cpuUsage: 0,
  cpuCores: 0,
  cpuLoad: '0.00',
  cpuStatus: 'healthy',
  cpuTagType: 'success',
  memoryUsage: 0,
  memoryUsed: '0 GB',
  memoryTotal: '0 GB',
  memoryStatus: 'healthy',
  memoryTagType: 'success',
  diskUsage: 0,
  diskUsed: '0 GB',
  diskTotal: '0 GB',
  diskStatus: 'healthy',
  diskTagType: 'success',
  startTime: '-',
  uptime: '-'
})

const dbHealth = reactive({
  status: 'healthy',
  statusText: '正常',
  tagType: 'success',
  details: null
})

const redisHealth = reactive({
  status: 'healthy',
  statusText: '正常',
  tagType: 'success',
  details: null
})

// 整体健康状态
const overallHealthTag = computed(() => {
  const hasCritical = systemHealth.cpuUsage > 90 ||
                      systemHealth.memoryUsage > 90 ||
                      systemHealth.diskUsage > 90 ||
                      dbHealth.status === 'unhealthy' ||
                      redisHealth.status === 'unhealthy'

  const hasWarning = systemHealth.cpuUsage > 70 ||
                     systemHealth.memoryUsage > 70 ||
                     systemHealth.diskUsage > 70 ||
                     dbHealth.status === 'warning' ||
                     redisHealth.status === 'warning'

  if (hasCritical) {
    return { type: 'danger', text: '故障', icon: CircleClose }
  } else if (hasWarning) {
    return { type: 'warning', text: '警告', icon: Warning }
  } else {
    return { type: 'success', text: '健康', icon: CircleCheck }
  }
})

// 性能数据
const performanceData = reactive({
  currentQPS: 0,
  maxQPS: 0,
  avgResponseTime: 0,
  p99ResponseTime: 0,
  currentErrorRate: 0,
  totalRequests: 0
})

// 图表引用
const qpsChartRef = ref(null)
const responseTimeChartRef = ref(null)
const errorRateChartRef = ref(null)
const resourceChartRef = ref(null)

let qpsChart = null
let responseTimeChart = null
let errorRateChart = null
let resourceChart = null

// 告警相关
const alerts = ref([])
const alertsLoading = ref(false)
const alertFilter = reactive({
  status: '',
  severity: ''
})
const alertPagination = reactive({
  page: 1,
  pageSize: 10,
  total: 0
})

const alertDetailVisible = ref(false)
const currentAlert = ref(null)
const resolveDialogVisible = ref(false)
const resolveFormRef = ref(null)
const resolveForm = reactive({
  resolution: ''
})
const resolveRules = {
  resolution: [
    { required: true, message: '请输入解决说明', trigger: 'blur' }
  ]
}
const resolving = ref(false)

// 加载健康状态
const loadHealthStatus = async () => {
  try {
    // 加载数据库健康状态
    const dbRes = await dbHealthCheck()
    if (dbRes.success && dbRes.data) {
      dbHealth.status = dbRes.data.status || 'healthy'
      dbHealth.statusText = dbRes.data.status === 'healthy' ? '正常' : '异常'
      dbHealth.tagType = dbRes.data.status === 'healthy' ? 'success' : 'danger'
      dbHealth.details = {
        responseTime: dbRes.data.response_time || 0,
        connections: dbRes.data.connections || 0,
        maxConnections: dbRes.data.max_connections || 100
      }
    }

    // 加载Redis健康状态
    const redisRes = await redisHealthCheck()
    if (redisRes.success && redisRes.data) {
      redisHealth.status = redisRes.data.status || 'healthy'
      redisHealth.statusText = redisRes.data.status === 'healthy' ? '正常' : '异常'
      redisHealth.tagType = redisRes.data.status === 'healthy' ? 'success' : 'danger'
      redisHealth.details = {
        responseTime: redisRes.data.response_time || 0,
        memoryUsage: redisRes.data.memory_usage || '0 MB'
      }
    }

    // 加载系统资源状态
    const sysRes = await systemHealthCheck()
    if (sysRes.success && sysRes.data) {
      const data = sysRes.data

      // CPU
      systemHealth.cpuUsage = Math.round(data.cpu?.usage || 0)
      systemHealth.cpuCores = data.cpu?.cores || 0
      systemHealth.cpuLoad = data.cpu?.load || '0.00'
      systemHealth.cpuStatus = getStatusByUsage(systemHealth.cpuUsage)
      systemHealth.cpuTagType = getTagTypeByUsage(systemHealth.cpuUsage)

      // 内存
      systemHealth.memoryUsage = Math.round(data.memory?.usage_percent || 0)
      systemHealth.memoryUsed = data.memory?.used || '0 GB'
      systemHealth.memoryTotal = data.memory?.total || '0 GB'
      systemHealth.memoryStatus = getStatusByUsage(systemHealth.memoryUsage)
      systemHealth.memoryTagType = getTagTypeByUsage(systemHealth.memoryUsage)

      // 磁盘
      systemHealth.diskUsage = Math.round(data.disk?.usage_percent || 0)
      systemHealth.diskUsed = data.disk?.used || '0 GB'
      systemHealth.diskTotal = data.disk?.total || '0 GB'
      systemHealth.diskStatus = getStatusByUsage(systemHealth.diskUsage)
      systemHealth.diskTagType = getTagTypeByUsage(systemHealth.diskUsage)

      // 运行时间
      systemHealth.startTime = data.start_time ? dayjs(data.start_time).format('YYYY-MM-DD HH:mm:ss') : '-'
      systemHealth.uptime = data.uptime || '-'
    }
  } catch (error) {
    console.error('加载健康状态失败:', error)
  }
}

// 根据使用率获取状态
const getStatusByUsage = (usage) => {
  if (usage >= 90) return 'critical'
  if (usage >= 70) return 'warning'
  return 'healthy'
}

// 根据使用率获取标签类型
const getTagTypeByUsage = (usage) => {
  if (usage >= 90) return 'danger'
  if (usage >= 70) return 'warning'
  return 'success'
}

// 加载性能数据
const loadPerformanceData = async () => {
  try {
    // 加载QPS数据
    const qpsRes = await getQPSStats()
    if (qpsRes.success && qpsRes.data) {
      performanceData.currentQPS = qpsRes.data.current_qps || 0
      performanceData.maxQPS = qpsRes.data.max_qps || 0
      initQPSChart(qpsRes.data.timeline || [])
    }

    // 加载响应时间数据
    const responseRes = await getResponseTimeStats()
    if (responseRes.success && responseRes.data) {
      performanceData.avgResponseTime = responseRes.data.avg_response_time || 0
      performanceData.p99ResponseTime = responseRes.data.p99_response_time || 0
      initResponseTimeChart(responseRes.data.timeline || [])
    }

    // 加载错误率数据
    const errorRes = await getErrorRateStats()
    if (errorRes.success && errorRes.data) {
      performanceData.currentErrorRate = (errorRes.data.current_error_rate || 0).toFixed(2)
      performanceData.totalRequests = errorRes.data.total_requests || 0
      initErrorRateChart(errorRes.data.timeline || [])
    }

    // 加载资源使用数据
    const resourceRes = await getResourceStats()
    if (resourceRes.success && resourceRes.data) {
      initResourceChart(resourceRes.data.timeline || [])
    }
  } catch (error) {
    console.error('加载性能数据失败:', error)
  }
}

// 初始化QPS图表
const initQPSChart = (timeline) => {
  if (!qpsChartRef.value) return

  if (qpsChart) {
    qpsChart.dispose()
  }

  qpsChart = echarts.init(qpsChartRef.value)

  const times = timeline.map(item => item.time)
  const values = timeline.map(item => item.qps || 0)

  const option = {
    tooltip: {
      trigger: 'axis',
      formatter: '{b}<br/>QPS: {c}',
      backgroundColor: 'rgba(255, 255, 255, 0.95)',
      borderColor: '#e5e7eb',
      borderWidth: 1,
      textStyle: { color: '#374151' }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      top: '8%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: times,
      axisLine: { lineStyle: { color: '#e5e7eb' } },
      axisLabel: { color: '#6b7280', fontSize: 12 }
    },
    yAxis: {
      type: 'value',
      axisLabel: { color: '#6b7280', fontSize: 12 },
      splitLine: { lineStyle: { color: '#f3f4f6', type: 'dashed' } }
    },
    series: [
      {
        name: 'QPS',
        type: 'line',
        smooth: true,
        data: values,
        itemStyle: { color: '#0F766E' },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(15, 118, 110, 0.25)' },
            { offset: 1, color: 'rgba(15, 118, 110, 0.02)' }
          ])
        },
        lineStyle: { width: 3, color: '#0F766E' },
        symbol: 'circle',
        symbolSize: 6
      }
    ]
  }

  qpsChart.setOption(option)
}

// 初始化响应时间图表
const initResponseTimeChart = (timeline) => {
  if (!responseTimeChartRef.value) return

  if (responseTimeChart) {
    responseTimeChart.dispose()
  }

  responseTimeChart = echarts.init(responseTimeChartRef.value)

  const times = timeline.map(item => item.time)
  const avgTimes = timeline.map(item => item.avg_time || 0)
  const p99Times = timeline.map(item => item.p99_time || 0)

  const option = {
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(255, 255, 255, 0.95)',
      borderColor: '#e5e7eb',
      borderWidth: 1,
      textStyle: { color: '#374151' }
    },
    legend: {
      data: ['平均响应时间', 'P99响应时间'],
      bottom: 0,
      textStyle: { color: '#6b7280', fontSize: 12 }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '15%',
      top: '8%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: times,
      axisLine: { lineStyle: { color: '#e5e7eb' } },
      axisLabel: { color: '#6b7280', fontSize: 12 }
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        formatter: '{value}ms',
        color: '#6b7280',
        fontSize: 12
      },
      splitLine: { lineStyle: { color: '#f3f4f6', type: 'dashed' } }
    },
    series: [
      {
        name: '平均响应时间',
        type: 'line',
        smooth: true,
        data: avgTimes,
        itemStyle: { color: '#3B82F6' },
        lineStyle: { width: 2 },
        symbol: 'circle',
        symbolSize: 6
      },
      {
        name: 'P99响应时间',
        type: 'line',
        smooth: true,
        data: p99Times,
        itemStyle: { color: '#F59E0B' },
        lineStyle: { width: 2 },
        symbol: 'circle',
        symbolSize: 6
      }
    ]
  }

  responseTimeChart.setOption(option)
}

// 初始化错误率图表
const initErrorRateChart = (timeline) => {
  if (!errorRateChartRef.value) return

  if (errorRateChart) {
    errorRateChart.dispose()
  }

  errorRateChart = echarts.init(errorRateChartRef.value)

  const times = timeline.map(item => item.time)
  const errorRates = timeline.map(item => (item.error_rate || 0).toFixed(2))

  const option = {
    tooltip: {
      trigger: 'axis',
      formatter: '{b}<br/>错误率: {c}%',
      backgroundColor: 'rgba(255, 255, 255, 0.95)',
      borderColor: '#e5e7eb',
      borderWidth: 1,
      textStyle: { color: '#374151' }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      top: '8%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: times,
      axisLine: { lineStyle: { color: '#e5e7eb' } },
      axisLabel: { color: '#6b7280', fontSize: 12 }
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        formatter: '{value}%',
        color: '#6b7280',
        fontSize: 12
      },
      splitLine: { lineStyle: { color: '#f3f4f6', type: 'dashed' } }
    },
    series: [
      {
        name: '错误率',
        type: 'line',
        smooth: true,
        data: errorRates,
        itemStyle: { color: '#EF4444' },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(239, 68, 68, 0.25)' },
            { offset: 1, color: 'rgba(239, 68, 68, 0.02)' }
          ])
        },
        lineStyle: { width: 3, color: '#EF4444' },
        symbol: 'circle',
        symbolSize: 6
      }
    ]
  }

  errorRateChart.setOption(option)
}

// 初始化资源使用图表
const initResourceChart = (timeline) => {
  if (!resourceChartRef.value) return

  if (resourceChart) {
    resourceChart.dispose()
  }

  resourceChart = echarts.init(resourceChartRef.value)

  const times = timeline.map(item => item.time)
  const cpuData = timeline.map(item => item.cpu_usage || 0)
  const memoryData = timeline.map(item => item.memory_usage || 0)
  const diskData = timeline.map(item => item.disk_usage || 0)

  const option = {
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(255, 255, 255, 0.95)',
      borderColor: '#e5e7eb',
      borderWidth: 1,
      textStyle: { color: '#374151' }
    },
    legend: {
      data: ['CPU', '内存', '磁盘'],
      bottom: 0,
      textStyle: { color: '#6b7280', fontSize: 12 }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '15%',
      top: '8%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: times,
      axisLine: { lineStyle: { color: '#e5e7eb' } },
      axisLabel: { color: '#6b7280', fontSize: 12 }
    },
    yAxis: {
      type: 'value',
      max: 100,
      axisLabel: {
        formatter: '{value}%',
        color: '#6b7280',
        fontSize: 12
      },
      splitLine: { lineStyle: { color: '#f3f4f6', type: 'dashed' } }
    },
    series: [
      {
        name: 'CPU',
        type: 'line',
        smooth: true,
        data: cpuData,
        itemStyle: { color: '#0F766E' },
        lineStyle: { width: 2 },
        symbol: 'circle',
        symbolSize: 6
      },
      {
        name: '内存',
        type: 'line',
        smooth: true,
        data: memoryData,
        itemStyle: { color: '#3B82F6' },
        lineStyle: { width: 2 },
        symbol: 'circle',
        symbolSize: 6
      },
      {
        name: '磁盘',
        type: 'line',
        smooth: true,
        data: diskData,
        itemStyle: { color: '#F59E0B' },
        lineStyle: { width: 2 },
        symbol: 'circle',
        symbolSize: 6
      }
    ]
  }

  resourceChart.setOption(option)
}

// 加载告警列表
const loadAlerts = async () => {
  alertsLoading.value = true
  try {
    const params = {
      page: alertPagination.page,
      page_size: alertPagination.pageSize,
      status: alertFilter.status,
      severity: alertFilter.severity
    }

    const res = await getAlerts(params)
    if (res.success && res.data) {
      alerts.value = res.data.items || []
      alertPagination.total = res.data.total || 0
    }
  } catch (error) {
    console.error('加载告警列表失败:', error)
    ElMessage.error('加载告警列表失败')
  } finally {
    alertsLoading.value = false
  }
}

// 获取告警级别标签类型
const getSeverityTagType = (severity) => {
  const typeMap = {
    critical: 'danger',
    warning: 'warning',
    info: 'info'
  }
  return typeMap[severity] || 'info'
}

// 获取告警级别文本
const getSeverityText = (severity) => {
  const textMap = {
    critical: '严重',
    warning: '警告',
    info: '信息'
  }
  return textMap[severity] || '信息'
}

// 获取告警行样式
const getAlertRowClass = ({ row }) => {
  if (row.status === 'resolved') {
    return 'resolved-row'
  }
  return `severity-${row.severity}`
}

// 格式化时间
const formatTime = (time) => {
  if (!time) return '-'
  return dayjs(time).format('YYYY-MM-DD HH:mm:ss')
}

// 解决告警
const handleResolveAlert = (alert) => {
  currentAlert.value = alert
  resolveForm.resolution = ''
  resolveDialogVisible.value = true
}

// 从详情对话框解决告警
const handleResolveFromDetail = () => {
  alertDetailVisible.value = false
  resolveForm.resolution = ''
  resolveDialogVisible.value = true
}

// 确认解决告警
const confirmResolveAlert = async () => {
  if (!resolveFormRef.value) return

  await resolveFormRef.value.validate(async (valid) => {
    if (!valid) return

    resolving.value = true
    try {
      const res = await resolveAlert(currentAlert.value.id, {
        resolution: resolveForm.resolution
      })

      if (res.success) {
        ElMessage.success('告警已解决')
        resolveDialogVisible.value = false
        loadAlerts()
        loadHealthStatus()
      } else {
        ElMessage.error(res.message || '解决告警失败')
      }
    } catch (error) {
      console.error('解决告警失败:', error)
      ElMessage.error('解决告警失败')
    } finally {
      resolving.value = false
    }
  })
}

// 查看告警详情
const handleViewAlertDetail = (alert) => {
  currentAlert.value = alert
  alertDetailVisible.value = true
}

// 清除已解决告警
const handleClearResolved = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要清除所有已解决的告警吗？',
      '确认操作',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    clearingResolved.value = true
    const res = await clearResolvedAlerts()

    if (res.success) {
      ElMessage.success('已清除所有已解决的告警')
      loadAlerts()
    } else {
      ElMessage.error(res.message || '清除告警失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('清除告警失败:', error)
      ElMessage.error('清除告警失败')
    }
  } finally {
    clearingResolved.value = false
  }
}

// 刷新数据
const handleRefresh = async () => {
  refreshing.value = true
  try {
    await Promise.all([
      loadHealthStatus(),
      loadPerformanceData(),
      loadAlerts()
    ])
    ElMessage.success('数据已刷新')
  } catch (error) {
    console.error('刷新数据失败:', error)
    ElMessage.error('刷新数据失败')
  } finally {
    refreshing.value = false
  }
}

// 窗口大小改变时重绘图表
const handleResize = () => {
  qpsChart?.resize()
  responseTimeChart?.resize()
  errorRateChart?.resize()
  resourceChart?.resize()
}

// 初始化
onMounted(async () => {
  await handleRefresh()
  window.addEventListener('resize', handleResize)
})

// 清理
onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  qpsChart?.dispose()
  responseTimeChart?.dispose()
  errorRateChart?.dispose()
  resourceChart?.dispose()
})
</script>

<style lang="scss" scoped>
.monitoring-dashboard {
  padding: 24px;
  background: var(--bg-secondary);
  min-height: calc(100vh - 60px);
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
  flex-wrap: wrap;
  gap: 16px;

  .header-content {
    .page-title {
      font-size: 28px;
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

  .header-actions {
    display: flex;
    gap: 12px;
  }
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;

  .section-title {
    font-size: 18px;
    font-weight: 600;
    color: var(--text-primary);
    margin: 0;
  }

  .status-icon {
    margin-right: 6px;
  }
}

// 健康状态卡片
.health-section {
  margin-bottom: 24px;
}

.health-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;

  @media (max-width: 1200px) {
    grid-template-columns: repeat(2, 1fr);
  }

  @media (max-width: 768px) {
    grid-template-columns: 1fr;
  }
}

.health-card {
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;

  &:hover {
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  }

  .health-card-header {
    display: flex;
    align-items: center;
    gap: 16px;
    margin-bottom: 16px;
  }

  .health-icon-wrapper {
    width: 48px;
    height: 48px;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 24px;

    &.healthy {
      background: rgba(16, 185, 129, 0.1);
      color: #10B981;
    }

    &.warning {
      background: rgba(245, 158, 11, 0.1);
      color: #F59E0B;
    }

    &.critical {
      background: rgba(239, 68, 68, 0.1);
      color: #EF4444;
    }

    &.success {
      background: rgba(16, 185, 129, 0.1);
      color: #10B981;
    }
  }

  .health-info {
    flex: 1;

    .health-title {
      font-size: 14px;
      font-weight: 600;
      color: var(--text-primary);
      margin: 0 0 6px 0;
    }
  }

  .health-details {
    display: flex;
    flex-direction: column;
    gap: 8px;
    padding-top: 12px;
    border-top: 1px solid var(--border-secondary);

    .detail-item {
      display: flex;
      justify-content: space-between;
      align-items: center;

      .detail-label {
        font-size: 13px;
        color: var(--text-muted);
      }

      .detail-value {
        font-size: 13px;
        font-weight: 500;
        color: var(--text-primary);
      }
    }
  }
}

// 图表区域
.charts-section {
  margin-bottom: 24px;

  .el-row {
    margin: 0 !important;
  }

  .el-col {
    padding: 0 12px;
    margin-bottom: 24px;

    &:first-child {
      padding-left: 0;
    }

    &:last-child {
      padding-right: 0;
    }

    @media (max-width: 992px) {
      padding: 0 !important;
    }
  }
}

.chart-card {
  background: white;
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  height: 100%;

  .chart-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;

    .chart-title {
      font-size: 16px;
      font-weight: 600;
      color: var(--text-primary);
      margin: 0;
    }

    .chart-summary {
      display: flex;
      gap: 20px;

      .summary-item {
        display: flex;
        flex-direction: column;
        align-items: flex-end;

        .summary-label {
          font-size: 12px;
          color: var(--text-muted);
        }

        .summary-value {
          font-size: 18px;
          font-weight: 600;
          color: var(--text-primary);

          &.error {
            color: #EF4444;
          }
        }
      }
    }

    .chart-legend {
      display: flex;
      gap: 16px;

      .legend-item {
        display: flex;
        align-items: center;
        gap: 6px;
        font-size: 13px;
        color: var(--text-muted);

        .legend-dot {
          width: 10px;
          height: 10px;
          border-radius: 50%;
        }

        &.cpu .legend-dot {
          background: #0F766E;
        }

        &.memory .legend-dot {
          background: #3B82F6;
        }

        &.disk .legend-dot {
          background: #F59E0B;
        }
      }
    }
  }

  .chart-container {
    height: 280px;
    width: 100%;
  }
}

// 告警列表
.alerts-section {
  background: white;
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);

  .alert-filters {
    display: flex;
    gap: 12px;
  }
}

.alerts-table-wrapper {
  margin-top: 16px;

  .alert-content {
    .alert-title {
      font-size: 14px;
      font-weight: 500;
      color: var(--text-primary);
      margin-bottom: 4px;
    }

    .alert-message {
      font-size: 13px;
      color: var(--text-muted);
    }
  }

  .alert-source {
    font-size: 13px;
    color: var(--text-muted);
  }

  .alert-time {
    font-size: 13px;
    color: var(--text-muted);
  }

  :deep(.severity-critical) {
    background: rgba(239, 68, 68, 0.05);
  }

  :deep(.severity-warning) {
    background: rgba(245, 158, 11, 0.05);
  }

  :deep(.resolved-row) {
    opacity: 0.6;
  }
}

// 告警详情
.alert-detail {
  .detail-row {
    display: flex;
    align-items: flex-start;
    margin-bottom: 16px;

    &:last-child {
      margin-bottom: 0;
    }

    .detail-label {
      width: 100px;
      flex-shrink: 0;
      font-size: 14px;
      color: var(--text-muted);
      padding-top: 2px;
    }

    .detail-text {
      flex: 1;
      font-size: 14px;
      color: var(--text-primary);
      word-break: break-all;
    }
  }
}

@media screen and (max-width: 768px) {
  .monitoring-dashboard {
    padding: 16px;
  }

  .page-header {
    flex-direction: column;
    align-items: stretch;

    .header-actions {
      flex-direction: column;
    }
  }

  .chart-container {
    height: 240px !important;
  }
}
</style>
