<template>
  <div class="contract-list-page">
    <div class="page-header">
      <h2>合同管理</h2>
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
            {{ contract.contract_no }} - {{ contract.tenant_name }}（{{ contract.room_no }}）
            - 剩余 {{ contract.days_until_expiry }} 天到期
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
            placeholder="合同编号/租客姓名"
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
            <el-option label="待签约" value="pending" />
            <el-option label="履行中" value="active" />
            <el-option label="已到期" value="expired" />
            <el-option label="已终止" value="terminated" />
            <el-option label="已违约" value="breached" />
            <el-option label="已续签" value="renewed" />
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
        <el-table-column prop="contract_no" label="合同编号" min-width="120" sortable />
        <el-table-column prop="tenant_name" label="租客姓名" min-width="100" />
        <el-table-column prop="house_address" label="房源地址" min-width="180" show-overflow-tooltip />
        <el-table-column prop="room_no" label="房间号" width="80" />
        <el-table-column label="租期" min-width="150">
          <template #default="scope">
            <div class="lease-period">
              <span>{{ formatChineseDate(scope.row.start_date) }}</span>
              <span class="separator">至</span>
              <span>{{ formatChineseDate(scope.row.end_date) }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="rent_amount" label="租金 (元/月)" width="100" sortable>
          <template #default="scope">
            <span>¥{{ scope.row.rent_amount }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="deposit_amount" label="押金 (元)" width="100">
          <template #default="scope">
            <span>¥{{ scope.row.deposit_amount }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
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
              v-if="scope.row.status === 'pending' && hasPermission('edit')"
            >
              <el-icon><Edit /></el-icon>
              编辑
            </el-button>
            <el-button
              link
              type="success"
              @click="handleRenew(scope.row)"
              v-if="scope.row.status === 'expired' && hasPermission('edit')"
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
        <el-empty description="暂无合同数据">
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
        <el-descriptions-item label="租客姓名">
          {{ currentContract.tenant_name }}
        </el-descriptions-item>
        <el-descriptions-item label="租客手机号">
          {{ currentContract.tenant_phone || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="房源地址">
          {{ currentContract.house_address }}
        </el-descriptions-item>
        <el-descriptions-item label="房间号">
          {{ currentContract.room_no }}
        </el-descriptions-item>
        <el-descriptions-item label="租赁面积">
          {{ currentContract.room_area || '-' }}㎡
        </el-descriptions-item>
        <el-descriptions-item label="租期">
          {{ formatChineseDate(currentContract.start_date) }} 至 {{ formatChineseDate(currentContract.end_date) }}
        </el-descriptions-item>
        <el-descriptions-item label="租金">
          <span class="money">¥{{ currentContract.rent_amount }}</span> / 月
        </el-descriptions-item>
        <el-descriptions-item label="押金">
          <span class="money">¥{{ currentContract.deposit_amount }}</span>
        </el-descriptions-item>
        <el-descriptions-item label="支付方式">
          {{ getPaymentText(currentContract.payment_method) }}
        </el-descriptions-item>
        <el-descriptions-item label="签约日期">
          {{ currentContract.sign_date || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="创建时间">
          {{ currentContract.created_at || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="备注" :span="2">
          {{ currentContract.remark || '-' }}
        </el-descriptions-item>
      </el-descriptions>
      <template #footer>
        <el-button @click="detailVisible = false">关闭</el-button>
        <el-button
          type="primary"
          @click="handleEditFromDetail"
          v-if="currentContract.status === 'pending' && hasPermission('edit')"
        >
          编辑
        </el-button>
        <el-button
          type="success"
          @click="handleRenewFromDetail"
          v-if="currentContract.status === 'expired' && hasPermission('edit')"
        >
          续签
        </el-button>
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
        <el-form-item label="租客" prop="tenant_id">
          <el-select
            v-model="contractForm.tenant_id"
            placeholder="请选择租客"
            filterable
            style="width: 100%"
            :disabled="isViewMode"
          >
            <el-option
              v-for="tenant in tenantOptions"
              :key="tenant.id"
              :label="tenant.name"
              :value="tenant.id"
            >
              <span>{{ tenant.name }}</span>
              <span style="color: #8492a6; font-size: 13px; margin-left: 10px">
                ({{ tenant.phone }})
              </span>
            </el-option>
          </el-select>
        </el-form-item>

        <el-form-item label="房源" prop="house_id">
          <el-select
            v-model="contractForm.house_id"
            placeholder="请选择房源"
            filterable
            style="width: 100%"
            :disabled="isViewMode"
            @change="handleHouseChange"
          >
            <el-option
              v-for="house in houseOptions"
              :key="house.id"
              :label="house.address"
              :value="house.id"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="房间" prop="room_id">
          <el-select
            v-model="contractForm.room_id"
            placeholder="请选择房间"
            filterable
            style="width: 100%"
            :disabled="!contractForm.house_id || isViewMode"
          >
            <el-option
              v-for="room in roomOptions"
              :key="room.id"
              :label="room.room_no"
              :value="room.id"
            >
              <span>{{ room.room_no }}</span>
              <span style="color: #8492a6; font-size: 13px; margin-left: 10px">
                (¥{{ room.rent_price }}/月)
              </span>
            </el-option>
          </el-select>
        </el-form-item>

        <el-form-item label="租期" prop="lease_term">
          <el-date-picker
            v-model="contractForm.lease_term"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            style="width: 100%"
            :disabled="isViewMode"
            value-format="YYYY-MM-DD"
          />
        </el-form-item>

        <el-form-item label="租金" prop="rent_amount">
          <el-input-number
            v-model="contractForm.rent_amount"
            :min="0"
            :precision="2"
            :step="100"
            style="width: 100%"
            :disabled="isViewMode"
          />
          <span style="margin-left: 10px">元/月</span>
        </el-form-item>

        <el-form-item label="押金" prop="deposit_amount">
          <el-input-number
            v-model="contractForm.deposit_amount"
            :min="0"
            :precision="2"
            :step="100"
            style="width: 100%"
            :disabled="isViewMode"
          />
          <span style="margin-left: 10px">元</span>
        </el-form-item>

        <el-form-item label="支付方式" prop="payment_method">
          <el-select
            v-model="contractForm.payment_method"
            placeholder="请选择支付方式"
            style="width: 100%"
            :disabled="isViewMode"
          >
            <el-option label="押一付一" value="press_one_pay_one" />
            <el-option label="押一付三" value="press_one_pay_three" />
            <el-option label="押一付六" value="press_one_pay_six" />
            <el-option label="押一付十二" value="press_one_pay_twelve" />
            <el-option label="自定义" value="custom" />
          </el-select>
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
        租客：{{ currentContract.tenant_name }}，房间：{{ currentContract.room_no }}
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
        <el-form-item label="新租期" prop="lease_term">
          <el-date-picker
            v-model="renewForm.lease_term"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            style="width: 100%"
            value-format="YYYY-MM-DD"
            :disabled-date="disabledDate"
          />
        </el-form-item>
        <el-form-item label="新租金" prop="rent_amount">
          <el-input-number
            v-model="renewForm.rent_amount"
            :min="0"
            :precision="2"
            :step="100"
            style="width: 100%"
          />
          <span style="margin-left: 10px">元/月</span>
        </el-form-item>
        <el-form-item label="新押金" prop="deposit_amount">
          <el-input-number
            v-model="renewForm.deposit_amount"
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
  Delete
} from '@element-plus/icons-vue'
import {
  getContractList,
  getContractDetail,
  createContract,
  updateContract,
  deleteContract,
  renewContract
} from '@/api/contract'
import { getTenantList } from '@/api/tenant'
import { getHouseList } from '@/api/house'
import { useUserStore } from '@/store/user'
import { hasPermission } from '@/utils/permission'
import dayjs from 'dayjs'

const loading = ref(false)
const contractList = ref([])
const dialogVisible = ref(false)
const detailVisible = ref(false)
const renewVisible = ref(false)
const dialogTitle = ref('新建合同')
const submitLoading = ref(false)
const contractFormRef = ref(null)
const renewFormRef = ref(null)
const currentContract = ref({})
const isViewMode = ref(false)

// 选项数据
const tenantOptions = ref([])
const houseOptions = ref([])
const roomOptions = ref([])

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
  tenant_id: null,
  house_id: null,
  room_id: null,
  lease_term: [],
  rent_amount: 0,
  deposit_amount: 0,
  payment_method: 'press_one_pay_three',
  remark: ''
})

// 续签表单
const renewForm = reactive({
  lease_term: [],
  rent_amount: 0,
  deposit_amount: 0,
  remark: ''
})

// 表单验证规则
const formRules = {
  tenant_id: [{ required: true, message: '请选择租客', trigger: 'change' }],
  house_id: [{ required: true, message: '请选择房源', trigger: 'change' }],
  room_id: [{ required: true, message: '请选择房间', trigger: 'change' }],
  lease_term: [
    {
      required: true,
      type: 'array',
      message: '请选择租期',
      trigger: 'change',
      validator: (rule, value, callback) => {
        if (!value || !value[0] || !value[1]) {
          callback(new Error('请选择完整的租期'))
        } else {
          callback()
        }
      }
    }
  ],
  rent_amount: [{ required: true, message: '请输入租金', trigger: 'blur' }],
  deposit_amount: [{ required: true, message: '请输入押金', trigger: 'blur' }],
  payment_method: [{ required: true, message: '请选择支付方式', trigger: 'change' }]
}

const renewFormRules = {
  lease_term: [
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
  rent_amount: [{ required: true, message: '请输入新租金', trigger: 'blur' }],
  deposit_amount: [{ required: true, message: '请输入新押金', trigger: 'blur' }]
}

// 状态类型映射
const getStatusType = (status) => {
  const types = {
    draft: 'info',
    pending: 'warning',
    active: 'success',
    expired: 'info',
    terminated: 'danger',
    breached: 'danger',
    renewed: 'success'
  }
  return types[status] || 'info'
}

// 状态文本映射
const getStatusText = (status) => {
  const texts = {
    draft: '草稿',
    pending: '待签约',
    active: '履行中',
    expired: '已到期',
    terminated: '已终止',
    breached: '已违约',
    renewed: '已续签'
  }
  return texts[status] || status
}

// 支付方式文本
const getPaymentText = (method) => {
  const texts = {
    press_one_pay_one: '押一付一',
    press_one_pay_three: '押一付三',
    press_one_pay_six: '押一付六',
    press_one_pay_twelve: '押一付十二',
    custom: '自定义'
  }
  return texts[method] || method
}

// 格式化中文日期
const formatChineseDate = (dateStr) => {
  if (!dateStr) return '-'
  try {
    const date = dayjs(dateStr)
    return date.format('YYYY 年 M 月 D 日')
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
    const res = await getContractList(params)
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
    tenant_id: null,
    house_id: null,
    room_id: null,
    lease_term: [],
    rent_amount: 0,
    deposit_amount: 0,
    payment_method: 'press_one_pay_three',
    remark: ''
  })
}

// 重置续签表单
const resetRenewForm = () => {
  if (renewFormRef.value) {
    renewFormRef.value.resetFields()
  }
  Object.assign(renewForm, {
    lease_term: [],
    rent_amount: 0,
    deposit_amount: 0,
    remark: ''
  })
}

// 加载租客选项
const loadTenantOptions = async () => {
  try {
    const res = await getTenantList({ page: 1, per_page: 100 })
    tenantOptions.value = res.data?.items || []
  } catch (error) {
    console.error('加载租客列表失败:', error)
  }
}

// 加载房源选项
const loadHouseOptions = async () => {
  try {
    const res = await getHouseList({ page: 1, per_page: 100 })
    houseOptions.value = res.data?.items || []
  } catch (error) {
    console.error('加载房源列表失败:', error)
  }
}

// 房源变化时加载房间
const handleHouseChange = async (houseId) => {
  roomOptions.value = []
  contractForm.room_id = null
  
  if (!houseId) return
  
  try {
    const houseDetail = houseOptions.value.find(h => h.id === houseId)
    if (houseDetail && houseDetail.rooms) {
      roomOptions.value = houseDetail.rooms
    }
  } catch (error) {
    console.error('加载房间列表失败:', error)
  }
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
    const res = await getContractDetail(row.id)
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
const handleEdit = (row) => {
  dialogTitle.value = '编辑合同'
  isViewMode.value = false
  currentContract.value = { ...row }
  
  // 填充表单数据
  Object.assign(contractForm, {
    tenant_id: row.tenant_id || null,
    house_id: row.house_id || null,
    room_id: row.room_id || null,
    lease_term: row.start_date && row.end_date ? [row.start_date, row.end_date] : [],
    rent_amount: parseFloat(row.rent_amount) || 0,
    deposit_amount: parseFloat(row.deposit_amount) || 0,
    payment_method: row.payment_method || 'press_one_pay_three',
    remark: row.remark || ''
  })
  
  // 加载房间选项
  if (row.house_id) {
    const house = houseOptions.value.find(h => h.id === row.house_id)
    if (house && house.rooms) {
      roomOptions.value = house.rooms
    }
  }
  
  dialogVisible.value = true
}

// 从详情页编辑
const handleEditFromDetail = () => {
  handleEdit(currentContract.value)
  detailVisible.value = false
}

// 删除合同
const handleDelete = (row) => {
  ElMessageBox.confirm('确定要删除该合同吗？删除后不可恢复！', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      await deleteContract(row.id)
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
      tenant_id: contractForm.tenant_id,
      house_id: contractForm.house_id,
      room_id: contractForm.room_id,
      start_date: contractForm.lease_term[0],
      end_date: contractForm.lease_term[1],
      rent_amount: contractForm.rent_amount,
      deposit_amount: contractForm.deposit_amount,
      payment_method: contractForm.payment_method,
      remark: contractForm.remark
    }
    
    if (currentContract.value?.id) {
      await updateContract(currentContract.value.id, data)
      ElMessage.success('编辑成功')
    } else {
      await createContract(data)
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

// 续签合同
const handleRenew = (row) => {
  currentContract.value = { ...row }
  resetRenewForm()
  
  // 设置默认值
  renewForm.rent_amount = parseFloat(row.rent_amount) || 0
  renewForm.deposit_amount = parseFloat(row.deposit_amount) || 0
  
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
      start_date: renewForm.lease_term[0],
      end_date: renewForm.lease_term[1],
      rent_amount: renewForm.rent_amount,
      deposit_amount: renewForm.deposit_amount,
      remark: renewForm.remark
    }
    
    await renewContract(currentContract.value.id, data)
    ElMessage.success('续签成功')
    
    renewVisible.value = false
    loadContractList()
  } catch (error) {
    console.error('续签失败:', error)
    ElMessage.error('续签失败：' + (error.message || '请稍后重试'))
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
  console.log('排序:', prop, order)
}

// 初始化
onMounted(() => {
  loadContractList()
  loadTenantOptions()
  loadHouseOptions()
})
</script>

<style lang="scss" scoped>
.contract-list-page {
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

    .lease-period {
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
}
</style>
