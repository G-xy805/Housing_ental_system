<template>
  <el-tag
    :type="tagType"
    :size="size"
    :effect="effect"
    :class="['status-tag', `status-tag--${type}`]"
  >
    {{ statusText }}
  </el-tag>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  // 状态类型
  type: {
    type: String,
    required: true,
    validator: (value) => ['house', 'contract', 'payment', 'user'].includes(value)
  },
  // 状态值
  status: {
    type: String,
    required: true
  },
  // 标签大小
  size: {
    type: String,
    default: 'default',
    validator: (value) => ['large', 'default', 'small'].includes(value)
  },
  // 标签效果
  effect: {
    type: String,
    default: 'light',
    validator: (value) => ['dark', 'light', 'plain'].includes(value)
  }
})

// 房源状态映射
const houseStatusMap = {
  available: { text: '可租', type: 'success' },
  rented: { text: '已租', type: 'info' },
  maintenance: { text: '维修中', type: 'warning' },
  partially_rented: { text: '部分已租', type: 'warning' }
}

// 合同状态映射
const contractStatusMap = {
  draft: { text: '草稿', type: 'info' },
  pending: { text: '待签约', type: 'warning' },
  active: { text: '履行中', type: 'success' },
  expired: { text: '已到期', type: 'danger' },
  terminated: { text: '已终止', type: 'info' }
}

// 支付状态映射
const paymentStatusMap = {
  pending: { text: '待支付', type: 'warning' },
  paid: { text: '已支付', type: 'success' },
  overdue: { text: '逾期', type: 'danger' },
  partial: { text: '部分支付', type: 'warning' },
  refunded: { text: '已退款', type: 'info' }
}

// 用户状态映射
const userStatusMap = {
  active: { text: '活跃', type: 'success' },
  inactive: { text: '非活跃', type: 'info' },
  suspended: { text: '暂停', type: 'danger' },
  resigned: { text: '离职', type: 'info' },
  disabled: { text: '禁用', type: 'danger' }
}

// 房东状态映射
const landlordStatusMap = {
  active: { text: '正常', type: 'success' },
  inactive: { text: '停用', type: 'info' },
  blacklisted: { text: '黑名单', type: 'danger' }
}

// 租客状态映射
const tenantStatusMap = {
  active: { text: '在租', type: 'success' },
  expired: { text: '已退租', type: 'info' },
  blacklisted: { text: '黑名单', type: 'danger' }
}

// 获取状态配置
const getStatusConfig = computed(() => {
  const statusMaps = {
    house: houseStatusMap,
    contract: contractStatusMap,
    payment: paymentStatusMap,
    user: userStatusMap,
    landlord: landlordStatusMap,
    tenant: tenantStatusMap
  }
  
  const map = statusMaps[props.type] || {}
  return map[props.status] || { text: props.status, type: 'info' }
})

// 标签类型
const tagType = computed(() => getStatusConfig.value.type)

// 状态文本
const statusText = computed(() => getStatusConfig.value.text)
</script>

<style lang="scss" scoped>
@import '@/styles/variables.scss';

.status-tag {
  font-weight: $font-weight-medium;
  border-radius: $radius-lg;
  padding: 4px 12px;
  transition: all $transition-normal;
  cursor: default;
  letter-spacing: 0.02em;

  &:hover {
    transform: translateY(-1px);
    box-shadow: $shadow-sm;
  }

  // 房源状态
  &--house {
    min-width: 68px;
    text-align: center;
  }

  // 合同状态
  &--contract {
    min-width: 68px;
    text-align: center;
  }

  // 支付状态
  &--payment {
    min-width: 72px;
    text-align: center;
  }

  // 用户状态
  &--user {
    min-width: 60px;
    text-align: center;
  }

  // 成功状态样式增强
  :deep(.el-tag--success) {
    background-color: $success-bg;
    border-color: $success-lighter;
    color: $success-dark;

    &:hover {
      background-color: lighten($success-bg, 2%);
      border-color: $success-light;
    }
  }

  // 警告状态样式增强
  :deep(.el-tag--warning) {
    background-color: $warning-bg;
    border-color: $warning-lighter;
    color: $warning-dark;

    &:hover {
      background-color: lighten($warning-bg, 2%);
      border-color: $warning-light;
    }
  }

  // 危险状态样式增强
  :deep(.el-tag--danger) {
    background-color: $danger-bg;
    border-color: $danger-lighter;
    color: $danger-dark;

    &:hover {
      background-color: lighten($danger-bg, 2%);
      border-color: $danger-light;
    }
  }

  // 信息状态样式增强
  :deep(.el-tag--info) {
    background-color: $info-bg;
    border-color: $info-lighter;
    color: $info-dark;

    &:hover {
      background-color: lighten($info-bg, 2%);
      border-color: $info-light;
    }
  }

  // 不同尺寸样式
  :deep(.el-tag--large) {
    padding: 6px 16px;
    font-size: $font-size-base;
    border-radius: $radius-xl;
  }

  :deep(.el-tag--small) {
    padding: 2px 8px;
    font-size: $font-size-xs;
    border-radius: $radius-md;
  }
}
</style>
