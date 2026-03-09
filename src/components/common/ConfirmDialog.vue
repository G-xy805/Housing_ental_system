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
@import '@/styles/variables.scss';

.confirm-content {
  display: flex;
  align-items: flex-start;
  gap: $spacing-4;
  padding: $spacing-3 0;

  .confirm-icon {
    font-size: 48px;
    flex-shrink: 0;
    animation: iconPulse 0.5s ease-out;
    transition: transform $transition-normal;

    &--warning {
      color: $warning-color;
      filter: drop-shadow(0 2px 8px rgba($warning-color, 0.3));
    }

    &--success {
      color: $success-color;
      filter: drop-shadow(0 2px 8px rgba($success-color, 0.3));
    }

    &--danger {
      color: $danger-color;
      filter: drop-shadow(0 2px 8px rgba($danger-color, 0.3));
    }

    &--info {
      color: $info-color;
      filter: drop-shadow(0 2px 8px rgba($info-color, 0.3));
    }
  }

  .confirm-message {
    flex: 1;
    font-size: $font-size-sm;
    line-height: $line-height-relaxed;
    color: $text-regular;
    padding-top: 4px;

    p {
      margin: 0;
    }
  }
}

.confirm-footer {
  display: flex;
  justify-content: flex-end;
  gap: $spacing-3;
  padding-top: $spacing-2;

  :deep(.el-button) {
    min-width: 88px;
    border-radius: $radius-lg;
    font-weight: $font-weight-medium;
    padding: 10px 20px;
    transition: all $transition-normal;

    &:hover {
      transform: translateY(-1px);
    }

    &:active {
      transform: translateY(0);
    }
  }

  // 取消按钮
  :deep(.el-button:not([class*='el-button--'])) {
    border: 1px solid $border-secondary;
    background-color: $white;
    color: $text-regular;

    &:hover {
      border-color: $gray-300;
      background-color: $gray-50;
      color: $text-primary;
    }
  }

  // 确认按钮 - 主要
  :deep(.el-button--primary) {
    background: $gradient-btn-primary;
    border: none;
    box-shadow: $shadow-sm;

    &:hover {
      background: $gradient-btn-primary-hover;
      box-shadow: $shadow-md;
    }
  }

  // 确认按钮 - 成功
  :deep(.el-button--success) {
    background: $gradient-btn-success;
    border: none;
    box-shadow: $shadow-sm;

    &:hover {
      background: linear-gradient(135deg, $success-dark 0%, darken($success-dark, 5%) 100%);
      box-shadow: $shadow-md;
    }
  }

  // 确认按钮 - 警告
  :deep(.el-button--warning) {
    background: $gradient-btn-warning;
    border: none;
    box-shadow: $shadow-sm;

    &:hover {
      background: linear-gradient(135deg, $warning-dark 0%, darken($warning-dark, 5%) 100%);
      box-shadow: $shadow-md;
    }
  }

  // 确认按钮 - 危险
  :deep(.el-button--danger) {
    background: $gradient-btn-danger;
    border: none;
    box-shadow: $shadow-sm;

    &:hover {
      background: linear-gradient(135deg, $danger-dark 0%, darken($danger-dark, 5%) 100%);
      box-shadow: $shadow-md;
    }
  }
}

// 对话框样式
:deep(.el-dialog) {
  border-radius: $radius-xl;
  box-shadow: $shadow-2xl;
  overflow: hidden;
  animation: dialogSlideIn 0.3s ease-out;

  .el-dialog__header {
    padding: $spacing-4 $spacing-5;
    border-bottom: 1px solid $border-secondary;
    background: linear-gradient(180deg, $white 0%, $gray-50 100%);

    .el-dialog__title {
      color: $text-primary;
      font-weight: $font-weight-semibold;
      font-size: $font-size-lg;
    }

    .el-dialog__headerbtn {
      top: $spacing-4;
      right: $spacing-4;
      width: 32px;
      height: 32px;
      border-radius: $radius-md;
      transition: all $transition-fast;

      &:hover {
        background-color: $gray-100;
      }

      .el-dialog__close {
        color: $text-muted;
        font-size: 16px;
        transition: color $transition-fast;
      }

      &:hover .el-dialog__close {
        color: $text-primary;
      }
    }
  }

  .el-dialog__body {
    padding: $spacing-5;
  }

  .el-dialog__footer {
    padding: $spacing-3 $spacing-5 $spacing-4;
    border-top: 1px solid $border-secondary;
    background-color: $gray-50;
  }
}

// 遮罩层动画
:deep(.el-overlay) {
  animation: overlayFadeIn 0.2s ease-out;
}

// 图标脉冲动画
@keyframes iconPulse {
  0% {
    transform: scale(0.8);
    opacity: 0;
  }
  50% {
    transform: scale(1.1);
  }
  100% {
    transform: scale(1);
    opacity: 1;
  }
}

// 对话框滑入动画
@keyframes dialogSlideIn {
  0% {
    transform: translateY(-20px) scale(0.95);
    opacity: 0;
  }
  100% {
    transform: translateY(0) scale(1);
    opacity: 1;
  }
}

// 遮罩层淡入动画
@keyframes overlayFadeIn {
  0% {
    opacity: 0;
  }
  100% {
    opacity: 1;
  }
}

// 响应式设计
@media screen and (max-width: $breakpoint-sm) {
  .confirm-content {
    flex-direction: column;
    align-items: center;
    text-align: center;
    gap: $spacing-3;

    .confirm-icon {
      font-size: 56px;
    }

    .confirm-message {
      padding-top: 0;
      font-size: $font-size-base;
    }
  }

  .confirm-footer {
    flex-direction: column-reverse;
    gap: $spacing-2;

    :deep(.el-button) {
      width: 100%;
      margin: 0;
    }
  }

  :deep(.el-dialog) {
    width: 90% !important;
    max-width: 360px;
    margin: 10vh auto !important;

    .el-dialog__header {
      padding: $spacing-3 $spacing-4;

      .el-dialog__title {
        font-size: $font-size-base;
      }
    }

    .el-dialog__body {
      padding: $spacing-4;
    }

    .el-dialog__footer {
      padding: $spacing-2 $spacing-4 $spacing-3;
    }
  }
}

@media screen and (max-width: $breakpoint-xs) {
  :deep(.el-dialog) {
    width: 95% !important;
    max-width: 320px;
    border-radius: $radius-lg;
  }
}
</style>
