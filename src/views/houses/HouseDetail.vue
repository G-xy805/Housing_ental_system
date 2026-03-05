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
            ref="carouselRef"
            @change="handleCarouselChange"
            arrow="always"
            height="400px"
            v-if="imageList.length > 0"
          >
            <el-carousel-item v-for="(image, index) in imageList" :key="index">
              <el-image
                :src="image"
                :alt="`房源图片${index + 1}`"
                fit="contain"
                class="carousel-image"
                :preview-src-list="imageList"
                :initial-index="index"
                preview-teleported
                hide-on-click-modal
                :hide-on-modal-click="true"
                @error="handleImageError"
              >
                <template #error>
                  <div class="image-error">
                    <el-icon :size="50"><Picture /></el-icon>
                    <span>图片加载失败</span>
                  </div>
                </template>
              </el-image>
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
              @click="handleThumbnailClick(index)"
            >
              <el-image 
                :src="image" 
                fit="cover" 
                class="thumbnail-image"
                :alt="`缩略图${index + 1}`"
                @error="handleThumbnailError($event, index)"
              >
                <template #error>
                  <div class="thumbnail-error">
                    <el-icon :size="20"><Picture /></el-icon>
                  </div>
                </template>
              </el-image>
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
              {{ getTypeText(houseData.rental_type) }}
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
        <el-card class="rooms-card" v-if="houseData.rental_type === 'shared' && houseData.rooms && houseData.rooms.length > 0">
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
            <span class="card-title">房东信息</span>
          </template>
          <div class="contact-info">
            <div class="contact-item">
              <el-icon class="contact-icon"><User /></el-icon>
              <div class="contact-content">
                <span class="contact-label">房东</span>
                <span class="contact-value">{{ houseData.contact_name || '暂无' }}</span>
              </div>
            </div>
            <div class="contact-item">
              <el-icon class="contact-icon"><Phone /></el-icon>
              <div class="contact-content">
                <span class="contact-label">房东电话</span>
                <span class="contact-value">{{ houseData.contact_phone || '暂无' }}</span>
              </div>
            </div>
            <div class="contact-item">
              <el-icon class="contact-icon"><ChatDotRound /></el-icon>
              <div class="contact-content">
                <span class="contact-label">房东微信</span>
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
        @submit-success="handleSubmitSuccess"
      />
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted } from 'vue'
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
  ChatDotRound,
  Picture
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
const carouselRef = ref(null)
const currentImageIndex = ref(0)

// 默认占位图片
const DEFAULT_IMAGE = 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyMDAiIGhlaWdodD0iMTUwIiB2aWV3Qm94PSIwIDAgMjAwIDE1MCI+PHJlY3QgZmlsbD0iI2Y1ZjdmYSIgd2lkdGg9IjIwMCIgaGVpZ2h0PSIxNTAiLz48cGF0aCBmaWxsPSIjZDBkM2Q0IiBkPSJNMTAwIDUwYTIwIDIwIDAgMSAxIDAgNDAgMjAgMjAgMCAxIDEgMC00MHptLTQwIDQwYTIwIDIwIDAgMSAxIDAgNDAgMjAgMjAgMCAxIDEgMC00MHptODAgMGEyMCAyMCAwIDEgMSAwIDQwIDIwIDIwIDAgMSAxIDAtNDB6Ii8+PC9zdmc+'

// 房源数据
const houseData = ref({
  id: null,
  title: '',
  rental_type: 'whole',
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
  created_at: '',
  updated_at: ''
})

// 编辑数据
const editData = ref({})

// 图片列表
const imageList = computed(() => {
  const list = []
  const seen = new Set() // 用于去重
  
  // 处理 cover_image
  if (houseData.value.cover_image) {
    const coverImage = houseData.value.cover_image
    list.push(coverImage)
    seen.add(coverImage)
  }
  
  // 处理 images 数组
  if (houseData.value.images && Array.isArray(houseData.value.images)) {
    for (const img of houseData.value.images) {
      if (img && !seen.has(img)) {
        list.push(img)
        seen.add(img)
      }
    }
  }
  
  // 处理 media 字段（兼容后端可能返回的 media 数据）
  if (houseData.value.media) {
    let mediaList = []
    // 支持多种 media 格式
    if (Array.isArray(houseData.value.media)) {
      mediaList = houseData.value.media
    } else if (typeof houseData.value.media === 'string') {
      // 如果是 JSON 字符串，尝试解析
      try {
        mediaList = JSON.parse(houseData.value.media)
      } catch (e) {
        console.warn('media 字段解析失败:', e)
      }
    } else if (houseData.value.media.images) {
      mediaList = houseData.value.media.images
    }
    
    if (Array.isArray(mediaList)) {
      for (const img of mediaList) {
        const imgUrl = typeof img === 'string' ? img : img.file_url || img.url || img.image
        if (imgUrl && !seen.has(imgUrl)) {
          list.push(imgUrl)
          seen.add(imgUrl)
        }
      }
    }
  }
  
  return list.filter(img => img && typeof img === 'string')
})

// 监听 imageList 变化，重置 currentImageIndex
watch(imageList, (newList) => {
  if (newList.length === 0) {
    currentImageIndex.value = 0
  } else if (currentImageIndex.value >= newList.length) {
    currentImageIndex.value = 0
    // 确保轮播图同步
    if (carouselRef.value) {
      carouselRef.value.setActiveItem(0)
    }
  }
})

// 权限检查
const hasPermission = (action) => {
  // 管理员拥有所有权限
  if (userStore.isAdmin) {
    return true
  }
  
  // 房东权限：查看、创建、编辑（无删除）
  if (userStore.userType === 'landlord') {
    const landlordPermissions = ['view', 'create', 'edit', 'update']
    return landlordPermissions.includes(action)
  }
  
  return false
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
    maintenance: '维修中',
    partially_rented: '部分已租'
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

// 轮播图切换事件
const handleCarouselChange = (index) => {
  currentImageIndex.value = index
}

// 点击缩略图
const handleThumbnailClick = (index) => {
  currentImageIndex.value = index
  if (carouselRef.value) {
    carouselRef.value.setActiveItem(index)
  }
}

// 图片加载错误处理
const handleImageError = (error) => {
  console.warn('图片加载失败:', error)
  // 可以在这里添加错误统计逻辑
}

// 缩略图加载错误处理
const handleThumbnailError = (event, index) => {
  console.warn(`缩略图${index + 1}加载失败`)
  // 设置默认图片
  if (event.target) {
    event.target.src = DEFAULT_IMAGE
  }
}

// 加载房源详情
const loadHouseDetail = async () => {
  loading.value = true
  try {
    const res = await getHouseDetailApi(route.params.id)
    const data = res.data || {}
    
    // 处理配套设施数据：从 facilities 对象转换为 amenities 数组
    if (data.facilities && typeof data.facilities === 'object' && !Array.isArray(data.amenities)) {
      data.amenities = Object.keys(data.facilities).filter(key => data.facilities[key])
    }
    
    houseData.value = data
    editData.value = { ...data }
    // 重置图片索引
    currentImageIndex.value = 0
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
      // 显示后端返回的错误消息
      const errorMessage = error.response?.data?.error?.message || error.message || '删除失败，请重试'
      ElMessage.error(errorMessage)
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

// 提交成功回调
let submitSuccessCallback = null

const handleSubmitSuccess = (callback) => {
  submitSuccessCallback = callback
}

// 表单提交
const handleFormSubmit = async (data) => {
  formSubmitLoading.value = true
  try {
    const result = await houseStore.editHouse(houseData.value.id, data)
    ElMessage.success('编辑成功')
    
    // 调用成功回调，返回房源数据
    if (submitSuccessCallback) {
      submitSuccessCallback(result)
      submitSuccessCallback = null
    }
    
    dialogVisible.value = false
    loadHouseDetail()
  } catch (error) {
    console.error('提交失败:', error)
    // 抛出错误，让子组件知道提交失败
    throw error
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

    .image-error {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      width: 100%;
      height: 100%;
      background: #f5f7fa;
      color: #909399;
      gap: 10px;
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
        background: #f5f7fa;

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

        .thumbnail-error {
          display: flex;
          align-items: center;
          justify-content: center;
          width: 100%;
          height: 100%;
          background: #f5f7fa;
          color: #909399;
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
