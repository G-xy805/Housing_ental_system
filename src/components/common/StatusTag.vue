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
.status-tag {
  font-weight: 500;
  
  &--house,
  &--contract,
  &--payment,
  &--user {
    min-width: 60px;
    text-align: center;
  }
}
</style>
