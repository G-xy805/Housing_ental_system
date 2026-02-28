<template>
  <div class="room-list-container">
    <div class="room-header">
      <h3>房间列表</h3>
      <el-button type="primary" @click="handleAddRoom" v-if="showAddButton">
        <el-icon><Plus /></el-icon>
        添加房间
      </el-button>
    </div>

    <el-table :data="rooms" v-loading="loading" border stripe class="room-table">
      <el-table-column prop="room_number" label="房间号" width="100" />
      <el-table-column prop="room_name" label="房间名称" min-width="120" />
      <el-table-column label="户型" width="100">
        <template #default="{ row }">
          {{ row.room_count }}室{{ row.hall_count }}厅{{ row.bathroom_count }}卫
        </template>
      </el-table-column>
      <el-table-column prop="area" label="面积 (㎡)" width="90" />
      <el-table-column prop="floor" label="楼层" width="80" />
      <el-table-column prop="orientation" label="朝向" width="80">
        <template #default="{ row }">
          {{ getOrientationText(row.orientation) }}
        </template>
      </el-table-column>
      <el-table-column prop="rent_price" label="租金 (元/月)" width="110" />
      <el-table-column prop="status" label="状态" width="90">
        <template #default="{ row }">
          <el-tag :type="getStatusType(row.status)" size="small">
            {{ getStatusText(row.status) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="is_master" label="主卧" width="70">
        <template #default="{ row }">
          <el-tag :type="row.is_master ? 'success' : 'info'" size="small">
            {{ row.is_master ? '是' : '否' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="180" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="handleViewRoom(row)" v-if="showViewButton">
            查看
          </el-button>
          <el-button link type="primary" @click="handleEditRoom(row)" v-if="showEditButton">
            编辑
          </el-button>
          <el-button link type="danger" @click="handleDeleteRoom(row)" v-if="showDeleteButton">
            删除
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 添加/编辑房间对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="600px"
      :close-on-click-modal="false"
    >
      <el-form
        ref="roomFormRef"
        :model="roomFormData"
        :rules="roomFormRules"
        label-width="100px"
      >
        <el-form-item label="房间号" prop="room_number">
          <el-input v-model="roomFormData.room_number" placeholder="如：101、A 间" />
        </el-form-item>
        <el-form-item label="房间名称" prop="room_name">
          <el-input v-model="roomFormData.room_name" placeholder="如：主卧带卫、次卧 A" />
        </el-form-item>
        <el-form-item label="租金 (元/月)" prop="rent_price">
          <el-input-number
            v-model="roomFormData.rent_price"
            :min="0"
            :precision="2"
            :step="100"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="面积 (㎡)" prop="area">
          <el-input-number
            v-model="roomFormData.area"
            :min="0"
            :precision="2"
            :step="1"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="楼层" prop="floor">
          <el-input-number
            v-model="roomFormData.floor"
            :min="1"
            :step="1"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="朝向" prop="orientation">
          <el-select v-model="roomFormData.orientation" placeholder="请选择朝向" style="width: 100%">
            <el-option label="南" value="south" />
            <el-option label="北" value="north" />
            <el-option label="东" value="east" />
            <el-option label="西" value="west" />
            <el-option label="东南" value="southeast" />
            <el-option label="西南" value="southwest" />
            <el-option label="东北" value="northeast" />
            <el-option label="西北" value="northwest" />
          </el-select>
        </el-form-item>
        <el-form-item label="房间状态" prop="status">
          <el-select v-model="roomFormData.status" placeholder="请选择状态" style="width: 100%">
            <el-option label="可租" value="available" />
            <el-option label="已租" value="rented" />
            <el-option label="维修中" value="maintenance" />
          </el-select>
        </el-form-item>
        <el-form-item label="是否主卧" prop="is_master">
          <el-switch v-model="roomFormData.is_master" />
        </el-form-item>
        <el-form-item label="房间描述" prop="description">
          <el-input
            v-model="roomFormData.description"
            type="textarea"
            :rows="3"
            placeholder="请输入房间描述"
            maxlength="500"
            show-word-limit
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleConfirmRoom" :loading="submitLoading">
          确定
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'

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
  }
})

const emit = defineEmits(['update:modelValue', 'add', 'edit', 'delete', 'view'])

// 房间列表
const rooms = ref([...props.modelValue])

watch(() => props.modelValue, (newVal) => {
  rooms.value = [...newVal]
}, { deep: true })

// 对话框
const dialogVisible = ref(false)
const dialogTitle = ref('添加房间')
const submitLoading = ref(false)

// 房间表单
const roomFormRef = ref(null)
const defaultRoomData = {
  room_number: '',
  room_name: '',
  rent_price: 0,
  area: 0,
  floor: 1,
  orientation: 'south',
  status: 'available',
  is_master: false,
  description: '',
  room_count: 1,
  hall_count: 0,
  bathroom_count: 1
}

const roomFormData = reactive({ ...defaultRoomData })

// 当前编辑的房间
const currentRoom = ref(null)

// 表单验证规则
const roomFormRules = {
  room_number: [
    { required: true, message: '请输入房间号', trigger: 'blur' }
  ],
  room_name: [
    { required: true, message: '请输入房间名称', trigger: 'blur' }
  ],
  rent_price: [
    { required: true, message: '请输入租金', trigger: 'blur' }
  ],
  area: [
    { required: true, message: '请输入面积', trigger: 'blur' }
  ],
  floor: [
    { required: true, message: '请输入楼层', trigger: 'blur' }
  ],
  orientation: [
    { required: true, message: '请选择朝向', trigger: 'change' }
  ],
  status: [
    { required: true, message: '请选择状态', trigger: 'change' }
  ]
}

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

// 添加房间
const handleAddRoom = () => {
  dialogTitle.value = '添加房间'
  currentRoom.value = null
  Object.assign(roomFormData, defaultRoomData)
  dialogVisible.value = true
}

// 编辑房间
const handleEditRoom = (row) => {
  dialogTitle.value = '编辑房间'
  currentRoom.value = { ...row }
  Object.assign(roomFormData, row)
  dialogVisible.value = true
}

// 查看房间
const handleViewRoom = (row) => {
  emit('view', row)
}

// 删除房间
const handleDeleteRoom = (row) => {
  ElMessageBox.confirm('确定要删除该房间吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(() => {
    emit('delete', row)
    ElMessage.success('删除成功')
  }).catch(() => {})
}

// 确认添加/编辑
const handleConfirmRoom = async () => {
  try {
    await roomFormRef.value.validate()
    submitLoading.value = true
    
    const data = { ...roomFormData }
    
    if (currentRoom.value) {
      // 编辑
      emit('edit', { ...currentRoom.value, ...data })
      ElMessage.success('编辑成功')
    } else {
      // 添加
      emit('add', data)
      ElMessage.success('添加成功')
    }
    
    dialogVisible.value = false
  } catch (error) {
    console.error('表单验证失败:', error)
  } finally {
    submitLoading.value = false
  }
}

// 暴露方法
defineExpose({
  resetForm: () => {
    Object.assign(roomFormData, defaultRoomData)
    roomFormRef.value?.resetFields()
  }
})
</script>

<style lang="scss" scoped>
.room-list-container {
  .room-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 15px;

    h3 {
      margin: 0;
      color: #333;
      font-size: 16px;
    }
  }

  .room-table {
    width: 100%;
  }
}
</style>
