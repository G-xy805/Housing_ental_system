<template>
  <div class="landlord-contract-list-page">
    <div class="page-header">
      <h2>房东合同管理</h2>
      <el-button type="primary" @click="handleAdd" v-if="hasPermission('create')">
        <el-icon><Plus /></el-icon>
        新建合同
      </el-button>
    </div>

    <!-- 即将到期提醒 -->
    <el-alert
      v-if="expiringContracts.length > 0"
      title="即将到期合同提醒"
      type="warning"
      :closable="false"
      show-icon
      class="expiring-alert"
    >
      <template #default>
        <div class="expiring-contracts">
          <el-tag
            v-for="contract in expiringContracts"
            :key="contract.id"
            type="warning"
            size="small"
            class="expiring-tag"
            @click="handleView(contract)"
          >
            {{ contract.contract_no }} - {{ contract.landlord?.name || '-' }} - 剩余 {{ contract.days_until_expiry }} 天到期
          </el-tag>
        </div>
      </template>
    </el-alert>

    <!-- 搜索筛选区域 -->
    <el-card class="search-card" shadow="hover">
      <el-form :inline="true" :model="searchForm" class="search-form">
        <el-form-item label="关键词">
          <el-input
            v-model="searchForm.keyword"
            placeholder="合同编号/房东姓名"
            clearable
            style="width: 200px"
            @keyup.enter="handleSearch"
          />
        </el-form-item>
        <el-form-item label="合同状态">
          <el-select
            v-model="searchForm.status"
            placeholder="全部"
            clearable
            style="width: 120px"
          >
            <el-option label="全部" value="" />
            <el-option label="草稿" value="draft" />
            <el-option label="生效中" value="active" />
            <el-option label="已过期" value="expired" />
            <el-option label="已终止" value="terminated" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">
            <el-icon><Search /></el-icon>
            查询
          </el-button>
          <el-button @click="handleReset">
            <el-icon><Refresh /></el-icon>
            重置
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 合同列表表格 -->
    <el-card class="table-card" shadow="hover">
      <el-table
        :data="contractList"
        style="width: 100%"
        v-loading="loading"
        @sort-change="handleSortChange"
      >
        <el-table-column prop="contract_no" label="合同编号" min-width="160" sortable />
        <el-table-column prop="title" label="合同标题" min-width="140" show-overflow-tooltip />
        <el-table-column label="房东姓名" width="90">
          <template #default="scope">
            {{ scope.row.landlord?.name || '-' }}
          </template>
        </el-table-column>
        <el-table-column label="房源数" width="70" align="center">
          <template #default="scope">
            {{ scope.row.house_ids?.length || 0 }}
          </template>
        </el-table-column>
        <el-table-column prop="contract_amount" label="合同金额 (元)" width="110" sortable>
          <template #default="scope">
            <span>¥{{ scope.row.contract_amount }}</span>
          </template>
        </el-table-column>
        <el-table-column label="合同期限" min-width="200">
          <template #default="scope">
            <div class="contract-period">
              <span>{{ formatChineseDate(scope.row.start_date) }}</span>
              <span class="separator">至</span>
              <span>{{ formatChineseDate(scope.row.end_date) }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="90">
          <template #default="scope">
            <el-tag :type="getStatusType(scope.row.status)">
              {{ getStatusText(scope.row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="320" fixed="right">
          <template #default="scope">
            <el-button link type="primary" @click="handleView(scope.row)">
              <el-icon><View /></el-icon>
              查看
            </el-button>
            <el-button
              link
              type="primary"
              @click="handleEdit(scope.row)"
              v-if="scope.row.status === 'draft' && hasPermission('edit')"
            >
              <el-icon><Edit /></el-icon>
              编辑
            </el-button>
            <el-button
              link
              type="success"
              @click="handleActivate(scope.row)"
              v-if="scope.row.status === 'draft' && hasPermission('edit')"
            >
              <el-icon><CircleCheck /></el-icon>
              激活
            </el-button>
            <el-button
              link
              type="warning"
              @click="handleTerminate(scope.row)"
              v-if="scope.row.status === 'active' && hasPermission('edit')"
            >
              <el-icon><CircleClose /></el-icon>
              终止
            </el-button>
            <el-button
              link
              type="success"
              @click="handleRenew(scope.row)"
              v-if="(scope.row.status === 'active' || scope.row.status === 'expired') && hasPermission('edit')"
            >
              <el-icon><RefreshRight /></el-icon>
              续签
            </el-button>
            <el-button
              link
              type="danger"
              @click="handleDelete(scope.row)"
              v-if="hasPermission('delete')"
            >
              <el-icon><Delete /></el-icon>
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      <template #empty>
        <el-empty description="暂无房东合同数据">
          <el-button type="primary" @click="handleAdd" v-if="hasPermission('create')">
            新建合同
          </el-button>
        </el-empty>
      </template>
    </el-card>

    <!-- 分页 -->
    <el-card class="pagination-card" v-if="contractList.length > 0">
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

    <!-- 合同详情对话框 -->
    <el-dialog
      v-model="detailVisible"
      title="合同详情"
      width="800px"
      destroy-on-close
    >
      <el-descriptions :column="2" border>
        <el-descriptions-item label="合同编号">
          {{ currentContract.contract_no }}
        </el-descriptions-item>
        <el-descriptions-item label="合同状态">
          <el-tag :type="getStatusType(currentContract.status)">
            {{ getStatusText(currentContract.status) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="合同标题">
          {{ currentContract.title }}
        </el-descriptions-item>
        <el-descriptions-item label="房东姓名">
          {{ currentContract.landlord?.name || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="房东电话">
          {{ currentContract.landlord?.phone || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="房源数量">
          {{ currentContract.house_ids?.length || 0 }}
        </el-descriptions-item>
        <el-descriptions-item label="合同金额">
          <span class="money">¥{{ currentContract.contract_amount }}</span>
        </el-descriptions-item>
        <el-descriptions-item label="服务费率">
          {{ currentContract.service_fee_rate || 0 }}%
        </el-descriptions-item>
        <el-descriptions-item label="最低服务费">
          <span class="money">¥{{ currentContract.minimum_fee || 0 }}</span>
        </el-descriptions-item>
        <el-descriptions-item label="付款周期">
          {{ getPaymentCycleText(currentContract.payment_cycle) }}
        </el-descriptions-item>
        <el-descriptions-item label="合同期限">
          {{ formatChineseDate(currentContract.start_date) }} 至 {{ formatChineseDate(currentContract.end_date) }}
        </el-descriptions-item>
        <el-descriptions-item label="创建时间">
          {{ currentContract.created_at || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="备注" :span="2">
          {{ currentContract.remark || '-' }}
        </el-descriptions-item>
      </el-descriptions>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="detailVisible = false">关闭</el-button>
          <el-button
            type="primary"
            @click="handleEditFromDetail"
            v-if="currentContract.status === 'draft' && hasPermission('edit')"
          >
            编辑
          </el-button>
          <el-button
            type="success"
            @click="handleActivateFromDetail"
            v-if="currentContract.status === 'draft' && hasPermission('edit')"
          >
            激活
          </el-button>
          <el-button
            type="warning"
            @click="handleTerminateFromDetail"
            v-if="currentContract.status === 'active' && hasPermission('edit')"
          >
            终止
          </el-button>
          <el-button
            type="success"
            @click="handleRenewFromDetail"
            v-if="(currentContract.status === 'active' || currentContract.status === 'expired') && hasPermission('edit')"
          >
            续签
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 新建/编辑合同对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="700px"
      :close-on-click-modal="false"
      destroy-on-close
    >
      <el-form
        ref="contractFormRef"
        :model="contractForm"
        :rules="formRules"
        label-width="100px"
        label-position="right"
      >
        <el-form-item label="合同标题" prop="title">
          <el-input
            v-model="contractForm.title"
            placeholder="请输入合同标题"
            :disabled="isViewMode"
          />
        </el-form-item>

        <el-form-item label="房东" prop="landlord_id">
          <el-select
            v-model="contractForm.landlord_id"
            placeholder="请选择房东"
            filterable
            style="width: 100%"
            :disabled="isViewMode"
            @change="handleLandlordChange"
          >
            <el-option
              v-for="landlord in landlordOptions"
              :key="landlord.id"
              :label="landlord.name"
              :value="landlord.id"
            >
              <span>{{ landlord.name }}</span>
              <span style="color: #8492a6; font-size: 13px; margin-left: 10px">
                ({{ landlord.phone }})
              </span>
            </el-option>
          </el-select>
        </el-form-item>

        <el-form-item label="房源" prop="house_ids">
          <el-select
            v-model="contractForm.house_ids"
            multiple
            placeholder="请选择房源"
            filterable
            style="width: 100%"
            :disabled="isViewMode"
          >
            <el-option
              v-for="house in houseOptions"
              :key="house.id"
              :label="house.address"
              :value="house.id"
            >
              <span>{{ house.address }}</span>
              <span style="color: #8492a6; font-size: 13px; margin-left: 10px">
                ({{ house.type }})
              </span>
            </el-option>
          </el-select>
        </el-form-item>

        <el-form-item label="合同金额" prop="contract_amount">
          <el-input-number
            v-model="contractForm.contract_amount"
            :min="0"
            :precision="2"
            :step="100"
            style="width: 100%"
            :disabled="isViewMode"
          />
          <span style="margin-left: 10px">元</span>
        </el-form-item>

        <el-form-item label="服务费率" prop="service_fee_rate">
          <el-input-number
            v-model="contractForm.service_fee_rate"
            :min="0"
            :max="100"
            :precision="2"
            :step="0.1"
            style="width: 100%"
            :disabled="isViewMode"
          />
          <span style="margin-left: 10px">%</span>
        </el-form-item>

        <el-form-item label="最低服务费" prop="minimum_fee">
          <el-input-number
            v-model="contractForm.minimum_fee"
            :min="0"
            :precision="2"
            :step="100"
            style="width: 100%"
            :disabled="isViewMode"
          />
          <span style="margin-left: 10px">元</span>
        </el-form-item>

        <el-form-item label="付款周期" prop="payment_cycle">
          <el-select
            v-model="contractForm.payment_cycle"
            placeholder="请选择付款周期"
            style="width: 100%"
            :disabled="isViewMode"
          >
            <el-option label="1个月" value="1" />
            <el-option label="3个月" value="3" />
            <el-option label="6个月" value="6" />
            <el-option label="12个月" value="12" />
          </el-select>
        </el-form-item>

        <el-form-item label="合同期限" prop="contract_period">
          <el-date-picker
            v-model="contractForm.contract_period"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            style="width: 100%"
            :disabled="isViewMode"
            value-format="YYYY-MM-DD"
          />
        </el-form-item>

        <el-form-item label="备注" prop="remark">
          <el-input
            v-model="contractForm.remark"
            type="textarea"
            :rows="3"
            placeholder="请输入备注信息"
            :disabled="isViewMode"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button
            type="primary"
            @click="handleSubmit"
            :loading="submitLoading"
            v-if="!isViewMode"
          >
            确定
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 合同终止对话框 -->
    <el-dialog
      v-model="terminateVisible"
      title="终止合同"
      width="600px"
      :close-on-click-modal="false"
      destroy-on-close
    >
      <el-alert
        title="终止确认"
        type="warning"
        :closable="false"
        show-icon
        style="margin-bottom: 20px"
      >
        即将终止合同 <strong>{{ currentContract.contract_no }}</strong>，
        房东：{{ currentContract.landlord?.name || '-' }}，此操作不可恢复！
      </el-alert>
      <el-form
        ref="terminateFormRef"
        :model="terminateForm"
        :rules="terminateFormRules"
        label-width="100px"
        label-position="right"
      >
        <el-form-item label="终止原因" prop="reason">
          <el-input
            v-model="terminateForm.reason"
            type="textarea"
            :rows="3"
            placeholder="请输入终止原因"
          />
        </el-form-item>
        <el-form-item label="终止日期" prop="terminate_date">
          <el-date-picker
            v-model="terminateForm.terminate_date"
            type="date"
            placeholder="选择终止日期"
            style="width: 100%"
            value-format="YYYY-MM-DD"
          />
        </el-form-item>
        <el-form-item label="赔偿金额" prop="settlement_amount">
          <el-input-number
            v-model="terminateForm.settlement_amount"
            :min="0"
            :precision="2"
            :step="100"
            style="width: 100%"
            placeholder="可选"
          />
          <span style="margin-left: 10px">元</span>
        </el-form-item>
        <el-form-item label="备注" prop="remark">
          <el-input
            v-model="terminateForm.remark"
            type="textarea"
            :rows="2"
            placeholder="请输入备注信息（可选）"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="terminateVisible = false">取消</el-button>
          <el-button type="warning" @click="handleTerminateSubmit" :loading="submitLoading">
            确定终止
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 合同续签对话框 -->
    <el-dialog
      v-model="renewVisible"
      title="合同续签"
      width="600px"
      :close-on-click-modal="false"
      destroy-on-close
    >
      <el-alert
        title="续签提示"
        type="info"
        :closable="false"
        show-icon
        style="margin-bottom: 20px"
      >
        即将为合同 <strong>{{ currentContract.contract_no }}</strong> 办理续签，
        房东：{{ currentContract.landlord?.name || '-' }}
      </el-alert>
      <el-form
        ref="renewFormRef"
        :model="renewForm"
        :rules="renewFormRules"
        label-width="100px"
        label-position="right"
      >
        <el-form-item label="原到期日期">
          <span>{{ formatChineseDate(currentContract.end_date) }}</span>
        </el-form-item>
        <el-form-item label="新租期" prop="contract_period">
          <el-date-picker
            v-model="renewForm.contract_period"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            style="width: 100%"
            value-format="YYYY-MM-DD"
            :disabled-date="disabledDate"
          />
        </el-form-item>
        <el-form-item label="新合同金额" prop="contract_amount">
          <el-input-number
            v-model="renewForm.contract_amount"
            :min="0"
            :precision="2"
            :step="100"
            style="width: 100%"
          />
          <span style="margin-left: 10px">元</span>
        </el-form-item>
        <el-form-item label="新服务费率" prop="service_fee_rate">
          <el-input-number
            v-model="renewForm.service_fee_rate"
            :min="0"
            :max="100"
            :precision="2"
            :step="0.1"
            style="width: 100%"
          />
          <span style="margin-left: 10px">%</span>
        </el-form-item>
        <el-form-item label="新最低服务费" prop="minimum_fee">
          <el-input-number
            v-model="renewForm.minimum_fee"
            :min="0"
            :precision="2"
            :step="100"
            style="width: 100%"
          />
          <span style="margin-left: 10px">元</span>
        </el-form-item>
        <el-form-item label="备注" prop="remark">
          <el-input
            v-model="renewForm.remark"
            type="textarea"
            :rows="3"
            placeholder="请输入备注信息"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="renewVisible = false">取消</el-button>
          <el-button type="primary" @click="handleRenewSubmit" :loading="submitLoading">
            确定
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Plus,
  Search,
  Refresh,
  RefreshRight,
  View,
  Edit,
  Delete,
  CircleCheck,
  CircleClose
} from '@element-plus/icons-vue'
import {
  getLandlordContractList,
  getLandlordContractDetail,
  createLandlordContract,
  updateLandlordContract,
  deleteLandlordContract,
  activateLandlordContract,
  terminateLandlordContract,
  renewLandlordContract
} from '@/api/landlordContract'
import { getLandlordList } from '@/api/landlord'
import { getHouseList } from '@/api/house'
import { useUserStore } from '@/store/user'
import { hasPermission } from '@/utils/permission'
import dayjs from 'dayjs'

const userStore = useUserStore()
const loading = ref(false)
const contractList = ref([])
const dialogVisible = ref(false)
const detailVisible = ref(false)
const terminateVisible = ref(false)
const renewVisible = ref(false)
const dialogTitle = ref('新建合同')
const submitLoading = ref(false)
const contractFormRef = ref(null)
const terminateFormRef = ref(null)
const renewFormRef = ref(null)
const currentContract = ref({})
const isViewMode = ref(false)

// 选项数据
const landlordOptions = ref([])
const houseOptions = ref([])

// 即将到期合同
const expiringContracts = ref([])

// 搜索表单
const searchForm = reactive({
  keyword: '',
  status: '',
  page: 1,
  per_page: 10
})

// 分页
const pagination = reactive({
  page: 1,
  per_page: 10,
  total: 0
})

// 合同表单
const contractForm = reactive({
  title: '',
  landlord_id: null,
  house_ids: [],
  contract_amount: 0,
  service_fee_rate: 0,
  minimum_fee: 0,
  payment_cycle: 3,
  contract_period: [],
  remark: ''
})

// 终止表单
const terminateForm = reactive({
  reason: '',
  terminate_date: '',
  settlement_amount: 0,
  remark: ''
})

// 续签表单
const renewForm = reactive({
  contract_period: [],
  contract_amount: 0,
  service_fee_rate: 0,
  minimum_fee: 0,
  remark: ''
})

// 表单验证规则
const formRules = {
  title: [{ required: true, message: '请输入合同标题', trigger: 'blur' }],
  landlord_id: [{ required: true, message: '请选择房东', trigger: 'change' }],
  house_ids: [{
    required: true,
    type: 'array',
    message: '请选择房源',
    trigger: 'change',
    validator: (rule, value, callback) => {
      if (!value || value.length === 0) {
        callback(new Error('请选择至少一个房源'))
      } else {
        callback()
      }
    }
  }],
  contract_amount: [{ required: true, message: '请输入合同金额', trigger: 'blur' }],
  service_fee_rate: [{ required: true, message: '请输入服务费率', trigger: 'blur' }],
  contract_period: [
    {
      required: true,
      type: 'array',
      message: '请选择合同期限',
      trigger: 'change',
      validator: (rule, value, callback) => {
        if (!value || !value[0] || !value[1]) {
          callback(new Error('请选择完整的合同期限'))
        } else {
          callback()
        }
      }
    }
  ]
}

const terminateFormRules = {
  reason: [{ required: true, message: '请输入终止原因', trigger: 'blur' }],
  terminate_date: [{ required: true, message: '请选择终止日期', trigger: 'change' }]
}

const renewFormRules = {
  contract_period: [
    {
      required: true,
      type: 'array',
      message: '请选择新租期',
      trigger: 'change',
      validator: (rule, value, callback) => {
        if (!value || !value[0] || !value[1]) {
          callback(new Error('请选择完整的新租期'))
        } else {
          callback()
        }
      }
    }
  ],
  contract_amount: [{ required: true, message: '请输入新合同金额', trigger: 'blur' }],
  service_fee_rate: [{ required: true, message: '请输入新服务费率', trigger: 'blur' }],
  minimum_fee: [{ required: true, message: '请输入新最低服务费', trigger: 'blur' }]
}

// 状态类型映射
const getStatusType = (status) => {
  const types = {
    draft: 'info',
    active: 'success',
    expired: 'info',
    terminated: 'danger'
  }
  return types[status] || 'info'
}

// 状态文本映射
const getStatusText = (status) => {
  const texts = {
    draft: '草稿',
    active: '生效中',
    expired: '已过期',
    terminated: '已终止'
  }
  return texts[status] || status
}

// 付款周期文本
const getPaymentCycleText = (cycle) => {
  const texts = {
    1: '1个月',
    3: '3个月',
    6: '6个月',
    12: '12个月'
  }
  return texts[cycle] || `${cycle}个月`
}

// 格式化日期为 YYYY-MM-DD
const formatChineseDate = (dateStr) => {
  if (!dateStr) return '-'
  try {
    const date = dayjs(dateStr)
    return date.format('YYYY-MM-DD')
  } catch (error) {
    return dateStr
  }
}

// 加载合同列表
const loadContractList = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      per_page: pagination.per_page,
      ...searchForm
    }
    const res = await getLandlordContractList(params)
    contractList.value = res.data?.items || []
    pagination.total = res.data?.pagination?.total || 0

    // 检查即将到期的合同
    checkExpiringContracts(contractList.value)
  } catch (error) {
    console.error('加载合同列表失败:', error)
    ElMessage.error('加载合同列表失败')
  } finally {
    loading.value = false
  }
}

// 检查即将到期的合同（30 天内）
const checkExpiringContracts = (contracts) => {
  const today = dayjs()
  expiringContracts.value = contracts
    .filter(contract => {
      if (contract.status !== 'active' || !contract.end_date) return false
      const endDate = dayjs(contract.end_date)
      const diffDays = endDate.diff(today, 'day')
      return diffDays >= 0 && diffDays <= 30
    })
    .map(contract => ({
      ...contract,
      days_until_expiry: dayjs(contract.end_date).diff(today, 'day')
    }))
}

// 搜索
const handleSearch = () => {
  pagination.page = 1
  loadContractList()
}

// 重置
const handleReset = () => {
  Object.assign(searchForm, {
    keyword: '',
    status: '',
    page: 1,
    per_page: 10
  })
  handleSearch()
}

// 重置表单
const resetForm = () => {
  if (contractFormRef.value) {
    contractFormRef.value.resetFields()
  }
  Object.assign(contractForm, {
    title: '',
    landlord_id: null,
    house_ids: [],
    contract_amount: 0,
    service_fee_rate: 0,
    minimum_fee: 0,
    payment_cycle: 3,
    contract_period: [],
    remark: ''
  })
  // 清空房源选项
  houseOptions.value = []
}

// 重置终止表单
const resetTerminateForm = () => {
  if (terminateFormRef.value) {
    terminateFormRef.value.resetFields()
  }
  Object.assign(terminateForm, {
    reason: '',
    terminate_date: dayjs().format('YYYY-MM-DD'),
    settlement_amount: 0,
    remark: ''
  })
}

// 重置续签表单
const resetRenewForm = () => {
  if (renewFormRef.value) {
    renewFormRef.value.resetFields()
  }
  Object.assign(renewForm, {
    contract_period: [],
    contract_amount: 0,
    service_fee_rate: 0,
    minimum_fee: 0,
    remark: ''
  })
}

// 加载房东选项
const loadLandlordOptions = async () => {
  try {
    const res = await getLandlordList({ page: 1, per_page: 100 })
    landlordOptions.value = res.data?.items || []
  } catch (error) {
    console.error('加载房东列表失败:', error)
  }
}

// 加载房源选项
const loadHouseOptions = async (landlordId = null) => {
  try {
    const params = { page: 1, per_page: 100 }
    if (landlordId) {
      params.landlord_id = landlordId
    }
    const res = await getHouseList(params)
    houseOptions.value = res.data?.items || []
  } catch (error) {
    console.error('加载房源列表失败:', error)
  }
}

// 房东变更时加载对应房源
const handleLandlordChange = async (landlordId) => {
  // 清空房源选择
  contractForm.house_ids = []
  // 加载该房东的房源
  await loadHouseOptions(landlordId)
}

// 新建合同
const handleAdd = () => {
  dialogTitle.value = '新建合同'
  isViewMode.value = false
  resetForm()
  currentContract.value = {}
  dialogVisible.value = true
}

// 查看合同详情
const handleView = async (row) => {
  try {
    const res = await getLandlordContractDetail(row.id)
    currentContract.value = res.data || row
    detailVisible.value = true
  } catch (error) {
    console.error('加载合同详情失败:', error)
    ElMessage.error('加载合同详情失败')
    currentContract.value = { ...row }
    detailVisible.value = true
  }
}

// 编辑合同
const handleEdit = async (row) => {
  dialogTitle.value = '编辑合同'
  isViewMode.value = false
  currentContract.value = { ...row }
  
  // 填充表单数据
  Object.assign(contractForm, {
    title: row.title || '',
    landlord_id: row.landlord_id || null,
    house_ids: row.house_ids || [],
    contract_amount: parseFloat(row.contract_amount) || 0,
    service_fee_rate: parseFloat(row.service_fee_rate) || 0,
    minimum_fee: parseFloat(row.minimum_fee) || 0,
    payment_cycle: row.payment_cycle || 3,
    contract_period: row.start_date && row.end_date ? [row.start_date, row.end_date] : [],
    remark: row.remark || ''
  })
  
  // 加载该房东的房源
  if (row.landlord_id) {
    await loadHouseOptions(row.landlord_id)
  } else {
    houseOptions.value = []
  }
  
  dialogVisible.value = true
}

// 从详情页编辑
const handleEditFromDetail = async () => {
  await handleEdit(currentContract.value)
  detailVisible.value = false
}

// 激活合同
const handleActivate = (row) => {
  ElMessageBox.confirm('确定要激活该合同吗？激活后合同将生效！', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      await activateLandlordContract(row.id)
      ElMessage.success('激活成功')
      loadContractList()
    } catch (error) {
      console.error('激活失败:', error)
      ElMessage.error('激活失败')
    }
  }).catch(() => {})
}

// 从详情页激活
const handleActivateFromDetail = () => {
  handleActivate(currentContract.value)
  detailVisible.value = false
}

// 终止合同
const handleTerminate = (row) => {
  currentContract.value = { ...row }
  resetTerminateForm()
  terminateVisible.value = true
}

// 从详情页终止
const handleTerminateFromDetail = () => {
  handleTerminate(currentContract.value)
  detailVisible.value = false
}

// 提交终止
const handleTerminateSubmit = async () => {
  if (!terminateFormRef.value) return
  
  try {
    await terminateFormRef.value.validate()
  } catch (error) {
    return
  }
  
  // 二次确认
  ElMessageBox.confirm('确定要终止该合同吗？此操作不可恢复！', '终止确认', {
    confirmButtonText: '确定终止',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    submitLoading.value = true
    try {
      const data = {
        reason: terminateForm.reason,
        terminate_date: terminateForm.terminate_date,
        settlement_amount: terminateForm.settlement_amount,
        remark: terminateForm.remark
      }
      
      await terminateLandlordContract(currentContract.value.id, data)
      ElMessage.success('终止成功')
      
      terminateVisible.value = false
      loadContractList()
    } catch (error) {
      console.error('终止失败:', error)
      ElMessage.error('终止失败')
    } finally {
      submitLoading.value = false
    }
  }).catch(() => {})
}

// 续签合同
const handleRenew = (row) => {
  currentContract.value = { ...row }
  resetRenewForm()
  
  // 设置默认值
  renewForm.contract_amount = parseFloat(row.contract_amount) || 0
  renewForm.service_fee_rate = parseFloat(row.service_fee_rate) || 0
  renewForm.minimum_fee = parseFloat(row.minimum_fee) || 0
  
  renewVisible.value = true
}

// 从详情页续签
const handleRenewFromDetail = () => {
  handleRenew(currentContract.value)
  detailVisible.value = false
}

// 禁用日期（不能选择原到期日之前的日期）
const disabledDate = (time) => {
  if (!currentContract.value.end_date) return false
  const endDate = dayjs(currentContract.value.end_date)
  return time.getTime() < endDate.toDate().getTime()
}

// 提交续签
const handleRenewSubmit = async () => {
  if (!renewFormRef.value) return
  
  try {
    await renewFormRef.value.validate()
  } catch (error) {
    return
  }
  
  submitLoading.value = true
  try {
    const data = {
      start_date: renewForm.contract_period[0],
      end_date: renewForm.contract_period[1],
      contract_amount: renewForm.contract_amount,
      service_fee_rate: renewForm.service_fee_rate,
      minimum_fee: renewForm.minimum_fee,
      remark: renewForm.remark
    }
    
    await renewLandlordContract(currentContract.value.id, data)
    ElMessage.success('续签成功')
    
    renewVisible.value = false
    loadContractList()
  } catch (error) {
    console.error('续签失败:', error)
    ElMessage.error('续签失败')
  } finally {
    submitLoading.value = false
  }
}

// 删除合同
const handleDelete = (row) => {
  ElMessageBox.confirm('确定要删除该合同吗？删除后不可恢复！', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      await deleteLandlordContract(row.id)
      ElMessage.success('删除成功')
      loadContractList()
    } catch (error) {
      console.error('删除失败:', error)
      ElMessage.error('删除失败')
    }
  }).catch(() => {})
}

// 提交表单
const handleSubmit = async () => {
  if (!contractFormRef.value) return
  
  try {
    await contractFormRef.value.validate()
  } catch (error) {
    return
  }
  
  submitLoading.value = true
  try {
    const data = {
      title: contractForm.title,
      landlord_id: contractForm.landlord_id,
      house_ids: contractForm.house_ids,
      contract_amount: contractForm.contract_amount,
      service_fee_rate: contractForm.service_fee_rate,
      minimum_fee: contractForm.minimum_fee,
      payment_cycle: contractForm.payment_cycle,
      start_date: contractForm.contract_period[0],
      end_date: contractForm.contract_period[1],
      remark: contractForm.remark
    }
    
    if (currentContract.value?.id) {
      await updateLandlordContract(currentContract.value.id, data)
      ElMessage.success('编辑成功')
    } else {
      await createLandlordContract(data)
      ElMessage.success('创建成功')
    }
    
    dialogVisible.value = false
    loadContractList()
  } catch (error) {
    console.error('提交失败:', error)
    ElMessage.error('提交失败：' + (error.message || '请检查表单'))
  } finally {
    submitLoading.value = false
  }
}

// 分页处理
const handleSizeChange = (size) => {
  pagination.per_page = size
  pagination.page = 1
  loadContractList()
}

const handlePageChange = (page) => {
  pagination.page = page
  loadContractList()
}

// 排序处理
const handleSortChange = ({ prop, order }) => {
  // 可以根据排序参数重新请求数据
}

// 初始化
onMounted(() => {
  loadContractList()
  loadLandlordOptions()
  // 不自动加载房源，等待选择房东后再加载
})
</script>

<style lang="scss" scoped>
.landlord-contract-list-page {
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
  }

  .expiring-alert {
    margin-bottom: 20px;

    .expiring-contracts {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin-top: 10px;

      .expiring-tag {
        cursor: pointer;
        transition: all 0.3s;

        &:hover {
          transform: translateY(-2px);
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
        }
      }
    }
  }

  .search-card {
    margin-bottom: 20px;

    .search-form {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
    }
  }

  .table-card {
    margin-bottom: 20px;

    .contract-period {
      display: flex;
      align-items: center;
      gap: 8px;

      .separator {
        color: #909399;
      }
    }

    .money {
      color: #f56c6c;
      font-weight: bold;
    }
  }

  .pagination-card {
    .el-pagination {
      display: flex;
      justify-content: flex-end;
    }
  }

  .dialog-footer {
    display: flex;
    justify-content: flex-end;
    gap: 10px;
  }
}
</style>