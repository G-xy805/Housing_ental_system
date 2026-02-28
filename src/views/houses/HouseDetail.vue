<template>
  <div class="house-detail-page">
    <!-- 返回按钮 -->
    <div class="back-bar">
      <el-button @click="handleBack">
        <el-icon><ArrowLeft /></el-icon>
        返回列表
      </el-button>
      <div class="action-buttons">
        <el-button type="primary" @click="handleEdit" v-if="hasPermission('edit')">
          <el-icon><Edit /></el-icon>
          编辑
        </el-button>
        <el-button type="danger" @click="handleDelete" v-if="hasPermission('delete')">
          <el-icon><Delete /></el-icon>
          删除
        </el-button>
      </div>
    </div>

    <el-row v-loading="loading" :gutter="20">
      <!-- 左侧：图片和基本信息 -->
      <el-col :xs="24" :md="16">
        <!-- 图片轮播 -->
        <el-card class="image-card">
          <el-carousel
            v-model:current-page="currentImageIndex"
            trigger="click"
            arrow="always"
            height="400px"
            v-if="imageList.length > 0"
          >
            <el-carousel-item v-for="(image, index) in imageList" :key="index">
              <el-image
                :src="image"
                fit="contain"
                class="carousel-image"
                :preview-src-list="imageList"
                :initial-index="index"
                preview-teleported
              />
            </el-carousel-item>
          </el-carousel>
          <el-empty v-else description="暂无图片" :image-size="100" />
          
          <!-- 缩略图 -->
          <div class="thumbnail-list" v-if="imageList.length > 1">
            <div
              v-for="(image, index) in imageList"
              :key="index"
              class="thumbnail-item"
              :class="{ active: currentImageIndex === index }"
              @click="currentImageIndex = index"
            >
              <el-image :src="image" fit="cover" class="thumbnail-image" />
            </div>
          </div>
        </el-card>

        <!-- 基本信息 -->
        <el-card class="info-card">
          <template #header>
            <div class="card-header">
              <span class="card-title">基本信息</span>
              <el-tag :type="getStatusType(houseData.status)" size="large">
                {{ getStatusText(houseData.status) }}
              </el-tag>
            </div>
          </template>

          <el-descriptions :column="2" border>
            <el-descriptions-item label="房源标题" :span="2">
              {{ houseData.title }}
            </el-descriptions-item>
            <el-descriptions-item label="房源类型">
              {{ getTypeText(houseData.type) }}
            </el-descriptions-item>
            <el-descriptions-item label="房源状态">
              <el-tag :type="getStatusType(houseData.status)" size="small">
                {{ getStatusText(houseData.status) }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="所在城市">
              {{ houseData.city }}
            </el-descriptions-item>
            <el-descriptions-item label="所在区域">
              {{ houseData.district }}
            </el-descriptions-item>
            <el-descriptions-item label="详细地址" :span="2">
              <el-icon><Location /></el-icon>
              {{ houseData.address }}
            </el-descriptions-item>
            <el-descriptions-item label="租金价格">
              <span class="price-text">¥{{ houseData.rent_price }}</span>
              <span class="price-unit">/月</span>
            </el-descriptions-item>
            <el-descriptions-item label="押金方式">
              {{ getDepositText(houseData.deposit_method) }}
            </el-descriptions-item>
            <el-descriptions-item label="建筑面积">
              {{ houseData.area }}㎡
            </el-descriptions-item>
            <el-descriptions-item label="户型格局">
              {{ houseData.room_count }}室{{ houseData.hall_count }}厅{{ houseData.bathroom_count }}卫
            </el-descriptions-item>
            <el-descriptions-item label="楼层信息">
              {{ houseData.floor }}/{{ houseData.total_floors }}层
            </el-descriptions-item>
            <el-descriptions-item label="房屋朝向">
              {{ getOrientationText(houseData.orientation) }}
            </el-descriptions-item>
            <el-descriptions-item label="装修情况">
              {{ getDecorationText(houseData.decoration) }}
            </el-descriptions-item>
            <el-descriptions-item label="房源描述" :span="2">
              <p class="description-text">{{ houseData.description || '暂无描述' }}</p>
            </el-descriptions-item>
          </el-descriptions>
        </el-card>

        <!-- 配套设施 -->
        <el-card class="amenities-card" v-if="houseData.amenities && houseData.amenities.length > 0">
          <template #header>
            <span class="card-title">配套设施</span>
          </template>
          <div class="amenities-list">
            <div
              v-for="amenity in houseData.amenities"
              :key="amenity"
              class="amenity-item"
            >
              <el-icon class="amenity-icon"><CircleCheck /></el-icon>
              <span>{{ getAmenityText(amenity) }}</span>
            </div>
          </div>
        </el-card>

        <!-- 房间列表（合租模式） -->
        <el-card class="rooms-card" v-if="houseData.type === 'shared' && houseData.rooms && houseData.rooms.length > 0">
          <template #header>
            <span class="card-title">房间列表</span>
          </template>
          <RoomList
            :model-value="houseData.rooms"
            :show-add-button="false"
            :show-edit-button="hasPermission('edit')"
            :show-delete-button="hasPermission('delete')"
            @edit="handleEditRoom"
            @delete="handleDeleteRoom"
            @view="handleViewRoom"
          />
        </el-card>
      </el-col>

      <!-- 右侧：联系信息 -->
      <el-col :xs="24" :md="8">
        <!-- 联系卡片 -->
        <el-card class="contact-card">
          <template #header>
            <span class="card-title">联系信息</span>
          </template>
          <div class="contact-info">
            <div class="contact-item">
              <el-icon class="contact-icon"><User /></el-icon>
              <div class="contact-content">
                <span class="contact-label">联系人</span>
                <span class="contact-value">{{ houseData.contact_name || '暂无' }}</span>
              </div>
            </div>
            <div class="contact-item">
              <el-icon class="contact-icon"><Phone /></el-icon>
              <div class="contact-content">
                <span class="contact-label">联系电话</span>
                <span class="contact-value">{{ houseData.contact_phone || '暂无' }}</span>
              </div>
            </div>
            <div class="contact-item">
              <el-icon class="contact-icon"><ChatDotRound /></el-icon>
              <div class="contact-content">
                <span class="contact-label">微信</span>
                <span class="contact-value">{{ houseData.contact_wechat || '暂无' }}</span>
              </div>
            </div>
          </div>
        </el-card>

        <!-- 地图位置（可选） -->
        <el-card class="map-card" v-if="houseData.latitude && houseData.longitude">
          <template #header>
            <span class="card-title">地理位置</span>
          </template>
          <div class="map-container">
            <el-empty description="地图功能待接入" :image-size="80" />
          </div>
        </el-card>

        <!-- 房源统计 -->
        <el-card class="stats-card">
          <template #header>
            <span class="card-title">房源统计</span>
          </template>
          <div class="stats-list">
            <div class="stat-item">
              <span class="stat-label">浏览次数</span>
              <span class="stat-value">{{ houseData.view_count || 0 }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">收藏次数</span>
              <span class="stat-value">{{ houseData.favorite_count || 0 }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">发布时间</span>
              <span class="stat-value">{{ formatDate(houseData.created_at) }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">更新时间</span>
              <span class="stat-value">{{ formatDate(houseData.updated_at) }}</span>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      title="编辑房源"
      width="900px"
      :close-on-click-modal="false"
      destroy-on-close
    >
      <HouseForm
        ref="houseFormRef"
        v-model="editData"
        :is-edit="true"
        :submit-loading="formSubmitLoading"
        @submit="handleFormSubmit"
        @cancel="dialogVisible = false"
      />
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  ArrowLeft,
  Edit,
  Delete,
  Location,
  CircleCheck,
  User,
  Phone,
  ChatDotRound
} from '@element-plus/icons-vue'
import { getHouseDetail as getHouseDetailApi, deleteHouse } from '@/api/house'
import { useHouseStore } from '@/store/house'
import { useUserStore } from '@/store/user'
import HouseForm from '@/components/house/HouseForm.vue'
import RoomList from '@/components/house/RoomList.vue'

const router = useRouter()
const route = useRoute()
const houseStore = useHouseStore()
const userStore = useUserStore()

const loading = ref(false)
const dialogVisible = ref(false)
const formSubmitLoading = ref(false)
const houseFormRef = ref(null)
const currentImageIndex = ref(0)

// 房源数据
const houseData = ref({
  id: null,
  title: '',
  type: 'whole',
  status: 'available',
  city: '',
  district: '',
  address: '',
  rent_price: 0,
  deposit_method: 'press1_pay3',
  area: 0,
  room_count: 0,
  hall_count: 0,
  bathroom_count: 0,
  floor: 1,
  total_floors: 1,
  orientation: 'south',
  decoration: 'simple',
  amenities: [],
  description: '',
  cover_image: '',
  images: [],
  rooms: [],
  contact_name: '',
  contact_phone: '',
  contact_wechat: '',
  view_count: 0,
  favorite_count: 0,
  created_at: '',
  updated_at: ''
})

// 编辑数据
const editData = ref({})

// 图片列表
const imageList = computed(() => {
  const list = []
  if (houseData.value.cover_image) {
    list.push(houseData.value.cover_image)
  }
  if (houseData.value.images && Array.isArray(houseData.value.images)) {
    list.push(...houseData.value.images)
  }
  return list
})

// 权限检查
const hasPermission = (action) => {
  return userStore.isAdmin || userStore.userType === 'landlord'
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

// 获取类型文本
const getTypeText = (type) => {
  const texts = {
    whole: '整租',
    shared: '合租',
    apartment: '公寓',
    villa: '别墅'
  }
  return texts[type] || type
}

// 获取押金方式文本
const getDepositText = (method) => {
  const texts = {
    press1_pay3: '押一付三',
    press1_pay1: '押一付一',
    press2_pay3: '押二付三',
    negotiable: '面议'
  }
  return texts[method] || method
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

// 获取装修情况文本
const getDecorationText = (decoration) => {
  const texts = {
    rough: '毛坯',
    simple: '简装',
    fine: '精装',
    luxury: '豪华装修'
  }
  return texts[decoration] || decoration
}

// 获取配套设施文本
const getAmenityText = (amenity) => {
  const texts = {
    wifi: 'WiFi',
    air_conditioning: '空调',
    refrigerator: '冰箱',
    washing_machine: '洗衣机',
    water_heater: '热水器',
    bed: '床',
    wardrobe: '衣柜',
    desk: '书桌',
    chair: '椅子',
    sofa: '沙发',
    tv: '电视',
    microwave: '微波炉',
    induction_cooker: '电磁炉',
    range_hood: '抽油烟机',
    balcony: '阳台',
    bay_window: '飘窗',
    private_bathroom: '独立卫生间',
    private_kitchen: '独立厨房'
  }
  return texts[amenity] || amenity
}

// 格式化日期
const formatDate = (date) => {
  if (!date) return '暂无'
  return new Date(date).toLocaleString('zh-CN')
}

// 加载房源详情
const loadHouseDetail = async () => {
  loading.value = true
  try {
    const res = await getHouseDetailApi(route.params.id)
    houseData.value = res.data || {}
    editData.value = { ...res.data }
  } catch (error) {
    console.error('加载房源详情失败:', error)
    ElMessage.error('加载房源详情失败')
  } finally {
    loading.value = false
  }
}

// 返回
const handleBack = () => {
  router.back()
}

// 编辑
const handleEdit = () => {
  editData.value = { ...houseData.value }
  dialogVisible.value = true
}

// 删除
const handleDelete = () => {
  ElMessageBox.confirm('确定要删除该房源吗？删除后不可恢复！', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      await deleteHouse(houseData.value.id)
      ElMessage.success('删除成功')
      router.push('/houses')
    } catch (error) {
      console.error('删除失败:', error)
    }
  }).catch(() => {})
}

// 编辑房间
const handleEditRoom = (room) => {
  console.log('编辑房间:', room)
  ElMessage.info('房间编辑功能待实现')
}

// 删除房间
const handleDeleteRoom = (room) => {
  console.log('删除房间:', room)
  ElMessage.info('房间删除功能待实现')
}

// 查看房间
const handleViewRoom = (room) => {
  console.log('查看房间:', room)
  ElMessage.info('房间详情功能待实现')
}

// 表单提交
const handleFormSubmit = async (data) => {
  formSubmitLoading.value = true
  try {
    await houseStore.editHouse(houseData.value.id, data)
    ElMessage.success('编辑成功')
    dialogVisible.value = false
    loadHouseDetail()
  } catch (error) {
    console.error('提交失败:', error)
  } finally {
    formSubmitLoading.value = false
  }
}

onMounted(() => {
  loadHouseDetail()
})
</script>

<style lang="scss" scoped>
.house-detail-page {
  padding: 20px;

  .back-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;

    .action-buttons {
      display: flex;
      gap: 10px;
    }
  }

  .image-card {
    margin-bottom: 20px;

    .carousel-image {
      width: 100%;
      height: 100%;
      object-fit: contain;
    }

    .thumbnail-list {
      display: flex;
      gap: 10px;
      margin-top: 15px;
      overflow-x: auto;

      .thumbnail-item {
        flex-shrink: 0;
        width: 80px;
        height: 60px;
        border-radius: 4px;
        overflow: hidden;
        cursor: pointer;
        border: 2px solid transparent;
        transition: all 0.3s;

        &:hover {
          border-color: #409eff;
        }

        &.active {
          border-color: #409eff;
        }

        .thumbnail-image {
          width: 100%;
          height: 100%;
          object-fit: cover;
        }
      }
    }
  }

  .info-card,
  .amenities-card,
  .rooms-card,
  .contact-card,
  .map-card,
  .stats-card {
    margin-bottom: 20px;

    .card-title {
      font-size: 16px;
      font-weight: bold;
      color: #333;
    }
  }

  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .price-text {
    font-size: 20px;
    color: #f56c6c;
    font-weight: bold;
  }

  .price-unit {
    color: #909399;
    margin-left: 4px;
  }

  .description-text {
    margin: 0;
    line-height: 1.6;
    color: #606266;
    white-space: pre-wrap;
  }

  .amenities-list {
    display: flex;
    flex-wrap: wrap;
    gap: 15px;

    .amenity-item {
      display: flex;
      align-items: center;
      gap: 5px;
      padding: 8px 12px;
      background: #f5f7fa;
      border-radius: 4px;
      font-size: 14px;
      color: #606266;

      .amenity-icon {
        color: #67c23a;
      }
    }
  }

  .contact-info {
    .contact-item {
      display: flex;
      align-items: flex-start;
      gap: 10px;
      padding: 15px 0;
      border-bottom: 1px solid #ebeef5;

      &:last-child {
        border-bottom: none;
      }

      .contact-icon {
        font-size: 20px;
        color: #409eff;
        flex-shrink: 0;
      }

      .contact-content {
        display: flex;
        flex-direction: column;
        gap: 4px;

        .contact-label {
          font-size: 12px;
          color: #909399;
        }

        .contact-value {
          font-size: 15px;
          color: #333;
          font-weight: 500;
        }
      }
    }
  }

  .map-container {
    height: 300px;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .stats-list {
    .stat-item {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 12px 0;
      border-bottom: 1px solid #ebeef5;

      &:last-child {
        border-bottom: none;
      }

      .stat-label {
        color: #909399;
        font-size: 14px;
      }

      .stat-value {
        color: #333;
        font-size: 14px;
        font-weight: 500;
      }
    }
  }
}
</style>
