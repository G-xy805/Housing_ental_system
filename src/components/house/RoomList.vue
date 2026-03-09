<template>
  <div class="room-list-container">
    <div class="room-header">
      <h3>房间列表</h3>
      <el-button type="primary" @click="handleAddRoom" v-if="showAddButton && !isNewHouse">
        <el-icon><Plus /></el-icon>
        添加房间
      </el-button>
    </div>
    
    <el-alert
      v-if="isNewHouse"
      title="请先保存房源后再添加房间"
      type="info"
      :closable="false"
      show-icon
      style="margin-bottom: 15px;"
    >
      <template #default>
        <span>您需要先保存房源基本信息，然后才能添加房间。</span>
      </template>
    </el-alert>

    <el-table :data="rooms" v-loading="loading" border stripe class="room-table">
      <el-table-column prop="room_number" label="房间号" width="120">
        <template #default="{ row }">
          {{ row.room_number }}
        </template>
      </el-table-column>
      <el-table-column prop="room_name" label="房间名称" width="150">
        <template #default="{ row }">
          {{ row.room_name || '暂无' }}
        </template>
      </el-table-column>
      
      <!-- 简化模式只显示基本信息 -->
      <template v-if="simpleMode">
        <el-table-column prop="rent_price" label="租金 (元/月)" width="120">
          <template #default="{ row }">
            {{ row.rent_price }}
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" size="small">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
      </template>
      
      <!-- 完整模式显示所有信息 -->
      <template v-else>
        <el-table-column prop="area" label="面积 (㎡)" width="100">
          <template #default="{ row }">
            {{ row.area }}
          </template>
        </el-table-column>
        <el-table-column prop="floor" label="楼层" width="90">
          <template #default="{ row }">
            {{ row.floor }}
          </template>
        </el-table-column>
        <el-table-column prop="orientation" label="朝向" width="100">
          <template #default="{ row }">
            {{ getOrientationText(row.orientation) }}
          </template>
        </el-table-column>
        <el-table-column prop="rent_price" label="租金 (元/月)" width="120">
          <template #default="{ row }">
            {{ row.rent_price }}
          </template>
        </el-table-column>
        <el-table-column prop="deposit" label="押金 (元)" width="100">
          <template #default="{ row }">
            {{ row.deposit }}
          </template>
        </el-table-column>
        <el-table-column prop="payment_method" label="付款方式" width="100">
          <template #default="{ row }">
            {{ getPaymentMethodText(row.payment_method) }}
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" size="small">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="facilities" label="配套设施" min-width="250">
          <template #default="{ row }">
            <div v-if="row.facilities && Object.keys(row.facilities).length > 0" class="facilities-tags" style="display: flex; flex-wrap: wrap; gap: 4px;">
              <template v-for="(value, key) in row.facilities" :key="key">
                <el-tag
                  v-if="value"
                  size="small"
                  type="info"
                  style="margin: 2px"
                >
                  {{ getFacilityText(key) }}
                </el-tag>
              </template>
            </div>
            <span v-else style="color: #909399">暂无</span>
          </template>
        </el-table-column>
        <el-table-column prop="is_master" label="主卧" width="80">
          <template #default="{ row }">
            <el-tag :type="row.is_master ? 'success' : 'info'" size="small">
              {{ row.is_master ? '是' : '否' }}
            </el-tag>
          </template>
        </el-table-column>
      </template>
      
      <el-table-column label="操作" :width="simpleMode ? '100' : '220'" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="handleViewRoom(row)" v-if="showViewButton">
            查看
          </el-button>
          <el-button link type="primary" @click="handleEditRoom(row)" v-if="showEditButton">
            编辑
          </el-button>
          <el-button link type="success" @click="handleCreateContract(row)" v-if="showCreateContractButton && row.status === 'available'">
            创建合同
          </el-button>
          <el-button link type="danger" @click="handleDeleteRoom(row)" v-if="showDeleteButton">
            删除
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 房间表单对话框 -->
    <RoomFormDialog
      v-model="dialogVisible"
      :room-data="currentRoom"
      :house-id="houseId"
      @success="handleDialogSuccess"
    />
    
    <!-- 房间详情对话框 -->
    <RoomDetailDialog
      v-model="detailDialogVisible"
      :room="currentRoom"
    />
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import RoomFormDialog from './RoomFormDialog.vue'
import RoomDetailDialog from './RoomDetailDialog.vue'
import request from '@/api/request'

const props = defineProps({
  modelValue: {
    type: Array,
    default: () => []
  },
  loading: {
    type: Boolean,
    default: false
  },
  showAddButton: {
    type: Boolean,
    default: true
  },
  showViewButton: {
    type: Boolean,
    default: false
  },
  showEditButton: {
    type: Boolean,
    default: true
  },
  showDeleteButton: {
    type: Boolean,
    default: true
  },
  showCreateContractButton: {
    type: Boolean,
    default: false
  },
  houseId: {
    type: [String, Number],
    required: true
  },
  simpleMode: {
    type: Boolean,
    default: false
  },
  isNewHouse: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:modelValue', 'add', 'edit', 'delete', 'view', 'createContract'])

// 房间列表
const rooms = ref([...props.modelValue])

watch(() => props.modelValue, (newVal) => {
  rooms.value = [...newVal]
}, { deep: true })

// 对话框
const dialogVisible = ref(false)
const detailDialogVisible = ref(false)

// 当前编辑的房间
const currentRoom = ref(null)

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
  return texts[orientation] || orientation
}

// 获取付款方式文本
const getPaymentMethodText = (payment_method) => {
  const texts = {
    press1_pay3: '押一付三',
    press1_pay1: '押一付一',
    press2_pay3: '押二付三',
    negotiable: '面议'
  }
  return texts[payment_method] || payment_method
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

// 添加房间
const handleAddRoom = () => {
  currentRoom.value = null
  dialogVisible.value = true
}

// 编辑房间
const handleEditRoom = (row) => {
  // 深拷贝 facilities 对象，避免引用问题
  currentRoom.value = {
    ...row,
    facilities: row.facilities ? JSON.parse(JSON.stringify(row.facilities)) : {}
  }
  dialogVisible.value = true
}

// 查看房间详情
const handleViewRoom = (row) => {
  currentRoom.value = { ...row }
  detailDialogVisible.value = true
}

// 创建合同
const handleCreateContract = (row) => {
  emit('createContract', row)
}

// 删除房间
const handleDeleteRoom = async (row) => {
  try {
    await ElMessageBox.confirm(
      `<div>
        <p>确定要删除以下房间吗？</p>
        <div style="margin-top: 10px; padding: 10px; background-color: #f5f7fa; border-radius: 4px;">
          <p><strong>房间号：</strong>${row.room_number}</p>
          <p><strong>房间名称：</strong>${row.room_name}</p>
          <p><strong>租金：</strong>${row.rent_price} 元/月</p>
          <p><strong>面积：</strong>${row.area} ㎡</p>
        </div>
        <p style="margin-top: 10px; color: #f56c6c;">删除后数据将不可恢复，请谨慎操作。</p>
      </div>`,
      '确认删除',
      {
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
        type: 'warning',
        dangerouslyUseHTMLString: true,
        center: true,
        confirmButtonClass: 'el-button--danger',
        cancelButtonClass: 'el-button--info'
      }
    )

    // 调用 API 删除房间
    await request.delete(`/houses/rooms/${row.id}`)
    
    ElMessage.success('删除成功')
    emit('delete', row)
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
      const errorMessage = error.response?.data?.message || '删除失败，请重试'
      ElMessage.error(errorMessage)
    }
    ElMessage.info('已取消删除操作')
  }
}

// 处理对话框成功事件
const handleDialogSuccess = (result) => {
  if (currentRoom.value && currentRoom.value.id) {
    emit('edit', result)
  } else {
    emit('add', result)
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

.room-list-container {
  width: 100%;
  overflow-x: visible;
  display: block;

  .room-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    padding-right: 20px;

    h3 {
      margin: 0;
      color: #1f2937;
      font-size: 18px;
      font-weight: 600;
      position: relative;
      padding-left: 12px;

      &::before {
        content: '';
        position: absolute;
        left: 0;
        top: 50%;
        transform: translateY(-50%);
        width: 4px;
        height: 20px;
        background: linear-gradient(180deg, $primary-color 0%, $accent-color 100%);
        border-radius: 2px;
      }
    }

    :deep(.el-button) {
      border-radius: $border-radius;
      font-weight: 500;
      transition: all $transition-normal ease;
      padding: 10px 20px;
      height: auto;

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

        .el-icon {
          margin-right: 6px;
          transition: transform $transition-fast ease;
        }

        &:hover .el-icon {
          transform: rotate(90deg);
        }
      }
    }
  }

  // 提示框样式
  :deep(.el-alert) {
    border-radius: $border-radius;
    border: 1px solid rgba(20, 184, 166, 0.2);
    background: rgba(20, 184, 166, 0.06);
    margin-bottom: 20px;

    .el-alert__title {
      color: $primary-dark;
      font-size: 14px;
    }

    .el-alert__icon {
      color: $primary-color;
    }
  }

  .room-table {
    width: auto;
    min-width: 100%;
    border-radius: $border-radius;
    overflow: hidden;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05), 0 1px 2px rgba(0, 0, 0, 0.03);

    :deep(.el-table__header-wrapper) {
      th {
        background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
        font-weight: 600;
        color: #374151;
        font-size: 14px;
        border-bottom: 2px solid $primary-light;
      }
    }

    :deep(.el-table__body-wrapper) {
      overflow-x: auto;
    }

    :deep(.el-table__row) {
      transition: all $transition-normal ease;

      &:hover {
        background: rgba(20, 184, 166, 0.04) !important;

        td {
          border-bottom-color: rgba(20, 184, 166, 0.15);
        }
      }

      td {
        transition: all $transition-fast ease;
      }
    }

    :deep(.el-table__row:first-child) {
      background-color: #f9fafb;

      &:hover {
        background-color: rgba(20, 184, 166, 0.04);
      }
    }

    :deep(.el-table__fixed-right) {
      height: 100% !important;
      box-shadow: -2px 0 8px rgba(0, 0, 0, 0.05);
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

    // 配套设施标签
    .facilities-tags {
      :deep(.el-tag) {
        margin: 2px;
        border-radius: 6px;
        font-size: 12px;
        background: rgba(20, 184, 166, 0.08);
        color: $primary-dark;
        border: 1px solid rgba(20, 184, 166, 0.2);
      }
    }

    // 操作按钮样式
    :deep(.el-button--link) {
      font-weight: 500;
      padding: 4px 8px;
      border-radius: 6px;
      transition: all $transition-fast ease;

      &:hover {
        background: rgba(20, 184, 166, 0.08);
      }

      &.el-button--primary {
        color: $primary-color;

        &:hover {
          color: $primary-dark;
        }
      }

      &.el-button--success {
        color: #22c55e;

        &:hover {
          color: #16a34a;
          background: rgba(34, 197, 94, 0.08);
        }
      }

      &.el-button--danger {
        color: #ef4444;

        &:hover {
          color: #dc2626;
          background: rgba(239, 68, 68, 0.08);
        }
      }
    }
  }

  // 空状态样式
  :deep(.el-table__empty-block) {
    padding: 60px 20px;

    .el-table__empty-text {
      color: #9ca3af;
    }
  }

  .户型-inputs {
    display: flex;
    align-items: center;
    gap: 4px;
    flex-wrap: wrap;

    span {
      font-size: 12px;
      color: #6b7280;
      font-weight: 500;
    }
  }
}

// 响应式调整
@media screen and (max-width: 1400px) {
  .room-list-container {
    .room-table {
      min-width: 1000px;
    }
  }
}

@media screen and (max-width: 1200px) {
  .room-list-container {
    .room-table {
      min-width: 800px;
    }
  }
}
</style>
