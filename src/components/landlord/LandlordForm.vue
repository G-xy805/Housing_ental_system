<template>
  <el-form
    ref="formRef"
    :model="formData"
    :rules="formRules"
    label-width="120px"
    class="landlord-form"
  >
    <el-row :gutter="20">
      <el-col :span="12">
        <el-form-item label="姓名" prop="name">
          <el-input v-model="formData.name" placeholder="请输入房东姓名" maxlength="50" show-word-limit />
        </el-form-item>
      </el-col>
      <el-col :span="12">
        <el-form-item label="身份证号" prop="id_card">
          <el-input 
            v-model="formData.id_card" 
            placeholder="请输入 18 位身份证号" 
            maxlength="18"
            @input="handleIdCardInput"
          />
        </el-form-item>
      </el-col>
    </el-row>

    <el-row :gutter="20">
      <el-col :span="12">
        <el-form-item label="手机号" prop="phone">
          <el-input 
            v-model="formData.phone" 
            placeholder="请输入 11 位手机号" 
            maxlength="11"
            @input="handlePhoneInput"
          />
        </el-form-item>
      </el-col>
      <el-col :span="12">
        <el-form-item label="状态" prop="status" v-if="isEdit">
          <el-select v-model="formData.status" placeholder="请选择状态" style="width: 100%">
            <el-option label="正常" value="active" />
            <el-option label="停用" value="inactive" />
            <el-option label="黑名单" value="blacklisted" />
          </el-select>
        </el-form-item>
      </el-col>
    </el-row>

    <el-divider content-position="left">银行卡信息</el-divider>

    <el-row :gutter="20">
      <el-col :span="12">
        <el-form-item label="银行卡号" prop="bank_card">
          <el-input 
            v-model="formData.bank_card" 
            placeholder="请输入银行卡号（可选）"
            maxlength="19"
            @input="handleBankCardInput"
          />
        </el-form-item>
      </el-col>
      <el-col :span="12">
        <el-form-item label="开户行名称" prop="bank_name">
          <el-input v-model="formData.bank_name" placeholder="请输入开户行名称（可选）" maxlength="100" show-word-limit />
        </el-form-item>
      </el-col>
    </el-row>

    <el-divider content-position="left">房产信息</el-divider>

    <el-row :gutter="20">
      <el-col :span="12">
        <el-form-item label="房产证编号" prop="property_cert_no">
          <el-input v-model="formData.property_cert_no" placeholder="请输入房产证编号（可选）" maxlength="50" show-word-limit />
        </el-form-item>
      </el-col>
      <el-col :span="12">
        <el-form-item label="房产地址" prop="address">
          <el-input v-model="formData.address" placeholder="请输入房产地址（可选）" maxlength="255" show-word-limit />
        </el-form-item>
      </el-col>
    </el-row>

    <el-divider content-position="left">其他信息</el-divider>

    <el-form-item label="备注" prop="remark">
      <el-input
        v-model="formData.remark"
        type="textarea"
        :rows="3"
        placeholder="请输入备注信息（可选）"
        maxlength="500"
        show-word-limit
      />
    </el-form-item>

    <el-form-item>
      <el-button type="primary" @click="handleSubmit" :loading="submitLoading">
        {{ isEdit ? '保存修改' : '立即创建' }}
      </el-button>
      <el-button @click="handleCancel">取消</el-button>
      <el-button 
        v-if="isEdit && showDeleteButton" 
        type="danger" 
        @click="handleDelete"
        :disabled="deleteDisabled"
      >
        删除
      </el-button>
    </el-form-item>
  </el-form>
</template>

<script setup>
import { ref, reactive, watch } from 'vue'
import { ElMessage } from 'element-plus'

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
  showDeleteButton: {
    type: Boolean,
    default: true
  },
  deleteDisabled: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:modelValue', 'submit', 'cancel', 'delete'])

// 表单引用
const formRef = ref(null)

// 默认表单数据
const defaultFormData = {
  name: '',
  id_card: '',
  phone: '',
  bank_card: '',
  bank_name: '',
  property_cert_no: '',
  address: '',
  status: 'active',
  remark: ''
}

const formData = reactive({ ...defaultFormData })

// 表单验证规则
const formRules = {
  name: [
    { required: true, message: '请输入房东姓名', trigger: 'blur' },
    { min: 2, max: 50, message: '长度在 2 到 50 个字符', trigger: 'blur' }
  ],
  id_card: [
    { required: true, message: '请输入身份证号', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (!value) {
          callback(new Error('请输入身份证号'))
          return
        }
        // 验证身份证号格式：18 位，前 17 位数字，最后一位数字或 X
        const idCardRegex = /^[1-9]\d{5}(18|19|20)\d{2}(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])\d{3}[\dXx]$/
        if (!idCardRegex.test(value)) {
          callback(new Error('请输入正确的 18 位身份证号格式'))
          return
        }
        callback()
      },
      trigger: 'blur'
    }
  ],
  phone: [
    { required: true, message: '请输入手机号', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (!value) {
          callback(new Error('请输入手机号'))
          return
        }
        // 验证手机号格式：11 位，1 开头，第二位 3-9
        const phoneRegex = /^1[3-9]\d{9}$/
        if (!phoneRegex.test(value)) {
          callback(new Error('请输入正确的 11 位手机号码'))
          return
        }
        callback()
      },
      trigger: 'blur'
    }
  ],
  bank_card: [
    {
      validator: (rule, value, callback) => {
        if (value && !/^\d+$/.test(value)) {
          callback(new Error('银行卡号必须是数字'))
          return
        }
        callback()
      },
      trigger: 'blur'
    }
  ]
}

// 身份证号输入处理（自动转大写 X）
const handleIdCardInput = (value) => {
  // 将最后一位如果是 x 转为 X
  if (value && value.length === 18) {
    const lastChar = value.charAt(17)
    if (lastChar === 'x') {
      formData.id_card = value.slice(0, 17) + 'X'
    }
  }
}

// 手机号输入处理（只允许数字）
const handlePhoneInput = (value) => {
  // 移除所有非数字字符
  formData.phone = value.replace(/\D/g, '')
}

// 银行卡号输入处理（只允许数字）
const handleBankCardInput = (value) => {
  // 移除所有非数字字符
  formData.bank_card = value.replace(/\D/g, '')
}

// 初始化表单数据
const initFormData = () => {
  if (props.modelValue && Object.keys(props.modelValue).length > 0) {
    const modelValueCopy = {
      ...defaultFormData,
      ...props.modelValue
    }
    Object.assign(formData, modelValueCopy)
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
    
    // 准备提交数据
    const submitData = {
      name: formData.name,
      id_card: formData.id_card,
      phone: formData.phone,
      bank_card: formData.bank_card || undefined,
      bank_name: formData.bank_name || undefined,
      property_cert_no: formData.property_cert_no || undefined,
      address: formData.address || undefined,
      remark: formData.remark || undefined
    }

    // 如果是编辑模式，添加状态字段
    if (props.isEdit) {
      submitData.status = formData.status
    }
    
    console.log('提交数据:', submitData)
    
    // 触发提交事件
    emit('submit', submitData)
  } catch (error) {
    console.error('表单验证失败:', error)
    // 如果是表单验证失败，不显示错误提示（表单会显示具体错误）
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

// 删除
const handleDelete = () => {
  emit('delete', formData)
}

// 重置表单
const resetForm = () => {
  formRef.value?.resetFields()
  Object.assign(formData, defaultFormData)
}

// 暴露方法给父组件
defineExpose({
  resetForm,
  validate: () => formRef.value?.validate()
})
</script>

<style lang="scss" scoped>
.landlord-form {
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
}
</style>
