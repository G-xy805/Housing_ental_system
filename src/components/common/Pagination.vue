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
@import '@/styles/variables.scss';

.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  padding: $spacing-4 0;

  :deep(.el-pagination) {
    gap: $spacing-2;

    // 总条数
    .el-pagination__total {
      margin-right: $spacing-3;
      color: $text-regular;
      font-size: $font-size-sm;
      font-weight: $font-weight-medium;
      height: 32px;
      line-height: 32px;
    }

    // 每页数量选择器
    .el-pagination__sizes {
      margin-right: $spacing-3;

      .el-select {
        .el-input__wrapper {
          border-radius: $radius-lg;
          transition: all $transition-normal;
          box-shadow: none;
          border: 1px solid $border-secondary;

          &:hover {
            border-color: $primary-light;
          }

          &.is-focus {
            border-color: $primary-color;
            box-shadow: 0 0 0 2px rgba($primary-color, 0.1);
          }
        }
      }
    }

    // 页码按钮组
    .el-pager {
      li {
        min-width: 32px;
        height: 32px;
        line-height: 30px;
        border-radius: $radius-lg;
        font-weight: $font-weight-medium;
        color: $text-regular;
        background-color: $white;
        border: 1px solid $border-secondary;
        margin: 0 4px;
        transition: all $transition-normal;

        &:hover {
          color: $primary-color;
          border-color: $primary-light;
          background-color: $bg-primary;
        }

        // 当前页激活状态
        &.is-active {
          background: $gradient-primary;
          border-color: transparent;
          color: $white;
          box-shadow: $shadow-sm;

          &:hover {
            background: $gradient-btn-primary-hover;
          }
        }

        // 禁用状态
        &.is-disabled {
          color: $text-disabled;
          background-color: $gray-100;
          border-color: $gray-200;
          cursor: not-allowed;

          &:hover {
            color: $text-disabled;
            background-color: $gray-100;
            border-color: $gray-200;
          }
        }
      }
    }

    // 上一页/下一页按钮
    .btn-prev,
    .btn-next {
      min-width: 32px;
      height: 32px;
      line-height: 30px;
      border-radius: $radius-lg;
      font-weight: $font-weight-medium;
      color: $text-regular;
      background-color: $white;
      border: 1px solid $border-secondary;
      transition: all $transition-normal;

      &:hover:not(:disabled) {
        color: $primary-color;
        border-color: $primary-light;
        background-color: $bg-primary;
      }

      &:disabled {
        color: $text-disabled;
        background-color: $gray-100;
        border-color: $gray-200;
        cursor: not-allowed;
      }

      .el-icon {
        font-size: 14px;
      }
    }

    // 快速跳转
    .el-pagination__jump {
      margin-left: $spacing-3;
      color: $text-regular;
      font-size: $font-size-sm;
      font-weight: $font-weight-medium;
      height: 32px;
      line-height: 32px;

      .el-input {
        width: 50px;
        margin: 0 8px;

        .el-input__wrapper {
          border-radius: $radius-lg;
          transition: all $transition-normal;
          box-shadow: none;
          border: 1px solid $border-secondary;
          padding: 0 8px;

          &:hover {
            border-color: $primary-light;
          }

          &.is-focus {
            border-color: $primary-color;
            box-shadow: 0 0 0 2px rgba($primary-color, 0.1);
          }
        }

        .el-input__inner {
          text-align: center;
          font-weight: $font-weight-medium;
        }
      }
    }
  }

  // 小型分页样式
  :deep(.el-pagination--small) {
    .el-pager li,
    .btn-prev,
    .btn-next {
      min-width: 28px;
      height: 28px;
      line-height: 26px;
      font-size: $font-size-xs;
    }

    .el-pagination__total,
    .el-pagination__jump {
      font-size: $font-size-xs;
      height: 28px;
      line-height: 28px;
    }
  }
}

// 响应式适配
@media screen and (max-width: $breakpoint-sm) {
  .pagination-wrapper {
    justify-content: center;
    padding: $spacing-3 0;

    :deep(.el-pagination) {
      flex-wrap: wrap;
      justify-content: center;

      .el-pagination__total {
        width: 100%;
        text-align: center;
        margin-right: 0;
        margin-bottom: $spacing-2;
      }

      .el-pagination__sizes {
        margin-right: $spacing-2;
      }

      .el-pagination__jump {
        margin-left: 0;
        margin-top: $spacing-2;
        width: 100%;
        text-align: center;
      }
    }
  }
}
</style>
