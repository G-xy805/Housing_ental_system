<template>
  <div class="payment-list-page">
    <div class="page-header">
      <h2>租金管理</h2>
      <el-button type="primary" @click="handleBatchRemind" v-if="overdueList.length > 0">
        <el-icon><Bell /></el-icon>
        批量催缴 ({{ overdueList.length }})
      </el-button>
    </div>

    <!-- 逾期支付提醒 -->
    <el-alert
      v-if="overdueList.length > 0"
      title="逾期支付提醒"
      type="error"
      :closable="false"
      show-icon
      class="overdue-alert"
    >
      <template #default>
        <div class="overdue-payments">
          <el-tag
            v-for="payment in overdueList"
            :key="payment.id"
            type="danger"
            size="small"
            class="overdue-tag"
            @click="handlePay(payment)"
          >
            {{ payment.contract_no }} - {{ payment.tenant_name }} 
            ({{ payment.room_no }}) - 逾期 {{ payment.overdue_days }} 天
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
        <el-form-item label="支付状态">
          <el-select
            v-model="searchForm.status"
            placeholder="全部"
            clearable
            style="width: 120px"
          >
            <el-option label="全部" value="" />
            <el-option label="待支付" value="pending" />
            <el-option label="已支付" value="paid" />
            <el-option label="逾期" value="overdue" />
            <el-option label="部分支付" value="partial" />
          </el-select>
        </el-form-item>
        <el-form-item label="应缴日期">
          <el-date-picker
            v-model="searchForm.date_range"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            style="width: 240px"
            value-format="YYYY-MM-DD"
          />
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

    <!-- 支付记录列表 -->
    <el-card class="table-card" shadow="hover">
      <el-table
        :data="paymentList"
        style="width: 100%"
        v-loading="loading"
        @sort-change="handleSortChange"
        :row-class-name="getRowClassName"
      >
        <el-table-column prop="contract_no" label="合同编号" min-width="120" />
        <el-table-column prop="tenant_name" label="租客姓名" min-width="100" />
        <el-table-column prop="amount" label="应缴金额" width="100" sortable>
          <template #default="scope">
            <span class="money">¥{{ scope.row.amount }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="paid_amount" label="已缴金额" width="100" sortable>
          <template #default="scope">
            <span class="money paid">¥{{ scope.row.paid_amount || 0 }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="支付状态" width="90">
          <template #default="scope">
            <el-tag :type="getStatusType(scope.row.status)" size="small">
              {{ getStatusText(scope.row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="due_date" label="应缴日期" width="100" sortable />
        <el-table-column label="操作" min-width="280" fixed="right">
          <template #default="scope">
            <el-button
              link
              type="primary"
              @click="handlePay(scope.row)"
              v-if="scope.row.status === 'pending' || scope.row.status === 'overdue'"
            >
              <el-icon><Wallet /></el-icon>
              缴纳
            </el-button>
            <el-button
              link
              type="success"
              @click="handleRefundDeposit(scope.row)"
              v-if="scope.row.deposit_amount > 0 && scope.row.status === 'paid'"
            >
              <el-icon><Coin /></el-icon>
              退押金
            </el-button>
            <el-button link type="primary" @click="handleView(scope.row)">
              <el-icon><View /></el-icon>
              详情
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      <template #empty>
        <el-empty description="暂无支付记录">
          <el-button type="primary" @click="handleReset">刷新列表</el-button>
        </el-empty>
      </template>
    </el-card>

    <!-- 分页 -->
    <el-card class="pagination-card" v-if="paymentList.length > 0">
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

    <!-- 租金缴纳对话框 -->
    <el-dialog
      v-model="payDialogVisible"
      title="租金缴纳"
      width="600px"
      :close-on-click-modal="false"
      destroy-on-close
    >
      <el-alert
        title="缴费信息"
        type="info"
        :closable="false"
        show-icon
        style="margin-bottom: 20px"
      >
        <template #default>
          <div class="payment-info">
            <p><strong>合同编号：</strong>{{ currentPayment.contract_no }}</p>
            <p><strong>租客姓名：</strong>{{ currentPayment.tenant_name }}</p>
            <p><strong>房间号：</strong>{{ currentPayment.room_no }}</p>
            <p><strong>应缴金额：</strong><span class="money">¥{{ currentPayment.amount }}</span></p>
            <p v-if="currentPayment.late_fee > 0">
              <strong>滞纳金：</strong><span class="money late-fee">¥{{ currentPayment.late_fee }}</span>
            </p>
            <p><strong>合计应缴：</strong>
              <span class="money total">
                ¥{{ (currentPayment.amount + (currentPayment.late_fee || 0)).toFixed(2) }}
              </span>
            </p>
          </div>
        </template>
      </el-alert>

      <el-form
        ref="payFormRef"
        :model="payForm"
        :rules="payFormRules"
        label-width="100px"
        label-position="right"
      >
        <el-form-item label="实付金额" prop="paid_amount">
          <el-input-number
            v-model="payForm.paid_amount"
            :min="0.01"
            :precision="2"
            :step="100"
            style="width: 100%"
            :max="currentPayment.amount + (currentPayment.late_fee || 0)"
          />
          <span style="margin-left: 10px">元</span>
        </el-form-item>

        <el-form-item label="支付方式" prop="payment_method">
          <el-select v-model="payForm.payment_method" placeholder="请选择支付方式" style="width: 100%">
            <el-option label="微信支付" value="wechat">
              <span>💳 微信支付</span>
            </el-option>
            <el-option label="支付宝" value="alipay">
              <span>💳 支付宝</span>
            </el-option>
            <el-option label="银行卡转账" value="bank">
              <span>🏦 银行卡转账</span>
            </el-option>
            <el-option label="现金支付" value="cash">
              <span>💵 现金支付</span>
            </el-option>
          </el-select>
        </el-form-item>

        <el-form-item label="支付凭证" prop="voucher">
          <el-upload
            ref="voucherUploadRef"
            action="#"
            :auto-upload="false"
            :limit="3"
            :on-change="handleVoucherChange"
            :on-remove="handleVoucherRemove"
            :file-list="payForm.voucher_files"
            list-type="picture-card"
          >
            <el-icon><Plus /></el-icon>
            <template #tip>
              <div class="el-upload__tip">
                支持上传支付凭证截图，最多 3 张
              </div>
            </template>
          </el-upload>
        </el-form-item>

        <el-form-item label="备注" prop="remark">
          <el-input
            v-model="payForm.remark"
            type="textarea"
            :rows="3"
            placeholder="请输入备注信息（可选）"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="payDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handlePaySubmit" :loading="paySubmitLoading">
            确认支付
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 押金退还对话框 -->
    <el-dialog
      v-model="refundDialogVisible"
      title="押金退还"
      width="600px"
      :close-on-click-modal="false"
      destroy-on-close
    >
      <el-alert
        title="押金信息"
        type="warning"
        :closable="false"
        show-icon
        style="margin-bottom: 20px"
      >
        <template #default>
          <div class="deposit-info">
            <p><strong>合同编号：</strong>{{ currentPayment.contract_no }}</p>
            <p><strong>租客姓名：</strong>{{ currentPayment.tenant_name }}</p>
            <p><strong>房间号：</strong>{{ currentPayment.room_no }}</p>
            <p><strong>押金金额：</strong><span class="money deposit">¥{{ currentPayment.deposit_amount }}</span></p>
            <p v-if="currentPayment.deduction_amount > 0">
              <strong>扣除金额：</strong><span class="money deduction">¥{{ currentPayment.deduction_amount }}</span>
            </p>
            <p><strong>应退金额：</strong>
              <span class="money refund">
                ¥{{ (currentPayment.deposit_amount - (currentPayment.deduction_amount || 0)).toFixed(2) }}
              </span>
            </p>
          </div>
        </template>
      </el-alert>

      <el-form
        ref="refundFormRef"
        :model="refundForm"
        :rules="refundFormRules"
        label-width="100px"
        label-position="right"
      >
        <el-form-item label="退还金额" prop="refund_amount">
          <el-input-number
            v-model="refundForm.refund_amount"
            :min="0"
            :precision="2"
            :step="100"
            style="width: 100%"
            :max="currentPayment.deposit_amount"
          />
          <span style="margin-left: 10px">元</span>
        </el-form-item>

        <el-form-item label="退还方式" prop="refund_method">
          <el-select v-model="refundForm.refund_method" placeholder="请选择退还方式" style="width: 100%">
            <el-option label="微信退款" value="wechat" />
            <el-option label="支付宝退款" value="alipay" />
            <el-option label="银行卡退款" value="bank" />
            <el-option label="现金退还" value="cash" />
          </el-select>
        </el-form-item>

        <el-form-item label="扣除原因" prop="deduction_reason">
          <el-input
            v-model="refundForm.deduction_reason"
            type="textarea"
            :rows="3"
            placeholder="如有扣除押金，请说明原因（可选）"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="refundDialogVisible = false">取消</el-button>
          <el-button type="warning" @click="handleRefundSubmit" :loading="refundSubmitLoading">
            确认退还
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 支付详情对话框 -->
    <el-dialog
      v-model="detailVisible"
      title="支付详情"
      width="850px"
      destroy-on-close
    >
      <el-descriptions :column="2" border>
        <el-descriptions-item label="合同编号">
          {{ currentPayment.contract_no }}
        </el-descriptions-item>
        <el-descriptions-item label="支付状态">
          <el-tag :type="getStatusType(currentPayment.status)" size="small">
            {{ getStatusText(currentPayment.status) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="租客姓名">
          {{ currentPayment.tenant_name }}
        </el-descriptions-item>
        <el-descriptions-item label="租客手机号">
          {{ currentPayment.tenant_phone || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="房源地址">
          {{ currentPayment.house_address }}
        </el-descriptions-item>
        <el-descriptions-item label="房间号">
          {{ currentPayment.room_no }}
        </el-descriptions-item>
        <el-descriptions-item label="应缴金额">
          <span class="money">¥{{ currentPayment.amount }}</span>
        </el-descriptions-item>
        <el-descriptions-item label="已缴金额">
          <span class="money paid">¥{{ currentPayment.paid_amount || 0 }}</span>
        </el-descriptions-item>
        <el-descriptions-item label="滞纳金" v-if="currentPayment.late_fee > 0">
          <span class="money late-fee">¥{{ currentPayment.late_fee }}</span>
        </el-descriptions-item>
        <el-descriptions-item label="押金金额" v-if="currentPayment.deposit_amount > 0">
          <span class="money deposit">¥{{ currentPayment.deposit_amount }}</span>
        </el-descriptions-item>
        <el-descriptions-item label="扣除金额" v-if="currentPayment.deduction_amount > 0">
          <span class="money deduction">¥{{ currentPayment.deduction_amount }}</span>
        </el-descriptions-item>
        <el-descriptions-item label="支付方式" v-if="currentPayment.payment_method">
          {{ getPaymentMethodText(currentPayment.payment_method) }}
        </el-descriptions-item>
        <el-descriptions-item label="应缴日期">
          {{ currentPayment.due_date }}
        </el-descriptions-item>
        <el-descriptions-item label="实付日期" v-if="currentPayment.payment_date">
          {{ currentPayment.payment_date }}
        </el-descriptions-item>
        <el-descriptions-item label="支付时间" v-if="currentPayment.paid_at">
          {{ currentPayment.paid_at }}
        </el-descriptions-item>
        <el-descriptions-item label="备注" :span="2" v-if="currentPayment.remark">
          {{ currentPayment.remark }}
        </el-descriptions-item>
      </el-descriptions>

      <!-- 支付凭证 -->
      <div v-if="currentPayment.voucher_urls && currentPayment.voucher_urls.length > 0" class="voucher-section">
        <h4>支付凭证</h4>
        <div class="voucher-list">
          <el-image
            v-for="(url, index) in currentPayment.voucher_urls"
            :key="index"
            :src="url"
            :preview-src-list="currentPayment.voucher_urls"
            :initial-index="index"
            fit="cover"
            class="voucher-image"
          />
        </div>
      </div>

      <template #footer>
        <div style="display: flex; justify-content: flex-end; gap: 12px;">
          <el-button @click="detailVisible = false">关闭</el-button>
          <el-button
            type="primary"
            @click="handlePayFromDetail"
            v-if="currentPayment.status === 'pending' || currentPayment.status === 'overdue'"
          >
            去支付
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
  Bell,
  Wallet,
  Coin,
  View
} from '@element-plus/icons-vue'
import {
  getPaymentList,
  getPaymentDetail,
  createPayment,
  verifyPayment,
  getOverduePayments,
  updateLateFees
} from '@/api/payment'
import dayjs from 'dayjs'

const loading = ref(false)
const paymentList = ref([])
const payDialogVisible = ref(false)
const refundDialogVisible = ref(false)
const detailVisible = ref(false)
const paySubmitLoading = ref(false)
const refundSubmitLoading = ref(false)
const payFormRef = ref(null)
const refundFormRef = ref(null)
const voucherUploadRef = ref(null)
const currentPayment = ref({})
const overdueList = ref([])

// 搜索表单
const searchForm = reactive({
  keyword: '',
  status: '',
  date_range: [],
  page: 1,
  per_page: 10
})

// 分页
const pagination = reactive({
  page: 1,
  per_page: 10,
  total: 0
})

// 支付表单
const payForm = reactive({
  paid_amount: 0,
  payment_method: '',
  voucher_files: [],
  remark: ''
})

// 退还表单
const refundForm = reactive({
  refund_amount: 0,
  refund_method: '',
  deduction_reason: ''
})

// 支付表单验证规则
const payFormRules = {
  paid_amount: [
    { required: true, message: '请输入实付金额', trigger: 'blur' },
    {
      type: 'number',
      min: 0.01,
      message: '实付金额必须大于 0',
      trigger: 'blur'
    }
  ],
  payment_method: [
    { required: true, message: '请选择支付方式', trigger: 'change' }
  ]
}

// 退还表单验证规则
const refundFormRules = {
  refund_amount: [
    { required: true, message: '请输入退还金额', trigger: 'blur' },
    {
      type: 'number',
      min: 0,
      message: '退还金额必须大于等于 0',
      trigger: 'blur'
    }
  ],
  refund_method: [
    { required: true, message: '请选择退还方式', trigger: 'change' }
  ]
}

// 状态类型映射
const getStatusType = (status) => {
  const types = {
    pending: 'warning',
    paid: 'success',
    overdue: 'danger',
    partial: 'info'
  }
  return types[status] || 'info'
}

// 状态文本映射
const getStatusText = (status) => {
  const texts = {
    pending: '待支付',
    paid: '已支付',
    overdue: '逾期',
    partial: '部分支付'
  }
  return texts[status] || status
}

// 支付方式文本
const getPaymentMethodText = (method) => {
  const texts = {
    wechat: '微信支付',
    alipay: '支付宝',
    bank: '银行卡转账',
    cash: '现金支付'
  }
  return texts[method] || method
}

// 获取行类名（用于高亮逾期记录）
const getRowClassName = ({ row }) => {
  if (row.status === 'overdue') {
    return 'overdue-row'
  }
  return ''
}

// 加载支付列表
const loadPaymentList = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      per_page: pagination.per_page,
      ...searchForm
    }
    
    // 处理日期范围
    if (searchForm.date_range && searchForm.date_range.length === 2) {
      params.start_date = searchForm.date_range[0]
      params.end_date = searchForm.date_range[1]
    }
    
    const res = await getPaymentList(params)
    paymentList.value = res.data?.items || []
    pagination.total = res.data?.pagination?.total || 0
  } catch (error) {
    console.error('加载支付列表失败:', error)
    ElMessage.error('加载支付列表失败')
  } finally {
    loading.value = false
  }
}

// 加载逾期支付记录
const loadOverduePayments = async () => {
  try {
    const res = await getOverduePayments({ status: 'overdue' })
    overdueList.value = res.data?.items || []
  } catch (error) {
    console.error('加载逾期记录失败:', error)
  }
}

// 更新滞纳金
const handleUpdateLateFees = async () => {
  try {
    await updateLateFees()
    ElMessage.success('滞纳金更新成功')
    loadPaymentList()
  } catch (error) {
    console.error('更新滞纳金失败:', error)
  }
}

// 搜索
const handleSearch = () => {
  pagination.page = 1
  loadPaymentList()
}

// 重置
const handleReset = () => {
  Object.assign(searchForm, {
    keyword: '',
    status: '',
    date_range: [],
    page: 1,
    per_page: 10
  })
  handleSearch()
}

// 重置支付表单
const resetPayForm = () => {
  if (payFormRef.value) {
    payFormRef.value.resetFields()
  }
  if (voucherUploadRef.value) {
    voucherUploadRef.value.clearFiles()
  }
  Object.assign(payForm, {
    paid_amount: 0,
    payment_method: '',
    voucher_files: [],
    remark: ''
  })
}

// 重置退还表单
const resetRefundForm = () => {
  if (refundFormRef.value) {
    refundFormRef.value.resetFields()
  }
  Object.assign(refundForm, {
    refund_amount: 0,
    refund_method: '',
    deduction_reason: ''
  })
}

// 缴纳租金
const handlePay = (row) => {
  currentPayment.value = { ...row }
  resetPayForm()
  
  // 设置默认实付金额为应缴总额
  const totalAmount = row.amount + (row.late_fee || 0)
  payForm.paid_amount = totalAmount
  
  payDialogVisible.value = true
}

// 从详情页支付
const handlePayFromDetail = () => {
  handlePay(currentPayment.value)
  detailVisible.value = false
}

// 押金退还
const handleRefundDeposit = (row) => {
  currentPayment.value = { ...row }
  resetRefundForm()
  
  // 设置默认退还金额
  refundForm.refund_amount = row.deposit_amount - (row.deduction_amount || 0)
  
  refundDialogVisible.value = true
}

// 查看详情
const handleView = async (row) => {
  try {
    const res = await getPaymentDetail(row.id)
    currentPayment.value = res.data || row
    detailVisible.value = true
  } catch (error) {
    console.error('加载支付详情失败:', error)
    ElMessage.error('加载支付详情失败')
    currentPayment.value = { ...row }
    detailVisible.value = true
  }
}

// 处理凭证变化
const handleVoucherChange = (file, fileList) => {
  payForm.voucher_files = fileList
}

// 处理凭证移除
const handleVoucherRemove = (file, fileList) => {
  payForm.voucher_files = fileList
}

// 提交支付
const handlePaySubmit = async () => {
  if (!payFormRef.value) return
  
  try {
    await payFormRef.value.validate()
  } catch (error) {
    return
  }
  
  paySubmitLoading.value = true
  try {
    const formData = new FormData()
    formData.append('payment_id', currentPayment.value.id)
    formData.append('paid_amount', payForm.paid_amount)
    formData.append('payment_method', payForm.payment_method)
    formData.append('remark', payForm.remark || '')
    
    // 添加凭证文件
    payForm.voucher_files.forEach((file) => {
      formData.append('voucher', file.raw)
    })
    
    await verifyPayment(currentPayment.value.id, formData)
    ElMessage.success('支付成功')
    
    payDialogVisible.value = false
    loadPaymentList()
    loadOverduePayments()
  } catch (error) {
    console.error('支付失败:', error)
    ElMessage.error('支付失败：' + (error.message || '请稍后重试'))
  } finally {
    paySubmitLoading.value = false
  }
}

// 提交退还
const handleRefundSubmit = async () => {
  if (!refundFormRef.value) return
  
  try {
    await refundFormRef.value.validate()
  } catch (error) {
    return
  }
  
  refundSubmitLoading.value = true
  try {
    const data = {
      refund_amount: refundForm.refund_amount,
      refund_method: refundForm.refund_method,
      deduction_reason: refundForm.deduction_reason || ''
    }
    
    // 这里调用退还押金的 API（需要根据实际后端接口调整）
    await updatePayment(currentPayment.value.id, {
      ...data,
      status: 'refunded'
    })
    
    ElMessage.success('押金退还成功')
    
    refundDialogVisible.value = false
    loadPaymentList()
  } catch (error) {
    console.error('退还失败:', error)
    ElMessage.error('退还失败：' + (error.message || '请稍后重试'))
  } finally {
    refundSubmitLoading.value = false
  }
}

// 批量催缴
const handleBatchRemind = () => {
  ElMessageBox.confirm(
    `确定要向 ${overdueList.length} 位逾期租客发送催缴通知吗？`,
    '批量催缴',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(async () => {
    try {
      // 这里调用批量催缴的 API（需要根据实际后端接口调整）
      const remindCount = overdueList.length
      ElMessage.success(`已向 ${remindCount} 位租客发送催缴通知`)
      loadOverduePayments()
    } catch (error) {
      console.error('催缴失败:', error)
      ElMessage.error('催缴失败')
    }
  }).catch(() => {})
}

// 分页大小改变
const handleSizeChange = (size) => {
  pagination.per_page = size
  pagination.page = 1
  loadPaymentList()
}

// 页码改变
const handlePageChange = (page) => {
  pagination.page = page
  loadPaymentList()
}

// 排序处理
const handleSortChange = ({ prop, order }) => {
  console.log('排序:', prop, order)
  // 可以根据排序参数重新请求数据
}

// 更新支付（辅助函数）
const updatePayment = async (id, data) => {
  const { updatePayment: updatePaymentApi } = await import('@/api/payment')
  return updatePaymentApi(id, data)
}

// 初始化
onMounted(() => {
  loadPaymentList()
  loadOverduePayments()
  handleUpdateLateFees()
})
</script>

<style lang="scss" scoped>
.payment-list-page {
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

  .overdue-alert {
    margin-bottom: 20px;

    .overdue-payments {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin-top: 10px;

      .overdue-tag {
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

    .money {
      color: #f56c6c;
      font-weight: bold;

      &.paid {
        color: #67c23a;
      }

      &.late-fee {
        color: #e6a23c;
      }

      &.total {
        color: #f56c6c;
        font-size: 16px;
      }

      &.deposit {
        color: #e6a23c;
      }

      &.refund {
        color: #67c23a;
      }

      &.deduction {
        color: #f56c6c;
      }
    }

    :deep(.overdue-row) {
      background-color: #fef0f0;

      &:hover {
        td {
          background-color: #fde2e2 !important;
        }
      }
    }
  }

  .pagination-card {
    .el-pagination {
      display: flex;
      justify-content: flex-end;
    }
  }

  .payment-info,
  .deposit-info {
    p {
      margin: 8px 0;
      font-size: 14px;
      line-height: 1.6;

      strong {
        color: #606266;
      }
    }
  }

  .voucher-section {
    margin-top: 20px;
    padding-top: 20px;
    border-top: 1px solid #ebeef5;

    h4 {
      margin: 0 0 12px;
      color: #333;
      font-size: 14px;
    }

    .voucher-list {
      display: flex;
      gap: 10px;
      flex-wrap: wrap;

      .voucher-image {
        width: 100px;
        height: 100px;
        border-radius: 4px;
        cursor: pointer;
        transition: all 0.3s;

        &:hover {
          transform: scale(1.05);
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
        }
      }
    }
  }
}
</style>
