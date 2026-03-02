<template>
  <el-dialog
    v-model="dialogVisible"
    title="承包合同详情"
    width="900px"
    destroy-on-close
    :close-on-click-modal="false"
  >
    <div v-loading="loading" element-loading-text="加载中...">
      <!-- 到期提醒 -->
      <el-alert
        v-if="expiryInfo.showAlert"
        :title="expiryInfo.title"
        :type="expiryInfo.type"
        :closable="false"
        show-icon
        class="expiry-alert"
      >
        <template #default>
          <span>{{ expiryInfo.message }}</span>
        </template>
      </el-alert>

      <!-- 合同基本信息 -->
      <el-descriptions title="合同基本信息" :column="2" border>
        <el-descriptions-item label="合同编号" :span="2">
          {{ contractData.contract_no || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="合同标题" :span="2">
          {{ contractData.contract_title || '-' }}
        </el-descriptions-item>
        
        <!-- 房东信息 -->
        <el-descriptions-item label="房东姓名">
          <el-icon><User /></el-icon>
          {{ contractData.landlord_name || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="联系电话">
          <el-icon><Phone /></el-icon>
          {{ contractData.landlord_phone || '-' }}
        </el-descriptions-item>
        
        <!-- 金额信息 -->
        <el-descriptions-item label="合同金额">
          <span class="money-text">¥{{ formatMoney(contractData.contract_amount) }}</span>
        </el-descriptions-item>
        <el-descriptions-item label="服务费率">
          {{ contractData.service_rate || 0 }}%
        </el-descriptions-item>
        <el-descriptions-item label="最低服务费">
          <span class="money-text">¥{{ formatMoney(contractData.min_service_fee) }}</span>
        </el-descriptions-item>
        <el-descriptions-item label="付款周期">
          {{ getPaymentCycleText(contractData.payment_cycle) }}
        </el-descriptions-item>
        
        <!-- 日期信息 -->
        <el-descriptions-item label="开始日期">
          {{ formatDate(contractData.start_date) }}
        </el-descriptions-item>
        <el-descriptions-item label="结束日期">
          {{ formatDate(contractData.end_date) }}
        </el-descriptions-item>
        <el-descriptions-item label="合同期限">
          {{ contractDuration }}
        </el-descriptions-item>
        <el-descriptions-item label="服务费金额">
          <span class="money-text">¥{{ formatMoney(calculatedServiceFee) }}</span>
        </el-descriptions-item>
        
        <!-- 状态和描述 -->
        <el-descriptions-item label="合同状态">
          <el-tag :type="getStatusType(contractData.status)" size="large">
            {{ getStatusText(contractData.status) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="创建日期">
          {{ formatDate(contractData.created_at) }}
        </el-descriptions-item>
        <el-descriptions-item label="描述" :span="2">
          <p class="description-text">{{ contractData.description || '暂无描述' }}</p>
        </el-descriptions-item>
        <el-descriptions-item label="备注" :span="2">
          <p class="remark-text">{{ contractData.remark || '暂无备注' }}</p>
        </el-descriptions-item>
      </el-descriptions>

      <!-- 关联房源列表 -->
      <el-card class="houses-card" shadow="never">
        <template #header>
          <div class="card-header">
            <span class="card-title">
              <el-icon><House /></el-icon>
              关联房源列表
            </span>
            <el-tag type="info" size="small">
              共 {{ houseList.length }} 套
            </el-tag>
          </div>
        </template>
        
        <el-table
          :data="houseList"
          style="width: 100%"
          :max-height="400"
          @row-click="handleHouseClick"
        >
          <el-table-column prop="title" label="房源标题" min-width="180" show-overflow-tooltip />
          <el-table-column prop="address" label="地址" min-width="200" show-overflow-tooltip />
          <el-table-column label="类型" width="80">
            <template #default="scope">
              <el-tag size="small" :type="getTypeTag(scope.row.type)">
                {{ getTypeText(scope.row.type) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="租金" width="100">
            <template #default="scope">
              <span class="rent-price">¥{{ scope.row.rent_price }}</span>
              <span class="unit">/月</span>
            </template>
          </el-table-column>
          <el-table-column label="状态" width="80">
            <template #default="scope">
              <el-tag size="small" :type="getStatusTag(scope.row.status)">
                {{ getStatusText(scope.row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="100" fixed="right">
            <template #default="scope">
              <el-button
                link
                type="primary"
                size="small"
                @click.stop="handleViewHouse(scope.row)"
              >
                查看详情
              </el-button>
            </template>
          </el-table-column>
        </el-table>
        
        <el-empty v-if="houseList.length === 0" description="暂无关联房源" />
      </el-card>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="dialogVisible = false">关闭</el-button>
        <el-button
          type="primary"
          @click="handleEdit"
          v-if="hasPermission('edit') && contractData.status === 'draft'"
        >
          <el-icon><Edit /></el-icon>
          编辑
        </el-button>
      </div>
    </template>
  </el-dialog>

  <!-- 房源详情对话框 -->
  <el-dialog
    v-model="houseDetailVisible"
    title="房源详情"
    width="800px"
    destroy-on-close
  >
    <el-descriptions :column="2" border>
      <el-descriptions-item label="房源标题" :span="2">
        {{ currentHouse.title || '-' }}
      </el-descriptions-item>
      <el-descriptions-item label="房源地址" :span="2">
        {{ currentHouse.address || '-' }}
      </el-descriptions-item>
      <el-descriptions-item label="房源类型">
        <el-tag :type="getTypeTag(currentHouse.type)">
          {{ getTypeText(currentHouse.type) }}
        </el-tag>
      </el-descriptions-item>
      <el-descriptions-item label="租金">
        <span class="rent-price">¥{{ currentHouse.rent_price }}</span>
        <span class="unit">/月</span>
      </el-descriptions-item>
      <el-descriptions-item label="房源状态">
        <el-tag :type="getStatusTag(currentHouse.status)">
          {{ getStatusText(currentHouse.status) }}
        </el-tag>
      </el-descriptions-item>
      <el-descriptions-item label="建筑面积">
        {{ currentHouse.building_area || '-' }}㎡
      </el-descriptions-item>
      <el-descriptions-item label="楼层">
        {{ currentHouse.floor || '-' }} / {{ currentHouse.total_floors || '-' }}层
      </el-descriptions-item>
      <el-descriptions-item label="朝向">
        {{ currentHouse.orientation || '-' }}
      </el-descriptions-item>
      <el-descriptions-item label="装修情况">
        {{ currentHouse.decoration || '-' }}
      </el-descriptions-item>
      <el-descriptions-item label="描述" :span="2">
        <p class="description-text">{{ currentHouse.description || '暂无描述' }}</p>
      </el-descriptions-item>
    </el-descriptions>
    <template #footer>
      <el-button @click="houseDetailVisible = false">关闭</el-button>
      <el-button type="primary" @click="handleGoToHouseDetail">
        查看详情
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, reactive, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  User,
  Phone,
  House,
  Edit
} from '@element-plus/icons-vue'
import { getLandlordContractDetail } from '@/api/landlordContract'
import { useUserStore } from '@/store/user'
import dayjs from 'dayjs'
import duration from 'dayjs/plugin/duration'
import relativeTime from 'dayjs/plugin/relativeTime'
import 'dayjs/locale/zh-cn'

// 扩展 dayjs 插件
dayjs.extend(duration)
dayjs.extend(relativeTime)
dayjs.locale('zh-cn')

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  contractId: {
    type: [Number, String],
    default: null
  }
})

const emit = defineEmits(['update:modelValue', 'edit', 'view-house'])

const router = useRouter()
const userStore = useUserStore()

const dialogVisible = ref(false)
const loading = ref(false)
const contractData = ref({})
const houseList = ref([])
const houseDetailVisible = ref(false)
const currentHouse = ref({})

// 到期提醒信息
const expiryInfo = computed(() => {
  const today = dayjs()
  const endDate = dayjs(contractData.value.end_date)
  const diffDays = endDate.diff(today, 'day')
  
  if (diffDays < 0) {
    return {
      showAlert: true,
      title: '合同已过期',
      type: 'error',
      message: `该合同已于 ${formatDate(contractData.value.end_date)} 过期，已过 ${Math.abs(diffDays)} 天`
    }
  } else if (diffDays <= 30) {
    return {
      showAlert: true,
      title: '合同即将到期',
      type: 'warning',
      message: `距离合同到期还有 ${diffDays} 天，请及时处理`
    }
  } else {
    return {
      showAlert: false,
      title: '',
      type: 'info',
      message: ''
    }
  }
})

// 合同期限（月数）
const contractDuration = computed(() => {
  if (!contractData.value.start_date || !contractData.value.end_date) return '-'
  const start = dayjs(contractData.value.start_date)
  const end = dayjs(contractData.value.end_date)
  const months = end.diff(start, 'month')
  const days = end.diff(start.add(months, 'month'), 'day')
  return `${months}个月${days > 0 ? days + '天' : ''}`
})

// 服务费金额计算
const calculatedServiceFee = computed(() => {
  const amount = parseFloat(contractData.value.contract_amount) || 0
  const rate = parseFloat(contractData.value.service_rate) || 0
  const minFee = parseFloat(contractData.value.min_service_fee) || 0
  const calculatedFee = amount * (rate / 100)
  return Math.max(calculatedFee, minFee)
})

// 监听对话框显示
watch(() => props.modelValue, (val) => {
  dialogVisible.value = val
  if (val && props.contractId) {
    loadContractDetail()
  }
})

watch(dialogVisible, (val) => {
  emit('update:modelValue', val)
})

// 加载合同详情
const loadContractDetail = async () => {
  if (!props.contractId) return
  
  loading.value = true
  try {
    const res = await getLandlordContractDetail(props.contractId)
    contractData.value = res.data || {}
    houseList.value = res.data?.houses || []
  } catch (error) {
    console.error('加载合同详情失败:', error)
    ElMessage.error('加载合同详情失败')
  } finally {
    loading.value = false
  }
}

// 格式化金额
const formatMoney = (value) => {
  if (!value) return '0.00'
  return parseFloat(value).toFixed(2)
}

// 格式化日期
const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  return dayjs(dateStr).format('YYYY-MM-DD')
}

// 获取付款周期文本
const getPaymentCycleText = (cycle) => {
  const texts = {
    'monthly': '月付',
    'quarterly': '季付',
    'semiannual': '半年付',
    'annual': '年付',
    'custom': '自定义'
  }
  return texts[cycle] || cycle || '-'
}

// 获取状态类型
const getStatusType = (status) => {
  const types = {
    'draft': 'info',
    'active': 'success',
    'expired': 'warning',
    'terminated': 'danger',
    'renewed': 'success'
  }
  return types[status] || 'info'
}

// 获取状态文本
const getStatusText = (status) => {
  const texts = {
    'draft': '草稿',
    'active': '生效中',
    'expired': '已过期',
    'terminated': '已终止',
    'renewed': '已续签'
  }
  return texts[status] || status || '-'
}

// 获取房源类型标签
const getTypeTag = (type) => {
  const tags = {
    'entire': 'success',
    'room': 'warning',
    'shared': 'info'
  }
  return tags[type] || 'info'
}

// 获取房源类型文本
const getTypeText = (type) => {
  const texts = {
    'entire': '整租',
    'room': '单间',
    'shared': '合租'
  }
  return texts[type] || type || '-'
}

// 获取房源状态标签
const getStatusTag = (status) => {
  const tags = {
    'available': 'success',
    'occupied': 'warning',
    'maintenance': 'info'
  }
  return tags[status] || 'info'
}

// 房源行点击
const handleHouseClick = (row) => {
  currentHouse.value = row
}

// 查看房源详情
const handleViewHouse = (row) => {
  currentHouse.value = row
  houseDetailVisible.value = true
}

// 编辑合同
const handleEdit = () => {
  emit('edit', contractData.value)
}

// 检查权限
const hasPermission = (action) => {
  return userStore.hasPermission(`landlord_contract_${action}`)
}

// 跳转到房源详情页面
const handleGoToHouseDetail = () => {
  router.push(`/houses/${currentHouse.id}`)
  houseDetailVisible.value = false
}
</script>

<style lang="scss" scoped>
.expiry-alert {
  margin-bottom: 20px;
}

.money-text {
  color: #f56c6c;
  font-weight: bold;
  font-size: 16px;
}

.description-text,
.remark-text {
  margin: 0;
  color: #606266;
  line-height: 1.6;
  max-height: 200px;
  overflow-y: auto;
}

.houses-card {
  margin-top: 20px;

  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;

    .card-title {
      display: flex;
      align-items: center;
      gap: 8px;
      font-weight: bold;
      font-size: 16px;
      color: #303133;

      .el-icon {
        color: #409EFF;
      }
    }
  }

  .rent-price {
    color: #f56c6c;
    font-weight: bold;
    font-size: 15px;
  }

  .unit {
    color: #909399;
    font-size: 12px;
    margin-left: 4px;
  }
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
</style>