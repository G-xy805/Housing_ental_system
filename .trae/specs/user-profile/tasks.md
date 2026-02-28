# Tasks

- [ ] Task 1: 扩展用户数据模型
  - [ ] SubTask 1.1: 创建用户偏好设置表（UserPreference 模型）
  - [ ] SubTask 1.2: 创建登录日志表（LoginLog 模型）
  - [ ] SubTask 1.3: 创建密码历史表（PasswordHistory 模型）
  - [ ] SubTask 1.4: 创建数据库迁移脚本

- [ ] Task 2: 实现个人中心后端 API
  - [ ] SubTask 2.1: 实现获取个人信息 API（GET /api/user/profile）
  - [ ] SubTask 2.2: 实现更新个人信息 API（PUT /api/user/profile）
  - [ ] SubTask 2.3: 实现上传头像 API（POST /api/user/avatar）
  - [ ] SubTask 2.4: 实现删除头像 API（DELETE /api/user/avatar）
  - [ ] SubTask 2.5: 实现修改密码 API（POST /api/user/change-password）
  - [ ] SubTask 2.6: 实现获取偏好设置 API（GET /api/user/preferences）
  - [ ] SubTask 2.7: 实现更新偏好设置 API（PUT /api/user/preferences）

- [ ] Task 3: 实现安全相关 API
  - [ ] SubTask 3.1: 实现获取登录日志 API（GET /api/user/login-logs）
  - [ ] SubTask 3.2: 实现登出其他设备 API（POST /api/user/logout-other-devices）
  - [ ] SubTask 3.3: 实现获取通知设置 API（GET /api/user/notification-settings）
  - [ ] SubTask 3.4: 实现更新通知设置 API（PUT /api/user/notification-settings）
  - [ ] SubTask 3.5: 实现绑定手机号 API（POST /api/user/bind-phone）
  - [ ] SubTask 3.6: 实现绑定邮箱 API（POST /api/user/bind-email）

- [ ] Task 4: 实现文件上传功能
  - [ ] SubTask 4.1: 配置文件上传模块
  - [ ] SubTask 4.2: 实现图片压缩和裁剪
  - [ ] SubTask 4.3: 实现缩略图生成
  - [ ] SubTask 4.4: 实现文件存储管理

- [ ] Task 5: 实现个人中心前端页面
  - [ ] SubTask 5.1: 创建个人中心页面布局
  - [ ] SubTask 5.2: 实现个人信息展示和编辑
  - [ ] SubTask 5.3: 实现头像上传组件
  - [ ] SubTask 5.4: 实现密码修改表单
  - [ ] SubTask 5.5: 实现偏好设置页面
  - [ ] SubTask 5.6: 实现登录日志展示
  - [ ] SubTask 5.7: 实现通知设置页面

- [ ] Task 6: 实现主题切换功能
  - [ ] SubTask 6.1: 定义 CSS 变量主题配置
  - [ ] SubTask 6.2: 实现明亮/黑暗主题样式
  - [ ] SubTask 6.3: 实现主题切换逻辑
  - [ ] SubTask 6.4: 持久化主题设置

- [ ] Task 7: 实现安全验证功能
  - [ ] SubTask 7.1: 实现短信验证码发送
  - [ ] SubTask 7.2: 实现邮件验证码发送
  - [ ] SubTask 7.3: 实现验证码验证逻辑
  - [ ] SubTask 7.4: 实现二次验证功能

- [ ] Task 8: 测试和验证
  - [ ] SubTask 8.1: 测试个人信息修改
  - [ ] SubTask 8.2: 测试头像上传功能
  - [ ] SubTask 8.3: 测试密码修改功能
  - [ ] SubTask 8.4: 测试偏好设置
  - [ ] SubTask 8.5: 测试主题切换
  - [ ] SubTask 8.6: 测试登录日志
  - [ ] SubTask 8.7: 修复发现的问题

# Task Dependencies
- [Task 2] depends on [Task 1]
- [Task 3] depends on [Task 1]
- [Task 4] independent
- [Task 5] depends on [Task 2], [Task 3], [Task 4]
- [Task 6] depends on [Task 5]
- [Task 7] depends on [Task 3]
- [Task 8] depends on [Task 5], [Task 6], [Task 7]
