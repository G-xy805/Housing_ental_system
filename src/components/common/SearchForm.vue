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
.search-form-card {
  margin-bottom: 20px;
  
  :deep(.el-card__body) {
    padding: 16px 20px 0;
  }
  
  .search-form {
    display: flex;
    flex-wrap: wrap;
    
    .el-form-item {
      margin-bottom: 16px;
      margin-right: 16px;
    }
    
    .search-actions {
      margin-left: auto;
    }
  }
}

@media screen and (max-width: 768px) {
  .search-form-card {
    .search-form {
      .el-form-item {
        width: 100%;
        margin-right: 0;
        
        :deep(.el-form-item__content) {
          width: 100%;
          
          .el-input,
          .el-select,
          .el-date-picker,
          .el-input-number {
            width: 100% !important;
          }
        }
      }
      
      .search-actions {
        margin-left: 0;
        width: 100%;
        
        :deep(.el-form-item__content) {
          justify-content: flex-start;
        }
      }
    }
  }
}
</style>
