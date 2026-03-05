# 公共组件库使用说明

## 组件列表

### 1. Pagination 分页组件

封装 Element Plus 的分页组件,提供统一的使用接口。

#### 基础用法

```vue
<template>
  <Pagination
    v-model:currentPage="pagination.page"
    v-model:pageSize="pagination.per_page"
    :total="pagination.total"
    :page-sizes="[10, 20, 30, 50]"
    @change="handlePageChange"
  />
</template>

<script setup>
import { reactive } from 'vue'
import { Pagination } from '@/components/common'

const pagination = reactive({
  page: 1,
  per_page: 10,
  total: 100
})

const handlePageChange = ({ page, pageSize }) => {
  console.log('页码:', page, '每页数量:', pageSize)
  // 重新加载数据
  loadData()
}
</script>
```

#### Props

| 参数 | 说明 | 类型 | 默认值 |
|------|------|------|--------|
| currentPage | 当前页码 | Number | 1 |
| pageSize | 每页显示数量 | Number | 10 |
| total | 总条数 | Number | 0 |
| pageSizes | 每页显示个数选择器的选项设置 | Array | [10, 20, 30, 50, 100] |
| layout | 分页布局 | String | 'total, sizes, prev, pager, next, jumper' |
| background | 是否使用背景色 | Boolean | true |
| small | 是否使用小型分页样式 | Boolean | false |
| disabled | 是否禁用 | Boolean | false |
| hideOnSinglePage | 只有一页时是否隐藏 | Boolean | false |

#### Events

| 事件名 | 说明 | 回调参数 |
|--------|------|----------|
| update:currentPage | 页码改变时触发 | (page: number) |
| update:pageSize | 每页数量改变时触发 | (pageSize: number) |
| change | 页码或每页数量改变时触发 | ({ page, pageSize }) |

---

### 2. SearchForm 搜索表单组件

支持动态表单字段配置的搜索表单组件。

#### 基础用法

```vue
<template>
  <SearchForm
    v-model="searchForm"
    :fields="searchFields"
    @search="handleSearch"
    @reset="handleReset"
  >
    <template #extra-buttons>
      <el-button type="success" @click="handleExport">导出</el-button>
    </template>
  </SearchForm>
</template>

<script setup>
import { reactive } from 'vue'
import { SearchForm } from '@/components/common'

const searchForm = reactive({
  keyword: '',
  status: '',
  city: '',
  dateRange: []
})

const searchFields = [
  {
    name: 'keyword',
    label: '关键词',
    type: 'input',
    placeholder: '请输入关键词'
  },
  {
    name: 'status',
    label: '状态',
    type: 'select',
    options: [
      { label: '可租', value: 'available' },
      { label: '已租', value: 'rented' },
      { label: '维修中', value: 'maintenance' }
    ]
  },
  {
    name: 'city',
    label: '城市',
    type: 'input'
  },
  {
    name: 'dateRange',
    label: '日期范围',
    type: 'daterange'
  }
]

const handleSearch = (formData) => {
  console.log('搜索条件:', formData)
  // 执行搜索
}

const handleReset = () => {
  console.log('重置搜索条件')
}
</script>
```

#### 字段配置说明

```javascript
{
  name: 'fieldName',        // 字段名
  label: '字段标签',         // 字段标签
  type: 'input',            // 字段类型: input/number/select/date/daterange
  placeholder: '提示文本',   // 占位文本
  width: '200px',           // 字段宽度
  clearable: true,          // 是否可清空
  defaultValue: null,       // 默认值
  
  // select 类型专用
  options: [                // 选项列表
    { label: '选项1', value: 'value1' },
    { label: '选项2', value: 'value2' }
  ],
  multiple: false,          // 是否多选
  
  // number 类型专用
  min: 0,                   // 最小值
  max: 100,                 // 最大值
  precision: 0,             // 小数位数
  step: 1,                  // 步长
  
  // date/daterange 类型专用
  format: 'YYYY-MM-DD',     // 显示格式
  valueFormat: 'YYYY-MM-DD', // 绑定值格式
  rangeSeparator: '至',     // 范围分隔符
  startPlaceholder: '开始日期',
  endPlaceholder: '结束日期'
}
```

#### Props

| 参数 | 说明 | 类型 | 默认值 |
|------|------|------|--------|
| fields | 字段配置数组 | Array | [] |
| modelValue | 表单数据对象 | Object | {} |

#### Events

| 事件名 | 说明 | 回调参数 |
|--------|------|----------|
| update:modelValue | 表单数据改变时触发 | (formData: Object) |
| search | 点击查询按钮时触发 | (formData: Object) |
| reset | 点击重置按钮时触发 | - |

#### Slots

| 插槽名 | 说明 |
|--------|------|
| extra-buttons | 额外的操作按钮 |

---

### 3. StatusTag 状态标签组件

统一的状态标签展示组件,根据数据库模型定义的状态映射显示对应的标签。

#### 基础用法

```vue
<template>
  <!-- 房源状态 -->
  <StatusTag type="house" status="available" />
  <StatusTag type="house" status="rented" />
  <StatusTag type="house" status="maintenance" />
  
  <!-- 合同状态 -->
  <StatusTag type="contract" status="draft" />
  <StatusTag type="contract" status="active" />
  <StatusTag type="contract" status="expired" />
  
  <!-- 支付状态 -->
  <StatusTag type="payment" status="pending" />
  <StatusTag type="payment" status="paid" />
  <StatusTag type="payment" status="overdue" />
  
  <!-- 用户状态 -->
  <StatusTag type="user" status="active" />
  <StatusTag type="user" status="inactive" />
  <StatusTag type="user" status="suspended" />
</template>

<script setup>
import { StatusTag } from '@/components/common'
</script>
```

#### 支持的状态映射

**房源状态 (house)**
- `available` → 可租 (success)
- `rented` → 已租 (info)
- `maintenance` → 维修中 (warning)
- `partially_rented` → 部分已租 (warning)

**合同状态 (contract)**
- `draft` → 草稿 (info)
- `pending` → 待签约 (warning)
- `active` → 履行中 (success)
- `expired` → 已到期 (danger)
- `terminated` → 已终止 (info)

**支付状态 (payment)**
- `pending` → 待支付 (warning)
- `paid` → 已支付 (success)
- `overdue` → 逾期 (danger)
- `partial` → 部分支付 (warning)
- `refunded` → 已退款 (info)

**用户状态 (user)**
- `active` → 活跃 (success)
- `inactive` → 非活跃 (info)
- `suspended` → 暂停 (danger)
- `resigned` → 离职 (info)
- `disabled` → 禁用 (danger)

**房东状态 (landlord)**
- `active` → 正常 (success)
- `inactive` → 停用 (info)
- `blacklisted` → 黑名单 (danger)

**租客状态 (tenant)**
- `active` → 在租 (success)
- `expired` → 已退租 (info)
- `blacklisted` → 黑名单 (danger)

#### Props

| 参数 | 说明 | 类型 | 默认值 |
|------|------|------|--------|
| type | 状态类型 | String | - |
| status | 状态值 | String | - |
| size | 标签大小 | String | 'default' |
| effect | 标签效果 | String | 'light' |

---

### 4. ConfirmDialog 确认对话框组件

封装删除确认逻辑的对话框组件。

#### 基础用法

```vue
<template>
  <div>
    <el-button type="danger" @click="showDeleteDialog = true">
      删除
    </el-button>
    
    <ConfirmDialog
      v-model="showDeleteDialog"
      title="删除确认"
      message="确定要删除这条数据吗？删除后不可恢复！"
      type="danger"
      :loading="deleteLoading"
      @confirm="handleConfirm"
      @cancel="handleCancel"
    />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ConfirmDialog } from '@/components/common'

const showDeleteDialog = ref(false)
const deleteLoading = ref(false)

const handleConfirm = async () => {
  deleteLoading.value = true
  try {
    // 执行删除操作
    await deleteData()
    showDeleteDialog.value = false
    // 刷新列表
    loadData()
  } catch (error) {
    console.error(error)
  } finally {
    deleteLoading.value = false
  }
}

const handleCancel = () => {
  console.log('取消删除')
}
</script>
```

#### 自定义内容

```vue
<template>
  <ConfirmDialog
    v-model="showDialog"
    title="自定义内容"
    type="warning"
    @confirm="handleConfirm"
  >
    <div>
      <p>这是自定义的提示内容</p>
      <p>可以包含多个段落</p>
    </div>
  </ConfirmDialog>
</template>
```

#### Props

| 参数 | 说明 | 类型 | 默认值 |
|------|------|------|--------|
| modelValue | 是否显示对话框 | Boolean | false |
| title | 标题 | String | '提示' |
| message | 提示消息 | String | '' |
| type | 类型 | String | 'warning' |
| confirmText | 确认按钮文本 | String | '确定' |
| cancelText | 取消按钮文本 | String | '取消' |
| showIcon | 是否显示图标 | Boolean | true |
| width | 对话框宽度 | String | '420px' |
| showClose | 是否显示关闭按钮 | Boolean | true |
| center | 是否居中 | Boolean | true |
| closeOnClickModal | 是否可以通过点击 modal 关闭 | Boolean | false |
| closeOnPressEscape | 是否可以通过按下 ESC 关闭 | Boolean | true |
| customClass | 自定义类名 | String | 'confirm-dialog' |
| loading | 确认按钮加载状态 | Boolean | false |

#### Events

| 事件名 | 说明 | 回调参数 |
|--------|------|----------|
| update:modelValue | 对话框显示状态改变时触发 | (visible: boolean) |
| confirm | 点击确认按钮时触发 | - |
| cancel | 点击取消按钮时触发 | - |
| close | 对话框关闭时触发 | - |

---

## 全局注册

在 `main.js` 中全局注册所有公共组件:

```javascript
import { createApp } from 'vue'
import App from './App.vue'
import CommonComponents from '@/components/common'

const app = createApp(App)

// 全局注册公共组件
app.use(CommonComponents)

app.mount('#app')
```

全局注册后,可以直接在模板中使用:

```vue
<template>
  <Pagination
    v-model:currentPage="page"
    v-model:pageSize="pageSize"
    :total="total"
  />
  
  <StatusTag type="house" status="available" />
</template>
```

---

## 按需引入

推荐使用按需引入方式:

```vue
<script setup>
import { Pagination, SearchForm, StatusTag, ConfirmDialog } from '@/components/common'
</script>
```

---

## 设计原则

1. **一致性**: 所有组件遵循统一的设计规范和交互模式
2. **可复用性**: 组件设计考虑多种使用场景,提供灵活的配置选项
3. **类型安全**: 使用 TypeScript 风格的 prop 验证,确保类型正确
4. **响应式**: 所有组件支持响应式布局,适配移动端
5. **可访问性**: 遵循 WCAG 标准,确保组件可访问性
6. **性能优化**: 使用 computed 和 watch 优化性能,避免不必要的渲染

---

## 注意事项

1. 所有组件基于 Element Plus 开发,确保项目已安装 Element Plus
2. 组件样式使用 SCSS 编写,确保项目支持 SCSS
3. 状态映射严格遵循数据库模型设计文档中的定义
4. 建议使用按需引入方式,减少打包体积
