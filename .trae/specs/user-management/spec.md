# 用户管理功能 Spec

## Why
完善房屋租赁系统的用户管理体系，提供统一的用户信息管理、权限配置、角色管理等功能，支持系统安全管理和多用户协作。

## What Changes
- 新增用户管理主页面
- 实现用户信息 CRUD 功能
- 添加用户角色和权限管理
- 实现用户状态控制（启用/禁用）
- 添加用户操作日志记录
- 实现批量用户管理功能

## Impact
- 受影响的功能：用户认证、权限控制、系统管理
- 受影响的代码：后端用户 API、前端管理页面、数据库用户表、权限中间件

## ADDED Requirements

### Requirement: 用户信息管理
系统 SHALL 提供完整的用户信息管理功能
- 查看所有用户列表（管理员、员工）
- 用户详细信息查看
- 用户信息编辑（基本信息、联系方式）
- 用户头像上传和管理
- 用户密码修改和重置

#### Scenario: 查看用户列表
- **WHEN** 管理员访问用户管理页面
- **THEN** 系统展示所有用户信息，包含分页

#### Scenario: 编辑用户信息
- **WHEN** 管理员修改用户信息并保存
- **THEN** 系统更新用户信息并记录修改时间

### Requirement: 用户角色管理
系统 SHALL 提供用户角色分配和管理功能
- 预定义角色：管理员、高级员工、普通员工
- 自定义角色创建和编辑
- 角色权限配置
- 用户角色分配和切换

#### Scenario: 分配用户角色
- **WHEN** 管理员为用户分配角色
- **THEN** 系统更新用户角色并立即生效

#### Scenario: 创建自定义角色
- **WHEN** 管理员创建新角色并配置权限
- **THEN** 系统保存角色并可分配给用户

### Requirement: 用户权限管理
系统 SHALL 提供细粒度权限管理
- 菜单权限控制
- 操作权限控制（增删改查）
- 数据权限控制（可见范围）
- 权限继承和组合

#### Scenario: 权限验证
- **WHEN** 用户访问无权限的资源
- **THEN** 系统拒绝访问并返回 403 错误

#### Scenario: 数据权限控制
- **WHEN** 普通员工查看房源列表
- **THEN** 只能查看自己创建的房源（可配置）

### Requirement: 用户状态管理
系统 SHALL 提供用户账号状态管理
- 启用/禁用用户账号
- 用户账号锁定（多次登录失败）
- 用户注销管理
- 状态变更历史记录

#### Scenario: 禁用用户账号
- **WHEN** 管理员禁用违规用户
- **THEN** 用户立即无法登录，Token 失效

#### Scenario: 自动锁定账号
- **WHEN** 用户连续登录失败 5 次
- **THEN** 系统自动锁定账号 30 分钟

### Requirement: 用户操作日志
系统 SHALL 记录用户关键操作日志
- 登录/登出记录
- 数据修改操作
- 权限变更操作
- 日志查询和导出

#### Scenario: 查看操作日志
- **WHEN** 管理员查询用户操作日志
- **THEN** 系统展示详细的操作记录

### Requirement: 批量用户管理
系统 SHALL 提供批量操作功能
- 批量启用/禁用用户
- 批量分配角色
- 批量导入用户（Excel）
- 批量导出用户数据

#### Scenario: 批量导入用户
- **WHEN** 管理员上传用户 Excel 文件
- **THEN** 系统解析并批量创建用户账号

#### Scenario: 批量导出用户
- **WHEN** 管理员选择多个用户并导出
- **THEN** 系统生成包含选中用户的 Excel 文件

## 数据模型要求

### 用户表扩展字段
- user_id: 用户 ID（主键）
- username: 用户名（唯一）
- password: 密码（加密存储）
- email: 邮箱
- phone: 手机号
- avatar: 头像 URL
- role_id: 角色 ID（外键）
- status: 状态（active、disabled、locked）
- last_login: 最后登录时间
- login_attempts: 登录失败次数
- locked_until: 锁定截止时间
- created_by: 创建人
- created_at: 创建时间
- updated_at: 更新时间

### 角色表
- role_id: 角色 ID（主键）
- role_name: 角色名称
- role_code: 角色代码
- description: 角色描述
- permissions: 权限配置（JSON）
- created_at: 创建时间

### 操作日志表
- log_id: 日志 ID（主键）
- user_id: 操作用户 ID
- action: 操作类型
- resource: 操作资源
- result: 操作结果
- ip_address: IP 地址
- user_agent: 浏览器信息
- created_at: 操作时间

## 技术栈要求

### 后端实现
- **框架**：Flask
- **ORM**：SQLAlchemy
- **认证**：JWT Token
- **权限**：RBAC 模型
- **日志**：Python logging

### 前端实现
- **框架**：Vue.js 或 React
- **UI 组件**：Element UI 或 Ant Design
- **状态管理**：Vuex 或 Redux
- **文件上传**：支持头像上传
