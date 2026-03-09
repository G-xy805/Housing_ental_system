<template>
  <el-card class="search-form-card" shadow="never">
    <el-form
      :inline="true"
      :model="modelValue"
      class="search-form"
      @keyup.enter="handleSearch"
    >
      <template v-for="field in fields" :key="field.name">
        <!-- 输入框 -->
        <el-form-item
          v-if="field.type === 'input'"
          :label="field.label"
        >
          <el-input
            v-model="formData[field.name]"
            :placeholder="field.placeholder || `请输入${field.label}`"
            :clearable="field.clearable !== false"
            :style="{ width: field.width || '200px' }"
          />
        </el-form-item>

        <!-- 数字输入框 -->
        <el-form-item
          v-else-if="field.type === 'number'"
          :label="field.label"
        >
          <el-input-number
            v-model="formData[field.name]"
            :placeholder="field.placeholder || `请输入${field.label}`"
            :min="field.min"
            :max="field.max"
            :precision="field.precision"
            :step="field.step || 1"
            :style="{ width: field.width || '150px' }"
          />
        </el-form-item>

        <!-- 选择器 -->
        <el-form-item
          v-else-if="field.type === 'select'"
          :label="field.label"
        >
          <el-select
            v-model="formData[field.name]"
            :placeholder="field.placeholder || `请选择${field.label}`"
            :clearable="field.clearable !== false"
            :multiple="field.multiple"
            :style="{ width: field.width || '150px' }"
          >
            <el-option
              v-for="option in field.options"
              :key="option.value"
              :label="option.label"
              :value="option.value"
            />
          </el-select>
        </el-form-item>

        <!-- 日期选择器 -->
        <el-form-item
          v-else-if="field.type === 'date'"
          :label="field.label"
        >
          <el-date-picker
            v-model="formData[field.name]"
            type="date"
            :placeholder="field.placeholder || `请选择${field.label}`"
            :clearable="field.clearable !== false"
            :format="field.format || 'YYYY-MM-DD'"
            :value-format="field.valueFormat || 'YYYY-MM-DD'"
            :style="{ width: field.width || '180px' }"
          />
        </el-form-item>

        <!-- 日期范围选择器 -->
        <el-form-item
          v-else-if="field.type === 'daterange'"
          :label="field.label"
        >
          <el-date-picker
            v-model="formData[field.name]"
            type="daterange"
            :range-separator="field.rangeSeparator || '至'"
            :start-placeholder="field.startPlaceholder || '开始日期'"
            :end-placeholder="field.endPlaceholder || '结束日期'"
            :clearable="field.clearable !== false"
            :format="field.format || 'YYYY-MM-DD'"
            :value-format="field.valueFormat || 'YYYY-MM-DD'"
            :style="{ width: field.width || '260px' }"
          />
        </el-form-item>
      </template>

      <!-- 操作按钮 -->
      <el-form-item class="search-actions">
        <el-button type="primary" @click="handleSearch">
          <el-icon><Search /></el-icon>
          查询
        </el-button>
        <el-button @click="handleReset">
          <el-icon><Refresh /></el-icon>
          重置
        </el-button>
        <slot name="extra-buttons"></slot>
      </el-form-item>
    </el-form>
  </el-card>
</template>

<script setup>
import { reactive, watch } from 'vue'
import { Search, Refresh } from '@element-plus/icons-vue'

const props = defineProps({
  // 字段配置数组
  fields: {
    type: Array,
    default: () => []
  },
  // 表单数据对象
  modelValue: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['update:modelValue', 'search', 'reset'])

// 表单数据
const formData = reactive({})

// 监听 modelValue 变化，更新 formData
watch(
  () => props.modelValue,
  (newVal) => {
    Object.keys(newVal).forEach((key) => {
      formData[key] = newVal[key]
    })
  },
  { immediate: true, deep: true }
)

// 监听 formData 变化，更新 modelValue
watch(
  formData,
  (newVal) => {
    emit('update:modelValue', { ...newVal })
  },
  { deep: true }
)

// 搜索
const handleSearch = () => {
  emit('search', { ...formData })
}

// 重置
const handleReset = () => {
  // 重置所有字段为初始值
  props.fields.forEach((field) => {
    formData[field.name] = field.defaultValue ?? null
  })
  emit('reset')
  emit('search', { ...formData })
}
</script>

<style lang="scss" scoped>
@import '@/styles/variables.scss';

.search-form-card {
  margin-bottom: $spacing-5;
  border-radius: $radius-xl;
  border: 1px solid $border-secondary;
  background: $gradient-card;
  transition: all $transition-normal;

  &:hover {
    box-shadow: $shadow-md;
    border-color: $border-primary;
  }

  :deep(.el-card__body) {
    padding: $spacing-4 $spacing-5 $spacing-1;
  }

  .search-form {
    display: flex;
    flex-wrap: wrap;
    gap: $spacing-2;

    .el-form-item {
      margin-bottom: $spacing-4;
      margin-right: 0;

      :deep(.el-form-item__label) {
        color: $text-secondary;
        font-weight: $font-weight-medium;
        font-size: $font-size-sm;
        padding-right: $spacing-3;
      }

      // 输入框通用样式
      :deep(.el-input__wrapper),
      :deep(.el-select__wrapper),
      :deep(.el-date-editor) {
        border-radius: $radius-lg;
        transition: all $transition-normal;
        box-shadow: none;
        border: 1px solid $border-secondary;
        background-color: $white;

        &:hover {
          border-color: $primary-light;
          background-color: $bg-primary;
        }

        &.is-focus,
        &.is-focus .el-input__wrapper {
          border-color: $primary-color;
          box-shadow: 0 0 0 3px rgba($primary-color, 0.1);
          background-color: $white;
        }
      }

      // 输入框内部文字
      :deep(.el-input__inner) {
        color: $text-primary;
        font-weight: $font-weight-normal;

        &::placeholder {
          color: $text-placeholder;
        }
      }

      // 数字输入框
      :deep(.el-input-number) {
        .el-input__wrapper {
          padding-left: $spacing-5;
          padding-right: $spacing-5;
        }

        .el-input-number__decrease,
        .el-input-number__increase {
          border-radius: $radius-md;
          transition: all $transition-fast;

          &:hover {
            color: $primary-color;
            background-color: $bg-primary;
          }
        }
      }

      // 选择器
      :deep(.el-select) {
        .el-select__selected-item {
          color: $text-primary;
          font-weight: $font-weight-medium;
        }

        .el-select__placeholder {
          color: $text-placeholder;
        }
      }

      // 日期选择器
      :deep(.el-date-editor) {
        .el-input__prefix,
        .el-input__suffix {
          color: $text-muted;
          transition: color $transition-fast;
        }

        &:hover .el-input__prefix,
        &:hover .el-input__suffix {
          color: $primary-color;
        }

        // 日期范围分隔符
        .el-range-separator {
          color: $text-muted;
          font-weight: $font-weight-medium;
        }
      }
    }

    // 操作按钮区域
    .search-actions {
      margin-left: auto;
      margin-bottom: $spacing-4;

      :deep(.el-form-item__content) {
        gap: $spacing-3;
      }

      // 查询按钮
      :deep(.el-button--primary) {
        background: $gradient-btn-primary;
        border: none;
        border-radius: $radius-lg;
        font-weight: $font-weight-medium;
        padding: 10px 20px;
        transition: all $transition-normal;
        box-shadow: $shadow-sm;

        &:hover {
          background: $gradient-btn-primary-hover;
          transform: translateY(-1px);
          box-shadow: $shadow-md;
        }

        &:active {
          transform: translateY(0);
        }

        .el-icon {
          margin-right: 6px;
        }
      }

      // 重置按钮
      :deep(.el-button:not(.el-button--primary)) {
        border-radius: $radius-lg;
        font-weight: $font-weight-medium;
        padding: 10px 20px;
        border: 1px solid $border-secondary;
        background-color: $white;
        color: $text-regular;
        transition: all $transition-normal;

        &:hover {
          border-color: $primary-light;
          color: $primary-color;
          background-color: $bg-primary;
        }

        &:active {
          background-color: $white;
        }

        .el-icon {
          margin-right: 6px;
        }
      }
    }
  }
}

// 响应式布局
@media screen and (max-width: $breakpoint-md) {
  .search-form-card {
    :deep(.el-card__body) {
      padding: $spacing-4 $spacing-4 $spacing-1;
    }

    .search-form {
      .el-form-item {
        width: calc(50% - #{$spacing-2});

        :deep(.el-form-item__content) {
          width: 100%;

          .el-input,
          .el-select,
          .el-date-editor,
          .el-input-number {
            width: 100% !important;
          }
        }
      }

      .search-actions {
        margin-left: 0;
        width: 100%;
        order: 1;

        :deep(.el-form-item__content) {
          justify-content: flex-start;
          flex-wrap: wrap;
        }
      }
    }
  }
}

@media screen and (max-width: $breakpoint-sm) {
  .search-form-card {
    margin-bottom: $spacing-4;
    border-radius: $radius-lg;

    :deep(.el-card__body) {
      padding: $spacing-3 $spacing-3 0;
    }

    .search-form {
      gap: 0;

      .el-form-item {
        width: 100%;
        margin-right: 0;
        margin-bottom: $spacing-3;

        :deep(.el-form-item__label) {
          font-size: $font-size-xs;
          padding-bottom: $spacing-1;
        }

        :deep(.el-form-item__content) {
          width: 100%;

          .el-input,
          .el-select,
          .el-date-editor,
          .el-input-number {
            width: 100% !important;
          }
        }
      }

      .search-actions {
        margin-left: 0;
        margin-bottom: $spacing-3;
        width: 100%;

        :deep(.el-form-item__content) {
          justify-content: space-between;

          .el-button {
            flex: 1;
            padding: 10px 16px;
          }
        }
      }
    }
  }
}
</style>
