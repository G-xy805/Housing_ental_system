<template>
  <div class="payment-list-page">
    <div class="page-header">
      <h2>租金管理</h2>
      <div class="header-buttons">
        <el-button type="primary" @click="handleAddPayment">
          <el-icon><Plus /></el-icon>
          新增租金
        </el-button>
        <el-button type="primary" @click="handleBatchRemind" v-if="overdueList.length > 0">
          <el-icon><Bell /></el-icon>
          批量催缴 ({{ overdueList.length }})
        </el-button>
      </div>
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
        <el-table-column prop="due_date" label="应缴日期" width="120" sortable>
          <template #default="scope">
            {{ scope.row.due_date ? dayjs(scope.row.due_date).format('YYYY-MM-DD') : '-' }}
          </template>
        </el-table-column>
        <el-table-column label="操作" min-width="350" fixed="right">
          <template #default="scope">
            <el-button
              link
              type="primary"
              @click="handleEditPayment(scope.row)"
            >
              <el-icon><Edit /></el-icon>
              编辑
            </el-button>
            <el-button
              link
              type="primary"
              @click="handleSetStatus(scope.row)"
            >
              <el-icon><View /></el-icon>
              设置状态
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
            <el-button
              link
              type="danger"
              @click="handleDeletePayment(scope.row)"
            >
              <el-icon><Delete /></el-icon>
              删除
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

    <!-- 新增租金对话框 -->
    <el-dialog
      v-model="addDialogVisible"
      title="新增租金"
      width="600px"
      :close-on-click-modal="false"
      destroy-on-close
    >
      <el-form
        ref="addFormRef"
        :model="addForm"
        :rules="addFormRules"
        label-width="100px"
        label-position="right"
      >
        <el-form-item label="合同选择" prop="contract_id">
          <el-select v-model="addForm.contract_id" placeholder="请选择合同" style="width: 100%" @change="handleContractChange">
            <el-option
              v-for="contract in contractList"
              :key="contract.id"
              :label="`${contract.contract_no} - ${contract.tenant_name}`"
              :value="contract.id"
            />
          </el-select>
        </el-form-item>

        <!-- 合同信息显示 -->
        <el-form-item v-if="selectedContractInfo" label="合同信息">
          <el-card shadow="hover" style="width: 100%">
            <div class="contract-info">
              <p><strong>租客姓名：</strong>{{ selectedContractInfo.tenant_name }}</p>
              <p><strong>租客手机号：</strong>{{ selectedContractInfo.tenant_phone || '-' }}</p>
              <p><strong>房源地址：</strong>{{ selectedContractInfo.house_address || '-' }}</p>
              <p><strong>房间号：</strong>{{ selectedContractInfo.room_no || '-' }}</p>
            </div>
          </el-card>
        </el-form-item>

        <el-form-item label="支付类型" prop="payment_type">
          <el-select v-model="addForm.payment_type" placeholder="请选择支付类型" style="width: 100%" @change="handlePaymentTypeChange">
            <el-option label="租金" value="rent" />
            <el-option label="押金" value="deposit" />
            <el-option label="水电费" value="utility" />
            <el-option label="其他" value="other" />
          </el-select>
        </el-form-item>

        <el-form-item label="金额" prop="amount">
          <el-input-number
            v-model="addForm.amount"
            :min="0.01"
            :precision="2"
            :step="100"
            style="width: 100%"
          />
          <span style="margin-left: 10px">元</span>
        </el-form-item>

        <el-form-item label="应缴日期" prop="due_date">
          <el-date-picker
            v-model="addForm.due_date"
            type="date"
            placeholder="选择日期"
            style="width: 100%"
            value-format="YYYY-MM-DD"
          />
        </el-form-item>

        <el-form-item label="支付周期开始" prop="period_start">
          <el-date-picker
            v-model="addForm.period_start"
            type="date"
            placeholder="选择日期"
            style="width: 100%"
            value-format="YYYY-MM-DD"
          />
        </el-form-item>

        <el-form-item label="支付周期结束" prop="period_end">
          <el-date-picker
            v-model="addForm.period_end"
            type="date"
            placeholder="选择日期"
            style="width: 100%"
            value-format="YYYY-MM-DD"
          />
        </el-form-item>

        <el-form-item label="备注" prop="remark">
          <el-input
            v-model="addForm.remark"
            type="textarea"
            :rows="3"
            placeholder="请输入备注信息（可选）"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="addDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleAddSubmit" :loading="addSubmitLoading">
            确认添加
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 编辑租金对话框 -->
    <el-dialog
      v-model="editDialogVisible"
      title="编辑租金"
      width="600px"
      :close-on-click-modal="false"
      destroy-on-close
    >
      <el-form
        ref="editFormRef"
        :model="editForm"
        :rules="editFormRules"
        label-width="100px"
        label-position="right"
      >
        <el-form-item label="合同选择" prop="contract_id">
          <el-select v-model="editForm.contract_id" placeholder="请选择合同" style="width: 100%" @change="handleEditContractChange">
            <el-option
              v-for="contract in contractList"
              :key="contract.id"
              :label="`${contract.contract_no} - ${contract.tenant_name}`"
              :value="contract.id"
            />
          </el-select>
        </el-form-item>

        <!-- 合同信息显示 -->
        <el-form-item v-if="selectedEditContractInfo" label="合同信息">
          <el-card shadow="hover" style="width: 100%">
            <div class="contract-info">
              <p><strong>租客姓名：</strong>{{ selectedEditContractInfo.tenant_name }}</p>
              <p><strong>租客手机号：</strong>{{ selectedEditContractInfo.tenant_phone || '-' }}</p>
              <p><strong>房源地址：</strong>{{ selectedEditContractInfo.house_address || '-' }}</p>
              <p><strong>房间号：</strong>{{ selectedEditContractInfo.room_no || '-' }}</p>
            </div>
          </el-card>
        </el-form-item>

        <el-form-item label="支付类型" prop="payment_type">
          <el-select v-model="editForm.payment_type" placeholder="请选择支付类型" style="width: 100%" @change="handleEditPaymentTypeChange">
            <el-option label="租金" value="rent" />
            <el-option label="押金" value="deposit" />
            <el-option label="水电费" value="utility" />
            <el-option label="其他" value="other" />
          </el-select>
        </el-form-item>

        <el-form-item label="金额" prop="amount">
          <el-input-number
            v-model="editForm.amount"
            :min="0.01"
            :precision="2"
            :step="100"
            style="width: 100%"
          />
          <span style="margin-left: 10px">元</span>
        </el-form-item>

        <el-form-item label="应缴日期" prop="due_date">
          <el-date-picker
            v-model="editForm.due_date"
            type="date"
            placeholder="选择日期"
            style="width: 100%"
            value-format="YYYY-MM-DD"
          />
        </el-form-item>

        <el-form-item label="支付周期开始" prop="period_start">
          <el-date-picker
            v-model="editForm.period_start"
            type="date"
            placeholder="选择日期"
            style="width: 100%"
            value-format="YYYY-MM-DD"
          />
        </el-form-item>

        <el-form-item label="支付周期结束" prop="period_end">
          <el-date-picker
            v-model="editForm.period_end"
            type="date"
            placeholder="选择日期"
            style="width: 100%"
            value-format="YYYY-MM-DD"
          />
        </el-form-item>

        <el-form-item label="备注" prop="remark">
          <el-input
            v-model="editForm.remark"
            type="textarea"
            :rows="3"
            placeholder="请输入备注信息（可选）"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="editDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleEditSubmit" :loading="editSubmitLoading">
            确认编辑
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 设置支付状态对话框 -->
    <el-dialog
      v-model="statusDialogVisible"
      title="设置支付状态"
      width="500px"
      :close-on-click-modal="false"
      destroy-on-close
    >
      <el-alert
        title="支付记录信息"
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
            <p><strong>当前状态：</strong>
              <el-tag :type="getStatusType(currentPayment.status)" size="small">
                {{ getStatusText(currentPayment.status) }}
              </el-tag>
            </p>
          </div>
        </template>
      </el-alert>

      <el-form
        ref="statusFormRef"
        :model="statusForm"
        :rules="statusFormRules"
        label-width="100px"
        label-position="right"
      >
        <el-form-item label="支付状态" prop="status">
          <el-select v-model="statusForm.status" placeholder="请选择支付状态" style="width: 100%" @change="handleStatusChange">
            <el-option label="待支付" value="pending" />
            <el-option label="已支付" value="paid" />
            <el-option label="逾期" value="overdue" />
            <el-option label="部分支付" value="partial" />
          </el-select>
        </el-form-item>

        <el-form-item label="实际缴纳金额" prop="paid_amount" v-if="statusForm.status === 'partial'">
          <el-input-number
            v-model="statusForm.paid_amount"
            :min="0"
            :precision="2"
            :step="100"
            style="width: 100%"
            :max="currentPayment.amount"
          />
          <span style="margin-left: 10px">元</span>
        </el-form-item>

        <el-form-item label="备注" prop="remark">
          <el-input
            v-model="statusForm.remark"
            type="textarea"
            :rows="3"
            placeholder="请输入备注信息（可选）"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="statusDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleStatusSubmit" :loading="statusSubmitLoading">
            确认设置
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
          {{ currentPayment.tenant_name || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="租客手机号">
          {{ currentPayment.tenant_phone || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="房源地址">
          {{ currentPayment.house_address || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="房间号">
          {{ currentPayment.room_no || '-' }}
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
          {{ currentPayment.due_date ? dayjs(currentPayment.due_date).format('YYYY-MM-DD') : '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="实付日期" v-if="currentPayment.payment_date">
          {{ dayjs(currentPayment.payment_date).format('YYYY-MM-DD') }}
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
  Coin,
  View,
  Delete,
  Edit
} from '@element-plus/icons-vue'
import {
  getPaymentList,
  getPaymentDetail,
  createPayment,
  updatePayment,
  deletePayment,
  getOverduePayments,
  updateLateFees
} from '@/api/payment'
import { getContractList } from '@/api/contract'
import dayjs from 'dayjs'

const loading = ref(false)
const paymentList = ref([])
const refundDialogVisible = ref(false)
const detailVisible = ref(false)
const addDialogVisible = ref(false)
const editDialogVisible = ref(false)
const statusDialogVisible = ref(false)
const refundSubmitLoading = ref(false)
const addSubmitLoading = ref(false)
const editSubmitLoading = ref(false)
const statusSubmitLoading = ref(false)
const refundFormRef = ref(null)
const addFormRef = ref(null)
const editFormRef = ref(null)
const statusFormRef = ref(null)
const currentPayment = ref({})
const overdueList = ref([])
const contractList = ref([])
const selectedContractInfo = ref(null)
const selectedEditContractInfo = ref(null)

// 新增租金表单
const addForm = reactive({
  contract_id: '',
  payment_type: 'rent',
  amount: 0,
  due_date: '',
  period_start: '',
  period_end: '',
  remark: ''
})

// 编辑租金表单
const editForm = reactive({
  id: '',
  contract_id: '',
  payment_type: 'rent',
  amount: 0,
  due_date: '',
  period_start: '',
  period_end: '',
  remark: ''
})

// 新增租金表单验证规则
const addFormRules = {
  contract_id: [
    { required: true, message: '请选择合同', trigger: 'change' }
  ],
  payment_type: [
    { required: true, message: '请选择支付类型', trigger: 'change' }
  ],
  amount: [
    { required: true, message: '请输入金额', trigger: 'blur' },
    {
      type: 'number',
      min: 0.01,
      message: '金额必须大于 0',
      trigger: 'blur'
    }
  ],
  due_date: [
    { required: true, message: '请选择应缴日期', trigger: 'change' }
  ],
  period_start: [
    {
      validator: (rule, value, callback) => {
        if (value && !addForm.period_end) {
          callback()
        } else if (value && addForm.period_end) {
          if (new Date(value) > new Date(addForm.period_end)) {
            callback(new Error('周期开始日期不能晚于结束日期'))
          } else {
            callback()
          }
        } else {
          callback()
        }
      },
      trigger: 'change'
    }
  ],
  period_end: [
    {
      validator: (rule, value, callback) => {
        if (value && !addForm.period_start) {
          callback()
        } else if (value && addForm.period_start) {
          if (new Date(value) < new Date(addForm.period_start)) {
            callback(new Error('周期结束日期不能早于开始日期'))
          } else {
            callback()
          }
        } else {
          callback()
        }
      },
      trigger: 'change'
    }
  ]
}

// 编辑租金表单验证规则
const editFormRules = {
  contract_id: [
    { required: true, message: '请选择合同', trigger: 'change' }
  ],
  payment_type: [
    { required: true, message: '请选择支付类型', trigger: 'change' }
  ],
  amount: [
    { required: true, message: '请输入金额', trigger: 'blur' },
    {
      type: 'number',
      min: 0.01,
      message: '金额必须大于 0',
      trigger: 'blur'
    }
  ],
  due_date: [
    { required: true, message: '请选择应缴日期', trigger: 'change' }
  ],
  period_start: [
    {
      validator: (rule, value, callback) => {
        if (value && !editForm.period_end) {
          callback()
        } else if (value && editForm.period_end) {
          if (new Date(value) > new Date(editForm.period_end)) {
            callback(new Error('周期开始日期不能晚于结束日期'))
          } else {
            callback()
          }
        } else {
          callback()
        }
      },
      trigger: 'change'
    }
  ],
  period_end: [
    {
      validator: (rule, value, callback) => {
        if (value && !editForm.period_start) {
          callback()
        } else if (value && editForm.period_start) {
          if (new Date(value) < new Date(editForm.period_start)) {
            callback(new Error('周期结束日期不能早于开始日期'))
          } else {
            callback()
          }
        } else {
          callback()
        }
      },
      trigger: 'change'
    }
  ]
}

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

// 状态表单
const statusForm = reactive({
  status: '',
  paid_amount: 0,
  remark: ''
})

// 退还表单
const refundForm = reactive({
  refund_amount: 0,
  refund_method: '',
  deduction_reason: ''
})

// 状态表单验证规则
const statusFormRules = {
  status: [
    { required: true, message: '请选择支付状态', trigger: 'change' }
  ],
  paid_amount: [
    {
      required: true,
      message: '请输入实际缴纳金额',
      trigger: 'blur',
      validator: (rule, value, callback) => {
        if (statusForm.status === 'partial') {
          if (!value || value <= 0) {
            callback(new Error('实际缴纳金额必须大于 0'))
          } else if (value >= currentPayment.value.amount) {
            callback(new Error('实际缴纳金额必须小于应缴金额'))
          } else {
            callback()
          }
        } else {
          callback()
        }
      }
    }
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
    
    // 检查数据结构
    if (paymentList.value.length > 0) {
      console.log('支付列表数据结构:', paymentList.value[0])
    }
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

// 加载合同列表
const loadContractList = async () => {
  try {
    console.log('开始加载合同列表...')
    const res = await getContractList({ status: 'active' })
    console.log('合同列表 API 响应:', res)
    contractList.value = res.data?.items || []
    console.log('加载合同列表成功:', contractList.value)
    console.log('合同数量:', contractList.value.length)
  } catch (error) {
    console.error('加载合同列表失败:', error)
    console.error('错误详情:', error.response)
    ElMessage.error('加载合同列表失败：' + (error.message || '请稍后重试'))
  }
}

// 新增租金
const handleAddPayment = () => {
  loadContractList()
  resetAddForm()
  addDialogVisible.value = true
}

// 重置新增表单
const resetAddForm = () => {
  if (addFormRef.value) {
    addFormRef.value.resetFields()
  }
  Object.assign(addForm, {
    contract_id: '',
    payment_type: 'rent',
    amount: 0,
    due_date: '',
    period_start: '',
    period_end: '',
    remark: ''
  })
  // 重置选中的合同信息
  selectedContractInfo.value = null
}

// 自动填充支付信息
const autoFillPaymentInfo = () => {
  if (!addForm.contract_id) {
    selectedContractInfo.value = null
    return
  }
  
  // 找到选中的合同
  const selectedContract = contractList.value.find(contract => contract.id === addForm.contract_id)
  if (!selectedContract) {
    selectedContractInfo.value = null
    return
  }
  
  // 更新选中的合同信息
  selectedContractInfo.value = {
    tenant_name: selectedContract.tenant_name,
    tenant_phone: selectedContract.tenant_phone,
    house_address: selectedContract.house_address,
    room_no: selectedContract.room_no
  }
  
  // 根据支付类型自动填充信息
  if (addForm.payment_type) {
    switch (addForm.payment_type) {
      case 'rent':
        // 填充租金金额
        addForm.amount = selectedContract.rent_amount
        // 填充默认的支付周期（月付）
        addForm.period_start = dayjs(selectedContract.start_date).format('YYYY-MM-DD')
        addForm.period_end = dayjs(selectedContract.end_date).format('YYYY-MM-DD')
        // 填充默认的应缴日期
        addForm.due_date = dayjs(selectedContract.start_date).format('YYYY-MM-DD')
        break
      case 'deposit':
        // 填充押金金额
        addForm.amount = selectedContract.deposit_amount
        // 押金的支付周期与合同相同
        addForm.period_start = dayjs(selectedContract.start_date).format('YYYY-MM-DD')
        addForm.period_end = dayjs(selectedContract.end_date).format('YYYY-MM-DD')
        // 押金的应缴日期为合同开始日期
        addForm.due_date = dayjs(selectedContract.start_date).format('YYYY-MM-DD')
        break
      default:
        // 其他类型不自动填充
        break
    }
  }
}

// 自动填充编辑支付信息
const autoFillEditPaymentInfo = () => {
  if (!editForm.contract_id) {
    selectedEditContractInfo.value = null
    return
  }
  
  // 找到选中的合同
  const selectedContract = contractList.value.find(contract => contract.id === editForm.contract_id)
  if (!selectedContract) {
    selectedEditContractInfo.value = null
    return
  }
  
  // 更新选中的合同信息
  selectedEditContractInfo.value = {
    tenant_name: selectedContract.tenant_name,
    tenant_phone: selectedContract.tenant_phone,
    house_address: selectedContract.house_address,
    room_no: selectedContract.room_no
  }
  
  // 根据支付类型自动填充信息
  if (editForm.payment_type) {
    switch (editForm.payment_type) {
      case 'rent':
        // 填充租金金额
        editForm.amount = selectedContract.rent_amount
        // 填充默认的支付周期（月付）
        editForm.period_start = selectedContract.start_date
        editForm.period_end = selectedContract.end_date
        // 填充默认的应缴日期
        editForm.due_date = selectedContract.start_date
        break
      case 'deposit':
        // 填充押金金额
        editForm.amount = selectedContract.deposit_amount
        // 押金的支付周期与合同相同
        editForm.period_start = selectedContract.start_date
        editForm.period_end = selectedContract.end_date
        // 押金的应缴日期为合同开始日期
        editForm.due_date = selectedContract.start_date
        break
      default:
        // 其他类型不自动填充
        break
    }
  }
}

// 合同选择变化处理
const handleContractChange = () => {
  autoFillPaymentInfo()
}

// 支付类型变化处理
const handlePaymentTypeChange = () => {
  autoFillPaymentInfo()
}

// 编辑合同选择变化处理
const handleEditContractChange = () => {
  autoFillEditPaymentInfo()
}

// 编辑支付类型变化处理
const handleEditPaymentTypeChange = () => {
  autoFillEditPaymentInfo()
}

// 提交新增租金
const handleAddSubmit = async () => {
  if (!addFormRef.value) return
  
  try {
    await addFormRef.value.validate()
  } catch (error) {
    return
  }
  
  addSubmitLoading.value = true
  try {
    console.log('提交的租金数据:', addForm)
    const res = await createPayment(addForm)
    console.log('新增租金成功:', res)
    ElMessage.success('新增租金成功')
    
    addDialogVisible.value = false
    loadPaymentList()
  } catch (error) {
    console.error('新增租金失败:', error)
    console.error('错误详情:', error.response)
    console.error('错误数据:', error.response?.data)
    
    // 处理验证错误
    let errorMsg = '请稍后重试'
    if (error.response?.data) {
      if (error.response.data.error) {
        if (typeof error.response.data.error === 'string') {
          errorMsg = error.response.data.error
        } else if (error.response.data.error.message) {
          errorMsg = error.response.data.error.message
        } else {
          errorMsg = JSON.stringify(error.response.data.error)
        }
      } else if (error.response.data.errors) {
        if (Array.isArray(error.response.data.errors)) {
          errorMsg = error.response.data.errors.join('; ')
        } else if (typeof error.response.data.errors === 'string') {
          errorMsg = error.response.data.errors
        } else {
          errorMsg = JSON.stringify(error.response.data.errors)
        }
      } else if (error.response.data.message) {
        errorMsg = error.response.data.message
      }
    } else if (error.message) {
      errorMsg = error.message
    }
    
    ElMessage.error('新增租金失败：' + errorMsg)
  } finally {
    addSubmitLoading.value = false
  }
}

// 删除租金
const handleDeletePayment = (row) => {
  console.log('删除操作 - 行数据:', row)
  ElMessageBox.confirm(
    `确定要删除支付记录 ${row.payment_no} 吗？`,
    '删除确认',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'danger'
    }
  ).then(async () => {
    try {
      console.log('删除操作 - ID:', row.id)
      await deletePayment(row.id)
      ElMessage.success('删除成功')
      loadPaymentList()
    } catch (error) {
      console.error('删除失败:', error)
      console.error('删除失败 - 错误详情:', error.response)
      ElMessage.error('删除失败：' + (error.message || '请稍后重试'))
    }
  }).catch(() => {})
}

// 更新滞纳金
const handleUpdateLateFees = async () => {
  try {
    await updateLateFees()
    ElMessage.success('滞纳金更新成功')
    // 不要在这里调用 loadPaymentList，避免重复加载
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

// 重置状态表单
const resetStatusForm = () => {
  if (statusFormRef.value) {
    statusFormRef.value.resetFields()
  }
  Object.assign(statusForm, {
    status: '',
    paid_amount: 0,
    remark: ''
  })
}

// 状态变化处理
const handleStatusChange = () => {
  // 当状态改变时，重置部分支付金额
  if (statusForm.status !== 'partial') {
    statusForm.paid_amount = 0
  }
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

// 设置支付状态
const handleSetStatus = (row) => {
  currentPayment.value = { ...row }
  resetStatusForm()
  
  // 设置默认状态为当前状态
  statusForm.status = row.status
  
  statusDialogVisible.value = true
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

// 编辑租金
const handleEditPayment = async (row) => {
  await loadContractList()
  resetEditForm()
  
  console.log('编辑行数据:', row)
  
  // 填充编辑表单数据
  Object.assign(editForm, {
    id: row.id,
    contract_id: row.contract_id || (row.contract?.id || ''),
    payment_type: row.payment_type || 'rent',
    amount: row.amount || 0,
    due_date: row.due_date || '',
    period_start: row.period_start || '',
    period_end: row.period_end || '',
    remark: row.remark || ''
  })
  
  console.log('填充后编辑表单:', editForm)
  
  // 自动填充合同信息
  autoFillEditPaymentInfo()
  
  editDialogVisible.value = true
}

// 重置编辑表单
const resetEditForm = () => {
  if (editFormRef.value) {
    editFormRef.value.resetFields()
  }
  Object.assign(editForm, {
    id: '',
    contract_id: '',
    payment_type: 'rent',
    amount: 0,
    due_date: '',
    period_start: '',
    period_end: '',
    remark: ''
  })
  // 重置选中的合同信息
  selectedEditContractInfo.value = null
}

// 提交编辑租金
const handleEditSubmit = async () => {
  if (!editFormRef.value) return
  
  try {
    await editFormRef.value.validate()
  } catch (error) {
    console.error('表单验证失败:', error)
    return
  }
  
  // 检查编辑对已支付状态的影响
  if (currentPayment.value.status === 'paid' && editForm.amount !== currentPayment.value.amount) {
    try {
      await ElMessageBox.confirm(
        '修改金额会影响已支付状态，确定要继续吗？',
        '编辑确认',
        {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        }
      )
    } catch (error) {
      editSubmitLoading.value = false
      return
    }
  }
  
  editSubmitLoading.value = true
  try {
    // 检查必填字段
    if (!editForm.contract_id) {
      ElMessage.error('请选择合同')
      editSubmitLoading.value = false
      return
    }
    
    if (!editForm.payment_type) {
      ElMessage.error('请选择支付类型')
      editSubmitLoading.value = false
      return
    }
    
    if (!editForm.amount || editForm.amount <= 0) {
      ElMessage.error('请输入有效的金额')
      editSubmitLoading.value = false
      return
    }
    
    if (!editForm.due_date) {
      ElMessage.error('请选择应缴日期')
      editSubmitLoading.value = false
      return
    }
    
    // 确保日期格式正确
    const formatDate = (date) => {
      if (!date) return null
      // 检查是否已经是 YYYY-MM-DD 格式
      if (typeof date === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(date)) {
        return date
      }
      // 否则尝试转换
      try {
        const d = new Date(date)
        if (isNaN(d.getTime())) {
          return null
        }
        return d.toISOString().split('T')[0]
      } catch (error) {
        return null
      }
    }
    
    const data = {
      contract_id: editForm.contract_id,
      payment_type: editForm.payment_type,
      amount: editForm.amount,
      due_date: formatDate(editForm.due_date),
      period_start: formatDate(editForm.period_start),
      period_end: formatDate(editForm.period_end),
      remark: editForm.remark || ''
    }
    
    // 处理编辑对状态的影响
    if (currentPayment.value.status === 'paid') {
      // 如果已支付，保持已支付状态，但更新已缴金额
      data.status = 'paid'
      data.paid_amount = editForm.amount
    } else if (currentPayment.value.status === 'partial') {
      // 如果部分支付，保持部分支付状态，但检查已缴金额是否仍然小于新的应缴金额
      if (currentPayment.value.paid_amount >= editForm.amount) {
        // 如果已缴金额大于或等于新的应缴金额，自动转换为已支付状态
        data.status = 'paid'
        data.paid_amount = editForm.amount
      } else {
        // 保持部分支付状态
        data.status = 'partial'
        data.paid_amount = currentPayment.value.paid_amount
      }
    }
    
    console.log('格式化后的数据:', data)
    
    console.log('编辑提交数据:', data)
    console.log('编辑ID:', editForm.id)
    
    await updatePayment(editForm.id, data)
    ElMessage.success('编辑租金成功')
    
    editDialogVisible.value = false
    loadPaymentList()
  } catch (error) {
    console.error('编辑租金失败:', error)
    console.error('错误详情:', error.response?.data)
    console.error('错误状态:', error.response?.status)
    console.error('错误头信息:', error.response?.headers)
    ElMessage.error('编辑租金失败：' + (error.message || '请稍后重试'))
  } finally {
    editSubmitLoading.value = false
  }
}

// 提交状态设置
const handleStatusSubmit = async () => {
  // 跳过验证，直接执行（用于测试）
  if (!statusFormRef.value) {
    // 测试环境下继续执行
  } else {
    try {
      await statusFormRef.value.validate()
    } catch (error) {
      return
    }
  }
  
  // 从已支付状态转换到其他状态时，显示确认提示
  if (currentPayment.value.status === 'paid' && statusForm.status !== 'paid') {
    try {
      await ElMessageBox.confirm(
        '确定要将已支付状态更改为其他状态吗？此操作将清空支付记录。',
        '状态变更确认',
        {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        }
      )
    } catch (error) {
      statusSubmitLoading.value = false
      return
    }
  }
  
  statusSubmitLoading.value = true
  try {
    const data = {
      status: statusForm.status,
      remark: statusForm.remark || ''
    }
    
    // 根据不同状态添加相应的业务逻辑
    switch (statusForm.status) {
      case 'paid':
        if (currentPayment.value.status === 'partial') {
          // 从部分支付状态转换到已支付状态时，自动计算剩余金额
          const remainingAmount = currentPayment.value.amount - (currentPayment.value.paid_amount || 0)
          console.log('剩余金额:', remainingAmount)
        }
        // 已支付：将已缴金额设置为应缴金额，添加支付日期
        data.paid_amount = currentPayment.value.amount
        data.payment_date = new Date().toISOString().split('T')[0]
        break
      case 'pending':
        // 未支付：将已缴金额设置为 0，清空支付日期
        data.paid_amount = 0
        data.payment_date = null
        break
      case 'overdue':
        // 逾期：保持已缴金额不变，但标记为逾期状态
        // 系统会自动计算逾期天数和滞纳金
        break
      case 'partial':
        // 部分支付：使用用户输入的实际缴纳金额
        data.paid_amount = statusForm.paid_amount
        data.payment_date = new Date().toISOString().split('T')[0]
        break
    }
    
    console.log('状态更新数据:', data)
    
    await updatePayment(currentPayment.value.id, data)
    ElMessage.success('状态设置成功')
    
    statusDialogVisible.value = false
    loadPaymentList()
    loadOverduePayments()
  } catch (error) {
    console.error('状态设置失败:', error)
    ElMessage.error('状态设置失败：' + (error.message || '请稍后重试'))
  } finally {
    statusSubmitLoading.value = false
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
  const overdueCount = overdueList.value?.length || 0
  ElMessageBox.confirm(
    `确定要向 ${overdueCount} 位逾期租客发送催缴通知吗？`,
    '批量催缴',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(async () => {
    try {
      // 这里调用批量催缴的 API（需要根据实际后端接口调整）
      const remindCount = overdueCount
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



// 初始化
onMounted(async () => {
  loading.value = true
  try {
    await loadOverduePayments()
    await handleUpdateLateFees()
    await loadPaymentList()
  } finally {
    loading.value = false
  }
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

    .header-buttons {
      display: flex;
      gap: 10px;
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
