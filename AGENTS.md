# AGENTS.md - 房屋租赁系统开发指南

本文档为在此代码库上工作的智能体提供指南和命令。

---

## 1. 构建、代码检查和测试命令

### 后端 (Python/Flask)

```bash
# 激活虚拟环境
.venv\Scripts\activate  # Windows

# 运行 Flask 开发服务器
python -m flask run
```

#### 测试命令
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
```

测试标记：`unit` | `integration` | `api` | `slow` | `auth` | `encryption`

### 前端 (Vue 3 + Vite)

```bash
npm run dev        # 开发服务器（端口 5173）
npm run build      # 生产构建
npm run lint       # ESLint 检查修复
npm test           # 测试（监听模式）
npm run test:run   # 测试（CI 模式）
npx vitest run src/__tests__/example.test.js  # 单个测试文件
```

---

## 2. 代码风格指南

### Python (Flask 后端)

- 遵循 PEP 8 编码规范，使用 4 空格缩进
- 为函数参数和返回值使用类型提示
- 为所有公共函数和类编写文档字符串

#### 命名约定
- **类**：`PascalCase`（如 `User`）
- **函数/变量**：`snake_case`（如 `get_user_by_id`）
- **常量**：`UPPER_SNAKE_CASE`（如 `MAX_UPLOAD_SIZE`）
- **私有方法**：下划线前缀（如 `_internal_method`）
- **数据库表**：`snake_case`（在 `__tablename__` 中定义）

#### 导入顺序
```python
# 标准库 → 第三方包 → 本地应用导入 → 本地相对导入
import os
import jwt
from app.models import db
from .config import config
```

#### 错误处理
使用 `app/utils/responses.py` 中的 `APIResponse` 类：
```python
from app.utils.responses import APIResponse

return APIResponse.success(data=user_data, message="创建成功")
return APIResponse.error(error_code="NOT_FOUND", message="未找到", status_code=404)
```

#### 数据库模型
继承 `BaseModel` 自动获取 `created_at`、`updated_at`：
```python
class House(BaseModel):
    __tablename__ = 'houses'
    title = db.Column(db.String(100), nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    owner = db.relationship('User', back_populates='houses')
```

#### 路由定义
```python
houses_bp = Blueprint('houses', __name__, url_prefix='/api/houses')

@houses_bp.route('', methods=['GET'])
@login_required
def get_houses():
    """获取所有房源。"""
    return APIResponse.success(data=[h.to_dict() for h in houses])
```

---

### Vue 3 (前端)

- 使用 Composition API 的 `<script setup>` 语法
- 使用 2 空格缩进，组件名使用 `PascalCase`

#### API 请求
```javascript
// src/api/house.js
import request from './request'

export const getHouses = (params) => request.get('/houses', { params })
export const createHouse = (data) => request.post('/houses', data)
```

#### Store (Pinia)
```javascript
export const useUserStore = defineStore('user', () => {
  const token = ref(localStorage.getItem('token') || '')
  const isLoggedIn = computed(() => !!token.value)
  return { token, isLoggedIn, login, logout }
})
```

#### 路由认证
```javascript
router.beforeEach((to, from, next) => {
  const userStore = useUserStore()
  if (to.meta.requiresAuth && !userStore.isLoggedIn) {
    next('/login')
  } else {
    next()
  }
})
```

---

## 3. 项目结构

```
Housing_ental_system/
├── app/              # Flask 后端
│   ├── models/       # SQLAlchemy 模型
│   ├── routes/       # API 蓝图/路由
│   ├── utils/        # 工具函数（decorators, responses, jwt）
│   └── config.py     # 配置文件
├── src/              # Vue 3 前端
│   ├── api/          # API 请求模块
│   ├── components/   # Vue 组件
│   ├── views/        # 页面组件
│   ├── router/       # Vue Router
│   └── store/        # Pinia 状态管理
├── tests/            # pytest 测试
└── instance/         # SQLite 数据库
```

---

## 4. 认证

- JWT 认证，Token 在 `Authorization: Bearer <token>` 请求头中
- 使用 `@login_required` 装饰器保护路由
- 使用 `get_jwt_identity()` 获取当前用户 ID
