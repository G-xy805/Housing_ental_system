# Tasks

- [ ] Task 1: 扩展租客数据模型
  - [ ] SubTask 1.1: 添加租客状态字段枚举定义
  - [ ] SubTask 1.2: 添加租客统计计算字段
  - [ ] SubTask 1.3: 优化租客查询索引

- [ ] Task 2: 实现租客管理后端 API
  - [ ] SubTask 2.1: 实现租客列表查询 API（GET /api/tenants）
  - [ ] SubTask 2.2: 实现租客详情查询 API（GET /api/tenants/:id）
  - [ ] SubTask 2.3: 实现租客信息更新 API（PUT /api/tenants/:id）
  - [ ] SubTask 2.4: 实现租客搜索 API（GET /api/tenants/search）
  - [ ] SubTask 2.5: 实现租客统计 API（GET /api/tenants/statistics）
  - [ ] SubTask 2.6: 实现租客历史记录 API（GET /api/tenants/:id/history）

- [ ] Task 3: 实现左侧菜单扩展
  - [ ] SubTask 3.1: 添加租客管理菜单项
  - [ ] SubTask 3.2: 配置菜单路由
  - [ ] SubTask 3.3: 添加菜单权限控制
  - [ ] SubTask 3.4: 测试菜单导航

- [ ] Task 4: 实现租客列表前端页面
  - [ ] SubTask 4.1: 创建租客列表页面布局
  - [ ] SubTask 4.2: 实现租客表格展示
  - [ ] SubTask 4.3: 实现分页功能
  - [ ] SubTask 4.4: 实现排序功能
  - [ ] SubTask 4.5: 实现状态筛选功能

- [ ] Task 5: 实现租客搜索功能
  - [ ] SubTask 5.1: 创建搜索表单组件
  - [ ] SubTask 5.2: 实现姓名模糊搜索
  - [ ] SubTask 5.3: 实现组合条件搜索
  - [ ] SubTask 5.4: 实现搜索历史记录

- [ ] Task 6: 实现租客详情页面
  - [ ] SubTask 6.1: 创建租客详情页面布局
  - [ ] SubTask 6.2: 展示基本信息卡片
  - [ ] SubTask 6.3: 展示紧急联系人信息
  - [ ] SubTask 6.4: 展示当前入住房源
  - [ ] SubTask 6.5: 展示历史合同列表
  - [ ] SubTask 6.6: 展示支付记录汇总

- [ ] Task 7: 实现租客编辑功能
  - [ ] SubTask 7.1: 创建租客编辑表单
  - [ ] SubTask 7.2: 实现表单验证
  - [ ] SubTask 7.3: 实现保存功能
  - [ ] SubTask 7.4: 实现备注管理功能

- [ ] Task 8: 实现租客统计功能
  - [ ] SubTask 8.1: 创建统计卡片组件
  - [ ] SubTask 8.2: 实现租客数量统计
  - [ ] SubTask 8.3: 实现租客状态分布图表
  - [ ] SubTask 8.4: 实现趋势图表

- [ ] Task 9: 测试和验证
  - [ ] SubTask 9.1: 测试租客列表显示
  - [ ] SubTask 9.2: 测试搜索和筛选功能
  - [ ] SubTask 9.3: 测试详情页数据准确性
  - [ ] SubTask 9.4: 测试编辑功能
  - [ ] SubTask 9.5: 修复发现的问题

# Task Dependencies
- [Task 2] depends on [Task 1]
- [Task 3] independent
- [Task 4] depends on [Task 2], [Task 3]
- [Task 5] depends on [Task 2]
- [Task 6] depends on [Task 2]
- [Task 7] depends on [Task 2]
- [Task 8] depends on [Task 2]
- [Task 9] depends on [Task 4], [Task 5], [Task 6], [Task 7], [Task 8]
