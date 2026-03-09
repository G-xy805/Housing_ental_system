<template>
  <el-dialog
    v-model="visible"
    title="处理退款"
    width="800px"
    :close-on-click-modal="false"
    destroy-on-close
  >
    <el-descriptions :column="2" border style="margin-bottom: 20px">
      <el-descriptions-item label="合同编号">
        {{ refundData.contract_no }}
      </el-descriptions-item>
      <el-descriptions-item label="租客姓名">
        {{ refundData.tenant_name }}
      </el-descriptions-item>
      <el-descriptions-item label="房源地址">
        {{ refundData.house_address }}
      </el-descriptions-item>
      <el-descriptions-item label="房间号">
        {{ refundData.room_no }}
      </el-descriptions-item>
      <el-descriptions-item label="原始押金">
        <span class="money">¥{{ refundData.original_deposit }}</span>
      </el-descriptions-item>
      <el-descriptions-item label="退款状态">
        <el-tag :type="getStatusType(refundData.status)">
          {{ getStatusText(refundData.status) }}
        </el-tag>
      </el-descriptions-item>
    </el-descriptions>

    <div class="deduction-section">
      <div class="section-header">
        <h3>扣款项</h3>
        <el-button type="primary" size="small" @click="handleAddDeduction">
          <el-icon><Plus /></el-icon>
          添加扣款
        </el-button>
      </div>
      <el-table :data="deductions" style="width: 100%">
        <el-table-column prop="item" label="扣款项" width="200">
          <template #default="scope">
            <el-input
              v-model="scope.row.item"
              placeholder="请输入扣款项"
              size="small"
            />
          </template>
        </el-table-column>
        <el-table-column prop="amount" label="金额" width="150">
          <template #default="scope">
            <el-input-number
              v-model="scope.row.amount"
              :min="0"
              :precision="2"
              :step="100"
              size="small"
              style="width: 100%"
            />
          </template>
        </el-table-column>
        <el-table-column prop="remark" label="备注">
          <template #default="scope">
            <el-input
              v-model="scope.row.remark"
              placeholder="请输入备注"
              size="small"
            />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="80">
          <template #default="scope">
            <el-button
              link
              type="danger"
              size="small"
              @click="handleDeleteDeduction(scope.$index)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <div class="summary-section">
      <div class="summary-item">
        <span>原始押金：</span>
        <span class="money">¥{{ refundData.original_deposit }}</span>
      </div>
      <div class="summary-item">
        <span>扣款总额：</span>
        <span class="money danger">¥{{ totalDeduction }}</span>
      </div>
      <div class="summary-item total">
        <span>退款金额：</span>
        <span class="money success">¥{{ refundAmount }}</span>
      </div>
    </div>

    <el-form :model="processForm" label-width="100px" style="margin-top: 20px">
      <el-form-item label="处理备注">
        <el-input
          v-model="processForm.remark"
          type="textarea"
          :rows="3"
          placeholder="请输入处理备注"
        />
      </el-form-item>
    </el-form>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleCancel">取消</el-button>
        <el-button
          type="warning"
          @click="handleProcess"
          :loading="loading"
          v-if="refundData.status === 'pending'"
        >
          处理
        </el-button>
        <el-button
          type="success"
          @click="handleComplete"
          :loading="loading"
          v-if="refundData.status === 'processing'"
        >
          完成
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { processRefund, completeRefund } from '@/api/depositRefund'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  refundData: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['update:modelValue', 'success'])

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const loading = ref(false)
const deductions = ref([])
const processForm = ref({
  remark: ''
})

const totalDeduction = computed(() => {
  return deductions.value.reduce((sum, item) => sum + (item.amount || 0), 0)
})

const refundAmount = computed(() => {
  const original = parseFloat(props.refundData.original_deposit) || 0
  return Math.max(0, original - totalDeduction.value)
})

const getStatusType = (status) => {
  const types = {
    pending: 'warning',
    processing: 'primary',
    completed: 'success',
    cancelled: 'danger'
  }
  return types[status] || 'info'
}

const getStatusText = (status) => {
  const texts = {
    pending: '待处理',
    processing: '处理中',
    completed: '已完成',
    cancelled: '已取消'
  }
  return texts[status] || status
}

const handleAddDeduction = () => {
  deductions.value.push({
    item: '',
    amount: 0,
    remark: ''
  })
}

const handleDeleteDeduction = (index) => {
  deductions.value.splice(index, 1)
}

const handleProcess = async () => {
  loading.value = true
  try {
    const data = {
      deductions: deductions.value,
      remark: processForm.value.remark
    }
    await processRefund(props.refundData.id, data)
    ElMessage.success('处理成功')
    emit('success')
    visible.value = false
  } catch (error) {
    console.error('处理退款失败:', error)
    ElMessage.error('处理退款失败：' + (error.message || '请稍后重试'))
  } finally {
    loading.value = false
  }
}

const handleComplete = async () => {
  loading.value = true
  try {
    const data = {
      remark: processForm.value.remark
    }
    await completeRefund(props.refundData.id, data)
    ElMessage.success('完成成功')
    emit('success')
    visible.value = false
  } catch (error) {
    console.error('完成退款失败:', error)
    ElMessage.error('完成退款失败：' + (error.message || '请稍后重试'))
  } finally {
    loading.value = false
  }
}

const handleCancel = () => {
  visible.value = false
}

watch(() => props.modelValue, (val) => {
  if (val) {
    deductions.value = props.refundData.deductions || []
    processForm.value.remark = props.refundData.process_remark || ''
  }
})
</script>

<style lang="scss" scoped>
.deduction-section {
  margin-bottom: 20px;

  .section-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 10px;

    h3 {
      margin: 0;
      font-size: 16px;
      color: #333;
    }
  }
}

.summary-section {
  background: #f5f7fa;
  padding: 15px;
  border-radius: 4px;

  .summary-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 8px 0;
    font-size: 14px;

    &.total {
      border-top: 1px solid #dcdfe6;
      margin-top: 8px;
      padding-top: 12px;
      font-size: 16px;
      font-weight: bold;
    }

    .money {
      font-weight: bold;

      &.danger {
        color: #f56c6c;
      }

      &.success {
        color: #67c23a;
      }
    }
  }
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
</style>
