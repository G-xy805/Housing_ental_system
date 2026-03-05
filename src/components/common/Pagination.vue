<template>
  <div class="pagination-wrapper">
    <el-pagination
      v-model:current-page="currentPageModel"
      v-model:page-size="pageSizeModel"
      :total="total"
      :page-sizes="pageSizes"
      :layout="layout"
      :background="background"
      :small="small"
      :disabled="disabled"
      :hide-on-single-page="hideOnSinglePage"
      @size-change="handleSizeChange"
      @current-change="handleCurrentChange"
    />
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  // 当前页码
  currentPage: {
    type: Number,
    default: 1
  },
  // 每页显示数量
  pageSize: {
    type: Number,
    default: 10
  },
  // 总条数
  total: {
    type: Number,
    default: 0
  },
  // 每页显示个数选择器的选项设置
  pageSizes: {
    type: Array,
    default: () => [10, 20, 30, 50, 100]
  },
  // 分页布局
  layout: {
    type: String,
    default: 'total, sizes, prev, pager, next, jumper'
  },
  // 是否使用背景色
  background: {
    type: Boolean,
    default: true
  },
  // 是否使用小型分页样式
  small: {
    type: Boolean,
    default: false
  },
  // 是否禁用
  disabled: {
    type: Boolean,
    default: false
  },
  // 只有一页时是否隐藏
  hideOnSinglePage: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:currentPage', 'update:pageSize', 'change'])

// 双向绑定 currentPage
const currentPageModel = computed({
  get: () => props.currentPage,
  set: (val) => emit('update:currentPage', val)
})

// 双向绑定 pageSize
const pageSizeModel = computed({
  get: () => props.pageSize,
  set: (val) => emit('update:pageSize', val)
})

// 每页数量改变
const handleSizeChange = (val) => {
  emit('change', { page: props.currentPage, pageSize: val })
}

// 当前页改变
const handleCurrentChange = (val) => {
  emit('change', { page: val, pageSize: props.pageSize })
}
</script>

<style lang="scss" scoped>
.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  padding: 16px 0;
  
  :deep(.el-pagination) {
    .el-pagination__total,
    .el-pagination__sizes,
    .el-pagination__jump {
      margin-right: 10px;
    }
  }
}
</style>
