<template>
  <div class="house-list-page">
    <div class="page-header">
      <h2>房源管理</h2>
      <el-button type="primary" @click="handleAdd" v-if="hasPermission('create')">
        <el-icon><Plus /></el-icon>
        新增房源
      </el-button>
    </div>

    <!-- 搜索栏 -->
    <el-card class="search-card">
      <el-form :inline="true" :model="searchForm" class="search-form" @keyup.enter="handleSearch">
        <el-form-item label="关键词">
          <el-input
            v-model="searchForm.keyword"
            placeholder="房源标题/地址"
            clearable
            style="width: 200px"
            @input="debouncedSearch"
            @clear="handleSearch"
          />
        </el-form-item>
        <el-form-item label="城市">
          <el-input
            v-model="searchForm.city"
            placeholder="请输入城市"
            clearable
            style="width: 150px"
            @input="debouncedSearch"
            @clear="handleSearch"
          />
        </el-form-item>
        <el-form-item label="区域">
          <el-input
            v-model="searchForm.district"
            placeholder="请输入区域"
            clearable
            style="width: 150px"
            @input="debouncedSearch"
            @clear="handleSearch"
          />
        </el-form-item>
        <el-form-item label="房源类型">
          <el-select v-model="searchForm.rental_type" placeholder="请选择" clearable style="width: 120px">
            <el-option label="整租" value="whole" />
            <el-option label="合租" value="shared" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="searchForm.status" placeholder="请选择" clearable style="width: 120px">
            <el-option label="可租" value="available" />
            <el-option label="已租" value="rented" />
            <el-option label="维修中" value="maintenance" />
          </el-select>
        </el-form-item>
        <el-form-item label="租金范围">
          <el-input-number
            v-model="searchForm.min_price"
            :min="0"
            :precision="0"
            placeholder="最低"
            style="width: 120px"
          />
          <span class="range-separator">-</span>
          <el-input-number
            v-model="searchForm.max_price"
            :min="0"
            :precision="0"
            placeholder="最高"
            style="width: 120px"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">
            <el-icon><Search /></el-icon>
            查询
          </el-button>
          <el-button @click="handleReset">
            <el-icon><Refresh /></el-icon>
            重置
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 房源列表 -->
    <el-row :gutter="20" class="house-list">
      <el-col
        :xs="24"
        :sm="12"
        :md="8"
        :lg="6"
        v-for="house in houseList"
        :key="house.id"
        class="house-col"
      >
        <el-card class="house-card" shadow="hover" @click="handleView(house)">
          <template #header>
            <div class="card-header">
              <el-tag :type="getStatusType(house.status)" size="small">
                {{ getStatusText(house.status) }}
              </el-tag>
              <el-tag type="warning" size="small" v-if="house.rental_type === 'shared'">合租</el-tag>
            </div>
          </template>

          <!-- 封面图片 -->
          <div class="house-cover" @click.stop="handleView(house)">
            <el-image
              :src="house.cover_image || defaultCoverImage"
              fit="cover"
              class="cover-image"
              :preview-src-list="[house.cover_image || defaultCoverImage]"
              preview-teleported
            >
              <template #error>
                <div class="image-error">
                  <el-icon><Picture /></el-icon>
                </div>
              </template>
            </el-image>
            <div class="cover-overlay">
              <el-button type="primary" size="small" @click.stop="handleView(house)">
                查看详情
              </el-button>
            </div>
          </div>

          <div class="house-info">
            <h3 class="house-title" :title="house.title">{{ house.title }}</h3>
            <p class="house-address" :title="house.address">
              <el-icon><Location /></el-icon>
              {{ formatAddress(house) }}
            </p>
            <div class="house-specs">
              <span>{{ house.area }}㎡</span>
              <span>{{ house.room_count }}室{{ house.hall_count }}厅{{ house.bathroom_count }}卫</span>
              <span>{{ getFloorText(house) }}</span>
            </div>
            <!-- 出租进度 -->
            <div class="rental-progress" v-if="house.rental_type === 'shared'">
              <span class="progress-label">出租进度</span>
              <div class="progress-info">
                <span class="progress-text">{{ house.rented_rooms || 0 }}/{{ house.total_rooms || house.room_count }}间已租</span>
                <el-progress 
                  :percentage="((house.rented_rooms || 0) / (house.total_rooms || house.room_count) * 100).toFixed(0)" 
                  :stroke-width="6" 
                  :show-text="false"
                  class="progress-bar"
                />
              </div>
            </div>
            <div class="house-price" v-if="house.rental_type !== 'shared'">
              <span class="price-label">租金</span>
              <span class="price-value">¥{{ house.rent_price }}</span>
              <span class="price-unit">/月</span>
            </div>
          </div>

          <!-- 操作按钮 -->
          <div class="house-actions" @click.stop>
            <el-button
              link
              type="primary"
              @click="handleEdit(house)"
              v-if="hasPermission('edit')"
            >
              <el-icon><Edit /></el-icon>
              编辑
            </el-button>
            <el-button
              link
              type="danger"
              @click="handleDelete(house)"
              v-if="hasPermission('delete')"
            >
              <el-icon><Delete /></el-icon>
              删除
            </el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 空状态 -->
    <el-empty v-if="!loading && houseList.length === 0" description="暂无房源数据">
      <el-button type="primary" @click="handleAdd" v-if="hasPermission('create')">
        添加房源
      </el-button>
    </el-empty>

    <!-- 分页 -->
    <el-card class="pagination-card" v-if="houseList.length > 0">
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.per_page"
        :total="pagination.total"
        :page-sizes="[12, 24, 48, 96]"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleSizeChange"
        @current-change="handlePageChange"
      />
    </el-card>

    <!-- 新增/编辑房源对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="900px"
      :close-on-click-modal="false"
      destroy-on-close
    >
      <HouseForm
        ref="houseFormRef"
        v-model="currentHouseData"
        :is-edit="isEdit"
        :submit-loading="formSubmitLoading"
        @submit="handleFormSubmit"
        @cancel="dialogVisible = false"
        @submit-success="handleSubmitSuccess"
      />
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onBeforeUnmount, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, Refresh, Location, Picture, Edit, Delete } from '@element-plus/icons-vue'
import { debounce } from 'lodash-es'
import { getHouseList as getHouseListApi, deleteHouse, getHouseDetail as getHouseDetailApi } from '@/api/house'
import { useHouseStore } from '@/store/house'
import { useUserStore } from '@/store/user'
import HouseForm from '@/components/house/HouseForm.vue'

const router = useRouter()
const houseStore = useHouseStore()
const userStore = useUserStore()

const loading = ref(false)
const houseList = ref([])
const dialogVisible = ref(false)
const dialogTitle = ref('新增房源')
const isEdit = ref(false)
const formSubmitLoading = ref(false)
const houseFormRef = ref(null)
const currentHouseData = ref({})

// 默认封面图 - 使用 SVG 占位图，避免外部依赖
const defaultCoverImage = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAwIiBoZWlnaHQ9IjMwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iNDAwIiBoZWlnaHQ9IjMwMCIgZmlsbD0iI2UwZTBlMCIvPjx0ZXh0IHg9IjUwJSIgeT0iNTAlIiBmb250LWZhbWlseT0iQXJpYWwsIHNhbnMtc2VyaWYiIGZvbnQtc2l6ZT0iMjQiIGZpbGw9IiM5OTkiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGR5PSIuM2VtIj5ObyBJbWFnZTwvdGV4dD48L3N2Zz4='

// 搜索表单
const searchForm = reactive({
  keyword: '',
  city: '',
  district: '',
  rental_type: '',
  status: '',
  min_price: null,
  max_price: null
})

// 分页
const pagination = reactive({
  page: 1,
  per_page: 12,
  total: 0
})

// 权限检查
const hasPermission = (action) => {
  // 使用 userStore 的权限检查方法
  return userStore.hasPermission(action)
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

// 格式化地址
const formatAddress = (house) => {
  const parts = [house.city, house.district, house.address].filter(Boolean)
  return parts.join('') || '暂无地址'
}

// 获取楼层文本
const getFloorText = (house) => {
  if (house.floor && house.total_floors) {
    return `${house.floor}/${house.total_floors}层`
  }
  return '未知楼层'
}

// 加载房源列表
const loadHouseList = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      per_page: pagination.per_page,
      ...searchForm
    }
    const res = await getHouseListApi(params)
    houseList.value = res.data?.items || []
    pagination.total = res.data?.total || 0
  } catch (error) {
    console.error('加载房源列表失败:', error)
    ElMessage.error('加载房源列表失败')
  } finally {
    loading.value = false
  }
}

// 创建防抖搜索函数(延迟 500ms)
const debouncedSearch = debounce(() => {
  loadHouseList()
}, 500)

// 搜索
const handleSearch = () => {
  pagination.page = 1
  loadHouseList()
}

// 重置
const handleReset = () => {
  Object.assign(searchForm, {
    keyword: '',
    city: '',
    district: '',
    rental_type: '',
    status: '',
    min_price: null,
    max_price: null
  })
  handleSearch()
}

// 查看详情
const handleView = (house) => {
  router.push(`/houses/${house.id}`)
}

// 新增房源
const handleAdd = () => {
  dialogTitle.value = '新增房源'
  isEdit.value = false
  currentHouseData.value = {}
  dialogVisible.value = true
}

// 编辑房源
const handleEdit = async (house) => {
  try {
    // 先获取完整的房源详情（包含 rooms 字段）
    const res = await getHouseDetailApi(house.id)
    const houseDetail = res.data
    
    dialogTitle.value = '编辑房源'
    isEdit.value = true
    currentHouseData.value = houseDetail
    dialogVisible.value = true
  } catch (error) {
    console.error('获取房源详情失败:', error)
    ElMessage.error('获取房源详情失败，无法编辑')
  }
}

// 删除房源
const handleDelete = (house) => {
  ElMessageBox.confirm('确定要删除该房源吗？删除后不可恢复！', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      await deleteHouse(house.id)
      ElMessage.success('删除成功')
      loadHouseList()
    } catch (error) {
      console.error('删除失败:', error)
      // 显示后端返回的错误消息
      const errorMessage = error.response?.data?.error?.message || error.message || '删除失败，请重试'
      ElMessage.error(errorMessage)
    }
  }).catch(() => {})
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
    let result
    if (isEdit.value) {
      // 编辑
      result = await houseStore.editHouse(currentHouseData.value.id, data)
      ElMessage.success('编辑成功')
    } else {
      // 新增
      result = await houseStore.addHouse(data)
      ElMessage.success('创建成功')
    }
    
    // 调用成功回调，返回房源数据
    if (submitSuccessCallback) {
      submitSuccessCallback(result)
      submitSuccessCallback = null
    }
    
    dialogVisible.value = false
    loadHouseList()
  } catch (error) {
    console.error('提交失败:', error)
    // 抛出错误，让子组件知道提交失败
    throw error
  } finally {
    formSubmitLoading.value = false
  }
}

// 分页大小改变
const handleSizeChange = () => {
  loadHouseList()
}

// 页码改变
const handlePageChange = () => {
  loadHouseList()
}

onMounted(() => {
  loadHouseList()
})

onBeforeUnmount(() => {
  // 取消防抖函数,防止内存泄漏
  debouncedSearch.cancel()
})
</script>

<style lang="scss" scoped>
.house-list-page {
  padding: 20px;

  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;

    h2 {
      margin: 0;
      color: #333;
      font-size: 24px;
    }
  }

  .search-card {
    margin-bottom: 20px;

    .search-form {
      .range-separator {
        margin: 0 10px;
        color: #909399;
      }
    }
  }

  .house-list {
    margin-bottom: 20px;

    .house-col {
      margin-bottom: 20px;
    }

    .house-card {
      height: 100%;
      transition: all 0.3s;
      cursor: pointer;

      &:hover {
        transform: translateY(-5px);
      }

      .card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 10px;
      }

      .house-cover {
        position: relative;
        height: 200px;
        margin: -16px -16px 0;
        overflow: hidden;
        border-radius: 4px 4px 0 0;

        .cover-image {
          width: 100%;
          height: 100%;
          transition: all 0.3s;
        }

        &:hover {
          .cover-overlay {
            opacity: 1;
          }

          .cover-image {
            transform: scale(1.1);
          }
        }

        .cover-overlay {
          position: absolute;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: rgba(0, 0, 0, 0.5);
          display: flex;
          align-items: center;
          justify-content: center;
          opacity: 0;
          transition: opacity 0.3s;
        }

        .image-error {
          width: 100%;
          height: 100%;
          display: flex;
          align-items: center;
          justify-content: center;
          background: #f5f7fa;
          color: #909399;
          font-size: 40px;
        }
      }

      .house-info {
        padding: 12px 0;

        .house-title {
          margin: 0 0 8px;
          font-size: 16px;
          color: #333;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }

        .house-address {
          margin: 0 0 8px;
          font-size: 13px;
          color: #909399;
          display: flex;
          align-items: center;
          gap: 4px;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }

        .house-specs {
          display: flex;
          gap: 10px;
          margin-bottom: 8px;
          font-size: 13px;
          color: #606266;
        }

        .rental-progress {
          margin: 8px 0;

          .progress-label {
            font-size: 13px;
            color: #909399;
            display: block;
            margin-bottom: 4px;
          }

          .progress-info {
            display: flex;
            flex-direction: column;
            gap: 4px;

            .progress-text {
              font-size: 12px;
              color: #606266;
            }

            .progress-bar {
              width: 100%;
              height: 6px;

              .el-progress-bar__outer {
                background-color: #f0f2f5;
                border-radius: 3px;
              }

              .el-progress-bar__inner {
                background-color: #409eff;
                border-radius: 3px;
              }
            }
          }
        }

        .house-price {
          display: flex;
          align-items: baseline;
          gap: 4px;

          .price-label {
            font-size: 13px;
            color: #909399;
          }

          .price-value {
            font-size: 20px;
            color: #f56c6c;
            font-weight: bold;
          }

          .price-unit {
            font-size: 13px;
            color: #909399;
          }
        }
      }

      .house-actions {
        display: flex;
        justify-content: flex-end;
        gap: 10px;
        padding-top: 12px;
        border-top: 1px solid #ebeef5;
      }
    }
  }

  .pagination-card {
    .el-pagination {
      display: flex;
      justify-content: flex-end;
    }
  }
}
</style>
