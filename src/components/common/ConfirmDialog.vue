<template>
  <el-dialog
    v-model="visible"
    :title="title"
    :width="width"
    :close-on-click-modal="closeOnClickModal"
    :close-on-press-escape="closeOnPressEscape"
    :show-close="showClose"
    :center="center"
    :custom-class="customClass"
    @close="handleClose"
  >
    <div class="confirm-content">
      <el-icon
        v-if="showIcon"
        :class="['confirm-icon', `confirm-icon--${type}`]"
      >
        <component :is="iconComponent" />
      </el-icon>
      <div class="confirm-message">
        <p v-if="message">{{ message }}</p>
        <slot v-else></slot>
      </div>
    </div>

    <template #footer>
      <div class="confirm-footer">
        <el-button @click="handleCancel">
          {{ cancelText }}
        </el-button>
        <el-button
          :type="confirmButtonType"
          :loading="loading"
          @click="handleConfirm"
        >
          {{ confirmText }}
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import {
  WarningFilled,
  CircleCheckFilled,
  CircleCloseFilled,
  QuestionFilled
} from '@element-plus/icons-vue'

const props = defineProps({
  // 是否显示对话框
  modelValue: {
    type: Boolean,
    default: false
  },
  // 标题
  title: {
    type: String,
    default: '提示'
  },
  // 提示消息
  message: {
    type: String,
    default: ''
  },
  // 类型
  type: {
    type: String,
    default: 'warning',
    validator: (value) => ['warning', 'success', 'danger', 'info'].includes(value)
  },
  // 确认按钮文本
  confirmText: {
    type: String,
    default: '确定'
  },
  // 取消按钮文本
  cancelText: {
    type: String,
    default: '取消'
  },
  // 是否显示图标
  showIcon: {
    type: Boolean,
    default: true
  },
  // 对话框宽度
  width: {
    type: String,
    default: '420px'
  },
  // 是否显示关闭按钮
  showClose: {
    type: Boolean,
    default: true
  },
  // 是否居中
  center: {
    type: Boolean,
    default: true
  },
  // 是否可以通过点击 modal 关闭
  closeOnClickModal: {
    type: Boolean,
    default: false
  },
  // 是否可以通过按下 ESC 关闭
  closeOnPressEscape: {
    type: Boolean,
    default: true
  },
  // 自定义类名
  customClass: {
    type: String,
    default: 'confirm-dialog'
  },
  // 确认按钮加载状态
  loading: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:modelValue', 'confirm', 'cancel', 'close'])

// 对话框显示状态
const visible = ref(false)

// 监听 modelValue 变化
watch(
  () => props.modelValue,
  (val) => {
    visible.value = val
  },
  { immediate: true }
)

// 监听 visible 变化
watch(visible, (val) => {
  emit('update:modelValue', val)
})

// 图标组件
const iconComponent = computed(() => {
  const iconMap = {
    warning: WarningFilled,
    success: CircleCheckFilled,
    danger: CircleCloseFilled,
    info: QuestionFilled
  }
  return iconMap[props.type] || WarningFilled
})

// 确认按钮类型
const confirmButtonType = computed(() => {
  const typeMap = {
    warning: 'warning',
    success: 'success',
    danger: 'danger',
    info: 'primary'
  }
  return typeMap[props.type] || 'primary'
})

// 确认
const handleConfirm = () => {
  emit('confirm')
}

// 取消
const handleCancel = () => {
  visible.value = false
  emit('cancel')
}

// 关闭
const handleClose = () => {
  emit('close')
}
</script>

<style lang="scss" scoped>
.confirm-content {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  padding: 10px 0;
  
  .confirm-icon {
    font-size: 48px;
    flex-shrink: 0;
    
    &--warning {
      color: #E6A23C;
    }
    
    &--success {
      color: #67C23A;
    }
    
    &--danger {
      color: #F56C6C;
    }
    
    &--info {
      color: #409EFF;
    }
  }
  
  .confirm-message {
    flex: 1;
    font-size: 14px;
    line-height: 1.6;
    color: #606266;
    
    p {
      margin: 0;
    }
  }
}

.confirm-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

:deep(.el-dialog__header) {
  padding: 16px 20px;
  border-bottom: 1px solid #EBEEF5;
}

:deep(.el-dialog__body) {
  padding: 20px;
}

:deep(.el-dialog__footer) {
  padding: 12px 20px;
  border-top: 1px solid #EBEEF5;
}
</style>
