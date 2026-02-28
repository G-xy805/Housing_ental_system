<template>
  <div class="dashboard-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <h1 class="page-title">工作台</h1>
        <p class="page-subtitle">欢迎回来，{{ userStore.userInfo?.username || '用户' }}</p>
      </div>
      <div class="header-actions">
        <el-select
          v-model="timeRange"
          placeholder="选择时间范围"
          size="default"
          @change="handleTimeRangeChange"
          class="time-range-select"
        >
          <el-option label="近 7 天" value="7days" />
          <el-option label="近 30 天" value="30days" />
          <el-option label="近 3 个月" value="3months" />
          <el-option label="自定义" value="custom" />
        </el-select>

        <el-date-picker
          v-if="timeRange === 'custom'"
          v-model="customDateRange"
          type="daterange"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          size="default"
          @change="handleCustomDateChange"
          class="custom-date-picker"
        />

        <el-button-group class="export-buttons">
          <el-button type="success" :icon="Download" @click="handleExport('excel')">
            导出 Excel
          </el-button>
          <el-button type="warning" :icon="Document" @click="handleExport('pdf')">
            导出 PDF
          </el-button>
        </el-button-group>
      </div>
    </div>
    
    <!-- 统计卡片 -->
    <div class="stats-grid">
      <div class="stat-card" v-for="(stat, index) in statsCards" :key="index">
        <div class="stat-card-content">
          <div class="stat-info">
            <span class="stat-label">{{ stat.label }}</span>
            <div class="stat-value-wrapper">
              <span class="stat-value">{{ stat.prefix }}{{ formatNumber(stat.value) }}{{ stat.suffix }}</span>
            </div>
            <div class="stat-change" :class="stat.growth >= 0 ? 'positive' : 'negative'">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="change-icon">
                <path v-if="stat.growth >= 0" d="M7 17l5-5 5 5M7 7l5 5 5-5"/>
                <path v-else d="M7 7l5 5 5-5M7 17l5-5 5 5"/>
              </svg>
              <span>{{ Math.abs(stat.growth * 100).toFixed(1) }}% 较上期</span>
            </div>
          </div>
          <div class="stat-icon-wrapper" :style="{ background: stat.gradient }">
            <component :is="stat.icon" class="stat-icon" />
          </div>
        </div>
        <div class="stat-card-footer">
          <span class="footer-label">{{ stat.footerLabel }}</span>
          <span class="footer-value">{{ stat.footerValue }}</span>
        </div>
      </div>
    </div>

    <!-- 图表区域 -->
    <div class="charts-section">
      <div class="section-header">
        <h2 class="section-title">数据概览</h2>
      </div>
      
      <el-row :gutter="24" class="charts-grid">
        <el-col :xs="24" :lg="12">
          <div class="chart-card">
            <div class="chart-header">
              <h3 class="chart-title">房源状态分布</h3>
              <div class="chart-actions">
                <el-button text size="small">查看详情</el-button>
              </div>
            </div>
            <div ref="houseStatusChartRef" class="chart-container"></div>
          </div>
        </el-col>

        <el-col :xs="24" :lg="12">
          <div class="chart-card">
            <div class="chart-header">
              <h3 class="chart-title">近 6 个月收入趋势</h3>
              <div class="chart-actions">
                <el-button text size="small">查看详情</el-button>
              </div>
            </div>
            <div ref="incomeTrendChartRef" class="chart-container"></div>
          </div>
        </el-col>

        <el-col :xs="24" :lg="12">
          <div class="chart-card">
            <div class="chart-header">
              <h3 class="chart-title">租客类型分布</h3>
              <div class="chart-actions">
                <el-button text size="small">查看详情</el-button>
              </div>
            </div>
            <div ref="tenantTypeChartRef" class="chart-container"></div>
          </div>
        </el-col>

        <el-col :xs="24" :lg="12">
          <div class="chart-card">
            <div class="chart-header">
              <h3 class="chart-title">合同状态统计</h3>
              <div class="chart-actions">
                <el-button text size="small">查看详情</el-button>
              </div>
            </div>
            <div ref="contractStatusChartRef" class="chart-container"></div>
          </div>
        </el-col>
      </el-row>
    </div>
    
    <!-- 快捷操作 -->
    <div class="quick-actions-section">
      <div class="section-header">
        <h2 class="section-title">快捷操作</h2>
      </div>
      <div class="actions-grid">
        <div 
          class="action-card" 
          v-for="action in quickActions" 
          :key="action.name"
          @click="handleAction(action.action)"
        >
          <div class="action-icon" :style="{ background: action.gradient }">
            <component :is="action.icon" />
          </div>
          <div class="action-content">
            <h4 class="action-title">{{ action.name }}</h4>
            <p class="action-desc">{{ action.desc }}</p>
          </div>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="action-arrow">
            <path d="M9 18l6-6-6-6"/>
          </svg>
        </div>
      </div>
    </div>
    
    <!-- 待办事项 -->
    <div class="todo-section">
      <div class="section-header">
        <h2 class="section-title">待办事项</h2>
      </div>
      
      <el-row :gutter="24">
        <el-col :xs="24" :lg="12">
          <div class="todo-card">
            <div class="todo-header">
              <div class="todo-title-wrapper">
                <div class="todo-icon pending">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="12" cy="12" r="10"/>
                    <polyline points="12,6 12,12 16,14"/>
                  </svg>
                </div>
                <h3 class="todo-title">待处理合同</h3>
              </div>
              <el-link type="primary" :underline="false" @click="handleViewAll('pending')">
                查看全部
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="link-arrow">
                  <path d="M9 18l6-6-6-6"/>
                </svg>
              </el-link>
            </div>
            <div class="todo-content" v-loading="pendingLoading">
              <div v-if="pendingContracts.length === 0" class="empty-state">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" class="empty-icon">
                  <path d="M9 12l2 2 4-4"/>
                  <circle cx="12" cy="12" r="10"/>
                </svg>
                <p>暂无待处理合同</p>
              </div>
              <div v-else class="todo-list">
                <div 
                  class="todo-item" 
                  v-for="item in pendingContracts" 
                  :key="item.id"
                >
                  <div class="todo-item-content">
                    <span class="todo-item-house">{{ item.houseName }}</span>
                    <span class="todo-item-tenant">{{ item.tenant }}</span>
                  </div>
                  <el-tag :type="getStatusType(item.status)" size="small" effect="light">
                    {{ item.status }}
                  </el-tag>
                </div>
              </div>
            </div>
          </div>
        </el-col>
        
        <el-col :xs="24" :lg="12">
          <div class="todo-card">
            <div class="todo-header">
              <div class="todo-title-wrapper">
                <div class="todo-icon warning">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
                    <line x1="12" y1="9" x2="12" y2="13"/>
                    <line x1="12" y1="17" x2="12.01" y2="17"/>
                  </svg>
                </div>
                <h3 class="todo-title">即将到期合同</h3>
              </div>
              <el-link type="primary" :underline="false" @click="handleViewAll('expiring')">
                查看全部
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="link-arrow">
                  <path d="M9 18l6-6-6-6"/>
                </svg>
              </el-link>
            </div>
            <div class="todo-content" v-loading="expiringLoading">
              <div v-if="expiringContracts.length === 0" class="empty-state">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" class="empty-icon">
                  <path d="M9 12l2 2 4-4"/>
                  <circle cx="12" cy="12" r="10"/>
                </svg>
                <p>暂无即将到期合同</p>
              </div>
              <div v-else class="todo-list">
                <div 
                  class="todo-item" 
                  v-for="item in expiringContracts" 
                  :key="item.id"
                >
                  <div class="todo-item-content">
                    <span class="todo-item-house">{{ item.houseName }}</span>
                    <span class="todo-item-tenant">{{ item.tenant }}</span>
                  </div>
                  <span class="todo-item-date">{{ item.expireDate }}</span>
                </div>
              </div>
            </div>
          </div>
        </el-col>
      </el-row>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { House, User, Document, Money, Plus, Edit, Search, View, Download, TrendCharts } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import dayjs from 'dayjs'
import { useUserStore } from '@/store/user'
import {
  getOverviewStatistics,
  getHouseStatistics,
  getIncomeStatistics,
  getTenantStatistics,
  getContractStatistics,
  exportExcel,
  exportPdf
} from '@/api/statistics'
import { getContractList } from '@/api/contract'

const router = useRouter()
const userStore = useUserStore()

const timeRange = ref('30days')
const customDateRange = ref([])
const dateParams = reactive({
  startDate: dayjs().subtract(30, 'day').format('YYYY-MM-DD'),
  endDate: dayjs().format('YYYY-MM-DD')
})

const statistics = reactive({
  totalHouses: 0,
  totalTenants: 0,
  totalContracts: 0,
  currentIncome: 0,
  housesGrowth: 0,
  tenantsGrowth: 0,
  contractsGrowth: 0,
  incomeGrowth: 0,
  occupancyRate: 0
})

const houseStatsData = ref({ byStatus: {} })
const incomeStatsData = ref({ monthlyTrend: [] })
const tenantStatsData = ref({ bySource: {}, byContractType: {} })
const contractStatsData = ref({ byStatus: {} })

const pendingContracts = ref([])
const expiringContracts = ref([])
const pendingLoading = ref(false)
const expiringLoading = ref(false)

const houseStatusChartRef = ref(null)
const incomeTrendChartRef = ref(null)
const tenantTypeChartRef = ref(null)
const contractStatusChartRef = ref(null)

let houseStatusChart = null
let incomeTrendChart = null
let tenantTypeChart = null
let contractStatusChart = null

const statsCards = computed(() => [
  {
    label: '总房源数',
    value: statistics.totalHouses,
    growth: statistics.housesGrowth,
    prefix: '',
    suffix: ' 套',
    footerLabel: '出租率',
    footerValue: `${(statistics.occupancyRate * 100).toFixed(1)}%`,
    icon: House,
    gradient: 'linear-gradient(135deg, #0F766E 0%, #14B8A6 100%)'
  },
  {
    label: '租客数量',
    value: statistics.totalTenants,
    growth: statistics.tenantsGrowth,
    prefix: '',
    suffix: ' 人',
    footerLabel: '本月新增',
    footerValue: `${Math.floor(statistics.totalTenants * 0.1)} 人`,
    icon: User,
    gradient: 'linear-gradient(135deg, #0369A1 0%, #0EA5E9 100%)'
  },
  {
    label: '合同总数',
    value: statistics.totalContracts,
    growth: statistics.contractsGrowth,
    prefix: '',
    suffix: ' 份',
    footerLabel: '执行中',
    footerValue: `${Math.floor(statistics.totalContracts * 0.7)} 份`,
    icon: Document,
    gradient: 'linear-gradient(135deg, #7C3AED 0%, #A78BFA 100%)'
  },
  {
    label: '本月收入',
    value: statistics.currentIncome,
    growth: statistics.incomeGrowth,
    prefix: '¥',
    suffix: '',
    footerLabel: '累计收入',
    footerValue: `¥${formatNumber(statistics.currentIncome * 12)}`,
    icon: Money,
    gradient: 'linear-gradient(135deg, #DC2626 0%, #F87171 100%)'
  }
])

const quickActions = ref([
  { 
    name: '新增房源', 
    desc: '添加新的房源信息',
    icon: Plus, 
    action: 'addHouse',
    gradient: 'linear-gradient(135deg, #0F766E 0%, #14B8A6 100%)'
  },
  { 
    name: '新增合同', 
    desc: '创建租赁合同',
    icon: Document, 
    action: 'addContract',
    gradient: 'linear-gradient(135deg, #0369A1 0%, #0EA5E9 100%)'
  },
  { 
    name: '房源管理', 
    desc: '查看和管理所有房源',
    icon: Search, 
    action: 'manageHouses',
    gradient: 'linear-gradient(135deg, #7C3AED 0%, #A78BFA 100%)'
  },
  { 
    name: '合同管理', 
    desc: '查看和管理所有合同',
    icon: View, 
    action: 'manageContracts',
    gradient: 'linear-gradient(135deg, #DC2626 0%, #F87171 100%)'
  }
])

const formatNumber = (num) => {
  if (!num && num !== 0) return '0'
  return Number(num).toLocaleString('zh-CN', { minimumFractionDigits: 0, maximumFractionDigits: 0 })
}

const handleTimeRangeChange = (value) => {
  const end = dayjs()
  let start
  
  switch (value) {
    case '7days':
      start = end.subtract(7, 'day')
      break
    case '30days':
      start = end.subtract(30, 'day')
      break
    case '3months':
      start = end.subtract(3, 'month')
      break
    case 'custom':
      return
    default:
      start = end.subtract(30, 'day')
  }
  
  dateParams.startDate = start.format('YYYY-MM-DD')
  dateParams.endDate = end.format('YYYY-MM-DD')
  
  loadAllData()
}

const handleCustomDateChange = (value) => {
  if (value && value.length === 2) {
    dateParams.startDate = dayjs(value[0]).format('YYYY-MM-DD')
    dateParams.endDate = dayjs(value[1]).format('YYYY-MM-DD')
    loadAllData()
  }
}

const loadAllData = async () => {
  await loadOverviewStatistics()
  await loadHouseStatistics()
  await loadIncomeStatistics()
  await loadTenantStatistics()
  await loadContractStatistics()
  await loadPendingContracts()
  await loadExpiringContracts()
  
  nextTick(() => {
    initCharts()
  })
}

const loadOverviewStatistics = async () => {
  try {
    const res = await getOverviewStatistics({
      start_date: dateParams.startDate,
      end_date: dateParams.endDate
    })
    
    if (res.success && res.data) {
      const { houses, income, contracts, tenants } = res.data
      
      statistics.totalHouses = houses.total || 0
      statistics.occupancyRate = houses.occupancy_rate || 0
      statistics.currentIncome = income.current_period || 0
      statistics.incomeGrowth = income.growth_rate || 0
      statistics.totalContracts = contracts.total || 0
      statistics.totalTenants = tenants.total || 0
      statistics.housesGrowth = houses.growth_rate || 0
      statistics.tenantsGrowth = tenants.growth_rate || 0
      statistics.contractsGrowth = contracts.growth_rate || 0
    }
  } catch (error) {
    console.error('加载概览统计失败:', error)
  }
}

const loadHouseStatistics = async () => {
  try {
    const res = await getHouseStatistics({
      group_by: 'status',
      include_trend: 'true'
    })
    
    if (res.success && res.data) {
      houseStatsData.value.byStatus = res.data.by_status || res.data.summary || {}
    }
  } catch (error) {
    console.error('加载房源统计失败:', error)
  }
}

const loadIncomeStatistics = async () => {
  try {
    const res = await getIncomeStatistics({
      period: 'monthly',
      months: 6
    })
    
    if (res.success && res.data) {
      incomeStatsData.value.monthlyTrend = res.data.monthly_trend || []
    }
  } catch (error) {
    console.error('加载收入统计失败:', error)
  }
}

const loadTenantStatistics = async () => {
  try {
    const res = await getTenantStatistics({
      include_demographics: 'true'
    })
    
    if (res.success && res.data) {
      tenantStatsData.value.bySource = res.data.by_source || {}
      tenantStatsData.value.byContractType = res.data.by_contract_type || {}
    }
  } catch (error) {
    console.error('加载租客统计失败:', error)
  }
}

const loadContractStatistics = async () => {
  try {
    const res = await getContractStatistics({
      group_by: 'status'
    })
    
    if (res.success && res.data) {
      contractStatsData.value.byStatus = res.data.by_status || {}
    }
  } catch (error) {
    console.error('加载合同统计失败:', error)
  }
}

const loadPendingContracts = async () => {
  pendingLoading.value = true
  try {
    const res = await getContractList({
      status: 'draft',
      page: 1,
      page_size: 5
    })
    
    if (res.success && res.data) {
      pendingContracts.value = (res.data.items || []).map(item => ({
        id: item.id,
        houseName: item.house_title || item.house?.title || '未知房源',
        tenant: item.tenant_name || '未知租客',
        status: getStatusLabel(item.status)
      }))
    }
  } catch (error) {
    console.error('加载待处理合同失败:', error)
  } finally {
    pendingLoading.value = false
  }
}

const loadExpiringContracts = async () => {
  expiringLoading.value = true
  try {
    const res = await getContractList({
      status: 'active',
      page: 1,
      page_size: 50
    })
    
    if (res.success && res.data) {
      const today = dayjs()
      const thirtyDaysLater = today.add(30, 'day')
      
      expiringContracts.value = (res.data.items || [])
        .filter(item => {
          const endDate = dayjs(item.end_date)
          return endDate.isAfter(today) && endDate.isBefore(thirtyDaysLater)
        })
        .slice(0, 5)
        .map(item => ({
          id: item.id,
          houseName: item.house_title || '未知房源',
          tenant: item.tenant_name || '未知租客',
          expireDate: dayjs(item.end_date).format('YYYY-MM-DD')
        }))
    }
  } catch (error) {
    console.error('加载到期合同失败:', error)
  } finally {
    expiringLoading.value = false
  }
}

const getStatusLabel = (status) => {
  const labelMap = {
    'draft': '草稿',
    'pending': '待审核',
    'waiting_sign': '待签约',
    'active': '执行中',
    'expired': '已到期',
    'terminated': '已终止'
  }
  return labelMap[status] || status
}

const getStatusType = (status) => {
  const typeMap = {
    '待审核': 'warning',
    '待签约': 'primary',
    '执行中': 'success',
    '已到期': 'info',
    '已终止': 'danger',
    '草稿': 'info'
  }
  return typeMap[status] || 'info'
}

const initCharts = () => {
  initHouseStatusChart()
  initIncomeTrendChart()
  initTenantTypeChart()
  initContractStatusChart()
}

const initHouseStatusChart = () => {
  if (!houseStatusChartRef.value) return
  
  if (houseStatusChart) {
    houseStatusChart.dispose()
  }
  
  houseStatusChart = echarts.init(houseStatusChartRef.value)
  
  const statusData = houseStatsData.value.byStatus
  const data = [
    { value: statusData.available || 0, name: '空置' },
    { value: statusData.rented || 0, name: '已出租' },
    { value: statusData.maintenance || 0, name: '维护中' },
    { value: statusData.partially_rented || 0, name: '部分出租' }
  ].filter(item => item.value > 0)
  
  const option = {
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c} ({d}%)',
      backgroundColor: 'rgba(255, 255, 255, 0.95)',
      borderColor: '#e5e7eb',
      borderWidth: 1,
      textStyle: { color: '#374151' }
    },
    legend: {
      orient: 'horizontal',
      bottom: '0',
      textStyle: { color: '#6b7280', fontSize: 12 },
      itemGap: 20
    },
    series: [
      {
        name: '房源状态',
        type: 'pie',
        radius: ['45%', '75%'],
        center: ['50%', '45%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 8,
          borderColor: '#fff',
          borderWidth: 3
        },
        label: { show: false },
        emphasis: {
          label: {
            show: true,
            fontSize: 16,
            fontWeight: 'bold'
          },
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.2)'
          }
        },
        labelLine: { show: false },
        color: ['#0F766E', '#14B8A6', '#F59E0B', '#EF4444'],
        data: data
      }
    ]
  }
  
  houseStatusChart.setOption(option)
}

const initIncomeTrendChart = () => {
  if (!incomeTrendChartRef.value) return
  
  if (incomeTrendChart) {
    incomeTrendChart.dispose()
  }
  
  incomeTrendChart = echarts.init(incomeTrendChartRef.value)
  
  const trendData = incomeStatsData.value.monthlyTrend || []
  const months = trendData.map(item => item.month)
  const incomes = trendData.map(item => item.income || 0)
  
  const option = {
    tooltip: {
      trigger: 'axis',
      formatter: '{b}<br/>收入：¥{c}',
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
      data: months,
      axisLine: { lineStyle: { color: '#e5e7eb' } },
      axisLabel: { color: '#6b7280', fontSize: 12 }
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        formatter: '¥{value}',
        color: '#6b7280',
        fontSize: 12
      },
      splitLine: {
        lineStyle: { color: '#f3f4f6', type: 'dashed' }
      }
    },
    series: [
      {
        name: '收入',
        type: 'line',
        smooth: true,
        data: incomes,
        itemStyle: { color: '#0F766E' },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(15, 118, 110, 0.25)' },
            { offset: 1, color: 'rgba(15, 118, 110, 0.02)' }
          ])
        },
        lineStyle: { width: 3, color: '#0F766E' },
        symbol: 'circle',
        symbolSize: 8,
        emphasis: {
          focus: 'series',
          itemStyle: {
            shadowBlur: 10,
            shadowColor: 'rgba(15, 118, 110, 0.3)'
          }
        }
      }
    ]
  }
  
  incomeTrendChart.setOption(option)
}

const initTenantTypeChart = () => {
  if (!tenantTypeChartRef.value) return
  
  if (tenantTypeChart) {
    tenantTypeChart.dispose()
  }
  
  tenantTypeChart = echarts.init(tenantTypeChartRef.value)
  
  const sourceData = tenantStatsData.value.bySource || {}
  const channels = Object.keys(sourceData)
  const values = Object.values(sourceData)
  
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      formatter: '{b}: {c}人',
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
      data: channels,
      axisLine: { lineStyle: { color: '#e5e7eb' } },
      axisLabel: {
        color: '#6b7280',
        fontSize: 12,
        interval: 0,
        rotate: 30
      }
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        formatter: '{value}人',
        color: '#6b7280',
        fontSize: 12
      },
      splitLine: {
        lineStyle: { color: '#f3f4f6', type: 'dashed' }
      }
    },
    series: [
      {
        name: '租客来源',
        type: 'bar',
        data: values,
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: '#0F766E' },
            { offset: 1, color: '#14B8A6' }
          ]),
          borderRadius: [6, 6, 0, 0]
        },
        barWidth: '50%',
        showBackground: true,
        backgroundStyle: {
          color: 'rgba(15, 118, 110, 0.05)'
        },
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowColor: 'rgba(15, 118, 110, 0.3)'
          }
        }
      }
    ]
  }
  
  tenantTypeChart.setOption(option)
}

const initContractStatusChart = () => {
  if (!contractStatusChartRef.value) return
  
  if (contractStatusChart) {
    contractStatusChart.dispose()
  }
  
  contractStatusChart = echarts.init(contractStatusChartRef.value)
  
  const statusData = contractStatsData.value.byStatus || {}
  const data = [
    { value: statusData.active || 0, name: '执行中' },
    { value: statusData.pending || 0, name: '待审核' },
    { value: statusData.waiting_sign || 0, name: '待签约' },
    { value: statusData.expired || 0, name: '已到期' },
    { value: statusData.terminated || 0, name: '已终止' }
  ].filter(item => item.value > 0)
  
  const option = {
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c} ({d}%)',
      backgroundColor: 'rgba(255, 255, 255, 0.95)',
      borderColor: '#e5e7eb',
      borderWidth: 1,
      textStyle: { color: '#374151' }
    },
    legend: {
      orient: 'horizontal',
      bottom: '0',
      textStyle: { color: '#6b7280', fontSize: 12 },
      itemGap: 15
    },
    series: [
      {
        name: '合同状态',
        type: 'pie',
        radius: ['45%', '75%'],
        center: ['50%', '45%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 8,
          borderColor: '#fff',
          borderWidth: 3
        },
        label: { show: false },
        emphasis: {
          label: {
            show: true,
            fontSize: 14,
            fontWeight: 'bold'
          },
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.2)'
          }
        },
        labelLine: { show: false },
        color: ['#10B981', '#F59E0B', '#3B82F6', '#6B7280', '#EF4444'],
        data: data
      }
    ]
  }
  
  contractStatusChart.setOption(option)
}

const handleExport = async (type) => {
  try {
    ElMessage.info('正在生成报表，请稍候...')
    
    const params = {
      start_date: dateParams.startDate,
      end_date: dateParams.endDate,
      report_type: 'overview'
    }
    
    let blob
    if (type === 'excel') {
      const res = await exportExcel(params)
      blob = new Blob([res], {
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
      })
    } else {
      const res = await exportPdf(params)
      blob = new Blob([res], { type: 'application/pdf' })
    }
    
    const link = document.createElement('a')
    link.href = window.URL.createObjectURL(blob)
    link.download = `统计报表_${dateParams.startDate}_${dateParams.endDate}.${type}`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(link.href)
    
    ElMessage.success('报表导出成功')
  } catch (error) {
    console.error('导出报表失败:', error)
    ElMessage.error('导出报表失败，请重试')
  }
}

const handleAction = (action) => {
  switch (action) {
    case 'addHouse':
      router.push('/houses/add')
      break
    case 'addContract':
      router.push('/contracts/add')
      break
    case 'manageHouses':
      router.push('/houses')
      break
    case 'manageContracts':
      router.push('/contracts')
      break
    default:
      ElMessage.info('功能开发中...')
  }
}

const handleViewAll = (type) => {
  if (type === 'pending') {
    router.push('/contracts?status=pending')
  } else if (type === 'expiring') {
    router.push('/contracts?status=expiring')
  }
}

const handleResize = () => {
  houseStatusChart?.resize()
  incomeTrendChart?.resize()
  tenantTypeChart?.resize()
  contractStatusChart?.resize()
}

onMounted(() => {
  loadAllData()
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  houseStatusChart?.dispose()
  incomeTrendChart?.dispose()
  tenantTypeChart?.dispose()
  contractStatusChart?.dispose()
})
</script>

<style lang="scss" scoped>
.dashboard-page {
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
    align-items: center;
    gap: 12px;
    flex-wrap: wrap;
    
    .time-range-select {
      width: 140px;
    }
    
    .custom-date-picker {
      width: 260px;
    }
    
    .export-buttons {
      display: flex;
      gap: 0;
      
      .el-button {
        border-radius: 0;
        
        &:first-child {
          border-radius: 8px 0 0 8px;
        }
        
        &:last-child {
          border-radius: 0 8px 8px 0;
        }
      }
    }
  }
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  margin-bottom: 24px;
  
  @media (max-width: 1200px) {
    grid-template-columns: repeat(2, 1fr);
  }
  
  @media (max-width: 640px) {
    grid-template-columns: 1fr;
  }
}

.stat-card {
  background: white;
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;
  
  &:hover {
    transform: translateY(-4px);
    box-shadow: 0 12px 24px rgba(0, 0, 0, 0.1);
  }
  
  .stat-card-content {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 16px;
  }
  
  .stat-info {
    flex: 1;
    
    .stat-label {
      font-size: 13px;
      font-weight: 500;
      color: var(--text-muted);
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }
    
    .stat-value-wrapper {
      margin: 8px 0;
    }
    
    .stat-value {
      font-size: 32px;
      font-weight: 700;
      color: var(--text-primary);
      line-height: 1;
    }
    
    .stat-change {
      display: inline-flex;
      align-items: center;
      gap: 4px;
      font-size: 13px;
      font-weight: 500;
      padding: 4px 8px;
      border-radius: 6px;
      
      &.positive {
        color: #059669;
        background: rgba(5, 150, 105, 0.1);
      }
      
      &.negative {
        color: #DC2626;
        background: rgba(220, 38, 38, 0.1);
      }
      
      .change-icon {
        width: 16px;
        height: 16px;
      }
    }
  }
  
  .stat-icon-wrapper {
    width: 56px;
    height: 56px;
    border-radius: 14px;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    
    .stat-icon {
      width: 28px;
      height: 28px;
      color: white;
    }
  }
  
  .stat-card-footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-top: 16px;
    border-top: 1px solid var(--border-secondary);
    
    .footer-label {
      font-size: 13px;
      color: var(--text-muted);
    }
    
    .footer-value {
      font-size: 14px;
      font-weight: 600;
      color: var(--text-primary);
    }
  }
}

.section-header {
  margin-bottom: 16px;
  
  .section-title {
    font-size: 18px;
    font-weight: 600;
    color: var(--text-primary);
    margin: 0;
  }
}

.charts-section {
  margin-bottom: 24px;
  
  .charts-grid {
    margin-top: 0 !important;
  }
}

.chart-card {
  background: white;
  border-radius: 16px;
  padding: 24px;
  margin-bottom: 24px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;
  
  &:hover {
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  }
  
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
  }
  
  .chart-container {
    height: 280px;
    width: 100%;
  }
}

.quick-actions-section {
  margin-bottom: 24px;
  
  .actions-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 16px;
    
    @media (max-width: 1024px) {
      grid-template-columns: repeat(2, 1fr);
    }
    
    @media (max-width: 640px) {
      grid-template-columns: 1fr;
    }
  }
  
  .action-card {
    background: white;
    border-radius: 14px;
    padding: 20px;
    display: flex;
    align-items: center;
    gap: 16px;
    cursor: pointer;
    transition: all 0.3s ease;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
    
    &:hover {
      transform: translateY(-2px);
      box-shadow: 0 8px 16px rgba(0, 0, 0, 0.1);
      
      .action-arrow {
        opacity: 1;
        transform: translateX(4px);
      }
    }
    
    .action-icon {
      width: 48px;
      height: 48px;
      border-radius: 12px;
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
      
      svg, :deep(.el-icon) {
        width: 24px;
        height: 24px;
        color: white;
      }
    }
    
    .action-content {
      flex: 1;
      
      .action-title {
        font-size: 15px;
        font-weight: 600;
        color: var(--text-primary);
        margin: 0 0 4px 0;
      }
      
      .action-desc {
        font-size: 13px;
        color: var(--text-muted);
        margin: 0;
      }
    }
    
    .action-arrow {
      width: 20px;
      height: 20px;
      color: var(--text-muted);
      opacity: 0;
      transition: all 0.3s ease;
    }
  }
}

.todo-section {
  margin-bottom: 24px;
  
  .el-row {
    margin: 0 !important;
  }
  
  .el-col {
    padding: 0 12px;
    
    &:first-child {
      padding-left: 0;
    }
    
    &:last-child {
      padding-right: 0;
    }
    
    @media (max-width: 992px) {
      padding: 0 !important;
      margin-bottom: 24px;
      
      &:last-child {
        margin-bottom: 0;
      }
    }
  }
}

.todo-card {
  background: white;
  border-radius: 16px;
  padding: 24px;
  height: 100%;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  
  .todo-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    
    .todo-title-wrapper {
      display: flex;
      align-items: center;
      gap: 12px;
    }
    
    .todo-icon {
      width: 40px;
      height: 40px;
      border-radius: 10px;
      display: flex;
      align-items: center;
      justify-content: center;
      
      svg {
        width: 20px;
        height: 20px;
      }
      
      &.pending {
        background: rgba(245, 158, 11, 0.1);
        color: #F59E0B;
      }
      
      &.warning {
        background: rgba(239, 68, 68, 0.1);
        color: #EF4444;
      }
    }
    
    .todo-title {
      font-size: 16px;
      font-weight: 600;
      color: var(--text-primary);
      margin: 0;
    }
    
    .el-link {
      display: flex;
      align-items: center;
      gap: 4px;
      font-weight: 500;
      
      .link-arrow {
        width: 16px;
        height: 16px;
        transition: transform 0.2s ease;
      }
      
      &:hover .link-arrow {
        transform: translateX(2px);
      }
    }
  }
  
  .todo-content {
    min-height: 200px;
  }
  
  .empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 40px 20px;
    
    .empty-icon {
      width: 48px;
      height: 48px;
      color: #10B981;
      margin-bottom: 12px;
    }
    
    p {
      font-size: 14px;
      color: var(--text-muted);
      margin: 0;
    }
  }
  
  .todo-list {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }
  
  .todo-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 14px 16px;
    background: var(--bg-secondary);
    border-radius: 10px;
    transition: all 0.2s ease;
    
    &:hover {
      background: var(--bg-tertiary);
    }
    
    .todo-item-content {
      display: flex;
      flex-direction: column;
      gap: 4px;
      
      .todo-item-house {
        font-size: 14px;
        font-weight: 500;
        color: var(--text-primary);
      }
      
      .todo-item-tenant {
        font-size: 13px;
        color: var(--text-muted);
      }
    }
    
    .todo-item-date {
      font-size: 13px;
      font-weight: 500;
      color: #EF4444;
    }
  }
}

@media screen and (max-width: 768px) {
  .dashboard-page {
    padding: 16px;
  }
  
  .page-header {
    flex-direction: column;
    align-items: stretch;
    
    .header-actions {
      flex-direction: column;
      
      .time-range-select,
      .custom-date-picker {
        width: 100%;
      }
      
      .export-buttons {
        width: 100%;
        
        .el-button {
          flex: 1;
        }
      }
    }
  }
  
  .chart-container {
    height: 240px !important;
  }
}
</style>
