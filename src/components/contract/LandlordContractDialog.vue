<template>
  <el-dialog
    v-model="dialogVisible"
    :title="dialogTitle"
    width="800px"
    :close-on-click-modal="false"
    destroy-on-close
    @closed="handleClosed"
  >
    <LandlordContractForm
      ref="formRef"
      v-model="formData"
      :is-edit="isEdit"
      :submit-loading="submitLoading"
      @submit="handleSubmit"
      @cancel="handleCancel"
    />
  </el-dialog>
</template>

<script setup>
import { ref, reactive, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import LandlordContractForm from './LandlordContractForm.vue'
import {
  createLandlordContract,
  updateLandlordContract
} from '@/api/landlordContract'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  editData: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['update:modelValue', 'success'])

const formRef = ref(null)
const submitLoading = ref(false)
const formData = reactive({})

// 对话框标题
const dialogTitle = computed(() => {
  return isEdit.value ? '编辑承包合同' : '新建承包合同'
})

// 是否为编辑模式
const isEdit = computed(() => {
  return !!props.editData?.id
})

// 对话框可见性
const dialogVisible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

// 监听编辑数据变化
watch(() => props.editData, (newData) => {
  if (newData && Object.keys(newData).length > 0) {
    // 填充表单数据
    Object.assign(formData, {
      id: newData.id,
      title: newData.title || '',
      landlord_id: newData.landlord_id || null,
      properties: newData.properties || [],
      start_date: newData.start_date || '',
      end_date: newData.end_date || '',
      contract_amount: newData.contract_amount || 0,
      service_fee_rate: newData.service_fee_rate || 0,
      min_service_fee: newData.min_service_fee || null,
      payment_cycle: newData.payment_cycle || null,
      description: newData.description || '',
      remark: newData.remark || ''
    })
  } else {
    // 清空表单
    Object.assign(formData, {
      id: null,
      title: '',
      landlord_id: null,
      properties: [],
      start_date: '',
      end_date: '',
      contract_amount: 0,
      service_fee_rate: 0,
      min_service_fee: null,
      payment_cycle: null,
      description: '',
      remark: ''
    })
  }
}, { immediate: true, deep: true })

// 提交表单
const handleSubmit = async (data) => {
  submitLoading.value = true
  
  try {
    if (isEdit.value && formData.id) {
      // 编辑模式
      await updateLandlordContract(formData.id, data)
      ElMessage.success('编辑成功')
    } else {
      // 创建模式
      await createLandlordContract(data)
      ElMessage.success('创建成功')
    }
    
    // 关闭对话框
    dialogVisible.value = false
    
    // 通知父组件刷新列表
    emit('success')
  } catch (error) {
    console.error('提交失败:', error)
    ElMessage.error(error.message || '提交失败，请重试')
  } finally {
    submitLoading.value = false
  }
}

// 取消
const handleCancel = () => {
  dialogVisible.value = false
}

// 对话框关闭后清理
const handleClosed = () => {
  if (formRef.value) {
    formRef.value.resetForm()
  }
  Object.assign(formData, {
    id: null,
    title: '',
    landlord_id: null,
    properties: [],
    start_date: '',
    end_date: '',
    contract_amount: 0,
    service_fee_rate: 0,
    min_service_fee: null,
    payment_cycle: null,
    description: '',
    remark: ''
  })
}
</script>

<style lang="scss" scoped>
// 样式由子组件负责
</style>
