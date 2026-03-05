/**
 * Vitest 测试环境全局配置
 * 配置 Element Plus、Pinia、Vue Router 等的测试模拟
 */

import { config } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { vi } from 'vitest'

// ============================================
// Element Plus 组件模拟
// ============================================

// 模拟 Element Plus 的全局组件
// 这样在测试时不需要真正渲染 Element Plus 组件
const elementPlusComponents = [
  'ElButton',
  'ElInput',
  'ElInputNumber',
  'ElSelect',
  'ElOption',
  'ElTable',
  'ElTableColumn',
  'ElForm',
  'ElFormItem',
  'ElDialog',
  'ElMessage',
  'ElMessageBox',
  'ElPagination',
  'ElTag',
  'ElDatePicker',
  'ElSwitch',
  'ElRadio',
  'ElRadioGroup',
  'ElCheckbox',
  'ElCheckboxGroup',
  'ElUpload',
  'ElIcon',
  'ElLoading',
  'ElCard',
  'ElRow',
  'ElCol',
  'ElTabs',
  'ElTabPane',
  'ElBreadcrumb',
  'ElBreadcrumbItem',
  'ElMenu',
  'ElMenuItem',
  'ElSubMenu',
  'ElDropdown',
  'ElDropdownMenu',
  'ElDropdownItem',
  'ElBadge',
  'ElAvatar',
  'ElTooltip',
  'ElPopover',
  'ElDrawer',
  'ElProgress',
  'ElStatistic',
  'ElEmpty',
  'ElDivider',
  'ElAlert',
  'ElNotification',
  'ElDescriptions',
  'ElDescriptionsItem',
  'ElLink',
  'Close',
  'Check'
]

// 注册 Element Plus 组件模拟
elementPlusComponents.forEach(componentName => {
  config.global.components[componentName] = {
    name: componentName,
    template: `<div class="mock-${componentName.toLowerCase()}"><slot /></div>`
  }
})

// 特殊处理 ElTable 组件 - 需要传递数据给 slot
config.global.components.ElTable = {
  name: 'ElTable',
  props: ['data'],
  template: `
    <div class="mock-eltable">
      <slot />
    </div>
  `
}

// 特殊处理 ElTableColumn 组件
config.global.components.ElTableColumn = {
  name: 'ElTableColumn',
  props: ['prop', 'label', 'width', 'align'],
  template: `
    <div class="mock-el-table-column">
      <slot name="default" :row="{ id_card: '110101199001011234', status: 'active', created_at: '2024-01-01T00:00:00' }" :$index="0" />
    </div>
  `
}

// 特殊处理 ElInputNumber 组件
config.global.components.ElInputNumber = {
  name: 'ElInputNumber',
  props: ['modelValue', 'min', 'max', 'precision', 'step', 'disabled'],
  emits: ['update:modelValue'],
  template: `
    <input 
      class="mock-el-input-number" 
      type="number" 
      :value="modelValue" 
      :disabled="disabled"
      @input="$emit('update:modelValue', Number($event.target.value))"
    />
  `
}

// 特殊处理 ElDatePicker 组件
config.global.components.ElDatePicker = {
  name: 'ElDatePicker',
  props: ['modelValue', 'type', 'placeholder', 'disabled', 'valueFormat'],
  emits: ['update:modelValue'],
  template: `
    <input 
      class="mock-el-date-picker" 
      :value="modelValue" 
      :placeholder="placeholder"
      :disabled="disabled"
      @input="$emit('update:modelValue', $event.target.value)"
    />
  `
}

// 特殊处理 ElSelect 组件
config.global.components.ElSelect = {
  name: 'ElSelect',
  props: ['modelValue', 'placeholder', 'disabled', 'clearable', 'filterable'],
  emits: ['update:modelValue', 'change'],
  template: `
    <select 
      class="mock-el-select" 
      :value="modelValue" 
      :disabled="disabled"
      @change="$emit('update:modelValue', $event.target.value); $emit('change', $event.target.value)"
    >
      <slot />
    </select>
  `
}

// 特殊处理 ElInput 组件
config.global.components.ElInput = {
  name: 'ElInput',
  props: ['modelValue', 'placeholder', 'disabled', 'type', 'clearable'],
  emits: ['update:modelValue', 'input', 'change'],
  template: `
    <input 
      v-if="type !== 'textarea'"
      class="mock-elinput" 
      :value="modelValue" 
      :placeholder="placeholder"
      :disabled="disabled"
      @input="$emit('update:modelValue', $event.target.value); $emit('input', $event.target.value)"
      @change="$emit('change', $event.target.value)"
    />
    <textarea 
      v-else
      class="mock-elinput mock-el-textarea" 
      :value="modelValue" 
      :placeholder="placeholder"
      :disabled="disabled"
      @input="$emit('update:modelValue', $event.target.value); $emit('input', $event.target.value)"
      @change="$emit('change', $event.target.value)"
    ></textarea>
  `
}

// 特殊处理 ElPagination 组件
config.global.components.ElPagination = {
  name: 'ElPagination',
  props: [
    'currentPage', 'pageSize', 'total', 'pageSizes', 'layout',
    'background', 'small', 'disabled', 'hideOnSinglePage'
  ],
  emits: ['size-change', 'current-change'],
  template: `
    <div class="mock-el-pagination">
      <div class="el-pagination">
        <span class="el-pagination__total" v-if="layout.includes('total')">
          共 {{ total }} 条
        </span>
        <div class="el-pagination__sizes" v-if="layout.includes('sizes')">
          <select @change="$emit('size-change', Number($event.target.value))">
            <option v-for="size in pageSizes" :key="size" :value="size">
              {{ size }} 条/页
            </option>
          </select>
        </div>
        <div class="el-pagination__pager" v-if="layout.includes('pager')">
          页码: {{ currentPage }}
        </div>
      </div>
    </div>
  `
}

// 特殊处理 ElTag 组件
config.global.components.ElTag = {
  name: 'ElTag',
  props: ['type', 'size', 'effect'],
  template: `
    <span class="mock-el-tag el-tag" :class="[
      type ? 'el-tag--' + type : '',
      size ? 'el-tag--' + size : '',
      effect ? 'el-tag--' + effect : ''
    ]">
      <slot />
    </span>
  `
}

// 特殊处理 ElButton 组件
config.global.components.ElButton = {
  name: 'ElButton',
  props: {
    type: String,
    loading: Boolean,
    disabled: {
      type: Boolean,
      default: false
    }
  },
  emits: ['click'],
  template: `
    <button 
      class="mock-elbutton el-button" 
      :class="[
        type ? 'el-button--' + type : '',
        { 'is-loading': loading },
        { 'is-disabled': disabled }
      ]"
      :disabled="disabled"
      @click="$emit('click')"
    >
      <slot />
    </button>
  `
}

// 特殊处理 ElDialog 组件
config.global.components.ElDialog = {
  name: 'ElDialog',
  props: [
    'modelValue', 'title', 'width', 'closeOnClickModal',
    'closeOnPressEscape', 'showClose', 'center', 'customClass'
  ],
  emits: ['update:modelValue', 'close'],
  template: `
    <div class="mock-el-dialog el-dialog" v-if="modelValue">
      <div class="el-dialog__header">
        <span class="el-dialog__title">{{ title }}</span>
        <button v-if="showClose" class="el-dialog__headerbtn" @click="$emit('update:modelValue', false); $emit('close')">
          ×
        </button>
      </div>
      <div class="el-dialog__body">
        <slot />
      </div>
      <div class="el-dialog__footer">
        <slot name="footer" />
      </div>
    </div>
  `
}

// 特殊处理 ElForm 组件
config.global.components.ElForm = {
  name: 'ElForm',
  props: ['model', 'inline'],
  emits: ['submit'],
  methods: {
    validate: vi.fn(() => Promise.resolve(true)),
    validateField: vi.fn(() => Promise.resolve()),
    resetFields: vi.fn(),
    clearValidate: vi.fn()
  },
  template: `
    <form class="mock-el-form el-form" :class="{ 'el-form--inline': inline }" @submit.prevent="$emit('submit')">
      <slot />
    </form>
  `
}

// 特殊处理 ElFormItem 组件
config.global.components.ElFormItem = {
  name: 'ElFormItem',
  props: ['label'],
  template: `
    <div class="mock-el-form-item el-form-item">
      <label v-if="label" class="el-form-item__label">{{ label }}</label>
      <div class="el-form-item__content">
        <slot />
      </div>
    </div>
  `
}

// 特殊处理 ElCard 组件
config.global.components.ElCard = {
  name: 'ElCard',
  props: ['shadow'],
  template: `
    <div class="mock-el-card el-card" :class="{ 'is-shadowless': shadow === 'never' }">
      <div class="el-card__body">
        <slot />
      </div>
    </div>
  `
}

// 特殊处理 ElOption 组件
config.global.components.ElOption = {
  name: 'ElOption',
  props: ['label', 'value'],
  template: `
    <option :value="value">{{ label }}</option>
  `
}

// ============================================
// Element Plus 服务模拟
// ============================================

// 模拟 ElMessage
const mockMessage = {
  success: vi.fn(),
  warning: vi.fn(),
  info: vi.fn(),
  error: vi.fn(),
  close: vi.fn(),
  closeAll: vi.fn()
}

// 模拟 ElMessageBox
const mockMessageBox = {
  confirm: vi.fn(() => Promise.resolve('confirm')),
  alert: vi.fn(() => Promise.resolve('confirm')),
  prompt: vi.fn(() => Promise.resolve({ value: 'test', action: 'confirm' })),
  close: vi.fn()
}

// 模拟 ElNotification
const mockNotification = {
  success: vi.fn(),
  warning: vi.fn(),
  info: vi.fn(),
  error: vi.fn(),
  close: vi.fn(),
  closeAll: vi.fn()
}

// 模拟 ElLoading
const mockLoading = {
  service: vi.fn(() => ({
    close: vi.fn()
  })),
  directive: vi.fn()
}

// 全局挂载 Element Plus 服务模拟
config.global.mocks = {
  $message: mockMessage,
  $messageBox: mockMessageBox,
  $notify: mockNotification,
  $loading: mockLoading
}

// ============================================
// Pinia 状态管理模拟
// ============================================

// 在每个测试前重置 Pinia 实例
beforeEach(() => {
  setActivePinia(createPinia())
})

// ============================================
// Vue Router 模拟
// ============================================

// 创建模拟的 router 对象
const mockRouter = {
  push: vi.fn(),
  replace: vi.fn(),
  go: vi.fn(),
  back: vi.fn(),
  forward: vi.fn(),
  currentRoute: {
    value: {
      path: '/',
      params: {},
      query: {},
      meta: {},
      name: 'home'
    }
  },
  beforeEach: vi.fn(),
  afterEach: vi.fn(),
  beforeResolve: vi.fn()
}

// 创建模拟的 route 对象
const mockRoute = {
  path: '/',
  params: {},
  query: {},
  meta: {},
  name: 'home',
  fullPath: '/',
  hash: '',
  matched: [],
  redirectedFrom: null
}

// 全局挂载 Router 模拟
config.global.mocks.$router = mockRouter
config.global.mocks.$route = mockRoute

// ============================================
// Axios 模拟
// ============================================

// 创建模拟的 axios 实例
const mockAxios = {
  get: vi.fn(() => Promise.resolve({ data: {} })),
  post: vi.fn(() => Promise.resolve({ data: {} })),
  put: vi.fn(() => Promise.resolve({ data: {} })),
  delete: vi.fn(() => Promise.resolve({ data: {} })),
  patch: vi.fn(() => Promise.resolve({ data: {} })),
  create: vi.fn(() => mockAxios),
  interceptors: {
    request: {
      use: vi.fn(),
      eject: vi.fn()
    },
    response: {
      use: vi.fn(),
      eject: vi.fn()
    }
  }
}

config.global.mocks.$axios = mockAxios

// ============================================
// 全局配置
// ============================================

// 配置全局 stubs（存根）
config.global.stubs = {
  // 可以在这里添加需要存根的组件
  RouterLink: true,
  RouterView: true
}

// 配置全局 directives
config.global.directives = {
  // 模拟常用的指令
  loading: {
    mounted: vi.fn(),
    updated: vi.fn(),
    unmounted: vi.fn()
  }
}

// ============================================
// 测试工具函数
// ============================================

/**
 * 创建模拟的 Pinia Store
 * @param {Function} useStore - Store 定义函数
 * @param {Object} initialState - 初始状态
 * @returns {Object} Store 实例
 */
export function createMockStore(useStore, initialState = {}) {
  const pinia = createPinia()
  setActivePinia(pinia)
  const store = useStore(pinia)
  
  // 如果有初始状态，设置状态
  if (Object.keys(initialState).length > 0) {
    Object.keys(initialState).forEach(key => {
      if (store.$patch) {
        store.$patch(initialState)
      }
    })
  }
  
  return store
}

/**
 * 创建组件挂载选项
 * @param {Object} options - 自定义选项
 * @returns {Object} 挂载选项
 */
export function createMountOptions(options = {}) {
  const pinia = createPinia()
  setActivePinia(pinia)
  
  return {
    global: {
      plugins: [pinia],
      mocks: {
        $router: mockRouter,
        $route: { ...mockRoute, ...options.route },
        $message: mockMessage,
        $messageBox: mockMessageBox,
        $notify: mockNotification,
        $axios: mockAxios,
        ...options.mocks
      },
      stubs: {
        RouterLink: true,
        RouterView: true,
        ...options.stubs
      },
      components: {
        ...config.global.components,
        ...options.components
      },
      ...options.global
    },
    ...options
  }
}

/**
 * 重置所有模拟
 */
export function resetAllMocks() {
  vi.clearAllMocks()
  mockMessage.success.mockClear()
  mockMessage.warning.mockClear()
  mockMessage.info.mockClear()
  mockMessage.error.mockClear()
  mockMessageBox.confirm.mockClear()
  mockMessageBox.alert.mockClear()
  mockRouter.push.mockClear()
  mockRouter.replace.mockClear()
}

/**
 * 等待下一个 tick
 * @param {number} timeout - 超时时间（毫秒）
 */
export async function flushPromises(timeout = 0) {
  return new Promise(resolve => setTimeout(resolve, timeout))
}

// ============================================
// 导出模拟对象供测试使用
// ============================================

export {
  mockMessage,
  mockMessageBox,
  mockNotification,
  mockLoading,
  mockRouter,
  mockRoute,
  mockAxios
}
