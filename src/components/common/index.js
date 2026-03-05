/**
 * 公共组件库统一导出
 * 提供可复用的基础组件
 */

import Pagination from './Pagination.vue'
import SearchForm from './SearchForm.vue'
import StatusTag from './StatusTag.vue'
import ConfirmDialog from './ConfirmDialog.vue'

// 组件列表
const components = {
  Pagination,
  SearchForm,
  StatusTag,
  ConfirmDialog
}

// 插件安装方法
const install = (app) => {
  Object.keys(components).forEach((key) => {
    app.component(key, components[key])
  })
}

// 默认导出
export default {
  install,
  ...components
}

// 按需导出
export {
  Pagination,
  SearchForm,
  StatusTag,
  ConfirmDialog
}
