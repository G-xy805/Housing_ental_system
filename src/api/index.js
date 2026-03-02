/**
 * API 导出文件
 * 统一导出所有 API 方法，方便使用
 */

// 认证相关
export * from './user'

// 房源管理
export * from './house'

// 租客管理
export * from './tenant'

// 房东管理
export * from './landlord'

// 合同管理
export * from './contract'

// 房东合同管理
export * from './landlordContract'

// 租金管理
export * from './payment'

// 员工管理
export * from './employee'

// 统计分析
export * from './statistics'

// 数据备份
export * from './backup'

// 请求实例
export { default as request } from './request'
