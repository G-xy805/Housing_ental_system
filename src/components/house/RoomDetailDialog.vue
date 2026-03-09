<template>
  <el-dialog
    v-model="visible"
    :title="room?.room_name || '房间详情'"
    width="700px"
    :close-on-click-modal="false"
    destroy-on-close
  >
    <div v-if="room" class="room-detail">
      <!-- 基本信息 -->
      <el-descriptions title="基本信息" :column="2" border>
        <el-descriptions-item label="房间号">{{ room.room_number }}</el-descriptions-item>
        <el-descriptions-item label="房间名称">{{ room.room_name || '暂无' }}</el-descriptions-item>
        <el-descriptions-item label="面积">{{ room.area }} ㎡</el-descriptions-item>
        <el-descriptions-item label="楼层">{{ room.floor || '暂无' }}</el-descriptions-item>
        <el-descriptions-item label="朝向">{{ getOrientationText(room.orientation) }}</el-descriptions-item>
        <el-descriptions-item label="是否主卧">
          <el-tag :type="room.is_master ? 'success' : 'info'" size="small">
            {{ room.is_master ? '是' : '否' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="getStatusType(room.status)" size="small">
            {{ getStatusText(room.status) }}
          </el-tag>
        </el-descriptions-item>
      </el-descriptions>

      <!-- 租金信息 -->
      <el-descriptions title="租金信息" :column="2" border style="margin-top: 20px">
        <el-descriptions-item label="租金">{{ room.rent_price }} 元/月</el-descriptions-item>
        <el-descriptions-item label="押金">{{ room.deposit }} 元</el-descriptions-item>
        <el-descriptions-item label="付款方式" :span="2">{{ getPaymentMethodText(room.payment_method) }}</el-descriptions-item>
      </el-descriptions>

      <!-- 配套设施 -->
      <div style="margin-top: 20px">
        <h4 style="margin-bottom: 12px">配套设施</h4>
        <div v-if="room.facilities && Object.keys(room.facilities).filter(k => room.facilities[k]).length > 0" class="facilities-grid">
          <template v-for="(value, key) in room.facilities" :key="key">
            <el-tag
              v-if="value"
              size="default"
              type="info"
            >
              {{ getFacilityText(key) }}
            </el-tag>
          </template>
        </div>
        <el-empty v-else description="暂无配套设施" :image-size="60" />
      </div>

      <!-- 房间描述 -->
      <div v-if="room.description" style="margin-top: 20px">
        <h4 style="margin-bottom: 12px">房间描述</h4>
        <p style="color: #606266; line-height: 1.6">{{ room.description }}</p>
      </div>
    </div>

    <template #footer>
      <el-button @click="visible = false">关闭</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  room: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['update:modelValue'])

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

// 获取状态类型
const getStatusType = (status) => {
  const types = {
    available: 'success',
    rented: 'info',
    maintenance: 'warning'
  }
  return types[status] || 'info'
}

// 获取状态文本
const getStatusText = (status) => {
  const texts = {
    available: '可租',
    rented: '已租',
    maintenance: '维修中'
  }
  return texts[status] || status
}

// 获取朝向文本
const getOrientationText = (orientation) => {
  const texts = {
    south: '南',
    north: '北',
    east: '东',
    west: '西',
    southeast: '东南',
    southwest: '西南',
    northeast: '东北',
    northwest: '西北'
  }
  return texts[orientation] || orientation || '暂无'
}

// 获取付款方式文本
const getPaymentMethodText = (payment_method) => {
  const texts = {
    press1_pay3: '押一付三',
    press1_pay1: '押一付一',
    press2_pay3: '押二付三',
    negotiable: '面议'
  }
  return texts[payment_method] || payment_method || '暂无'
}

// 获取房间配套设施文本
const getFacilityText = (facility) => {
  const texts = {
    bed: '床',
    wardrobe: '衣柜',
    desk: '书桌',
    chair: '椅子',
    air_conditioner: '空调',
    heater: '暖气',
    private_bathroom: '独立卫生间',
    balcony: '阳台',
    tv: '电视',
    refrigerator: '小冰箱',
    microwave: '微波炉',
    water_dispenser: '饮水机'
  }
  return texts[facility] || facility
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
    max-height: 70vh;
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

    .el-button {
      min-width: 100px;
      height: 42px;
      border-radius: $border-radius;
      font-weight: 500;
      transition: all $transition-normal ease;
      border: 1px solid #d1d5db;
      background: #fff;

      &:hover {
        border-color: $primary-light;
        color: $primary-dark;
        background: rgba(20, 184, 166, 0.04);
      }
    }
  }
}

.room-detail {
  h4 {
    font-size: 16px;
    font-weight: 600;
    color: #1f2937;
    margin: 0;
    position: relative;
    padding-left: 12px;

    &::before {
      content: '';
      position: absolute;
      left: 0;
      top: 50%;
      transform: translateY(-50%);
      width: 4px;
      height: 18px;
      background: linear-gradient(180deg, $primary-color 0%, $accent-color 100%);
      border-radius: 2px;
    }
  }

  // 描述列表样式
  :deep(.el-descriptions) {
    border-radius: $border-radius;
    overflow: hidden;
    border: 1px solid #e5e7eb;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);

    .el-descriptions__title {
      font-size: 15px;
      font-weight: 600;
      color: $primary-dark;
      padding: 12px 16px;
      background: linear-gradient(135deg, rgba(20, 184, 166, 0.06) 0%, rgba(6, 182, 212, 0.04) 100%);
      border-bottom: 1px solid #e5e7eb;
      margin-bottom: 0;
    }

    .el-descriptions__body {
      background: #fff;

      .el-descriptions__table {
        border: none;

        .el-descriptions__cell {
          border-color: #f0f0f0;
          padding: 12px 16px;
        }

        .el-descriptions__label {
          font-weight: 500;
          color: #6b7280;
          background: #fafafa;
          width: 120px;
        }

        .el-descriptions__content {
          color: #1f2937;
          font-weight: 400;
        }
      }
    }
  }

  // 状态标签样式
  :deep(.el-tag) {
    border-radius: 8px;
    font-weight: 500;
    padding: 4px 12px;
    border: none;

    &.el-tag--success {
      background: rgba(34, 197, 94, 0.12);
      color: #16a34a;
    }

    &.el-tag--info {
      background: rgba(100, 116, 139, 0.12);
      color: #475569;
    }

    &.el-tag--warning {
      background: rgba(245, 158, 11, 0.12);
      color: #d97706;
    }
  }
}

.facilities-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  padding: 16px;
  background: #f8fafc;
  border-radius: $border-radius;
  border: 1px solid #e5e7eb;

  :deep(.el-tag) {
    margin: 0;
    border-radius: 8px;
    font-weight: 500;
    padding: 6px 14px;
    font-size: 13px;
    background: rgba(20, 184, 166, 0.08);
    color: $primary-dark;
    border: 1px solid rgba(20, 184, 166, 0.2);
    transition: all $transition-normal ease;

    &:hover {
      background: rgba(20, 184, 166, 0.12);
      transform: translateY(-1px);
      box-shadow: 0 2px 8px rgba(20, 184, 166, 0.15);
    }
  }
}

// 空状态样式
:deep(.el-empty) {
  padding: 30px 20px;

  .el-empty__image {
    width: 80px;
    animation: empty-float 3s ease-in-out infinite;
  }

  .el-empty__description {
    color: #9ca3af;
    font-size: 14px;
    margin-top: 12px;
  }
}

// 空状态浮动动画
@keyframes empty-float {
  0%, 100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-8px);
  }
}

// 房间描述样式
.room-detail > div:last-child {
  p {
    color: #4b5563;
    line-height: 1.7;
    padding: 16px;
    background: #f8fafc;
    border-radius: $border-radius;
    border: 1px solid #e5e7eb;
    margin: 0;
  }
}
</style>
