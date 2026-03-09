<template>
  <div class="deposit-refund-list-page">
    <div class="page-header">
      <h2>押金退款管理</h2>
    </div>

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
        <el-form-item label="退款状态">
          <el-select
            v-model="searchForm.status"
            placeholder="全部"
            clearable
            style="width: 120px"
          >
            <el-option label="全部" value="" />
            <el-option label="待处理" value="pending" />
            <el-option label="已处理" value="processed" />
            <el-option label="已完成" value="completed" />
            <el-option label="已取消" value="cancelled" />
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

    <el-card class="table-card" shadow="hover">
      <el-table
        :data="refundList"
        style="width: 100%"
        v-loading="loading"
      >
        <el-table-column prop="contract_no" label="合同编号" min-width="160" />
        <el-table-column prop="tenant_name" label="租客姓名" width="90" />
        <el-table-column prop="house_address" label="房源地址" min-width="180" show-overflow-tooltip />
        <el-table-column label="原始押金" width="100">
          <template #default="scope">
            <span>¥{{ scope.row.original_deposit }}</span>
          </template>
        </el-table-column>
        <el-table-column label="扣款金额" width="100">
          <template #default="scope">
            <span class="danger">¥{{ scope.row.deduction_amount || 0 }}</span>
          </template>
        </el-table-column>
        <el-table-column label="退款金额" width="100">
          <template #default="scope">
            <span class="success">¥{{ scope.row.refund_amount }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="90">
          <template #default="scope">
            <el-tag :type="getStatusType(scope.row.status)">
              {{ getStatusText(scope.row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="160" />
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="scope">
            <el-button link type="primary" @click="handleView(scope.row)">
              <el-icon><View /></el-icon>
              查看详情
            </el-button>
            <el-button
              link
              type="primary"
              @click="handleProcess(scope.row)"
              v-if="scope.row.status === 'pending' || scope.row.status === 'processed'"
            >
              <el-icon><Edit /></el-icon>
              处理退款
            </el-button>
            <el-button
              link
              type="danger"
              @click="handleCancel(scope.row)"
              v-if="scope.row.status === 'pending'"
            >
              <el-icon><Close /></el-icon>
              取消
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      <template #empty>
        <el-empty description="暂无退款数据" />
      </template>
    </el-card>

    <el-card class="pagination-card" v-if="refundList.length > 0">
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

    <el-dialog
      v-model="detailVisible"
      title="退款详情"
      width="800px"
      destroy-on-close
    >
      <el-descriptions :column="2" border>
        <el-descriptions-item label="合同编号">
          {{ currentRefund.contract_no }}
        </el-descriptions-item>
        <el-descriptions-item label="退款状态">
          <el-tag :type="getStatusType(currentRefund.status)">
            {{ getStatusText(currentRefund.status) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="租客姓名">
          {{ currentRefund.tenant_name }}
        </el-descriptions-item>
        <el-descriptions-item label="租客手机号">
          {{ currentRefund.tenant_phone || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="房源地址">
          {{ currentRefund.house_address }}
        </el-descriptions-item>
        <el-descriptions-item label="房间号">
          {{ currentRefund.room_no }}
        </el-descriptions-item>
        <el-descriptions-item label="原始押金">
          <span class="money">¥{{ currentRefund.original_deposit }}</span>
        </el-descriptions-item>
        <el-descriptions-item label="扣款总额">
          <span class="money danger">¥{{ currentRefund.deduction_amount || 0 }}</span>
        </el-descriptions-item>
        <el-descriptions-item label="退款金额">
          <span class="money success">¥{{ currentRefund.refund_amount }}</span>
        </el-descriptions-item>
        <el-descriptions-item label="创建时间">
          {{ currentRefund.created_at }}
        </el-descriptions-item>
        <el-descriptions-item label="处理备注" :span="2">
          {{ currentRefund.process_remark || '-' }}
        </el-descriptions-item>
      </el-descriptions>

      <div v-if="currentRefund.deductions && currentRefund.deductions.length > 0" style="margin-top: 20px">
        <h3>扣款项明细</h3>
        <el-table :data="currentRefund.deductions" style="width: 100%">
          <el-table-column prop="item" label="扣款项" />
          <el-table-column prop="amount" label="金额">
            <template #default="scope">
              <span class="danger">¥{{ scope.row.amount }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="remark" label="备注" />
        </el-table>
      </div>

      <template #footer>
        <el-button @click="detailVisible = false">关闭</el-button>
      </template>
    </el-dialog>

    <RefundProcessDialog
      v-model="processVisible"
      :refund-data="currentRefund"
      @success="loadRefundList"
    />
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Search,
  Refresh,
  View,
  Edit,
  Close
} from '@element-plus/icons-vue'
import {
  getDepositRefunds,
  getDepositRefund,
  cancelRefund
} from '@/api/depositRefund'
import RefundProcessDialog from './components/RefundProcessDialog.vue'

const loading = ref(false)
const refundList = ref([])
const detailVisible = ref(false)
const processVisible = ref(false)
const currentRefund = ref({})

const searchForm = reactive({
  keyword: '',
  status: '',
  page: 1,
  per_page: 10
})

const pagination = reactive({
  page: 1,
  per_page: 10,
  total: 0
})

const getStatusType = (status) => {
  const types = {
    pending: 'warning',
    processed: 'primary',
    completed: 'success',
    cancelled: 'danger'
  }
  return types[status] || 'info'
}

const getStatusText = (status) => {
  const texts = {
    pending: '待处理',
    processed: '已处理',
    completed: '已完成',
    cancelled: '已取消'
  }
  return texts[status] || status
}

const loadRefundList = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      per_page: pagination.per_page,
      ...searchForm
    }
    const res = await getDepositRefunds(params)
    refundList.value = res.data?.items || []
    pagination.total = res.data?.pagination?.total || 0
  } catch (error) {
    console.error('加载退款列表失败:', error)
    ElMessage.error('加载退款列表失败')
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  pagination.page = 1
  loadRefundList()
}

const handleReset = () => {
  Object.assign(searchForm, {
    keyword: '',
    status: '',
    page: 1,
    per_page: 10
  })
  handleSearch()
}

const handleView = async (row) => {
  try {
    const res = await getDepositRefund(row.id)
    currentRefund.value = res.data || row
    detailVisible.value = true
  } catch (error) {
    console.error('加载退款详情失败:', error)
    ElMessage.error('加载退款详情失败')
    currentRefund.value = { ...row }
    detailVisible.value = true
  }
}

const handleProcess = (row) => {
  currentRefund.value = { ...row }
  processVisible.value = true
}

const handleCancel = (row) => {
  ElMessageBox.confirm('确定要取消该退款吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      await cancelRefund(row.id, { remark: '用户取消' })
      ElMessage.success('取消成功')
      loadRefundList()
    } catch (error) {
      console.error('取消失败:', error)
      ElMessage.error('取消失败')
    }
  }).catch(() => {})
}

const handleSizeChange = (size) => {
  pagination.per_page = size
  pagination.page = 1
  loadRefundList()
}

const handlePageChange = (page) => {
  pagination.page = page
  loadRefundList()
}

onMounted(() => {
  loadRefundList()
})
</script>

<style lang="scss" scoped>
.deposit-refund-list-page {
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

    .danger {
      color: #f56c6c;
      font-weight: bold;
    }

    .success {
      color: #67c23a;
      font-weight: bold;
    }

    .money {
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
