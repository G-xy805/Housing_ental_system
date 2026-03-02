<template>
  <div class="landlord-list-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <h2>房东管理</h2>
      <el-button type="primary" @click="handleAdd" v-if="hasPermission('add')">
        <el-icon><Plus /></el-icon>
        新增房东
      </el-button>
    </div>

    <!-- 搜索栏 -->
    <el-card class="search-card">
      <el-form :inline="true" :model="searchForm" class="search-form" @keyup.enter="handleSearch">
        <el-form-item label="关键词">
          <el-input
            v-model="searchForm.keyword"
            placeholder="姓名/手机号"
            clearable
            style="width: 200px"
          />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="searchForm.status" placeholder="请选择" clearable style="width: 120px">
            <el-option label="正常" value="active" />
            <el-option label="停用" value="inactive" />
            <el-option label="黑名单" value="blacklisted" />
          </el-select>
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

    <!-- 房东列表 -->
    <el-card class="table-card" v-loading="loading">
      <el-table :data="landlordList" stripe style="width: 100%">
        <el-table-column prop="name" label="姓名" width="100" />
        <el-table-column prop="phone" label="手机号" width="130" />
        <el-table-column prop="id_card" label="身份证号" width="180">
          <template #default="{ row }">
            {{ maskIdCard(row.id_card) }}
          </template>
        </el-table-column>
        <el-table-column prop="houses_count" label="房源数" width="80" align="center" />
        <el-table-column prop="contracts_count" label="合同数" width="80" align="center" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="remark" label="备注" min-width="150" show-overflow-tooltip />
        <el-table-column prop="created_at" label="创建时间" width="160">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button
              link
              type="primary"
              @click="handleViewDetail(row)"
              v-if="hasPermission('view')"
            >
              <el-icon><View /></el-icon>
              详情
            </el-button>
            <el-button
              link
              type="primary"
              @click="handleEdit(row)"
              v-if="hasPermission('edit')"
            >
              <el-icon><Edit /></el-icon>
              编辑
            </el-button>
            <el-button
              link
              type="danger"
              @click="handleDelete(row)"
              v-if="hasPermission('delete')"
            >
              <el-icon><Delete /></el-icon>
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.per_page"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          :total="pagination.total"
          @size-change="handleSizeChange"
          @current-change="handlePageChange"
        />
      </div>
    </el-card>

    <!-- 房东详情对话框 -->
    <el-dialog
      v-model="detailVisible"
      title="房东详情"
      width="1000px"
      :close-on-click-modal="false"
      destroy-on-close
    >
      <div v-loading="detailLoading" class="detail-content">
        <!-- 基本信息 -->
        <el-descriptions title="基本信息" :column="2" border>
          <el-descriptions-item label="姓名">{{ currentLandlord.name }}</el-descriptions-item>
          <el-descriptions-item label="手机号">{{ currentLandlord.phone }}</el-descriptions-item>
          <el-descriptions-item label="身份证号">
            {{ maskIdCard(currentLandlord.id_card) }}
          </el-descriptions-item>
          <el-descriptions-item label="银行卡号">
            {{ maskBankCard(currentLandlord.bank_card) }}
          </el-descriptions-item>
          <el-descriptions-item label="开户行">{{ currentLandlord.bank_name || '-' }}</el-descriptions-item>
          <el-descriptions-item label="房产证编号">{{ currentLandlord.property_cert_no || '-' }}</el-descriptions-item>
          <el-descriptions-item label="房产地址" :span="2">
            {{ currentLandlord.property_address || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="getStatusType(currentLandlord.status)">
              {{ getStatusText(currentLandlord.status) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="备注" :span="2">
            {{ currentLandlord.remark || '-' }}
          </el-descriptions-item>
        </el-descriptions>

        <!-- 统计信息 -->
        <el-row :gutter="20" class="stats-row" v-if="statsData">
          <el-col :span="12">
            <el-card class="stat-card">
              <div class="stat-content">
                <div class="stat-icon houses">
                  <el-icon :size="32"><House /></el-icon>
                </div>
                <div class="stat-info">
                  <div class="stat-value">{{ statsData.houses_count || 0 }}</div>
                  <div class="stat-label">房源总数</div>
                </div>
              </div>
            </el-card>
          </el-col>
          <el-col :span="12">
            <el-card class="stat-card">
              <div class="stat-content">
                <div class="stat-icon contracts">
                  <el-icon :size="32"><Document /></el-icon>
                </div>
                <div class="stat-info">
                  <div class="stat-value">{{ statsData.contracts_count || 0 }}</div>
                  <div class="stat-label">合同总数</div>
                </div>
              </div>
            </el-card>
          </el-col>
        </el-row>

        <!-- 关联房源列表 -->
        <div class="section-title">
          <el-icon><House /></el-icon>
          关联房源
          <el-tag type="info" size="small" style="margin-left: 10px;">
            {{ housesList.length }} 个
          </el-tag>
        </div>
        <el-table :data="housesList" stripe style="margin-bottom: 20px;" v-loading="housesLoading">
          <el-table-column prop="title" label="标题" min-width="150" show-overflow-tooltip />
          <el-table-column prop="address" label="地址" min-width="180" show-overflow-tooltip />
          <el-table-column prop="type" label="类型" width="80">
            <template #default="{ row }">
              {{ getTypeText(row.type) }}
            </template>
          </el-table-column>
          <el-table-column prop="rent_price" label="租金" width="100">
            <template #default="{ row }">
              ¥{{ row.rent_price }}/月
            </template>
          </el-table-column>
          <el-table-column prop="status" label="状态" width="80">
            <template #default="{ row }">
              <el-tag :type="getHouseStatusType(row.status)" size="small">
                {{ getHouseStatusText(row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="80" fixed="right">
            <template #default="{ row }">
              <el-button
                link
                type="primary"
                @click="handleViewHouse(row)"
              >
                查看
              </el-button>
            </template>
          </el-table-column>
        </el-table>

        <!-- 关联承包合同列表 -->
        <div class="section-title">
          <el-icon><Document /></el-icon>
          关联承包合同
          <el-tag type="info" size="small" style="margin-left: 10px;">
            {{ contractsList.length }} 个
          </el-tag>
        </div>
        <el-table :data="contractsList" stripe v-loading="contractsLoading">
          <el-table-column prop="contract_no" label="合同编号" width="150" />
          <el-table-column prop="title" label="标题" min-width="180" show-overflow-tooltip />
          <el-table-column prop="amount" label="合同金额" width="100">
            <template #default="{ row }">
              ¥{{ row.amount }}
            </template>
          </el-table-column>
          <el-table-column label="期限" width="180">
            <template #default="{ row }">
              {{ formatDate(row.start_date) }} 至 {{ formatDate(row.end_date) }}
            </template>
          </el-table-column>
          <el-table-column prop="status" label="状态" width="80">
            <template #default="{ row }">
              <el-tag :type="getContractStatusType(row.status)" size="small">
                {{ getContractStatusText(row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="80" fixed="right">
            <template #default="{ row }">
              <el-button
                link
                type="primary"
                @click="handleViewContract(row)"
              >
                查看
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <template #footer>
        <div style="display: flex; justify-content: flex-end;">
          <el-button @click="detailVisible = false">关闭</el-button>
          <el-button type="primary" @click="handleEditFromDetail" v-if="hasPermission('edit')">
            编辑
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 新增/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="700px"
      :close-on-click-modal="false"
      destroy-on-close
      @close="handleDialogClose"
    >
      <LandlordForm
        ref="landlordFormRef"
        v-model="currentLandlordData"
        :is-edit="isEdit"
        :submit-loading="formSubmitLoading"
        :show-delete-button="hasPermission('delete')"
        :delete-disabled="currentLandlordData.houses_count > 0 || currentLandlordData.contracts_count > 0"
        @submit="handleSubmit"
        @cancel="handleDialogClose"
        @delete="handleDeleteFromDialog"
      />
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Plus,
  Search,
  Refresh,
  View,
  Edit,
  Delete,
  House,
  Document
} from '@element-plus/icons-vue'
import dayjs from 'dayjs'
import {
  getLandlordList,
  getLandlordDetail,
  createLandlord,
  updateLandlord,
  deleteLandlord,
  getLandlordHouses,
  getLandlordContracts
} from '@/api/landlord'
import { useUserStore } from '@/store/user'
import LandlordForm from '@/components/landlord/LandlordForm.vue'

const router = useRouter()
const userStore = useUserStore()

// 列表相关
const loading = ref(false)
const landlordList = ref([])
const searchForm = reactive({
  keyword: '',
  status: ''
})
const pagination = reactive({
  page: 1,
  per_page: 10,
  total: 0
})

// 详情对话框
const detailVisible = ref(false)
const detailLoading = ref(false)
const currentLandlord = ref({})
const statsData = ref(null)
const housesList = ref([])
const housesLoading = ref(false)
const contractsList = ref([])
const contractsLoading = ref(false)

// 新增/编辑对话框
const dialogVisible = ref(false)
const dialogTitle = ref('新增房东')
const isEdit = ref(false)
const formSubmitLoading = ref(false)
const landlordFormRef = ref(null)
const currentLandlordData = ref({})

// 权限检查
const hasPermission = (action) => {
  return userStore.isAdmin || userStore.userType === 'landlord'
}

// 获取状态类型
const getStatusType = (status) => {
  const types = {
    active: 'success',
    inactive: 'info',
    blacklisted: 'danger'
  }
  return types[status] || 'info'
}

// 获取状态文本
const getStatusText = (status) => {
  const texts = {
    active: '正常',
    inactive: '停用',
    blacklisted: '黑名单'
  }
  return texts[status] || status
}

// 获取房源类型文本
const getTypeText = (type) => {
  const texts = {
    whole: '整租',
    shared: '合租',
    apartment: '公寓',
    villa: '别墅'
  }
  return texts[type] || type
}

// 获取房源状态类型
const getHouseStatusType = (status) => {
  const types = {
    available: 'success',
    rented: 'info',
    maintenance: 'warning',
    partially_rented: 'success'
  }
  return types[status] || 'info'
}

// 获取房源状态文本
const getHouseStatusText = (status) => {
  const texts = {
    available: '可租',
    rented: '已租',
    maintenance: '维修中',
    partially_rented: '部分已租'
  }
  return texts[status] || status
}

// 获取合同状态类型
const getContractStatusType = (status) => {
  const types = {
    draft: 'info',
    active: 'success',
    expired: 'warning',
    terminated: 'danger'
  }
  return types[status] || 'info'
}

// 获取合同状态文本
const getContractStatusText = (status) => {
  const texts = {
    draft: '草稿',
    active: '执行中',
    expired: '已过期',
    terminated: '已终止'
  }
  return texts[status] || status
}

// 身份证号脱敏
const maskIdCard = (idCard) => {
  if (!idCard) return '-'
  if (idCard.length === 18) {
    return idCard.substring(0, 6) + '********' + idCard.substring(14)
  }
  return idCard
}

// 银行卡号脱敏
const maskBankCard = (bankCard) => {
  if (!bankCard) return '-'
  const cleaned = bankCard.replace(/\s/g, '')
  if (cleaned.length >= 8) {
    const last4 = cleaned.substring(cleaned.length - 4)
    return `6222 **** **** ${last4}`
  }
  return bankCard
}

// 格式化日期
const formatDate = (date) => {
  if (!date) return '-'
  return dayjs(date).format('YYYY-MM-DD HH:mm:ss')
}

// 加载房东列表
const loadLandlordList = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      per_page: pagination.per_page,
      keyword: searchForm.keyword,
      status: searchForm.status
    }
    const res = await getLandlordList(params)
    if (res.success && res.data) {
      landlordList.value = res.data.items || []
      pagination.total = res.data.pagination?.total || 0
    }
  } catch (error) {
    console.error('加载房东列表失败:', error)
    ElMessage.error('加载房东列表失败')
  } finally {
    loading.value = false
  }
}

// 加载房东详情
const loadLandlordDetail = async (id) => {
  detailLoading.value = true
  try {
    const res = await getLandlordDetail(id)
    if (res.success && res.data) {
      currentLandlord.value = res.data
      statsData.value = {
        houses_count: res.data.houses_count || 0,
        contracts_count: res.data.contracts_count || 0
      }
    }
  } catch (error) {
    console.error('加载房东详情失败:', error)
    ElMessage.error('加载房东详情失败')
  } finally {
    detailLoading.value = false
  }
}

// 加载房东的房源列表
const loadLandlordHouses = async (landlordId) => {
  housesLoading.value = true
  try {
    const res = await getLandlordHouses(landlordId, { page: 1, per_page: 100 })
    if (res.success && res.data) {
      housesList.value = res.data.houses || []
    }
  } catch (error) {
    console.error('加载房源列表失败:', error)
    housesList.value = []
  } finally {
    housesLoading.value = false
  }
}

// 加载房东的合同列表
const loadLandlordContracts = async (landlordId) => {
  contractsLoading.value = true
  try {
    const res = await getLandlordContracts(landlordId, { page: 1, per_page: 100 })
    if (res.success && res.data) {
      contractsList.value = res.data.contracts || []
    }
  } catch (error) {
    console.error('加载合同列表失败:', error)
    contractsList.value = []
  } finally {
    contractsLoading.value = false
  }
}

// 搜索
const handleSearch = () => {
  pagination.page = 1
  loadLandlordList()
}

// 重置
const handleReset = () => {
  searchForm.keyword = ''
  searchForm.status = ''
  pagination.page = 1
  loadLandlordList()
}

// 分页变化
const handleSizeChange = (size) => {
  pagination.per_page = size
  pagination.page = 1
  loadLandlordList()
}

const handlePageChange = (page) => {
  pagination.page = page
  loadLandlordList()
}

// 查看详情
const handleViewDetail = async (row) => {
  currentLandlord.value = {}
  statsData.value = null
  housesList.value = []
  contractsList.value = []
  detailVisible.value = true
  
  await loadLandlordDetail(row.id)
  await loadLandlordHouses(row.id)
  await loadLandlordContracts(row.id)
}

// 新增
const handleAdd = () => {
  isEdit.value = false
  dialogTitle.value = '新增房东'
  currentLandlordData.value = {}
  dialogVisible.value = true
}

// 编辑
const handleEdit = async (row) => {
  isEdit.value = true
  dialogTitle.value = '编辑房东'
  
  try {
    // 加载房东详情数据
    const res = await getLandlordDetail(row.id)
    if (res.success && res.data) {
      const detail = res.data
      currentLandlordData.value = {
        id: detail.id,
        name: detail.name,
        phone: detail.phone,
        id_card: detail.id_card || '',
        bank_card: detail.bank_card || '',
        bank_name: detail.bank_name || '',
        property_cert_no: detail.property_cert_no || '',
        address: detail.property_address || detail.address || '',
        status: detail.status,
        remark: detail.remark || '',
        houses_count: detail.houses_count || 0,
        contracts_count: detail.contracts_count || 0
      }
      dialogVisible.value = true
    }
  } catch (error) {
    console.error('加载房东详情失败:', error)
    ElMessage.error('加载房东详情失败')
  }
}

// 从详情编辑
const handleEditFromDetail = () => {
  detailVisible.value = false
  handleEdit(currentLandlord.value)
}

// 删除
const handleDelete = (row) => {
  ElMessageBox.confirm(`确定要删除房东"${row.name}"吗？删除后不可恢复！`, '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      await deleteLandlord(row.id)
      ElMessage.success('删除成功')
      loadLandlordList()
    } catch (error) {
      console.error('删除失败:', error)
      const errorMessage = error.response?.data?.error?.message || error.message || '删除失败，请重试'
      ElMessage.error(errorMessage)
    }
  }).catch(() => {})
}

// 从对话框删除
const handleDeleteFromDialog = (formData) => {
  const landlordName = formData.name || currentLandlordData.value.name
  ElMessageBox.confirm(`确定要删除房东"${landlordName}"吗？删除后不可恢复！`, '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      const landlordId = formData.id || currentLandlordData.value.id
      await deleteLandlord(landlordId)
      ElMessage.success('删除成功')
      dialogVisible.value = false
      loadLandlordList()
    } catch (error) {
      console.error('删除失败:', error)
      const errorMessage = error.response?.data?.error?.message || error.message || '删除失败，请重试'
      ElMessage.error(errorMessage)
    }
  }).catch(() => {})
}

// 查看房源
const handleViewHouse = (house) => {
  router.push(`/houses/${house.id}`)
}

// 查看合同
const handleViewContract = (contract) => {
  // 根据实际路由配置调整
  ElMessage.info('合同详情功能待实现')
}

// 提交
const handleSubmit = async (formData) => {
  formSubmitLoading.value = true
  try {
    if (isEdit.value) {
      await updateLandlord(formData.id, formData)
      ElMessage.success('编辑成功')
    } else {
      await createLandlord(formData)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    loadLandlordList()
  } catch (error) {
    console.error('提交失败:', error)
    const errorMessage = error.response?.data?.error?.message || error.message || '操作失败，请重试'
    ElMessage.error(errorMessage)
  } finally {
    formSubmitLoading.value = false
  }
}

// 关闭对话框
const handleDialogClose = () => {
  dialogVisible.value = false
  currentLandlordData.value = {}
  // 重置表单组件
  setTimeout(() => {
    landlordFormRef.value?.resetForm()
  }, 0)
}

onMounted(() => {
  loadLandlordList()
})
</script>

<style lang="scss" scoped>
.landlord-list-page {
  padding: 20px;

  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;

    h2 {
      margin: 0;
      font-size: 24px;
      font-weight: bold;
      color: #333;
    }
  }

  .search-card {
    margin-bottom: 20px;
  }

  .table-card {
    .pagination-container {
      display: flex;
      justify-content: flex-end;
      margin-top: 20px;
    }
  }

  .detail-content {
    .el-descriptions {
      margin-bottom: 20px;
    }

    .stats-row {
      margin-bottom: 20px;

      .stat-card {
        .stat-content {
          display: flex;
          align-items: center;
          gap: 15px;

          .stat-icon {
            width: 60px;
            height: 60px;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;

            &.houses {
              background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
              color: #fff;
            }

            &.contracts {
              background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
              color: #fff;
            }
          }

          .stat-info {
            flex: 1;

            .stat-value {
              font-size: 28px;
              font-weight: bold;
              color: #333;
              line-height: 1;
            }

            .stat-label {
              font-size: 14px;
              color: #909399;
              margin-top: 5px;
            }
          }
        }
      }
    }

    .section-title {
      display: flex;
      align-items: center;
      font-size: 16px;
      font-weight: bold;
      color: #333;
      margin: 20px 0 10px;
      padding-bottom: 10px;
      border-bottom: 2px solid #409eff;

      .el-icon {
        margin-right: 8px;
        color: #409eff;
      }
    }
  }
}
</style>
