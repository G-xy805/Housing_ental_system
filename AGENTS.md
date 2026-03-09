# AGENTS.md - 房屋租赁系统开发指南

本文档为在此代码库上工作的智能体提供指南和命令。

---

## 1. 构建、代码检查和测试命令

### 后端 (Python/Flask)

#### 运行应用程序
```bash
# 首先激活虚拟环境
.venv\Scripts\activate  # Windows

# 运行 Flask 开发服务器
python -m flask run

# 或直接运行
python app/__init__.py
```

#### 测试
```bash
# 运行所有测试并生成覆盖率报告
pytest

# 运行单个测试文件
pytest tests/test_auth.py

# 运行特定的测试类
pytest tests/test_auth.py::TestLoginAPI

# 运行特定的测试方法
pytest tests/test_auth.py::TestLoginAPI::test_login_success_with_username

# 运行匹配模式的测试
pytest -k "test_login"

# 运行带有特定标记的测试
pytest -m auth
pytest -m unit

# 不带覆盖率运行（更快）
pytest --no-cov

# 带详细输出运行
pytest -v --tb=short

# 生成 HTML 覆盖率报告
pytest --cov-report=html:htmlcov
```

`pytest.ini` 中可用的测试标记：
- `unit` - 单元测试
- `integration` - 集成测试
- `api` - API 接口测试
- `slow` - 慢速测试
- `auth` - 认证相关测试
- `encryption` - 加密相关测试

### 前端 (Vue 3 + Vite)

```bash
# 安装依赖
npm install

# 运行开发服务器（端口 5173）
npm run dev

# 构建生产版本
npm run build

# 预览生产构建
npm run preview

# 代码检查（ESLint 自动修复）
npm run lint

# 运行测试（监听模式）
npm test

# 运行测试一次（CI 模式）
npm run test:run

# 带覆盖率运行测试
npm run test:coverage

# 运行单个测试文件
npx vitest run src/__tests__/example.test.js
```

---

## 2. 代码风格指南

### Python (Flask 后端)

#### 通用规则
- 遵循 PEP 8 编码规范
- 为函数参数和返回值使用类型提示
- 为所有公共函数和类编写文档字符串
- 使用 4 个空格进行缩进（不使用 Tab）

#### 命名约定
- **类**：使用 `PascalCase`（例如 `User`、`LandlordContract`）
- **函数/变量**：使用 `snake_case`（例如 `get_user_by_id`、`house_list`）
- **常量**：使用 `UPPER_SNAKE_CASE`（例如 `MAX_UPLOAD_SIZE`）
- **私有方法**：使用下划线前缀（例如 `_internal_method`）
- **数据库表**：使用 `snake_case`（在 `__tablename__` 中定义）

#### 导入组织
```python
# 标准库
import os
import logging
from datetime import datetime

# 第三方包
import jwt
from flask import Blueprint, request, jsonify

# 本地应用导入
from app.models.user import User
from app.models import db
from app.utils.jwt import generate_token
from app.utils.decorators import login_required

# 本地相对导入
from .config import config
```

#### 类型提示
```python
from typing import Optional, List, Dict, Any

def get_user_by_id(user_id: int) -> Optional[User]:
    """根据 ID 获取用户。
    
    参数:
        user_id: 用户 ID
        
    返回:
        用户对象，如果未找到则返回 None
    """
    return User.query.get(user_id)

def process_data(items: List[Dict[str, Any]]) -> List[str]:
    """处理数据列表。"""
    return [str(item) for item in items]
```

#### 错误处理
- 使用 `app/utils/responses.py` 中的 `APIResponse` 类来保持一致的响应格式
- 始终返回 JSON 格式：`{"success": true/false, "message": "...", "data": ...}`
- 使用适当的 HTTP 状态码（200 表示成功，400 表示客户端错误，500 表示服务器错误）

```python
from app.utils.responses import APIResponse

# 成功响应
return APIResponse.success(data=user_data, message="用户创建成功")

# 错误响应
return APIResponse.error(error_code="USER_NOT_FOUND", message="用户未找到", status_code=404)
```

#### 数据库模型
- 继承 `BaseModel` 以自动获取时间戳列（`created_at`、`updated_at`）
- 使用 SQLAlchemy 定义关系
- 使用适当的列类型和约束

```python
class House(BaseModel):
    __tablename__ = 'houses'
    
    title = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(20), default='available')
    
    # 外键
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # 关系
    owner = db.relationship('User', back_populates='houses')
```

#### 路由定义
```python
from flask import Blueprint, request
from app.utils.decorators import login_required
from app.utils.responses import APIResponse

houses_bp = Blueprint('houses', __name__, url_prefix='/api/houses')

@houses_bp.route('', methods=['GET'])
@login_required
def get_houses():
    """获取所有房源。"""
    houses = House.query.all()
    return APIResponse.success(data=[h.to_dict() for h in houses])

@houses_bp.route('', methods=['POST'])
@login_required
def create_house():
    """创建新房源。"""
    data = request.get_json()
    # ... 验证和创建逻辑
    return APIResponse.success(data=house.to_dict(), message="房源创建成功", status_code=201)
```

---

### Vue 3 (前端)

#### 通用规则
- 使用 Composition API 的 `<script setup>` 语法
- 新组件尽量使用 TypeScript
- 使用 2 个空格进行缩进

#### 组件命名
- 组件名使用 `PascalCase`（例如 `HouseList.vue`、`UserForm.vue`）
- 使用类型前缀：`BaseButton.vue`、`TheHeader.vue`

#### Script Setup
```vue
<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getHouses } from '@/api/house'

const router = useRouter()
const houses = ref([])
const loading = ref(false)

const filteredHouses = computed(() => {
  return houses.value.filter(h => h.status === 'available')
})

onMounted(async () => {
  loading.value = true
  try {
    const { data } = await getHouses()
    houses.value = data
  } catch (error) {
    ElMessage.error('加载房源失败')
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="house-list">
    <el-table :data="filteredHouses" v-loading="loading">
      <el-table-column prop="title" label="标题" />
    </el-table>
  </div>
</template>

<style scoped>
.house-list {
  padding: 20px;
}
</style>
```

#### API 请求
- 使用 `@/api/request.js` 中的 Axios 实例
- 在 `@/api/` 目录创建 API 文件

```javascript
// src/api/house.js
import request from './request'

export const getHouses = (params) => {
  return request.get('/houses', { params })
}

export const createHouse = (data) => {
  return request.post('/houses', data)
}

export const updateHouse = (id, data) => {
  return request.put(`/houses/${id}`, data)
}

export const deleteHouse = (id) => {
  return request.delete(`/houses/${id}`)
}
```

#### Store (Pinia)
```javascript
// src/store/user.js
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { getUserInfo, login as apiLogin } from '@/api/user'

export const useUserStore = defineStore('user', () => {
  const token = ref(localStorage.getItem('token') || '')
  const userInfo = ref(null)

  const isLoggedIn = computed(() => !!token.value)
  const isAdmin = computed(() => userInfo.value?.role === 'admin')

  async function fetchUserInfo() {
    const { data } = await getUserInfo()
    userInfo.value = data
  }

  async function login(credentials) {
    const { data } = await apiLogin(credentials)
    token.value = data.access_token
    localStorage.setItem('token', data.access_token)
    await fetchUserInfo()
  }

  function logout() {
    token.value = ''
    userInfo.value = null
    localStorage.removeItem('token')
  }

  return {
    token,
    userInfo,
    isLoggedIn,
    isAdmin,
    fetchUserInfo,
    login,
    logout
  }
})
```

#### 路由配置
```javascript
// src/router/index.js
import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/store/user'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue')
  },
  {
    path: '/',
    redirect: '/dashboard'
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import('@/views/Dashboard.vue'),
    meta: { requiresAuth: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  const userStore = useUserStore()
  
  if (to.meta.requiresAuth && !userStore.isLoggedIn) {
    next('/login')
  } else {
    next()
  }
})

export default router
```

---

## 3. 项目结构

```
Housing_ental_system/
├── app/                    # Flask 后端
│   ├── models/            # SQLAlchemy 模型
│   ├── routes/            # API 蓝图/路由
│   ├── utils/             # 工具函数
│   ├── schemas/           # Marshmallow 模式
│   ├── config.py          # 配置文件
│   └── __init__.py        # 应用工厂
├── src/                   # Vue 3 前端
│   ├── api/               # API 请求模块
│   ├── components/        # Vue 组件
│   ├── views/             # 页面组件
│   ├── router/            # Vue Router 配置
│   ├── store/             # Pinia 状态管理
│   ├── utils/             # 前端工具函数
│   └── styles/            # SCSS 样式
├── tests/                 # 后端 pytest 测试
└── instance/              # SQLite 数据库
```

---

## 4. 关键配置文件

- `.env` - 环境变量（从 `.env.example` 创建）
- `pytest.ini` - Pytest 配置
- `vitest.config.js` - Vitest 配置
- `vite.config.js` - Vite 配置
- `requirements.txt` - Python 依赖
- `package.json` - Node.js 依赖

---

## 5. 数据库

- 默认：SQLite（`instance/housing_rental.db`）
- 支持通过环境变量配置 MySQL 和 PostgreSQL
- 模型使用 Flask-SQLAlchemy ORM

---

## 6. 认证

- 基于 JWT 的认证
- Token 存储在 `Authorization: Bearer <token>` 请求头中
- 使用 `@login_required` 装饰器保护路由
- 使用 `get_jwt_identity()` 获取当前用户 ID
