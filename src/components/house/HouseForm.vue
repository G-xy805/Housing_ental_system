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

      <el-form-item label="房源类型" prop="type">
        <el-select v-model="formData.type" placeholder="请选择房源类型" style="width: 100%">
          <el-option label="整租" value="whole" />
          <el-option label="合租" value="shared" />
          <el-option label="公寓" value="apartment" />
          <el-option label="别墅" value="villa" />
        </el-select>
      </el-form-item>

      <el-form-item label="房源状态" prop="status">
        <el-select v-model="formData.status" placeholder="请选择房源状态" style="width: 100%">
          <el-option label="可租" value="available" />
          <el-option label="已租" value="rented" />
          <el-option label="维修中" value="maintenance" />
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

      <!-- 房屋信息 -->
      <el-divider content-position="left">房屋信息</el-divider>

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

      <el-form-item label="押金方式" prop="deposit_method">
        <el-select v-model="formData.deposit_method" placeholder="请选择押金方式" style="width: 100%">
          <el-option label="押一付三" value="press1_pay3" />
          <el-option label="押一付一" value="press1_pay1" />
          <el-option label="押二付三" value="press2_pay3" />
          <el-option label="面议" value="negotiable" />
        </el-select>
      </el-form-item>

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
      <el-divider content-position="left">配套设施</el-divider>

      <el-form-item label="配套设施" prop="amenities">
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

      <!-- 图片上传 -->
      <el-divider content-position="left">房源图片</el-divider>

      <el-form-item label="封面图片" prop="cover_image">
        <el-upload
          class="image-uploader"
          action="#"
          :http-request="handleCoverUpload"
          :show-file-list="false"
          :before-upload="beforeImageUpload"
          accept="image/*"
        >
          <img v-if="formData.cover_image" :src="formData.cover_image" class="uploaded-image" />
          <el-icon v-else class="uploader-icon">
            <Plus />
          </el-icon>
        </el-upload>
        <div class="upload-tip">点击上传封面图片，支持 JPG/PNG 格式，大小不超过 5MB</div>
      </el-form-item>

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
        >
          <el-icon><Plus /></el-icon>
        </el-upload>
        <div class="upload-tip">可上传多张房源图片，支持 JPG/PNG 格式，每张不超过 5MB</div>
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
import { ref, reactive, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { uploadHouseImage } from '@/api/house'

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
  images: []
}

const formData = reactive({ ...defaultFormData })

// 表单验证规则
const formRules = {
  title: [
    { required: true, message: '请输入房源标题', trigger: 'blur' },
    { min: 5, max: 100, message: '长度在 5 到 100 个字符', trigger: 'blur' }
  ],
  type: [{ required: true, message: '请选择房源类型', trigger: 'change' }],
  status: [{ required: true, message: '请选择房源状态', trigger: 'change' }],
  city: [{ required: true, message: '请输入城市', trigger: 'blur' }],
  district: [{ required: true, message: '请输入区域', trigger: 'blur' }],
  address: [
    { required: true, message: '请输入详细地址', trigger: 'blur' },
    { min: 5, message: '详细地址至少 5 个字符', trigger: 'blur' }
  ],
  rent_price: [{ required: true, message: '请输入租金', trigger: 'blur' }],
  area: [{ required: true, message: '请输入建筑面积', trigger: 'blur' }],
  room_count: [{ required: true, message: '请输入房间数', trigger: 'blur' }],
  floor: [{ required: true, message: '请输入楼层', trigger: 'blur' }],
  total_floors: [{ required: true, message: '请输入总楼层', trigger: 'blur' }]
}

// 图片文件列表
const imageFileList = computed({
  get: () => {
    return (formData.images || []).map((url, index) => ({
      uid: index,
      name: `图片${index + 1}`,
      status: 'done',
      url: url
    }))
  },
  set: (val) => {
    formData.images = val.map(file => file.url)
  }
})

// 图片预览对话框
const dialogVisible = ref(false)
const dialogImageUrl = ref('')

// 初始化表单数据
const initFormData = () => {
  if (props.modelValue && Object.keys(props.modelValue).length > 0) {
    Object.assign(formData, defaultFormData, props.modelValue)
    // 确保 images 是数组
    if (!formData.images) {
      formData.images = []
    }
  } else {
    Object.assign(formData, defaultFormData)
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

// 处理封面图片上传
const handleCoverUpload = async (file) => {
  try {
    const formDataUpload = new FormData()
    formDataUpload.append('files', file.file)
    
    // 如果有 houseId，使用后端上传接口；否则使用本地预览
    const houseId = props.modelValue?.id
    if (houseId) {
      const res = await uploadHouseImage(formDataUpload, houseId)
      // 从响应中获取图片 URL
      if (res.data?.files && res.data.files.length > 0) {
        formData.cover_image = res.data.files[0].file_url
      }
    }
    
    // 如果没有返回 url，使用本地预览
    if (!formData.cover_image) {
      const reader = new FileReader()
      reader.onload = (e) => {
        formData.cover_image = e.target.result
      }
      reader.readAsDataURL(file.file)
    }
  } catch (error) {
    console.error('上传封面图片失败:', error)
    // 失败时使用本地预览
    const reader = new FileReader()
    reader.onload = (e) => {
      formData.cover_image = e.target.result
    }
    reader.readAsDataURL(file.file)
  }
}

// 处理图片集上传
const handleImagesUpload = async (file) => {
  try {
    const formDataUpload = new FormData()
    formDataUpload.append('files', file.file)
    
    // 如果有 houseId，使用后端上传接口；否则使用本地预览
    const houseId = props.modelValue?.id
    if (houseId) {
      const res = await uploadHouseImage(formDataUpload, houseId)
      // 从响应中获取图片 URL
      if (res.data?.files && res.data.files.length > 0) {
        formData.images.push(res.data.files[0].file_url)
      }
    }
    
    // 如果没有返回 url，使用本地预览
    if (formData.images.length === 0 || !formData.images[formData.images.length - 1]) {
      const reader = new FileReader()
      reader.onload = (e) => {
        formData.images.push(e.target.result)
      }
      reader.readAsDataURL(file.file)
    }
  } catch (error) {
    console.error('上传图片失败:', error)
    // 失败时使用本地预览
    const reader = new FileReader()
    reader.onload = (e) => {
      formData.images.push(e.target.result)
    }
    reader.readAsDataURL(file.file)
  }
}

// 处理图片移除
const handleImageRemove = (file, fileList) => {
  const index = formData.images.indexOf(file.url)
  if (index > -1) {
    formData.images.splice(index, 1)
  }
}

// 图片预览
const handlePictureCardPreview = (file) => {
  dialogImageUrl.value = file.url
  dialogVisible.value = true
}

// 提交表单
const handleSubmit = async () => {
  try {
    await formRef.value.validate()
    // 转换字段名以匹配后端 API
    const submitData = {
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
      rent_price: formData.rent_price,
      payment_method: formData.deposit_method,
      rental_type: formData.type,
      status: formData.status,
      orientation: formData.orientation,
      decoration: formData.decoration,
      facilities: Array.isArray(formData.amenities) 
        ? formData.amenities.reduce((acc, item) => {
            acc[item] = true
            return acc
          }, {})
        : {},
      cover_image: formData.cover_image || ''
    }
    console.log('提交数据:', submitData)
    emit('submit', submitData)
  } catch (error) {
    console.error('表单验证失败:', error)
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
}

// 暴露方法给父组件
defineExpose({
  resetForm,
  validate: () => formRef.value?.validate()
})
</script>

<style lang="scss" scoped>
.house-form-container {
  padding: 20px;

  .house-form {
    max-width: 800px;
    margin: 0 auto;

    .unit-label {
      margin-left: 10px;
      color: #909399;
    }

    .image-uploader {
      width: 148px;
      height: 148px;
      border: 1px dashed #d9d9d9;
      border-radius: 6px;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;

      &:hover {
        border-color: #409eff;
      }

      .uploaded-image {
        width: 100%;
        height: 100%;
        object-fit: cover;
      }

      .uploader-icon {
        font-size: 28px;
        color: #8c939d;
      }
    }

    .image-list-uploader {
      width: 100%;

      :deep(.el-upload-list__item) {
        transition: all 0.3s;
      }

      :deep(.el-upload--picture-card) {
        width: 100px;
        height: 100px;
      }

      :deep(.el-upload-list__item) {
        width: 100px;
        height: 100px;
      }
    }

    .upload-tip {
      margin-top: 10px;
      font-size: 12px;
      color: #909399;
      line-height: 1.5;
    }
  }
}
</style>
