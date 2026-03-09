<template>
  <el-dialog
    v-model="dialogVisible"
    :title="isEdit ? '编辑房间' : '添加房间'"
    width="600px"
    :close-on-click-modal="false"
    @close="handleClose"
    @open="handleOpen"
  >
    <el-form
      ref="formRef"
      :model="formData"
      :rules="formRules"
      label-width="100px"
      label-position="top"
    >
      <el-form-item label="房间号" prop="room_number">
        <el-input
          v-model="formData.room_number"
          placeholder="例如：101, A-1001"
          size="large"
          clearable
        />
      </el-form-item>

      <el-form-item label="房间名称" prop="room_name">
        <el-input
          v-model="formData.room_name"
          placeholder="例如：主卧带卫、次卧 A"
          size="large"
          clearable
        />
      </el-form-item>

      <el-form-item label="租金 (元/月)" prop="rent_price">
        <el-input-number
          v-model="formData.rent_price"
          :min="0"
          :precision="2"
          :step="100"
          placeholder="请输入月租金"
          style="width: 100%"
          size="large"
        />
      </el-form-item>

      <el-form-item label="押金 (元)" prop="deposit">
        <el-input-number
          v-model="formData.deposit"
          :min="0"
          :precision="2"
          :step="100"
          placeholder="请输入押金"
          style="width: 100%"
          size="large"
        />
      </el-form-item>

      <el-form-item label="付款方式" prop="payment_method">
        <el-select
          v-model="formData.payment_method"
          placeholder="请选择付款方式"
          size="large"
          style="width: 100%"
        >
          <el-option label="押一付三" value="press1_pay3" />
          <el-option label="押一付一" value="press1_pay1" />
          <el-option label="押二付三" value="press2_pay3" />
          <el-option label="面议" value="negotiable" />
        </el-select>
      </el-form-item>

      <el-form-item label="面积 (㎡)" prop="area">
        <el-input-number
          v-model="formData.area"
          :min="0"
          :precision="2"
          :step="0.1"
          placeholder="请输入房间面积"
          style="width: 100%"
          size="large"
        />
      </el-form-item>

      <el-form-item label="楼层" prop="floor">
        <el-input-number
          v-model="formData.floor"
          :min="1"
          placeholder="请输入楼层"
          style="width: 100%"
          size="large"
        />
      </el-form-item>

      <el-form-item label="朝向" prop="orientation">
        <el-select
          v-model="formData.orientation"
          placeholder="请选择朝向"
          size="large"
          style="width: 100%"
        >
          <el-option label="南" value="south" />
          <el-option label="北" value="north" />
          <el-option label="东" value="east" />
          <el-option label="西" value="west" />
          <el-option label="东南" value="southeast" />
          <el-option label="东北" value="northeast" />
          <el-option label="西南" value="southwest" />
          <el-option label="西北" value="northwest" />
        </el-select>
      </el-form-item>

      <el-form-item label="房间状态" prop="status">
        <el-select
          v-model="formData.status"
          placeholder="请选择状态"
          size="large"
          style="width: 100%"
        >
          <el-option label="可租" value="available" />
          <el-option label="已租" value="rented" />
          <el-option label="维修中" value="maintenance" />
        </el-select>
      </el-form-item>

      <el-form-item label="是否主卧" prop="is_master">
        <el-switch v-model="formData.is_master" />
      </el-form-item>

      <el-form-item label="配套设施" prop="facilities">
        <div class="facilities-grid">
          <el-checkbox
            v-for="facility in roomFacilities"
            :key="facility.value"
            :model-value="getFacilityValue(facility.value)"
            @update:model-value="setFacilityValue(facility.value, $event)"
            :label="facility.label"
          />
        </div>
      </el-form-item>

      <el-form-item label="房间描述" prop="description">
        <el-input
          v-model="formData.description"
          type="textarea"
          :rows="3"
          placeholder="请输入房间详细描述"
          size="large"
          maxlength="500"
          show-word-limit
        />
      </el-form-item>
    </el-form>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="dialogVisible = false" size="large">取消</el-button>
        <el-button
          type="primary"
          :loading="submitting"
          @click="handleSubmit"
          size="large"
        >
          {{ isEdit ? '保存修改' : '确定添加' }}
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, reactive, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import request from '@/api/request'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  roomData: {
    type: Object,
    default: null
  },
  houseId: {
    type: [String, Number],
    required: true
  }
})

const emit = defineEmits(['update:modelValue', 'success'])

const formRef = ref(null)
const submitting = ref(false)

const roomFacilities = [
  { value: 'bed', label: '床' },
  { value: 'wardrobe', label: '衣柜' },
  { value: 'desk', label: '书桌' },
  { value: 'chair', label: '椅子' },
  { value: 'air_conditioner', label: '空调' },
  { value: 'heater', label: '暖气' },
  { value: 'private_bathroom', label: '独立卫生间' },
  { value: 'balcony', label: '阳台' },
  { value: 'tv', label: '电视' },
  { value: 'refrigerator', label: '小冰箱' },
  { value: 'microwave', label: '微波炉' },
  { value: 'water_dispenser', label: '饮水机' }
]

const formRules = {
  room_number: [
    { required: true, message: '请输入房间号', trigger: 'blur' },
    { min: 1, max: 20, message: '房间号长度在 1 到 20 个字符', trigger: 'blur' }
  ],
  room_name: [
    { required: true, message: '请输入房间名称', trigger: 'blur' },
    { min: 1, max: 50, message: '房间名称长度在 1 到 50 个字符', trigger: 'blur' }
  ],
  rent_price: [
    { required: true, message: '请输入租金', trigger: 'blur' }
  ],
  deposit: [
    { required: true, message: '请输入押金', trigger: 'blur' }
  ],
  payment_method: [
    { required: true, message: '请选择付款方式', trigger: 'change' }
  ],
  area: [
    { required: true, message: '请输入面积', trigger: 'blur' }
  ]
}

const dialogVisible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const isEdit = computed(() => !!props.roomData?.id)

const formData = reactive({
  room_number: '',
  room_name: '',
  rent_price: 0,
  deposit: 0,
  payment_method: 'press1_pay3',
  area: 0,
  floor: 1,
  orientation: 'south',
  status: 'available',
  is_master: false,
  facilities: {},
  description: ''
})

function getFacilityValue(key) {
  return !!formData.facilities[key]
}

function setFacilityValue(key, value) {
  if (value) {
    formData.facilities[key] = true
  } else {
    delete formData.facilities[key]
  }
}

function handleOpen() {
  if (props.roomData) {
    formData.room_number = props.roomData.room_number || ''
    formData.room_name = props.roomData.room_name || ''
    formData.rent_price = props.roomData.rent_price || 0
    formData.deposit = props.roomData.deposit || 0
    formData.payment_method = props.roomData.payment_method || 'press1_pay3'
    formData.area = props.roomData.area || 0
    formData.floor = props.roomData.floor || 1
    formData.orientation = props.roomData.orientation || 'south'
    formData.status = props.roomData.status || 'available'
    formData.is_master = props.roomData.is_master || false
    formData.description = props.roomData.description || ''
    
    formData.facilities = props.roomData.facilities 
      ? JSON.parse(JSON.stringify(props.roomData.facilities)) 
      : {}
  } else {
    resetForm()
  }
}

function handleClose() {
  formRef.value?.resetFields()
  resetForm()
}

function resetForm() {
  formData.room_number = ''
  formData.room_name = ''
  formData.rent_price = 0
  formData.deposit = 0
  formData.payment_method = 'press1_pay3'
  formData.area = 0
  formData.floor = 1
  formData.orientation = 'south'
  formData.status = 'available'
  formData.is_master = false
  formData.description = ''
  formData.facilities = {}
}

const handleSubmit = async () => {
  try {
    await formRef.value?.validate()
    submitting.value = true

    const data = {
      room_number: formData.room_number,
      room_name: formData.room_name,
      rent_price: formData.rent_price,
      deposit: formData.deposit,
      payment_method: formData.payment_method,
      area: formData.area,
      floor: formData.floor,
      orientation: formData.orientation,
      status: formData.status,
      is_master: formData.is_master,
      description: formData.description,
      facilities: { ...formData.facilities }
    }
    
    if (isEdit.value && props.roomData?.id) {
      const response = await request.put(
        `/houses/rooms/${props.roomData.id}`,
        data
      )
      
      ElMessage.success('房间更新成功')
      emit('success', response.data)
      dialogVisible.value = false
    } else {
      const response = await request.post(
        `/houses/${props.houseId}/rooms`,
        data
      )
      
      ElMessage.success('房间添加成功')
      emit('success', response.data)
      dialogVisible.value = false
    }
  } catch (error) {
    console.error('表单提交失败:', error)
    const errorMessage = error.response?.data?.message || error.message || '操作失败，请重试'
    ElMessage.error(errorMessage)
  } finally {
    submitting.value = false
  }
}
</script>

<style lang="scss" scoped>
// 设计变量
$primary-color: #14b8a6; // Teal
$primary-light: #5eead4;
$primary-dark: #0d9488;
$accent-color: #06b6d4; // Cyan
$border-radius: 12px;
$border-radius-lg: 16px;
$transition-fast: 150ms;
$transition-normal: 250ms;
$transition-slow: 300ms;

.room-type-inputs {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;

  span {
    font-size: 14px;
    color: #6b7280;
    font-weight: 500;
  }
}

.facilities-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  width: 100%;
  padding: 16px;
  background: #f8fafc;
  border-radius: $border-radius;
  border: 1px solid #e5e7eb;

  :deep(.el-checkbox) {
    margin-right: 0;
    margin-bottom: 0;
    padding: 10px 14px;
    border-radius: 10px;
    border: 1px solid #e5e7eb;
    transition: all $transition-normal ease;
    background: #fff;

    &:hover {
      border-color: $primary-light;
      background: rgba(20, 184, 166, 0.04);
      transform: translateY(-1px);
      box-shadow: 0 2px 8px rgba(20, 184, 166, 0.1);
    }

    &.is-checked {
      border-color: $primary-color;
      background: rgba(20, 184, 166, 0.08);

      .el-checkbox__label {
        color: $primary-dark;
        font-weight: 500;
      }
    }

    .el-checkbox__input.is-checked .el-checkbox__inner {
      background-color: $primary-color;
      border-color: $primary-color;
    }

    .el-checkbox__input.is-checked + .el-checkbox__label {
      color: $primary-dark;
    }
  }
}

// 对话框样式
:deep(.el-dialog) {
  border-radius: $border-radius-lg;
  overflow: hidden;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);

  .el-dialog__header {
    padding: 20px 24px;
    background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
    border-bottom: 1px solid #e5e7eb;
    margin-right: 0;

    .el-dialog__title {
      font-weight: 600;
      font-size: 18px;
      color: #1f2937;
    }

    .el-dialog__headerbtn {
      top: 20px;
      right: 20px;
      width: 32px;
      height: 32px;
      border-radius: 8px;
      transition: all $transition-fast ease;

      &:hover {
        background: rgba(20, 184, 166, 0.1);

        .el-dialog__close {
          color: $primary-color;
        }
      }
    }
  }

  .el-dialog__body {
    padding: 24px;
    max-height: 60vh;
    overflow-y: auto;

    // 自定义滚动条
    &::-webkit-scrollbar {
      width: 6px;
    }

    &::-webkit-scrollbar-track {
      background: #f1f5f9;
      border-radius: 3px;
    }

    &::-webkit-scrollbar-thumb {
      background: #cbd5e1;
      border-radius: 3px;

      &:hover {
        background: $primary-light;
      }
    }
  }

  .el-dialog__footer {
    padding: 16px 24px;
    background: #fafafa;
    border-top: 1px solid #e5e7eb;
  }
}

// 表单项样式
:deep(.el-form-item) {
  margin-bottom: 20px;
  transition: all $transition-normal ease;

  .el-form-item__label {
    font-weight: 500;
    color: #374151;
    font-size: 14px;
    padding-bottom: 8px;
    transition: color $transition-fast ease;
  }

  &:focus-within {
    .el-form-item__label {
      color: $primary-color;
    }
  }
}

// 输入框样式
:deep(.el-input),
:deep(.el-select) {
  width: 100%;

  .el-input__wrapper {
    border-radius: $border-radius;
    transition: all $transition-normal ease;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
    border: 1px solid #e5e7eb;
    padding: 4px 15px;

    &:hover {
      border-color: $primary-light;
      box-shadow: 0 2px 6px rgba(20, 184, 166, 0.1);
    }

    &.is-focus,
    &.is-focused {
      border-color: $primary-color;
      box-shadow: 0 0 0 3px rgba(20, 184, 166, 0.15), 0 2px 8px rgba(20, 184, 166, 0.2);
    }
  }
}

:deep(.el-input-number) {
  width: 100%;

  .el-input__wrapper {
    border-radius: $border-radius;
  }
}

// 下拉选择框
:deep(.el-select) {
  .el-select__wrapper {
    border-radius: $border-radius;
    transition: all $transition-normal ease;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
    border: 1px solid #e5e7eb;

    &:hover {
      border-color: $primary-light;
      box-shadow: 0 2px 6px rgba(20, 184, 166, 0.1);
    }

    &.is-focused {
      border-color: $primary-color;
      box-shadow: 0 0 0 3px rgba(20, 184, 166, 0.15), 0 2px 8px rgba(20, 184, 166, 0.2);
    }
  }
}

// 文本域样式
:deep(.el-textarea__inner) {
  border-radius: $border-radius;
  transition: all $transition-normal ease;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  border: 1px solid #e5e7eb;
  padding: 12px 15px;

  &:hover {
    border-color: $primary-light;
    box-shadow: 0 2px 6px rgba(20, 184, 166, 0.1);
  }

  &:focus {
    border-color: $primary-color;
    box-shadow: 0 0 0 3px rgba(20, 184, 166, 0.15), 0 2px 8px rgba(20, 184, 166, 0.2);
  }
}

// 开关样式
:deep(.el-switch) {
  --el-switch-on-color: #{$primary-color};

  .el-switch__core {
    border-radius: 12px;
    transition: all $transition-normal ease;
  }

  &.is-checked .el-switch__core {
    box-shadow: 0 2px 8px rgba(20, 184, 166, 0.3);
  }
}

// 对话框底部按钮
.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;

  :deep(.el-button) {
    min-width: 100px;
    height: 42px;
    border-radius: $border-radius;
    font-weight: 500;
    font-size: 14px;
    transition: all $transition-normal ease;

    &:not(.el-button--primary) {
      border: 1px solid #d1d5db;
      background: #fff;

      &:hover {
        border-color: $primary-light;
        color: $primary-dark;
        background: rgba(20, 184, 166, 0.04);
      }
    }

    &.el-button--primary {
      background: linear-gradient(135deg, $primary-color 0%, $accent-color 100%);
      border: none;
      box-shadow: 0 2px 8px rgba(20, 184, 166, 0.3);

      &:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 16px rgba(20, 184, 166, 0.4);
      }

      &:active {
        transform: translateY(0);
      }
    }
  }
}
</style>
