<template>
  <el-form
    ref="formRef"
    :model="formData"
    :rules="formRules"
    label-width="120px"
    class="landlord-contract-form"
  >
    <!-- 基本信息 -->
    <el-divider content-position="left">基本信息</el-divider>
    
    <el-form-item label="合同标题" prop="title">
      <el-input 
        v-model="formData.title" 
        placeholder="请输入合同标题" 
        maxlength="100" 
        show-word-limit 
        :disabled="disabled"
      />
    </el-form-item>

    <el-form-item label="房东" prop="landlord_id">
      <el-select
        v-model="formData.landlord_id"
        placeholder="请选择房东"
        filterable
        style="width: 100%"
        :disabled="disabled"
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

    <!-- 房源信息 -->
    <el-divider content-position="left">房源信息</el-divider>

    <el-form-item label="房源" prop="properties">
      <el-select
        v-model="formData.properties"
        placeholder="请选择房源（可多选）"
        filterable
        multiple
        collapse-tags
        collapse-tags-tooltip
        style="width: 100%"
        :disabled="disabled"
        @change="handlePropertyChange"
      >
        <el-option
          v-for="property in propertyOptions"
          :key="property.id"
          :label="property.address"
          :value="property.id"
        >
          <span>{{ property.address }}</span>
          <span style="color: #8492a6; font-size: 13px; margin-left: 10px">
            ({{ property.type }})
          </span>
        </el-option>
      </el-select>
    </el-form-item>

    <el-form-item label="占用检查" prop="occupancy_check">
      <el-alert
        v-if="occupiedProperties.length > 0"
        title="以下房源已被其他生效合同占用"
        type="warning"
        :closable="false"
        show-icon
        class="occupancy-alert"
      >
        <div class="occupied-list">
          <el-tag
            v-for="prop in occupiedProperties"
            :key="prop.id"
            type="danger"
            size="small"
            class="occupied-tag"
          >
            {{ prop.address }}
          </el-tag>
        </div>
      </el-alert>
      <el-alert
        v-else-if="formData.properties.length > 0"
        title="所选房源均可用"
        type="success"
        :closable="false"
        show-icon
      />
      <span v-else class="form-tip">选择房源后将自动检查占用情况</span>
    </el-form-item>

    <!-- 合同期限 -->
    <el-divider content-position="left">合同期限</el-divider>

    <el-row :gutter="20">
      <el-col :span="12">
        <el-form-item label="开始日期" prop="start_date">
          <el-date-picker
            v-model="formData.start_date"
            type="date"
            placeholder="选择开始日期"
            style="width: 100%"
            :disabled="disabled"
            value-format="YYYY-MM-DD"
            :disabled-date="disabledStartDate"
          />
        </el-form-item>
      </el-col>
      <el-col :span="12">
        <el-form-item label="结束日期" prop="end_date">
          <el-date-picker
            v-model="formData.end_date"
            type="date"
            placeholder="选择结束日期"
            style="width: 100%"
            :disabled="disabled"
            value-format="YYYY-MM-DD"
            :disabled-date="disabledEndDate"
          />
        </el-form-item>
      </el-col>
    </el-row>

    <!-- 费用信息 -->
    <el-divider content-position="left">费用信息</el-divider>

    <el-row :gutter="20">
      <el-col :span="12">
        <el-form-item label="合同金额" prop="contract_amount">
          <el-input-number
            v-model="formData.contract_amount"
            :min="0"
            :precision="2"
            :step="100"
            placeholder="请输入合同金额"
            style="width: 100%"
            :disabled="disabled"
          />
          <span class="unit-label">元</span>
        </el-form-item>
      </el-col>
      <el-col :span="12">
        <el-form-item label="服务费率" prop="service_fee_rate">
          <el-input-number
            v-model="formData.service_fee_rate"
            :min="0"
            :max="100"
            :precision="2"
            :step="0.1"
            placeholder="请输入服务费率"
            style="width: 100%"
            :disabled="disabled"
          />
          <span class="unit-label">%</span>
        </el-form-item>
      </el-col>
    </el-row>

    <el-row :gutter="20">
      <el-col :span="12">
        <el-form-item label="最低服务费" prop="min_service_fee">
          <el-input-number
            v-model="formData.min_service_fee"
            :min="0"
            :precision="2"
            :step="100"
            placeholder="请输入最低服务费"
            style="width: 100%"
            :disabled="disabled"
          />
          <span class="unit-label">元</span>
        </el-form-item>
      </el-col>
      <el-col :span="12">
        <el-form-item label="付款周期" prop="payment_cycle">
          <el-input-number
            v-model="formData.payment_cycle"
            :min="1"
            :step="1"
            placeholder="请输入付款周期"
            style="width: 100%"
            :disabled="disabled"
          />
          <span class="unit-label">月</span>
        </el-form-item>
      </el-col>
    </el-row>

    <!-- 其他信息 -->
    <el-divider content-position="left">其他信息</el-divider>

    <el-form-item label="合同描述" prop="description">
      <el-input
        v-model="formData.description"
        type="textarea"
        :rows="3"
        placeholder="请输入合同描述（可选）"
        maxlength="500"
        show-word-limit
        :disabled="disabled"
      />
    </el-form-item>

    <el-form-item label="备注" prop="remark">
      <el-input
        v-model="formData.remark"
        type="textarea"
        :rows="3"
        placeholder="请输入备注信息（可选）"
        maxlength="500"
        show-word-limit
        :disabled="disabled"
      />
    </el-form-item>

    <!-- 提交按钮 -->
    <el-form-item>
      <el-button type="primary" @click="handleSubmit" :loading="submitLoading" :disabled="disabled">
        {{ isEdit ? '保存修改' : '立即创建' }}
      </el-button>
      <el-button @click="handleCancel" :disabled="disabled">取消</el-button>
    </el-form-item>
  </el-form>
</template>

<script setup>
import { ref, reactive, watch, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getLandlordList } from '@/api/landlord'
import { getHouseList } from '@/api/house'
import { getLandlordContractList } from '@/api/landlordContract'
import dayjs from 'dayjs'

const props = defineProps({
  modelValue: {
    type: Object,
    default: () => ({})
  },
  isEdit: {
    type: Boolean,
    default: false
  },
  submitLoading: {
    type: Boolean,
    default: false
  },
  disabled: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:modelValue', 'submit', 'cancel'])

// 表单引用
const formRef = ref(null)

// 选项数据
const landlordOptions = ref([])
const propertyOptions = ref([])
const occupiedProperties = ref([])

// 默认表单数据
const defaultFormData = {
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
}

const formData = reactive({ ...defaultFormData })

// 表单验证规则
const formRules = {
  title: [
    { required: true, message: '请输入合同标题', trigger: 'blur' },
    { min: 2, max: 100, message: '长度在 2 到 100 个字符', trigger: 'blur' }
  ],
  landlord_id: [
    { required: true, message: '请选择房东', trigger: 'change' }
  ],
  properties: [
    { required: true, message: '请至少选择一个房源', trigger: 'change' }
  ],
  start_date: [
    { required: true, message: '请选择开始日期', trigger: 'change' }
  ],
  end_date: [
    { required: true, message: '请选择结束日期', trigger: 'change' },
    {
      validator: (rule, value, callback) => {
        if (!value) {
          callback(new Error('请选择结束日期'))
          return
        }
        if (!formData.start_date) {
          callback()
          return
        }
        const startDate = dayjs(formData.start_date)
        const endDate = dayjs(value)
        if (endDate.isBefore(startDate) || endDate.isSame(startDate)) {
          callback(new Error('结束日期必须晚于开始日期'))
          return
        }
        callback()
      },
      trigger: 'change'
    }
  ],
  contract_amount: [
    { required: true, message: '请输入合同金额', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value < 0) {
          callback(new Error('合同金额不能为负数'))
          return
        }
        callback()
      },
      trigger: 'blur'
    }
  ],
  service_fee_rate: [
    { required: true, message: '请输入服务费率', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value < 0 || value > 100) {
          callback(new Error('服务费率必须在 0-100 之间'))
          return
        }
        callback()
      },
      trigger: 'blur'
    }
  ],
  min_service_fee: [
    {
      validator: (rule, value, callback) => {
        if (value !== null && value !== undefined && value < 0) {
          callback(new Error('最低服务费不能为负数'))
          return
        }
        callback()
      },
      trigger: 'blur'
    }
  ],
  payment_cycle: [
    {
      validator: (rule, value, callback) => {
        if (value !== null && value !== undefined && value < 1) {
          callback(new Error('付款周期至少为 1 个月'))
          return
        }
        callback()
      },
      trigger: 'blur'
    }
  ]
}

// 禁用开始日期（不能选择今天之前的日期）
const disabledStartDate = (time) => {
  return time.getTime() < Date.now() - 86400000
}

// 禁用结束日期（不能选择开始日期之前的日期）
const disabledEndDate = (time) => {
  if (!formData.start_date) return false
  const startDate = dayjs(formData.start_date)
  return time.getTime() <= startDate.toDate().getTime()
}

// 加载房东列表
const loadLandlordOptions = async () => {
  try {
    const res = await getLandlordList({ page: 1, page_size: 100 })
    landlordOptions.value = res.data?.items || []
  } catch (error) {
    console.error('加载房东列表失败:', error)
  }
}

// 加载房源列表
const loadPropertyOptions = async () => {
  try {
    const res = await getHouseList({ page: 1, page_size: 100 })
    propertyOptions.value = res.data?.items || []
  } catch (error) {
    console.error('加载房源列表失败:', error)
  }
}

// 检查房源占用情况
const checkPropertyOccupancy = async (propertyIds) => {
  if (!propertyIds || propertyIds.length === 0) {
    occupiedProperties.value = []
    return
  }

  try {
    // 获取所有生效中的合同
    const res = await getLandlordContractList({
      page: 1,
      page_size: 100,
      status: 'active'
    })
    
    const contracts = res.data?.items || []
    const today = dayjs()
    
    // 找出被占用的房源
    const occupiedMap = new Map()
    
    contracts.forEach(contract => {
      // 检查合同是否在有效期内
      const startDate = dayjs(contract.start_date)
      const endDate = dayjs(contract.end_date)
      
      if (today.isAfter(startDate) && today.isBefore(endDate)) {
        // 合同正在生效中
        if (contract.properties && Array.isArray(contract.properties)) {
          contract.properties.forEach(prop => {
            if (propertyIds.includes(prop.id)) {
              occupiedMap.set(prop.id, prop)
            }
          })
        }
      }
    })
    
    occupiedProperties.value = Array.from(occupiedMap.values())
    
    if (occupiedProperties.value.length > 0) {
      ElMessage.warning('部分房源已被其他生效合同占用，请重新选择')
    }
  } catch (error) {
    console.error('检查房源占用失败:', error)
  }
}

// 房东变化处理
const handleLandlordChange = () => {
  // 可以在这里添加房东变化后的逻辑
}

// 房源变化处理
const handlePropertyChange = (propertyIds) => {
  checkPropertyOccupancy(propertyIds)
}

// 初始化表单数据
const initFormData = () => {
  if (props.modelValue && Object.keys(props.modelValue).length > 0) {
    const modelValueCopy = {
      ...defaultFormData,
      ...props.modelValue
    }
    Object.assign(formData, modelValueCopy)
    
    // 如果是编辑模式，加载占用检查
    if (props.isEdit && formData.properties && formData.properties.length > 0) {
      const propertyIds = formData.properties.map(p => typeof p === 'object' ? p.id : p)
      checkPropertyOccupancy(propertyIds)
    }
  } else {
    Object.assign(formData, defaultFormData)
  }
}

watch(() => props.modelValue, () => {
  initFormData()
}, { immediate: true, deep: true })

// 提交表单
const handleSubmit = async () => {
  try {
    await formRef.value.validate()
    
    // 检查是否有房源被占用
    if (occupiedProperties.value.length > 0) {
      ElMessage.warning('存在被占用的房源，请重新选择')
      return false
    }
    
    // 准备提交数据
    const submitData = {
      title: formData.title,
      landlord_id: formData.landlord_id,
      properties: formData.properties.map(p => typeof p === 'object' ? p.id : p),
      start_date: formData.start_date,
      end_date: formData.end_date,
      contract_amount: formData.contract_amount,
      service_fee_rate: formData.service_fee_rate,
      min_service_fee: formData.min_service_fee || undefined,
      payment_cycle: formData.payment_cycle || undefined,
      description: formData.description || undefined,
      remark: formData.remark || undefined
    }
    
    console.log('提交数据:', submitData)
    
    // 触发提交事件
    emit('submit', submitData)
    return true
  } catch (error) {
    console.error('表单验证失败:', error)
    if (error.name === 'ValidationError') {
      return false
    }
    ElMessage.error(error.message || '提交失败，请重试')
    return false
  }
}

// 取消
const handleCancel = () => {
  emit('cancel')
}

// 重置表单
const resetForm = () => {
  formRef.value?.resetFields()
  Object.assign(formData, defaultFormData)
  occupiedProperties.value = []
}

// 暴露方法给父组件
defineExpose({
  resetForm,
  validate: () => formRef.value?.validate()
})

// 初始化
onMounted(() => {
  loadLandlordOptions()
  loadPropertyOptions()
})
</script>

<style lang="scss" scoped>
.landlord-contract-form {
  padding: 20px;
  
  :deep(.el-form-item) {
    margin-bottom: 22px;
  }
  
  :deep(.el-divider) {
    margin: 20px 0;
    
    .el-divider__text {
      font-weight: 600;
      color: #303133;
    }
  }
  
  .unit-label {
    margin-left: 10px;
    color: #909399;
  }
  
  .form-tip {
    font-size: 12px;
    color: #909399;
  }
  
  .occupancy-alert {
    margin-bottom: 10px;
    
    .occupied-list {
      margin-top: 10px;
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      
      .occupied-tag {
        cursor: default;
      }
    }
  }
}
</style>
