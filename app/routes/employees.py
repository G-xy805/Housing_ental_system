"""
员工管理路由模块
提供员工注册、列表、编辑、状态管理等功能
"""
from flask import Blueprint, request, jsonify, g, current_app
from typing import Optional, Dict, Any
from datetime import datetime

from app.models.user import User
from app.models import db
from app.utils.decorators import login_required, admin_required, permission_required
from app.utils.responses import APIResponse, PaginationResponse

# 创建蓝图
employees_bp = Blueprint('employees', __name__, url_prefix='/api/employees')


# ============================================================================
# 辅助函数
# ============================================================================

def validate_employee_data(data: Dict, is_update: bool = False) -> tuple:
    """
    验证员工数据
    
    Args:
        data: 请求数据
        is_update: 是否为更新操作
        
    Returns:
        tuple: (是否有效，错误消息，验证后的数据)
    """
    errors = []
    validated_data = {}
    
    # 姓名（必填）
    if not is_update or 'name' in data:
        name_value = data.get('name')
        if not name_value:
            errors.append('姓名不能为空')
        elif len(str(name_value)) > 50:
            errors.append('姓名不能超过 50 个字符')
        else:
            validated_data['name'] = str(name_value).strip()

    # 手机号（必填）
    if not is_update or 'phone' in data:
        phone_value = data.get('phone')
        if not phone_value:
            errors.append('手机号不能为空')
        elif len(str(phone_value)) > 20:
            errors.append('手机号格式不正确')
        else:
            validated_data['phone'] = str(phone_value).strip()
    
    # 邮箱（可选）
    if 'email' in data and data.get('email'):
        email_value = data.get('email')
        if '@' not in str(email_value):
            errors.append('邮箱格式不正确')
        else:
            validated_data['email'] = str(email_value).strip()
    elif not is_update:
        # 如果没有提供邮箱，设置为 None（仅创建时）
        validated_data['email'] = None
    # 更新操作时，如果没有提供邮箱，不修改邮箱字段

    # 身份证号（可选）
    if 'id_card' in data and data.get('id_card'):
        id_card_value = data.get('id_card')
        if len(str(id_card_value)) not in [15, 18]:
            errors.append('身份证号格式不正确')
        else:
            validated_data['id_card'] = str(id_card_value).strip()

    # 职位（可选）
    if 'position' in data:
        position_value = data.get('position')
        if position_value is not None:
            validated_data['position'] = str(position_value).strip()
        else:
            validated_data['position'] = None
    
    # 用户名（注册时必填）
    if not is_update:
        if not data.get('username'):
            errors.append('用户名不能为空')
        elif len(data.get('username', '')) > 50:
            errors.append('用户名不能超过 50 个字符')
        else:
            validated_data['username'] = data['username'].strip()
    
    # 密码（注册时必填）
    if not is_update:
        if not data.get('password'):
            errors.append('密码不能为空')
        elif len(data.get('password', '')) < 6:
            errors.append('密码长度不能少于 6 个字符')
        else:
            validated_data['password'] = data['password']
    
    # 角色（可选，默认 staff）
    if 'role' in data and data.get('role'):
        if data['role'] not in ['admin', 'staff']:
            errors.append('角色必须是 admin 或 staff')
        else:
            validated_data['role'] = data['role']
    
    # 状态（可选，默认 active）
    if 'status' in data:
        if data['status'] not in ['active', 'resigned', 'disabled']:
            errors.append('状态必须是 active(在职)、resigned(离职) 或 disabled(禁用)')
        else:
            validated_data['status'] = data['status']
    
    # 头像（可选）
    if 'avatar' in data:
        avatar_value = data.get('avatar')
        if avatar_value is not None:
            validated_data['avatar'] = str(avatar_value).strip()
        else:
            validated_data['avatar'] = None
    
    if errors:
        return False, '; '.join(errors), None
    
    return True, None, validated_data


def format_employee_response(user: User, include_details: bool = False) -> Dict:
    """
    格式化员工响应数据
    
    Args:
        user: 用户对象
        include_details: 是否包含详细信息
        
    Returns:
        dict: 员工响应数据
    """
    return user.to_dict(include_details=include_details)


def check_phone_duplicate(phone: str, exclude_id: int = None) -> Optional[User]:
    """
    检查手机号是否已存在
    
    Args:
        phone: 手机号
        exclude_id: 排除的用户 ID（更新时使用）
        
    Returns:
        User or None: 如果存在则返回用户对象
    """
    query = User.query.filter_by(phone=phone)
    if exclude_id:
        query = query.filter(User.id != exclude_id)
    return query.first()


def check_email_duplicate(email: str, exclude_id: int = None) -> Optional[User]:
    """
    检查邮箱是否已存在
    
    Args:
        email: 邮箱
        exclude_id: 排除的用户 ID（更新时使用）
        
    Returns:
        User or None: 如果存在则返回用户对象
    """
    query = User.query.filter_by(email=email)
    if exclude_id:
        query = query.filter(User.id != exclude_id)
    return query.first()


def check_username_duplicate(username: str, exclude_id: int = None) -> Optional[User]:
    """
    检查用户名是否已存在
    
    Args:
        username: 用户名
        exclude_id: 排除的用户 ID（更新时使用）
        
    Returns:
        User or None: 如果存在则返回用户对象
    """
    query = User.query.filter_by(username=username)
    if exclude_id:
        query = query.filter(User.id != exclude_id)
    return query.first()


def check_id_card_duplicate(id_card: str, exclude_id: int = None) -> Optional[User]:
    """
    检查身份证号是否已存在
    
    Args:
        id_card: 身份证号
        exclude_id: 排除的用户 ID（更新时使用）
        
    Returns:
        User or None: 如果存在则返回用户对象
    """
    import hashlib
    id_card_hash = hashlib.sha256(id_card.encode()).hexdigest()
    query = User.query.filter_by(id_card_hash=id_card_hash)
    if exclude_id:
        query = query.filter(User.id != exclude_id)
    return query.first()


# ============================================================================
# 员工 CRUD 接口
# ============================================================================

@employees_bp.route('', methods=['GET'])
@login_required
def get_employees():
    """
    获取员工列表（支持分页、筛选、搜索）
    
    Query Parameters:
        page: 页码，默认 1
        per_page: 每页数量，默认 20，最大 100
        keyword: 关键词搜索（姓名、手机号、邮箱）
        name: 姓名搜索
        phone: 手机号搜索
        status: 状态筛选 (active/resigned/disabled)
        role: 角色筛选 (admin/staff)
        order_by: 排序字段 (created_at/updated_at/name)
        order: 排序方向 (asc/desc)，默认 desc
        
    Response:
        {
            "success": true,
            "message": "获取成功",
            "data": {
                "items": [...],
                "pagination": {
                    "page": 1,
                    "per_page": 20,
                    "total": 100,
                    "pages": 5,
                    "has_next": true,
                    "has_prev": false
                }
            }
        }
    """
    try:
        # 获取查询参数
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', type=int)
        per_page_arg = request.args.get('per_page', type=int)
        per_page = min(page_size or per_page_arg or 20, 100)
        
        # 构建查询（使用 db.session.query 避免 SoftDeleteQuery 的 paginate 问题）
        query = db.session.query(User).filter(User.deleted_at.is_(None))
        
        # 关键词搜索（姓名、手机号、邮箱）
        keyword = request.args.get('keyword')
        if keyword:
            query = query.filter(
                db.or_(
                    User.name.ilike(f'%{keyword}%'),
                    User.phone.ilike(f'%{keyword}%'),
                    User.email.ilike(f'%{keyword}%')
                )
            )
        
        # 姓名搜索
        name = request.args.get('name')
        if name:
            query = query.filter(User.name.ilike(f'%{name}%'))
        
        # 手机号搜索
        phone = request.args.get('phone')
        if phone:
            query = query.filter(User.phone.ilike(f'%{phone}%'))
        
        # 状态筛选
        status = request.args.get('status')
        if status:
            if status not in ['active', 'resigned', 'disabled']:
                return APIResponse.bad_request("状态必须是 active(在职)、resigned(离职) 或 disabled(禁用)")
            query = query.filter(User.status == status)
        
        # 角色筛选
        role = request.args.get('role')
        if role:
            if role not in ['admin', 'staff']:
                return APIResponse.bad_request("角色必须是 admin 或 staff")
            query = query.filter(User.role == role)
        
        # 排序
        order_by = request.args.get('order_by', 'created_at')
        order = request.args.get('order', 'desc')
        
        order_column = getattr(User, order_by, User.created_at)
        if order == 'asc':
            query = query.order_by(order_column.asc())
        else:
            query = query.order_by(order_column.desc())
        
        # 执行分页查询
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        # 格式化响应数据
        items = [format_employee_response(user) for user in pagination.items]
        
        pagination_info = {
            'page': pagination.page,
            'per_page': pagination.per_page,
            'total': pagination.total,
            'pages': pagination.pages,
            'has_next': pagination.has_next,
            'has_prev': pagination.has_prev,
            'next_num': pagination.next_num if pagination.has_next else None,
            'prev_num': pagination.prev_num if pagination.has_prev else None
        }
        
        return APIResponse.success({
            'items': items,
            'pagination': pagination_info
        }, "获取员工列表成功")
        
    except Exception as e:
        current_app.logger.error(f"获取员工列表失败：{str(e)}")
        return APIResponse.server_error("获取员工列表失败")


@employees_bp.route('/<int:employee_id>', methods=['GET'])
@login_required
def get_employee(employee_id: int):
    """
    获取员工详情
    
    Path Parameters:
        employee_id: 员工 ID
        
    Response:
        {
            "success": true,
            "data": {
                "id": 1,
                "username": "zhangsan",
                "name": "张三",
                "phone": "13800138000",
                "email": "zhangsan@example.com",
                "position": "客服经理",
                "role": "staff",
                "status": "active",
                "avatar": "...",
                "last_login": "2024-01-01 10:00:00",
                "created_at": "2024-01-01 00:00:00"
            }
        }
    """
    try:
        user = User.query.get(employee_id)
        
        if not user:
            return APIResponse.not_found("员工不存在")
        
        # 格式化响应数据（包含详细信息）
        data = format_employee_response(user, include_details=True)
        
        return APIResponse.success(data, "获取员工详情成功")
        
    except Exception as e:
        current_app.logger.error(f"获取员工详情失败：{str(e)}")
        return APIResponse.server_error("获取员工详情失败")


@employees_bp.route('', methods=['POST'])
@login_required
@admin_required
def create_employee():
    """
    创建员工（注册）
    
    Request Body:
        {
            "username": "zhangsan",
            "password": "123456",
            "name": "张三",
            "phone": "13800138000",
            "email": "zhangsan@example.com",
            "id_card": "110101199001011234",
            "position": "客服经理",
            "role": "staff"
        }
        
    Response:
        {
            "success": true,
            "message": "员工创建成功",
            "data": {...}
        }
    """
    try:
        # 获取请求数据
        data = request.get_json()
        
        if not data:
            return APIResponse.bad_request("请求数据不能为空")
        
        # 验证数据
        is_valid, error_msg, validated_data = validate_employee_data(data, is_update=False)
        
        if not is_valid:
            return APIResponse.validation_error(error_msg)
        
        # 检查用户名是否重复
        if check_username_duplicate(validated_data['username']):
            return APIResponse.bad_request("用户名已存在")
        
        # 检查手机号是否重复
        if check_phone_duplicate(validated_data['phone']):
            return APIResponse.bad_request("手机号已存在")
        
        # 检查邮箱是否重复
        if 'email' in validated_data and check_email_duplicate(validated_data['email']):
            return APIResponse.bad_request("邮箱已存在")
        
        # 检查身份证号是否重复
        if 'id_card' in validated_data and validated_data['id_card']:
            if check_id_card_duplicate(validated_data['id_card']):
                return APIResponse.bad_request("身份证号已存在")
        
        # 如果没有提供邮箱，生成一个基于用户名的邮箱
        if 'email' not in validated_data or not validated_data['email']:
            validated_data['email'] = f"{validated_data['username']}@example.com"
        
        # 移除密码字段（将通过 set_password 方法设置）
        password = validated_data.pop('password')
        
        # 移除身份证号字段（将通过 set_id_card 方法设置）
        id_card = validated_data.pop('id_card', None)
        
        # 创建员工
        user = User(**validated_data)

        # 设置创建人
        user.created_by = getattr(g, 'user_id', None)

        # 先设置密码（这样 password_hash 就不会是 None）
        user.set_password(password)

        # 设置身份证号
        if id_card:
            user.set_id_card(id_card)

        # 添加到数据库并提交
        db.session.add(user)
        db.session.commit()
        
        # 刷新获取完整数据
        db.session.refresh(user)
        
        # 格式化响应
        result = format_employee_response(user)
        
        current_app.logger.info(f"管理员 {g.username} 创建了员工 {user.id}: {user.name}")
        
        return APIResponse.success(result, "员工创建成功", 201)
        
    except Exception as e:
        db.session.rollback()
        import traceback
        current_app.logger.error(f"创建员工失败：{str(e)}")
        current_app.logger.error(f"错误详情：{traceback.format_exc()}")
        return APIResponse.server_error("创建员工失败")


@employees_bp.route('/<int:employee_id>', methods=['PUT'])
@login_required
@admin_required
def update_employee(employee_id: int):
    """
    更新员工信息
    
    Path Parameters:
        employee_id: 员工 ID
        
    Request Body:
        {
            "name": "新的姓名",
            "phone": "新的手机号",
            "email": "新的邮箱",
            "position": "新的职位",
            "role": "staff",
            "status": "active"
        }
        
    Response:
        {
            "success": true,
            "message": "员工信息更新成功",
            "data": {...}
        }
    """
    try:
        user = User.query.get(employee_id)
        
        if not user:
            return APIResponse.not_found("员工不存在")
        
        # 获取请求数据
        data = request.get_json()
        
        if not data:
            return APIResponse.bad_request("请求数据不能为空")
        
        # 验证数据
        is_valid, error_msg, validated_data = validate_employee_data(data, is_update=True)
        
        if not is_valid:
            return APIResponse.validation_error(error_msg)
        
        # 检查用户名是否重复（排除自己）
        if 'username' in validated_data and check_username_duplicate(validated_data['username'], exclude_id=employee_id):
            return APIResponse.bad_request("用户名已存在")
        
        # 检查手机号是否重复（排除自己）
        if 'phone' in validated_data and check_phone_duplicate(validated_data['phone'], exclude_id=employee_id):
            return APIResponse.bad_request("手机号已存在")
        
        # 检查邮箱是否重复（排除自己）
        if 'email' in validated_data and check_email_duplicate(validated_data['email'], exclude_id=employee_id):
            return APIResponse.bad_request("邮箱已存在")
        
        # 检查身份证号是否重复（排除自己）
        if 'id_card' in validated_data and validated_data['id_card']:
            if check_id_card_duplicate(validated_data['id_card'], exclude_id=employee_id):
                return APIResponse.bad_request("身份证号已存在")
        
        # 更新员工信息
        for key, value in validated_data.items():
            if key == 'id_card' and value:
                user.set_id_card(value)
            elif key != 'password':  # 密码不通过此接口更新
                setattr(user, key, value)
        
        db.session.commit()
        
        # 刷新获取完整数据
        db.session.refresh(user)
        
        # 格式化响应
        result = format_employee_response(user)
        
        current_app.logger.info(f"管理员 {g.username} 更新了员工 {employee_id}: {user.name}")
        
        return APIResponse.success(result, "员工信息更新成功")
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"更新员工信息失败：{str(e)}")
        return APIResponse.server_error("更新员工信息失败")


@employees_bp.route('/<int:employee_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_employee(employee_id: int):
    """
    删除员工（仅管理员）
    
    Path Parameters:
        employee_id: 员工 ID
        
    Response:
        {
            "success": true,
            "message": "员工删除成功"
        }
    """
    try:
        user = User.query.get(employee_id)
        
        if not user:
            return APIResponse.not_found("员工不存在")
        
        # 不允许删除自己（优先检查）
        if user.id == g.user_id:
            return APIResponse.bad_request("不允许删除自己的账号")
        
        # 不允许删除管理员
        if user.role == 'admin':
            return APIResponse.bad_request("不允许删除管理员账号")
        
        employee_name = user.name
        
        # 处理关联的房源：将负责的房源转移给当前管理员
        from app.models.house import House
        houses = House.query.filter_by(owner_id=employee_id).all()
        for house in houses:
            house.owner_id = g.user_id
        
        # 删除员工
        db.session.delete(user)
        db.session.commit()
        
        current_app.logger.info(f"管理员 {g.username} 删除了员工 {employee_id}: {employee_name}")
        
        return APIResponse.success(None, "员工删除成功")
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"删除员工失败：{str(e)}")
        return APIResponse.server_error("删除员工失败")


# ============================================================================
# 员工状态管理接口
# ============================================================================

@employees_bp.route('/<int:employee_id>/status', methods=['PATCH'])
@login_required
@admin_required
def update_employee_status(employee_id: int):
    """
    更新员工状态
    
    Path Parameters:
        employee_id: 员工 ID
        
    Request Body:
        {
            "status": "active"  // active-在职，resigned-离职，disabled-禁用
        }
        
    Response:
        {
            "success": true,
            "message": "员工状态更新成功",
            "data": {...}
        }
    """
    try:
        user = User.query.get(employee_id)
        
        if not user:
            return APIResponse.not_found("员工不存在")
        
        # 获取请求数据
        data = request.get_json()
        
        if not data or 'status' not in data:
            return APIResponse.bad_request("状态不能为空")
        
        status = data['status']
        if status not in ['active', 'resigned', 'disabled']:
            return APIResponse.bad_request("状态必须是 active(在职)、resigned(离职) 或 disabled(禁用)")
        
        # 更新状态
        user.status = status
        
        # 如果禁用，清除登录状态
        if status == 'disabled':
            user.login_attempts = 0
            user.locked_until = None
        
        db.session.commit()
        
        # 刷新获取完整数据
        db.session.refresh(user)
        
        # 格式化响应
        result = format_employee_response(user)
        
        current_app.logger.info(f"管理员 {g.username} 更新了员工 {employee_id} 的状态为 {status}")
        
        return APIResponse.success(result, "员工状态更新成功")
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"更新员工状态失败：{str(e)}")
        return APIResponse.server_error("更新员工状态失败")


# ============================================================================
# 密码重置接口
# ============================================================================

@employees_bp.route('/<int:employee_id>/reset-password', methods=['POST'])
@login_required
@admin_required
def reset_employee_password(employee_id: int):
    """
    重置员工密码
    
    Path Parameters:
        employee_id: 员工 ID
        
    Request Body:
        {
            "new_password": "newpassword123"
        }
        
    Response:
        {
            "success": true,
            "message": "密码重置成功",
            "data": {
                "temporary_password": "..."
            }
        }
    """
    try:
        user = User.query.get(employee_id)
        
        if not user:
            return APIResponse.not_found("员工不存在")
        
        # 不允许重置管理员密码
        if user.role == 'admin':
            return APIResponse.bad_request("不允许重置管理员密码")
        
        # 获取请求数据
        data = request.get_json()
        
        if not data or 'new_password' not in data:
            return APIResponse.bad_request("新密码不能为空")
        
        new_password = data['new_password']
        
        if len(new_password) < 6:
            return APIResponse.bad_request("密码长度不能少于 6 个字符")
        
        # 设置新密码
        user.set_password(new_password)
        
        # 重置登录尝试次数
        user.login_attempts = 0
        user.locked_until = None
        
        db.session.commit()
        
        current_app.logger.info(f"管理员 {g.username} 重置了员工 {employee_id} 的密码")
        
        return APIResponse.success(
            {'temporary_password': new_password},
            "密码重置成功，请将临时密码告知员工"
        )
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"重置密码失败：{str(e)}")
        return APIResponse.server_error("重置密码失败")


# ============================================================================
# 批量操作
# ============================================================================

@employees_bp.route('/batch-action', methods=['POST'])
@login_required
@admin_required
def batch_action():
    """
    批量操作
    
    Request Body:
        {
            "user_ids": [1, 2, 3],
            "action": "disable"  // enable, disable, delete
        }
    """
    try:
        data = request.get_json()
        
        if not data:
            return APIResponse.bad_request("请求数据不能为空")
        
        user_ids = data.get('user_ids', [])
        action = data.get('action')
        
        if not user_ids:
            return APIResponse.bad_request("员工 ID 列表不能为空")
        
        if action not in ['enable', 'disable', 'delete']:
            return APIResponse.bad_request("操作必须是 enable, disable 或 delete")
        
        # 不允许对管理员进行操作
        admin_users = User.query.filter(User.id.in_(user_ids), User.role == 'admin').all()
        if admin_users:
            return APIResponse.bad_request(f"不允许对管理员账号进行操作")
        
        # 不允许删除自己
        if action == 'delete' and g.user_id in user_ids:
            return APIResponse.bad_request("不允许删除自己的账号")
        
        count = 0
        for user_id in user_ids:
            user = User.query.get(user_id)
            if user:
                if action == 'enable':
                    user.status = 'active'
                    user.login_attempts = 0
                    user.locked_until = None
                elif action == 'disable':
                    user.status = 'disabled'
                    user.login_attempts = 0
                    user.locked_until = None
                elif action == 'delete':
                    db.session.delete(user)
                count += 1
        
        db.session.commit()
        
        return APIResponse.success(
            {'count': count},
            f"批量{action}操作成功，共处理 {count} 个员工"
        )
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"批量操作失败：{str(e)}")
        return APIResponse.server_error("批量操作失败")


# ============================================================================
# 统计接口
# ============================================================================

@employees_bp.route('/stats', methods=['GET'])
@login_required
@admin_required
def get_employee_stats():
    """获取员工统计信息"""
    try:
        total = User.query.count()
        by_role = {
            'admin': User.query.filter(User.role == 'admin').count(),
            'staff': User.query.filter(User.role == 'staff').count()
        }
        by_status = {
            'active': User.query.filter(User.status == 'active').count(),
            'resigned': User.query.filter(User.status == 'resigned').count(),
            'disabled': User.query.filter(User.status == 'disabled').count()
        }
        
        return APIResponse.success({
            'total': total,
            'by_role': by_role,
            'by_status': by_status
        }, "获取员工统计成功")
        
    except Exception as e:
        current_app.logger.error(f"获取员工统计失败：{str(e)}")
        return APIResponse.server_error("获取员工统计失败")
