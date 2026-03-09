<template>
  <div class="house-form-container">
    <el-form
      ref="formRef"
      :model="formData"
      :rules="formRules"
      label-width="100px"
      class="house-form"
    >
      <!-- 基本信息 -->
      <el-divider content-position="left">基本信息</el-divider>
      
      <el-form-item label="房源标题" prop="title">
        <el-input v-model="formData.title" placeholder="请输入房源标题" maxlength="100" show-word-limit />
      </el-form-item>

      <el-form-item label="租赁类型" prop="rental_type">
        <el-select v-model="formData.rental_type" placeholder="请选择租赁类型" style="width: 100%" :disabled="isEdit">
          <el-option label="整租" value="whole" />
          <el-option label="合租" value="shared" />
        </el-select>
      </el-form-item>

      <el-form-item label="房源状态" prop="status">
        <el-select v-model="formData.status" placeholder="请选择房源状态" style="width: 100%">
          <el-option label="可租" value="available" />
          <el-option label="已租" value="rented" />
          <el-option label="维修中" value="maintenance" />
          <el-option label="部分已租" value="partially_rented" />
        </el-select>
      </el-form-item>

      <el-form-item label="城市" prop="city">
        <el-input v-model="formData.city" placeholder="请输入城市" />
      </el-form-item>

      <el-form-item label="区域" prop="district">
        <el-input v-model="formData.district" placeholder="请输入区域" />
      </el-form-item>

      <el-form-item label="详细地址" prop="address">
        <el-input
          v-model="formData.address"
          type="textarea"
          :rows="3"
          placeholder="请输入详细地址"
          maxlength="200"
          show-word-limit
        />
      </el-form-item>

      <!-- 房东信息 -->
      <el-divider content-position="left">房东信息</el-divider>

      <el-form-item label="选择房东" prop="landlord_id">
        <el-select v-model="selectedLandlordId" placeholder="请选择房东" filterable :loading="landlordLoading" @change="handleLandlordChange">
          <el-option
            v-for="landlord in landlordList"
            :key="landlord.id"
            :label="`${landlord.name} (${landlord.phone})`"
            :value="landlord.id"
          />
        </el-select>
      </el-form-item>

      <el-form-item label="房东姓名" prop="contact_name" v-if="formData.contact_name">
        <el-input v-model="formData.contact_name" placeholder="请输入房东姓名" maxlength="50" show-word-limit disabled />
      </el-form-item>

      <el-form-item label="房东电话" prop="contact_phone" v-if="formData.contact_phone">
        <el-input v-model="formData.contact_phone" placeholder="请输入 11 位手机号码" maxlength="11" show-word-limit disabled />
      </el-form-item>

      <el-form-item label="房东微信" prop="contact_wechat" v-if="formData.contact_wechat">
        <el-input v-model="formData.contact_wechat" placeholder="请输入房东微信（可选）" maxlength="50" show-word-limit disabled />
      </el-form-item>

      <!-- 房屋信息（整租特有） -->
      <el-divider content-position="left" v-if="formData.rental_type === 'whole'">房屋信息</el-divider>

      <template v-if="formData.rental_type === 'whole'">
        <el-form-item label="租金 (元/月)" prop="rent_price">
          <el-input-number
            v-model="formData.rent_price"
            :min="0"
            :precision="2"
            :step="100"
            placeholder="请输入租金"
            style="width: 100%"
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
          />
        </el-form-item>

        <el-form-item label="付款方式" prop="payment_method">
          <el-select v-model="formData.payment_method" placeholder="请选择付款方式" style="width: 100%">
            <el-option label="押一付三" value="press1_pay3" />
            <el-option label="押一付一" value="press1_pay1" />
            <el-option label="押二付三" value="press2_pay3" />
            <el-option label="面议" value="negotiable" />
          </el-select>
        </el-form-item>
      </template>

      <!-- 房屋基本信息（整租和合租共有） -->
      <el-divider content-position="left">房屋基本信息</el-divider>

      <el-form-item label="建筑面积 (㎡)" prop="area">
        <el-input-number
          v-model="formData.area"
          :min="0"
          :precision="2"
          :step="1"
          placeholder="请输入建筑面积"
          style="width: 100%"
        />
      </el-form-item>

      <el-form-item label="户型" prop="layout">
        <el-row :gutter="10">
          <el-col :span="8">
            <el-form-item prop="room_count">
              <el-input-number
                v-model="formData.room_count"
                :min="0"
                :step="1"
                placeholder="室"
                style="width: 100%"
              />
              <span class="unit-label">室</span>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item prop="hall_count">
              <el-input-number
                v-model="formData.hall_count"
                :min="0"
                :step="1"
                placeholder="厅"
                style="width: 100%"
              />
              <span class="unit-label">厅</span>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item prop="bathroom_count">
              <el-input-number
                v-model="formData.bathroom_count"
                :min="0"
                :step="1"
                placeholder="卫"
                style="width: 100%"
              />
              <span class="unit-label">卫</span>
            </el-form-item>
          </el-col>
        </el-row>
      </el-form-item>

      <el-form-item label="楼层" prop="floor_info">
        <el-row :gutter="10">
          <el-col :span="12">
            <el-form-item prop="floor">
              <el-input-number
                v-model="formData.floor"
                :min="1"
                :step="1"
                placeholder="当前楼层"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item prop="total_floors">
              <el-input-number
                v-model="formData.total_floors"
                :min="1"
                :step="1"
                placeholder="总楼层"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form-item>

      <el-form-item label="朝向" prop="orientation">
        <el-select v-model="formData.orientation" placeholder="请选择朝向" style="width: 100%">
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

      <el-form-item label="装修情况" prop="decoration">
        <el-select v-model="formData.decoration" placeholder="请选择装修情况" style="width: 100%">
          <el-option label="毛坯" value="rough" />
          <el-option label="简装" value="simple" />
          <el-option label="精装" value="fine" />
          <el-option label="豪华装修" value="luxury" />
        </el-select>
      </el-form-item>

      <!-- 配套设施 -->
      <el-divider content-position="left">
        {{ formData.rental_type === 'shared' ? '公共配套设施' : '配套设施' }}
      </el-divider>

      <el-form-item :label="formData.rental_type === 'shared' ? '公共配套设施' : '配套设施'" prop="amenities">
        <div v-if="formData.rental_type === 'shared'" class="facilities-tip">
          <el-alert
            title="提示：此处配置的是公共区域设施（所有租户共享），房间内部设施请在「房间管理」中为每个房间单独配置"
            type="info"
            :closable="false"
            show-icon
            style="margin-bottom: 12px"
          />
        </div>
        <el-checkbox-group v-model="formData.amenities">
          <el-row>
            <el-col :span="8" v-for="item in amenityOptions" :key="item.value">
              <el-checkbox :label="item.value" :value="item.value">
                {{ item.label }}
              </el-checkbox>
            </el-col>
          </el-row>
        </el-checkbox-group>
      </el-form-item>

      <!-- 房源描述 -->
      <el-divider content-position="left">房源描述</el-divider>

      <el-form-item label="房源描述" prop="description">
        <el-input
          v-model="formData.description"
          type="textarea"
          :rows="5"
          placeholder="请输入房源详细描述"
          maxlength="1000"
          show-word-limit
        />
      </el-form-item>

      <!-- 房间管理（仅合租时显示） -->
      <el-divider content-position="left" v-if="formData.rental_type === 'shared'">房间管理</el-divider>

      <div v-if="formData.rental_type === 'shared'" class="room-management">
        <RoomList
          v-model="rooms"
          :house-id="formData.id || 'temp'"
          :show-delete-button="true"
          :is-new-house="!formData.id"
          @add="handleAddRoom"
          @edit="handleEditRoom"
          @delete="handleDeleteRoom"
        />
      </div>

      <!-- 图片上传 -->
      <el-divider content-position="left">房源图片</el-divider>

      <el-form-item label="图片集" prop="images">
        <el-upload
          class="image-list-uploader"
          action="#"
          :http-request="handleImagesUpload"
          :file-list="imageFileList"
          :on-remove="handleImageRemove"
          :before-upload="beforeImageUpload"
          list-type="picture-card"
          :on-preview="handlePictureCardPreview"
          accept="image/*"
          multiple
          :limit="20"
        >
          <el-icon><Plus /></el-icon>
        </el-upload>
        <div class="upload-tip">可上传多张房源图片（最多 20 张），支持 JPG/PNG 格式，每张不超过 5MB</div>
      </el-form-item>

      <!-- 提交按钮 -->
      <el-form-item>
        <el-button type="primary" @click="handleSubmit" :loading="submitLoading">
          {{ isEdit ? '保存修改' : '立即创建' }}
        </el-button>
        <el-button @click="handleCancel">取消</el-button>
      </el-form-item>
    </el-form>

    <!-- 图片预览对话框 -->
    <el-dialog v-model="dialogVisible" title="图片预览" width="80%">
      <img w-full :src="dialogImageUrl" alt="预览图片" style="max-width: 100%; display: block; margin: 0 auto" />
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted } from 'vue'
import { ElMessage, ElLoading } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { uploadHouseImage, uploadImage, deleteMedia, setCoverImage } from '@/api/house'
import { getLandlordList } from '@/api/landlord'
import RoomList from './RoomList.vue'

const props = defineProps({
  modelValue: {
    type: Object,
    default: () => ({})
  },
  isEdit: {
    type: Boolean,
    default: false
  },
  submitLoading: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:modelValue', 'submit', 'cancel'])

// 表单引用
const formRef = ref(null)

// 配套设施选项
const amenityOptions = [
  { label: 'WiFi', value: 'wifi' },
  { label: '空调', value: 'air_conditioning' },
  { label: '冰箱', value: 'refrigerator' },
  { label: '洗衣机', value: 'washing_machine' },
  { label: '热水器', value: 'water_heater' },
  { label: '床', value: 'bed' },
  { label: '衣柜', value: 'wardrobe' },
  { label: '书桌', value: 'desk' },
  { label: '椅子', value: 'chair' },
  { label: '沙发', value: 'sofa' },
  { label: '电视', value: 'tv' },
  { label: '微波炉', value: 'microwave' },
  { label: '电磁炉', value: 'induction_cooker' },
  { label: '抽油烟机', value: 'range_hood' },
  { label: '阳台', value: 'balcony' },
  { label: '飘窗', value: 'bay_window' },
  { label: '独立卫生间', value: 'private_bathroom' },
  { label: '独立厨房', value: 'private_kitchen' }
]

// 表单数据
const defaultFormData = {
  title: '',
  rental_type: 'whole',
  status: 'available',
  city: '',
  district: '',
  address: '',
  rent_price: 0,
  deposit: 0,
  payment_method: 'press1_pay3',
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
  contact_name: '',
  contact_phone: '',
  contact_wechat: ''
}

const formData = reactive({ ...defaultFormData })

// 表单验证规则
const formRules = {
  title: [
    { required: true, message: '请输入房源标题', trigger: 'blur' },
    { min: 5, max: 100, message: '长度在 5 到 100 个字符', trigger: 'blur' }
  ],
  rental_type: [{ required: true, message: '请选择房源类型', trigger: 'change' }],
  status: [{ required: true, message: '请选择房源状态', trigger: 'change' }],
  city: [{ required: true, message: '请输入城市', trigger: 'blur' }],
  district: [{ required: true, message: '请输入区域', trigger: 'blur' }],
  address: [
    { required: true, message: '请输入详细地址', trigger: 'blur' },
    { min: 5, message: '详细地址至少 5 个字符', trigger: 'blur' }
  ],
  rent_price: [
    { 
      required: true, 
      message: '请输入租金', 
      trigger: 'blur',
      validator: (rule, value, callback) => {
        if (formData.rental_type === 'whole' && (!value || value <= 0)) {
          callback(new Error('请输入租金'))
          return
        }
        callback()
      }
    }
  ],
  deposit: [
    { 
      required: true, 
      message: '请输入押金', 
      trigger: 'blur',
      validator: (rule, value, callback) => {
        if (formData.rental_type === 'whole' && (!value || value <= 0)) {
          callback(new Error('请输入押金'))
          return
        }
        callback()
      }
    }
  ],
  payment_method: [
    { 
      required: true, 
      message: '请选择付款方式', 
      trigger: 'change',
      validator: (rule, value, callback) => {
        if (formData.rental_type === 'whole' && !value) {
          callback(new Error('请选择付款方式'))
          return
        }
        callback()
      }
    }
  ],
  area: [{ required: true, message: '请输入建筑面积', trigger: 'blur' }],
  room_count: [{ required: true, message: '请输入房间数', trigger: 'blur' }],
  floor: [{ required: true, message: '请输入楼层', trigger: 'blur' }],
  total_floors: [{ required: true, message: '请输入总楼层', trigger: 'blur' }],
  landlord_id: [
    { required: true, message: '请选择房东', trigger: 'change' }
  ],
  contact_name: [
    { required: true, message: '请输入房东姓名', trigger: 'blur' },
    { min: 2, max: 50, message: '长度在 2 到 50 个字符', trigger: 'blur' }
  ],
  contact_phone: [
    { required: true, message: '请输入房东电话', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (!value) {
          callback(new Error('请输入房东电话'))
          return
        }
        // 验证手机号格式：11 位数字，1 开头，第二位 3-9
        const phoneRegex = /^1[3-9]\d{9}$/
        if (!phoneRegex.test(value)) {
          callback(new Error('请输入正确的 11 位手机号码'))
          return
        }
        callback()
      },
      trigger: 'blur'
    }
  ],
  images: [
    {
      validator: (rule, value, callback) => {
        if (!value || value.length === 0) {
          callback(new Error('请至少上传一张房源图片'))
          return
        }
        callback()
      },
      trigger: 'change'
    }
  ],
  rooms: [
    {
      validator: (rule, value, callback) => {
        if (formData.rental_type === 'shared' && (!rooms.value || rooms.value.length === 0)) {
          callback(new Error('合租类型至少需要添加一个房间'))
          return
        }
        callback()
      },
      trigger: 'change'
    }
  ]
}

// 图片文件列表
const imageFileList = ref([])

// 房东相关状态
const landlordList = ref([])
const landlordLoading = ref(false)
const selectedLandlordId = ref(null)

// 监听 formData.images 变化，同步到 imageFileList
watch(() => formData.images, (newImages) => {
  const images = newImages || []
  imageFileList.value = images.map((img, index) => {
    // 处理不同的数据格式
    let imageUrl = ''
    let mediaId = null
    
    if (typeof img === 'string') {
      imageUrl = img
    } else if (img && typeof img === 'object') {
      imageUrl = img.file_url || img.url || ''
      mediaId = img.id || img.media_id || null
    }
    
    return {
      uid: img.id || index,
      name: `图片${index + 1}`,
      status: 'success',
      url: imageUrl,
      response: mediaId ? { id: mediaId } : null
    }
  })
}, { immediate: true, deep: true })

// 图片预览对话框
const dialogVisible = ref(false)
const dialogImageUrl = ref('')

// 房间列表
const rooms = ref([])

// 获取房东列表
async function fetchLandlordList() {
  landlordLoading.value = true
  try {
    const res = await getLandlordList({ page_size: 100, status: 'active' })
    landlordList.value = res.data?.items || []
  } catch (error) {
    console.error('获取房东列表失败:', error)
    ElMessage.error('获取房东列表失败，请重试')
  } finally {
    landlordLoading.value = false
  }
}

// 组件挂载时获取房东列表
onMounted(() => {
  fetchLandlordList()
})

// 处理房东选择变化
function handleLandlordChange(landlordId) {
  const selectedLandlord = landlordList.value.find(landlord => landlord.id === landlordId)
  if (selectedLandlord) {
    formData.contact_name = selectedLandlord.name
    formData.contact_phone = selectedLandlord.phone
    formData.contact_wechat = selectedLandlord.wechat || ''
  }
}

// 初始化表单数据
const initFormData = () => {
  if (props.modelValue && Object.keys(props.modelValue).length > 0) {
    // 从 media 字段提取图片信息（包含 ID）
    let images = []
    if (Array.isArray(props.modelValue.media)) {
      images = props.modelValue.media
        .filter(item => item.file_type === 'image')  // 只保留图片
        .map(item => ({
          id: item.id,
          file_url: item.file_url
        }))  // 保留 ID 和 URL
    } else if (Array.isArray(props.modelValue.images)) {
      images = props.modelValue.images.map(img => 
        typeof img === 'string' ? { file_url: img } : img
      )
    }
    
    // 处理配套设施数据
    let amenities = []
    if (Array.isArray(props.modelValue.amenities)) {
      amenities = [...props.modelValue.amenities]
    } else if (props.modelValue.facilities && typeof props.modelValue.facilities === 'object') {
      // 从 facilities 对象转换为 amenities 数组
      amenities = Object.keys(props.modelValue.facilities).filter(key => props.modelValue.facilities[key])
    }
    
    // 处理房间数据
    if (Array.isArray(props.modelValue.rooms)) {
      rooms.value = [...props.modelValue.rooms]
    } else {
      rooms.value = []
    }
    
    // 创建一个新的对象，确保数组是独立的
    const modelValueCopy = {
      ...props.modelValue,
      images: images,
      amenities: amenities
    }
    Object.assign(formData, defaultFormData, modelValueCopy)
    
    // 确保封面图片设置为第一张图片
    if (formData.images.length > 0) {
      const firstImage = formData.images[0]
      formData.cover_image = typeof firstImage === 'string' ? firstImage : (firstImage.file_url || firstImage.url)
    }
    
    // 设置选中的房东
    if (props.modelValue.landlord_id) {
      selectedLandlordId.value = props.modelValue.landlord_id
    } else if (formData.contact_name && formData.contact_phone && landlordList.value.length > 0) {
      // 如果没有 landlord_id，但有联系信息，尝试匹配房东
      const matchedLandlord = landlordList.value.find(landlord => 
        landlord.name === formData.contact_name && landlord.phone === formData.contact_phone
      )
      if (matchedLandlord) {
        selectedLandlordId.value = matchedLandlord.id
      }
    }
  } else {
    Object.assign(formData, defaultFormData)
    selectedLandlordId.value = null
    rooms.value = []
  }
}

watch(() => props.modelValue, () => {
  initFormData()
}, { immediate: true, deep: true })

// 上传前验证
const beforeImageUpload = (file) => {
  const isImage = file.type.startsWith('image/')
  const isLt5M = file.size / 1024 / 1024 < 5

  if (!isImage) {
    ElMessage.error('只能上传图片文件!')
  }
  if (!isLt5M) {
    ElMessage.error('图片大小不能超过 5MB!')
  }
  return isImage && isLt5M
}

// 封面图片上传方法已移除，现在使用图片集的第一张作为封面

// 处理文件变化（当用户选择文件时）
const handleFileChange = (file, fileList) => {
  // 只处理文件状态变化，不添加图片到数组
  // 图片添加逻辑已在 handleImagesUpload 中处理
}

// 处理图片集上传（仅在前端预览，不立即上传到服务器）
const handleImagesUpload = (options) => {
  const { file, onSuccess, onError } = options
  
  try {
    // 使用本地预览，不立即上传到服务器
    const reader = new FileReader()
    reader.onload = (e) => {
      const localUrl = e.target.result
      // 添加到 formData.images，watch 会自动更新 imageFileList
      formData.images.push(localUrl)
      
      // 如果是第一张图片，自动设为封面
      if (formData.images.length === 1) {
        formData.cover_image = localUrl
      }
      
      ElMessage.success('图片已添加到预览')
      onSuccess({ file_url: localUrl })
    }
    reader.readAsDataURL(file)
  } catch (error) {
    console.error('上传图片失败:', error)
    ElMessage.error('上传失败，请重试')
    onError(error)
  }
}

// 处理图片移除
const handleImageRemove = async (file, fileList) => {
  try {
    // 检查是否是封面图片
    const isCoverImage = formData.cover_image === file.url
    
    // 尝试从服务器删除
    if (file.response && file.response.id) {
      // 如果有媒体 ID，调用删除 API
      await deleteMedia(file.response.id)
      ElMessage.success('删除成功')
    }
    
    // 从本地数组移除
    const index = formData.images.findIndex(img => {
      if (typeof img === 'string') {
        return img === file.url
      } else if (img && typeof img === 'object') {
        return (img.file_url || img.url) === file.url
      }
      return false
    })
    
    if (index > -1) {
      formData.images.splice(index, 1)
    }
    
    // 如果删除后还有图片，确保第一张图片是封面
    if (formData.images.length > 0) {
      const firstImage = formData.images[0]
      const newCoverUrl = typeof firstImage === 'string' ? firstImage : (firstImage.file_url || firstImage.url)
      
      if (newCoverUrl) {
        formData.cover_image = newCoverUrl
        
        // 如果是编辑模式，调用 API 将第一张图片设为封面
        const houseId = props.modelValue?.id
        if (houseId) {
          // 找到第一张图片的媒体 ID
          const firstImageItem = formData.images[0]
          const mediaId = typeof firstImageItem === 'object' ? (firstImageItem.id || null) : null
          
          if (mediaId) {
            try {
              // 调用设置封面的 API
              await setCoverImage(mediaId, true)
              ElMessage.success('已自动设置新封面')
            } catch (coverError) {
              console.error('设置封面失败:', coverError)
              // 即使设置封面失败，也更新前端显示
            }
          }
        }
      }
    } else {
      // 如果没有图片了，清空封面
      formData.cover_image = ''
    }
  } catch (error) {
    console.error('删除失败:', error)
    ElMessage.error('删除失败，请重试')
    
    // 即使删除失败，也从本地移除（允许用户重试）
    const index = formData.images.findIndex(img => 
      (typeof img === 'string' ? img : (img.file_url || img.url)) === file.url
    )
    if (index > -1) {
      formData.images.splice(index, 1)
    }
    
    // 确保删除后封面正确
    if (formData.images.length > 0) {
      const firstImage = formData.images[0]
      const newCoverUrl = typeof firstImage === 'string' ? firstImage : (firstImage.file_url || firstImage.url)
      if (newCoverUrl) {
        formData.cover_image = newCoverUrl
      }
    } else {
      formData.cover_image = ''
    }
  }
}

// 图片预览
const handlePictureCardPreview = (file) => {
  try {
    // 处理不同的数据格式
    if (file && typeof file === 'object') {
      dialogImageUrl.value = file.file_url || file.url || ''
    } else if (typeof file === 'string') {
      dialogImageUrl.value = file
    } else {
      dialogImageUrl.value = file.url || ''
    }
    
    // 验证 URL 是否有效
    if (!dialogImageUrl.value) {
      ElMessage.warning('图片地址无效')
      return
    }
    
    dialogVisible.value = true
  } catch (error) {
    console.error('图片预览失败:', error)
    ElMessage.error('图片预览失败，请重试')
  }
}

// 提交表单
const handleSubmit = async () => {
  try {
    // 将 selectedLandlordId 赋值给 formData.landlord_id 用于表单验证
    formData.landlord_id = selectedLandlordId.value
    // 验证房间数据（如果是合租）
    if (formData.rental_type === 'shared') {
      await formRef.value.validateField('rooms')
    }
    await formRef.value.validate()
    
    // 先提交房源基本数据（不含图片）
    const basicData = {
      title: formData.title,
      description: formData.description,
      city: formData.city,
      district: formData.district,
      address: formData.address,
      area: formData.area,
      room_count: formData.room_count,
      hall_count: formData.hall_count,
      bathroom_count: formData.bathroom_count,
      floor: formData.floor,
      total_floors: formData.total_floors,
      orientation: formData.orientation,
      decoration: formData.decoration,
      rental_type: formData.rental_type,
      status: formData.status,
      facilities: Array.isArray(formData.amenities) 
        ? formData.amenities.reduce((acc, item) => {
            acc[item] = true
            return acc
          }, {})
        : {},
      landlord_id: selectedLandlordId.value,
      contact_name: formData.contact_name,
      contact_phone: formData.contact_phone,
      contact_wechat: formData.contact_wechat,
      rooms: rooms.value
    }
    
    // 整租时才包含租金、押金、付款方式
    if (formData.rental_type === 'whole') {
      basicData.rent_price = formData.rent_price
      basicData.deposit = formData.deposit
      basicData.payment_method = formData.payment_method
    }
    
    // 触发提交事件，等待父组件创建/更新房源
    const houseData = await new Promise((resolve, reject) => {
      const onSubmitSuccess = (data) => {
        resolve(data)
      }
      
      // 临时绑定成功事件
      const successEventName = 'submit-success'
      emit(successEventName, onSubmitSuccess)
      
      // 提交基本数据
      try {
        emit('submit', basicData)
        // 如果父组件没有立即抛出错误，设置一个定时器检查是否有响应
        const timeoutId = setTimeout(() => {
          reject(new Error('提交超时，请重试'))
        }, 30000) // 30秒超时
        
        // 保存定时器ID，以便在成功时清除
        window._submitTimeoutId = timeoutId
      } catch (error) {
        reject(error)
      }
    })
    
    // 清除超时定时器
    if (window._submitTimeoutId) {
      clearTimeout(window._submitTimeoutId)
      window._submitTimeoutId = null
    }
    
    const houseId = houseData.id
    
    // 检查是否有图片需要上传
    const needUpload = formData.images && formData.images.length > 0 && formData.images.some(img => {
      const imgUrl = typeof img === 'string' ? img : (img.file_url || img.url)
      return imgUrl && imgUrl.startsWith('data:')
    })
    
    if (needUpload) {
      const loading = ElLoading.service({
        lock: true,
        text: '正在上传图片...',
        background: 'rgba(0, 0, 0, 0.7)'
      })
      
      try {
        // 收集所有需要上传的图片
        const imagesToUpload = []
        
        // 处理图片集
        if (formData.images) {
          formData.images.forEach((img, index) => {
            const imgUrl = typeof img === 'string' ? img : (img.file_url || img.url)
            if (imgUrl && imgUrl.startsWith('data:')) {
              // 第一张图片设为封面
              imagesToUpload.push({ type: index === 0 ? 'cover' : 'image', url: imgUrl })
            }
          })
        }
        
        if (imagesToUpload.length > 0) {
          // 转换 base64 为 File 对象并上传
          const uploadPromises = imagesToUpload.map(async (item, index) => {
            const blob = await fetch(item.url).then(res => res.blob())
            const file = new File([blob], `image_${index}.jpg`, { type: 'image/jpeg' })
            
            const formDataUpload = new FormData()
            formDataUpload.append('files', file)
            
            // 使用房源上传接口，直接关联到房源
            const res = await uploadHouseImage(formDataUpload, houseId, item.type === 'cover')
            if (res.data?.files && res.data.files.length > 0) {
              return res.data.files[0].file_url
            }
            return null
          })
          
          const uploadedUrls = await Promise.all(uploadPromises)
          
          // 上传完成后刷新房源数据
          ElMessage.success('图片上传成功')
        }
        
        loading.close()
      } catch (uploadError) {
        loading.close()
        console.error('上传图片失败:', uploadError)
        ElMessage.error('上传图片失败，请重试')
        return false
      }
    }
  } catch (error) {
    console.error('提交失败:', error)
    // 清除超时定时器
    if (window._submitTimeoutId) {
      clearTimeout(window._submitTimeoutId)
      window._submitTimeoutId = null
    }
    // 如果是表单验证失败，显示验证错误
    if (error.name === 'ValidationError') {
      return false
    }
    // 其他错误（如房源提交失败），显示错误信息
    ElMessage.error(error.message || '提交失败，请重试')
    return false
  }
}

// 取消
const handleCancel = () => {
  emit('cancel')
}

// 重置表单
const resetForm = () => {
  formRef.value?.resetFields()
  Object.assign(formData, defaultFormData)
  rooms.value = []
}

// 处理添加房间
const handleAddRoom = (roomData) => {
  rooms.value.push(roomData)
}

// 处理编辑房间
const handleEditRoom = (roomData) => {
  const index = rooms.value.findIndex(room => room.id === roomData.id)
  if (index !== -1) {
    rooms.value[index] = roomData
  }
}

// 处理删除房间
const handleDeleteRoom = (roomData) => {
  const index = rooms.value.findIndex(room => room.id === roomData.id)
  if (index !== -1) {
    rooms.value.splice(index, 1)
  }
}

// 暴露方法给父组件
defineExpose({
  resetForm,
  validate: () => formRef.value?.validate()
})
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

.house-form-container {
  padding: 24px;
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  border-radius: $border-radius-lg;

  .house-form {
    max-width: 800px;
    margin: 0 auto;

    // 分隔线样式优化
    :deep(.el-divider) {
      margin: 32px 0 24px;

      .el-divider__text {
        background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
        font-weight: 600;
        font-size: 15px;
        color: $primary-dark;
        padding: 0 16px;
      }
    }

    // 表单项样式优化
    :deep(.el-form-item) {
      margin-bottom: 22px;
      transition: all $transition-normal ease;

      .el-form-item__label {
        font-weight: 500;
        color: #374151;
        font-size: 14px;
        transition: color $transition-fast ease;
      }

      &:focus-within {
        .el-form-item__label {
          color: $primary-color;
        }
      }
    }

    // 输入框聚焦效果
    :deep(.el-input__wrapper),
    :deep(.el-textarea__inner),
    :deep(.el-select .el-input__wrapper) {
      border-radius: $border-radius;
      transition: all $transition-normal ease;
      box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
      border: 1px solid #e5e7eb;

      &:hover {
        border-color: $primary-light;
        box-shadow: 0 2px 6px rgba(20, 184, 166, 0.1);
      }

      &.is-focus,
      &:focus {
        border-color: $primary-color;
        box-shadow: 0 0 0 3px rgba(20, 184, 166, 0.15), 0 2px 8px rgba(20, 184, 166, 0.2);
      }
    }

    // 数字输入框样式
    :deep(.el-input-number) {
      width: 100%;

      .el-input__wrapper {
        border-radius: $border-radius;
      }
    }

    // 下拉选择框样式
    :deep(.el-select) {
      width: 100%;

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

    // 复选框组样式
    :deep(.el-checkbox-group) {
      .el-checkbox {
        margin-right: 0;
        margin-bottom: 12px;
        padding: 10px 16px;
        border-radius: $border-radius;
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

    // 提示框样式
    :deep(.el-alert) {
      border-radius: $border-radius;
      border: 1px solid rgba(20, 184, 166, 0.2);
      background: rgba(20, 184, 166, 0.06);

      .el-alert__title {
        color: $primary-dark;
        font-size: 13px;
      }
    }

    .unit-label {
      margin-left: 10px;
      color: #6b7280;
      font-size: 13px;
      font-weight: 500;
    }

    .image-uploader {
      width: 148px;
      height: 148px;
      border: 2px dashed #d1d5db;
      border-radius: $border-radius;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: all $transition-normal ease;
      background: #fff;

      &:hover {
        border-color: $primary-color;
        background: rgba(20, 184, 166, 0.04);
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(20, 184, 166, 0.15);

        .uploader-icon {
          color: $primary-color;
          transform: scale(1.1);
        }
      }

      .uploaded-image {
        width: 100%;
        height: 100%;
        object-fit: cover;
        border-radius: $border-radius - 2;
      }

      .uploader-icon {
        font-size: 32px;
        color: #9ca3af;
        transition: all $transition-normal ease;
      }
    }

    .image-list-uploader {
      width: 100%;

      :deep(.el-upload--picture-card) {
        width: 104px;
        height: 104px;
        border: 2px dashed #d1d5db;
        border-radius: $border-radius;
        background: #fff;
        transition: all $transition-normal ease;

        &:hover {
          border-color: $primary-color;
          background: rgba(20, 184, 166, 0.04);
          transform: translateY(-2px);
          box-shadow: 0 4px 12px rgba(20, 184, 166, 0.15);

          .el-icon {
            color: $primary-color;
            transform: scale(1.15);
          }
        }

        .el-icon {
          color: #9ca3af;
          font-size: 24px;
          transition: all $transition-normal ease;
        }
      }

      :deep(.el-upload-list__item) {
        width: 104px;
        height: 104px;
        border-radius: $border-radius;
        transition: all $transition-normal ease;
        border: 1px solid #e5e7eb;
        overflow: hidden;

        &:hover {
          transform: translateY(-2px);
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);

          .el-upload-list__item-actions {
            opacity: 1;
          }
        }

        img {
          object-fit: cover;
          border-radius: $border-radius - 2;
        }
      }

      :deep(.el-upload-list__item-actions) {
        opacity: 0;
        transition: opacity $transition-fast ease;
        background: rgba(0, 0, 0, 0.5);
        border-radius: $border-radius - 2;
      }
    }

    .upload-tip {
      margin-top: 12px;
      font-size: 13px;
      color: #6b7280;
      line-height: 1.6;
      padding: 10px 14px;
      background: rgba(107, 114, 128, 0.06);
      border-radius: $border-radius;
      border-left: 3px solid $primary-light;
    }

    // 提交按钮样式
    :deep(.el-form-item:last-child) {
      margin-top: 32px;
      padding-top: 24px;
      border-top: 1px solid #e5e7eb;

      .el-button {
        min-width: 120px;
        height: 44px;
        border-radius: $border-radius;
        font-weight: 500;
        font-size: 15px;
        transition: all $transition-normal ease;

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

        &:not(.el-button--primary) {
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

    // 房间管理区域
    .room-management {
      margin-top: 16px;
      padding: 20px;
      background: #fff;
      border-radius: $border-radius;
      border: 1px solid #e5e7eb;
      box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
    }
  }
}
</style>
