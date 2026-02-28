"""
用户管理路由模块
提供用户 CRUD、角色管理、权限管理等功能
"""
from flask import Blueprint, request, jsonify, g, current_app
from typing import Optional, Dict, Any
from datetime import datetime

from app.models.user import User
from app.models import db
from app.utils.decorators import login_required, admin_required
from app.utils.responses import APIResponse

# 创建蓝图
users_bp = Blueprint('users', __name__, url_prefix='/api/users')


# ============================================================================
# 辅助函数
# ============================================================================

def format_user_response(user: User, include_details: bool = False) -> Dict:
    """
    格式化用户响应数据
    
    Args:
        user: 用户对象
        include_details: 是否包含详细信息
        
    Returns:
        dict: 用户响应数据
    """
    return user.to_dict(include_details=include_details)


def check_phone_duplicate(phone: str, exclude_id: int = None) -> Optional[User]:
    """检查手机号是否已存在"""
    query = User.query.filter_by(phone=phone)
    if exclude_id:
        query = query.filter(User.id != exclude_id)
    return query.first()


def check_email_duplicate(email: str, exclude_id: int = None) -> Optional[User]:
    """检查邮箱是否已存在"""
    query = User.query.filter_by(email=email)
    if exclude_id:
        query = query.filter(User.id != exclude_id)
    return query.first()


# ============================================================================
# 用户 CRUD 接口
# ============================================================================

@users_bp.route('', methods=['GET'])
@login_required
@admin_required
def get_users():
    """
    获取用户列表（支持分页、筛选、搜索）
    
    Query Parameters:
        page: 页码，默认 1
        per_page: 每页数量，默认 20，最大 100
        keyword: 关键词搜索（用户名、姓名、手机号、邮箱）
        username: 用户名搜索
        name: 姓名搜索
        phone: 手机号搜索
        email: 邮箱搜索
        role: 角色筛选 (admin/staff)
        status: 状态筛选 (active/resigned/disabled)
        order_by: 排序字段 (created_at/updated_at/name)
        order: 排序方向 (asc/desc)，默认 desc
        
    Response:
        {
            "success": true,
            "data": {
                "items": [...],
                "pagination": {...}
            }
        }
    """
    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        
        query = User.query
        
        # 关键词搜索
        keyword = request.args.get('keyword')
        if keyword:
            query = query.filter(
                db.or_(
                    User.username.ilike(f'%{keyword}%'),
                    User.name.ilike(f'%{keyword}%'),
                    User.phone.ilike(f'%{keyword}%'),
                    User.email.ilike(f'%{keyword}%')
                )
            )
        
        # 各字段搜索
        if request.args.get('username'):
            query = query.filter(User.username.ilike(f'%{request.args.get("username")}%'))
        
        if request.args.get('name'):
            query = query.filter(User.name.ilike(f'%{request.args.get("name")}%'))
        
        if request.args.get('phone'):
            query = query.filter(User.phone.ilike(f'%{request.args.get("phone")}%'))
        
        if request.args.get('email'):
            query = query.filter(User.email.ilike(f'%{request.args.get("email")}%'))
        
        # 角色筛选
        if request.args.get('role'):
            role = request.args.get('role')
            if role in ['admin', 'staff']:
                query = query.filter(User.role == role)
        
        # 状态筛选
        if request.args.get('status'):
            status = request.args.get('status')
            if status in ['active', 'resigned', 'disabled']:
                query = query.filter(User.status == status)
        
        # 排序
        order_by = request.args.get('order_by', 'created_at')
        order = request.args.get('order', 'desc')
        
        order_column = getattr(User, order_by, User.created_at)
        if order == 'asc':
            query = query.order_by(order_column.asc())
        else:
            query = query.order_by(order_column.desc())
        
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        items = [format_user_response(user) for user in pagination.items]
        
        pagination_info = {
            'page': pagination.page,
            'per_page': pagination.per_page,
            'total': pagination.total,
            'pages': pagination.pages,
            'has_next': pagination.has_next,
            'has_prev': pagination.has_prev
        }
        
        return APIResponse.success({
            'items': items,
            'pagination': pagination_info
        }, "获取用户列表成功")
        
    except Exception as e:
        current_app.logger.error(f"获取用户列表失败：{str(e)}")
        return APIResponse.server_error("获取用户列表失败")


@users_bp.route('/<int:user_id>', methods=['GET'])
@login_required
@admin_required
def get_user(user_id: int):
    """获取用户详情"""
    try:
        user = User.query.get(user_id)
        
        if not user:
            return APIResponse.not_found("用户不存在")
        
        data = format_user_response(user, include_details=True)
        return APIResponse.success(data, "获取用户详情成功")
        
    except Exception as e:
        current_app.logger.error(f"获取用户详情失败：{str(e)}")
        return APIResponse.server_error("获取用户详情失败")


@users_bp.route('/<int:user_id>', methods=['PUT'])
@login_required
@admin_required
def update_user(user_id: int):
    """
    更新用户信息
    
    Request Body:
        {
            "name": "姓名",
            "phone": "手机号",
            "email": "邮箱",
            "position": "职位",
            "role": "staff",
            "status": "active"
        }
    """
    try:
        user = User.query.get(user_id)
        
        if not user:
            return APIResponse.not_found("用户不存在")
        
        data = request.get_json()
        
        if not data:
            return APIResponse.bad_request("请求数据不能为空")
        
        # 不允许修改用户名
        if 'username' in data:
            return APIResponse.bad_request("不允许修改用户名")
        
        # 检查手机号重复
        if 'phone' in data and check_phone_duplicate(data['phone'], exclude_id=user_id):
            return APIResponse.bad_request("手机号已存在")
        
        # 检查邮箱重复
        if 'email' in data and check_email_duplicate(data['email'], exclude_id=user_id):
            return APIResponse.bad_request("邮箱已存在")
        
        # 更新字段
        updatable_fields = ['name', 'phone', 'email', 'position', 'role', 'status']
        for field in updatable_fields:
            if field in data:
                setattr(user, field, data[field])
        
        db.session.commit()
        db.session.refresh(user)
        
        result = format_user_response(user)
        return APIResponse.success(result, "用户信息更新成功")
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"更新用户失败：{str(e)}")
        return APIResponse.server_error("更新用户失败")


@users_bp.route('/<int:user_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_user(user_id: int):
    """删除用户（仅管理员）"""
    try:
        user = User.query.get(user_id)
        
        if not user:
            return APIResponse.not_found("用户不存在")
        
        # 不允许删除管理员
        if user.role == 'admin':
            return APIResponse.bad_request("不允许删除管理员账号")
        
        # 不允许删除自己
        if user.id == g.user_id:
            return APIResponse.bad_request("不允许删除自己的账号")
        
        user_name = user.name
        db.session.delete(user)
        db.session.commit()
        
        current_app.logger.info(f"管理员 {g.username} 删除了用户 {user_id}: {user_name}")
        return APIResponse.success(None, "用户删除成功")
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"删除用户失败：{str(e)}")
        return APIResponse.server_error("删除用户失败")


# ============================================================================
# 用户状态管理
# ============================================================================

@users_bp.route('/<int:user_id>/status', methods=['PATCH'])
@login_required
@admin_required
def update_user_status(user_id: int):
    """更新用户状态"""
    try:
        user = User.query.get(user_id)
        
        if not user:
            return APIResponse.not_found("用户不存在")
        
        data = request.get_json()
        
        if not data or 'status' not in data:
            return APIResponse.bad_request("状态不能为空")
        
        status = data['status']
        if status not in ['active', 'resigned', 'disabled']:
            return APIResponse.bad_request("状态必须是 active(在职)、resigned(离职) 或 disabled(禁用)")
        
        user.status = status
        
        if status == 'disabled':
            user.login_attempts = 0
            user.locked_until = None
        
        db.session.commit()
        db.session.refresh(user)
        
        result = format_user_response(user)
        return APIResponse.success(result, "用户状态更新成功")
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"更新用户状态失败：{str(e)}")
        return APIResponse.server_error("更新用户状态失败")


# ============================================================================
# 批量操作
# ============================================================================

@users_bp.route('/batch-action', methods=['POST'])
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
            return APIResponse.bad_request("用户 ID 列表不能为空")
        
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
            f"批量{action}操作成功，共处理 {count} 个用户"
        )
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"批量操作失败：{str(e)}")
        return APIResponse.server_error("批量操作失败")


# ============================================================================
# 统计接口
# ============================================================================

@users_bp.route('/stats', methods=['GET'])
@login_required
@admin_required
def get_user_stats():
    """获取用户统计信息"""
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
        }, "获取用户统计成功")
        
    except Exception as e:
        current_app.logger.error(f"获取用户统计失败：{str(e)}")
        return APIResponse.server_error("获取用户统计失败")
