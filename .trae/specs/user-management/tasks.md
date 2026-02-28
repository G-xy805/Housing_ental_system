# Tasks

- [ ] Task 1: 扩展用户数据模型
  - [ ] SubTask 1.1: 设计角色表结构（Role 模型）
  - [ ] SubTask 1.2: 设计操作日志表结构（OperationLog 模型）
  - [ ] SubTask 1.3: 扩展用户表字段（avatar、status、login_attempts 等）
  - [ ] SubTask 1.4: 创建数据库迁移脚本

- [ ] Task 2: 实现用户管理后端 API
  - [ ] SubTask 2.1: 实现用户列表查询 API（GET /api/users）
  - [ ] SubTask 2.2: 实现用户详情查询 API（GET /api/users/:id）
  - [ ] SubTask 2.3: 实现用户信息更新 API（PUT /api/users/:id）
  - [ ] SubTask 2.4: 实现用户状态更新 API（PATCH /api/users/:id/status）
  - [ ] SubTask 2.5: 实现用户删除 API（DELETE /api/users/:id）
  - [ ] SubTask 2.6: 实现批量操作 API（POST /api/users/batch-action）
  - [ ] SubTask 2.7: 实现用户导入 API（POST /api/users/import）
  - [ ] SubTask 2.8: 实现用户导出 API（GET /api/users/export）

- [ ] Task 3: 实现角色管理后端 API
  - [ ] SubTask 3.1: 实现角色列表查询 API（GET /api/roles）
  - [ ] SubTask 3.2: 实现角色创建 API（POST /api/roles）
  - [ ] SubTask 3.3: 实现角色更新 API（PUT /api/roles/:id）
  - [ ] SubTask 3.4: 实现角色删除 API（DELETE /api/roles/:id）
  - [ ] SubTask 3.5: 实现角色权限配置 API（PUT /api/roles/:id/permissions）

- [ ] Task 4: 实现操作日志后端 API
  - [ ] SubTask 4.1: 实现日志查询 API（GET /api/logs）
  - [ ] SubTask 4.2: 实现日志导出 API（GET /api/logs/export）
  - [ ] SubTask 4.3: 添加操作日志记录中间件

- [ ] Task 5: 实现权限控制中间件
  - [ ] SubTask 5.1: 实现 RBAC 权限验证逻辑
  - [ ] SubTask 5.2: 实现菜单权限过滤
  - [ ] SubTask 5.3: 实现数据权限过滤
  - [ ] SubTask 5.4: 实现账号锁定机制

- [ ] Task 6: 实现用户管理前端页面
  - [ ] SubTask 6.1: 创建用户列表页面
  - [ ] SubTask 6.2: 实现用户搜索和筛选功能
  - [ ] SubTask 6.3: 创建用户详情和编辑页面
  - [ ] SubTask 6.4: 实现批量操作功能
  - [ ] SubTask 6.5: 实现用户导入导出功能

- [ ] Task 7: 实现角色管理前端页面
  - [ ] SubTask 7.1: 创建角色列表页面
  - [ ] SubTask 7.2: 创建角色编辑页面（权限配置）
  - [ ] SubTask 7.3: 实现角色分配功能

- [ ] Task 8: 实现操作日志前端页面
  - [ ] SubTask 8.1: 创建日志列表页面
  - [ ] SubTask 8.2: 实现日志搜索和筛选功能
  - [ ] SubTask 8.3: 实现日志导出功能

- [ ] Task 9: 测试和验证
  - [ ] SubTask 9.1: 测试用户 CRUD 操作
  - [ ] SubTask 9.2: 测试角色和权限管理
  - [ ] SubTask 9.3: 测试批量操作功能
  - [ ] SubTask 9.4: 测试操作日志记录
  - [ ] SubTask 9.5: 修复发现的问题

# Task Dependencies
- [Task 2] depends on [Task 1]
- [Task 3] depends on [Task 1]
- [Task 4] depends on [Task 1]
- [Task 5] depends on [Task 1]
- [Task 6] depends on [Task 2], [Task 5]
- [Task 7] depends on [Task 3], [Task 5]
- [Task 8] depends on [Task 4]
- [Task 9] depends on [Task 6], [Task 7], [Task 8]
