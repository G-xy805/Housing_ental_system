# 用户个人中心和设置功能 Spec

## Why
为房屋租赁系统用户提供个人中心功能，允许用户查看和修改个人信息、修改密码、配置个人偏好设置，提升用户体验和系统安全性。

## What Changes
- 新增个人中心页面
- 实现个人信息查看和编辑
- 添加头像上传功能
- 实现密码修改功能
- 添加个人偏好设置
- 实现登录日志查看
- 添加消息通知设置

## Impact
- 受影响的功能：用户认证、个人设置、安全验证
- 受影响的代码：后端用户 API、前端个人中心页面、文件上传模块

## ADDED Requirements

### Requirement: 个人中心页面
系统 SHALL 提供个人中心入口和页面
- 顶部导航栏显示用户头像和姓名
- 点击头像进入个人中心
- 个人中心包含多个标签页
- 响应式设计，支持移动端

#### Scenario: 访问个人中心
- **WHEN** 用户点击顶部导航栏头像
- **THEN** 系统展示个人中心页面

### Requirement: 个人信息管理
系统 SHALL 提供个人信息查看和编辑功能
- 显示用户基本信息（用户名、姓名、手机号、邮箱）
- 可编辑信息：姓名、手机号、邮箱
- 不可修改：用户名
- 实时保存修改
- 修改敏感信息需验证身份

#### Scenario: 查看个人信息
- **WHEN** 用户访问个人中心
- **THEN** 系统展示用户完整信息

#### Scenario: 修改个人信息
- **WHEN** 用户修改手机号或邮箱
- **THEN** 系统验证唯一性并发送验证码

### Requirement: 头像管理
系统 SHALL 提供头像上传和裁剪功能
- 支持 JPG、PNG 格式
- 文件大小限制（最大 5MB）
- 图片裁剪和预览
- 自动生成缩略图
- 支持恢复默认头像

#### Scenario: 上传头像
- **WHEN** 用户上传头像图片
- **THEN** 系统裁剪并保存，立即更新显示

#### Scenario: 删除头像
- **WHEN** 用户删除头像
- **THEN** 系统恢复默认头像

### Requirement: 密码修改
系统 SHALL 提供安全的密码修改功能
- 验证当前密码
- 新密码强度校验（长度、复杂度）
- 两次输入一致性验证
- 修改成功后强制重新登录
- 记录密码修改历史

#### Scenario: 修改密码
- **WHEN** 用户输入当前密码和新密码
- **THEN** 系统验证并更新密码

#### Scenario: 密码强度校验
- **WHEN** 新密码过于简单
- **THEN** 系统拒绝并提示密码要求

### Requirement: 个人偏好设置
系统 SHALL 提供个人偏好配置功能
- 主题切换（明亮/黑暗模式）
- 语言选择（中文/英文）
- 日期格式设置
- 分页大小设置
- 自动保存偏好设置

#### Scenario: 切换主题
- **WHEN** 用户切换深色模式
- **THEN** 系统立即应用新主题并保存偏好

#### Scenario: 设置分页大小
- **WHEN** 用户修改默认分页大小
- **THEN** 系统保存设置并在列表页生效

### Requirement: 登录日志查看
系统 SHALL 提供用户登录日志查询功能
- 显示最近登录记录（时间、IP、设备）
- 登录地点显示
- 异常登录提醒
- 支持登出其他设备

#### Scenario: 查看登录日志
- **WHEN** 用户查看登录历史
- **THEN** 系统展示最近 30 天的登录记录

#### Scenario: 登出其他设备
- **WHEN** 用户选择登出其他设备
- **THEN** 系统使其他设备的 Token 失效

### Requirement: 消息通知设置
系统 SHALL 提供消息通知配置功能
- 合同到期提醒开关
- 租金逾期提醒开关
- 系统通知开关
- 通知方式选择（站内信、邮件、短信）
- 免打扰时段设置

#### Scenario: 配置通知
- **WHEN** 用户开启合同到期提醒
- **THEN** 系统在合同到期前发送提醒

### Requirement: 账号安全设置
系统 SHALL 提供账号安全管理功能
- 绑定手机号
- 绑定邮箱
- 登录保护（二次验证）
- 账号注销申请

#### Scenario: 绑定手机号
- **WHEN** 用户绑定手机号
- **THEN** 系统发送验证码并验证绑定

#### Scenario: 启用登录保护
- **WHEN** 用户启用二次验证
- **THEN** 系统要求登录时输入验证码

## 数据模型要求

### 用户偏好设置表
- preference_id: 偏好 ID（主键）
- user_id: 用户 ID（外键）
- theme: 主题（light/dark）
- language: 语言（zh/en）
- date_format: 日期格式
- page_size: 分页大小
- notification_settings: 通知设置（JSON）
- created_at: 创建时间
- updated_at: 更新时间

### 登录日志表
- log_id: 日志 ID（主键）
- user_id: 用户 ID
- login_time: 登录时间
- ip_address: IP 地址
- location: 登录地点
- device: 设备信息
- browser: 浏览器信息
- status: 登录状态（成功/失败）

### 密码修改历史表
- history_id: 历史 ID（主键）
- user_id: 用户 ID
- old_password_hash: 旧密码哈希
- changed_at: 修改时间
- changed_by: 修改人

## 技术栈要求

### 后端实现
- **框架**：Flask
- **文件上传**：Flask-Uploads
- **图片处理**：Pillow
- **密码加密**：bcrypt
- **IP 地理位置**：IP2Region

### 前端实现
- **框架**：Vue.js 或 React
- **UI 组件**：Element UI 或 Ant Design
- **图片裁剪**：Cropper.js
- **状态管理**：Vuex 或 Redux
- **主题切换**：CSS Variables
