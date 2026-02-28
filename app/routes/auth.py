"""
认证路由模块
提供用户登录、登出、Token 刷新等认证功能
"""
from flask import Blueprint, request, jsonify, current_app, g
from datetime import datetime
import re

from app.models.user import User
from app.models import db
from app.utils.jwt import (
    generate_token, verify_token, refresh_token,
    get_token_from_request, create_token_response,
    TokenExpiredError, TokenInvalidError, JWTError
)
from app.utils.decorators import login_required, token_required

# 创建蓝图
auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


# ============================================================================
# 密码验证工具函数
# ============================================================================

def validate_password_strength(password: str) -> tuple:
    """
    验证密码强度
    
    密码要求：
    1. 长度至少 6 位
    
    Args:
        password: 待验证的密码
        
    Returns:
        tuple: (是否有效，错误消息)
    """
    if len(password) < 6:
        return False, "密码长度至少为 6 位"
    
    return True, "密码强度符合要求"


# ============================================================================
# 认证路由
# ============================================================================

@auth_bp.route('/register', methods=['POST'])
def register():
    """
    用户注册接口
    
    Request Body:
    {
        "username": "用户名",
        "email": "邮箱",
        "password": "密码",
        "user_type": "tenant"  # tenant-租客，landlord-房东
    }
    
    Response:
    {
        "success": true,
        "message": "注册成功",
        "data": {
            "user": {
                "id": 1,
                "username": "admin",
                "email": "admin@example.com",
                "role": "user",
                "user_type": "tenant"
            }
        }
    }
    """
    try:
        # 获取请求数据
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'invalid_request',
                    'message': '请求数据不能为空'
                }
            }), 400
        
        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '')
        user_type = data.get('user_type', 'tenant')
        
        # 参数验证
        if not username:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'validation_error',
                    'message': '用户名不能为空'
                }
            }), 400
        
        if len(username) < 3 or len(username) > 50:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'validation_error',
                    'message': '用户名长度必须在 3-50 个字符之间'
                }
            }), 400
        
        if not email:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'validation_error',
                    'message': '邮箱不能为空'
                }
            }), 400
        
        # 验证邮箱格式
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            return jsonify({
                'success': False,
                'error': {
                    'code': 'validation_error',
                    'message': '邮箱格式不正确'
                }
            }), 400
        
        if not password:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'validation_error',
                    'message': '密码不能为空'
                }
            }), 400
        
        # 验证密码强度
        is_valid, message = validate_password_strength(password)
        if not is_valid:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'weak_password',
                    'message': message
                }
            }), 400
        
        # 验证用户类型
        if user_type not in ['tenant', 'landlord']:
            user_type = 'tenant'
        
        # 检查用户名是否已存在
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'username_exists',
                    'message': '用户名已存在'
                }
            }), 400
        
        # 检查邮箱是否已存在
        existing_email = User.query.filter_by(email=email).first()
        if existing_email:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'email_exists',
                    'message': '邮箱已被注册'
                }
            }), 400
        
        # 创建用户
        user = User(
            username=username,
            email=email,
            role='user',
            user_type=user_type
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        # 生成 Token
        token = generate_token(
            user_id=user.id,
            username=user.username,
            role=user.role,
            user_type=user.user_type,
            expires_in=86400
        )
        
        current_app.logger.info(f"新用户注册：{username} ({email})")
        
        # 返回响应
        return jsonify({
            'success': True,
            'message': '注册成功',
            'data': {
                'access_token': token,
                'token_type': 'Bearer',
                'expires_in': 86400,
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'role': user.role,
                    'user_type': user.user_type
                }
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"注册失败：{str(e)}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'register_failed',
                'message': '注册失败，请稍后重试'
            }
        }), 500


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    用户登录接口
    
    Request Body:
    {
        "username": "用户名/邮箱",
        "password": "密码",
        "remember_me": true  # 可选，是否记住我（延长 Token 过期时间）
    }
    
    Response:
    {
        "success": true,
        "message": "登录成功",
        "data": {
            "access_token": "JWT Token",
            "token_type": "Bearer",
            "expires_in": 86400,
            "user": {
                "id": 1,
                "username": "admin",
                "role": "admin",
                "user_type": "tenant"
            }
        }
    }
    """
    try:
        # 获取请求数据
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'invalid_request',
                    'message': '请求数据不能为空'
                }
            }), 400
        
        username = data.get('username', '').strip()
        password = data.get('password', '')
        remember_me = data.get('remember_me', False)
        
        # 参数验证
        if not username:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'validation_error',
                    'message': '用户名不能为空'
                }
            }), 400
        
        if not password:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'validation_error',
                    'message': '密码不能为空'
                }
            }), 400
        
        # 查找用户（支持用户名或邮箱登录）
        try:
            user = User.query.filter(
                (User.username == username) | (User.email == username)
            ).first()
            current_app.logger.error(f"查询用户结果: {user}")
        except Exception as e:
            current_app.logger.error(f"查询用户失败: {str(e)}")
            return jsonify({
                'success': False,
                'error': {
                    'code': 'login_failed',
                    'message': '登录失败，请稍后重试'
                }
            }), 500
        
        if not user:
            current_app.logger.error(f"用户不存在: {username}")
            return jsonify({
                'success': False,
                'error': {
                    'code': 'invalid_credentials',
                    'message': '用户名或密码错误'
                }
            }), 401
        
        # 验证密码
        if not user.check_password(password):
            current_app.logger.error(f"密码错误: {username}")
            return jsonify({
                'success': False,
                'error': {
                    'code': 'invalid_credentials',
                    'message': '用户名或密码错误'
                }
            }), 401
        
        # 生成 Token
        expires_in = 86400 * 7 if remember_me else 86400  # 记住我则 7 天过期
        token = generate_token(
            user_id=user.id,
            username=user.username,
            role=user.role,
            user_type=user.user_type,
            expires_in=expires_in
        )
        
        # 更新最后登录时间
        # user.last_login = datetime.utcnow()
        # db.session.commit()
        
        # 记录日志
        current_app.logger.info(f"用户 {user.username} 登录成功")
        
        # 返回响应
        return jsonify({
            'success': True,
            'message': '登录成功',
            'data': create_token_response(token, {
                'user_id': user.id,
                'username': user.username,
                'role': user.role,
                'user_type': user.user_type
            }, expires_in)
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"登录失败：{str(e)}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'login_failed',
                'message': '登录失败，请稍后重试'
            }
        }), 500


@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    """
    用户登出接口
    
    由于 JWT 是无状态的，登出主要是客户端删除 Token
    此接口可用于记录登出日志或将 Token 加入黑名单（可选）
    
    Response:
    {
        "success": true,
        "message": "登出成功"
    }
    """
    try:
        user = g.current_user
        current_app.logger.info(f"用户 {user.username} 登出")
        
        # TODO: 可以将 Token 加入黑名单（使用 Redis 等缓存）
        # 当前 Token 在过期前仍然有效，但客户端应该删除 Token
        
        return jsonify({
            'success': True,
            'message': '登出成功'
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"登出失败：{str(e)}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'logout_failed',
                'message': '登出失败，请稍后重试'
            }
        }), 500


@auth_bp.route('/me', methods=['GET'])
@login_required
def get_current_user_info():
    """
    获取当前登录用户信息
    
    Response:
    {
        "success": true,
        "data": {
            "id": 1,
            "username": "admin",
            "email": "admin@example.com",
            "real_name": "张三",
            "phone": "13800138000",
            "role": "admin",
            "user_type": "tenant",
            "department": "技术部",
            "avatar": "avatar.jpg",
            "last_login": "2024-01-01T12:00:00Z"
        }
    }
    """
    try:
        user = g.current_user
        
        return jsonify({
            'success': True,
            'data': user.to_dict()
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"获取用户信息失败：{str(e)}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'get_user_info_failed',
                'message': '获取用户信息失败'
            }
        }), 500


@auth_bp.route('/me', methods=['PUT'])
@login_required
def update_current_user_info():
    """
    更新当前登录用户信息
    
    Request Body:
    {
        "real_name": "张三",
        "phone": "13800138000",
        "avatar": "avatar.jpg",
        "department": "技术部"
    }
    
    Response:
    {
        "success": true,
        "message": "用户信息更新成功",
        "data": {
            "id": 1,
            "username": "admin",
            "email": "admin@example.com",
            "real_name": "张三",
            "phone": "13800138000",
            "role": "admin",
            "user_type": "tenant"
        }
    }
    """
    try:
        user = g.current_user
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'invalid_request',
                    'message': '请求数据不能为空'
                }
            }), 400
        
        # 可更新的字段
        updatable_fields = ['real_name', 'phone', 'avatar', 'department']
        
        for field in updatable_fields:
            if field in data:
                setattr(user, field, data[field])
        
        db.session.commit()
        
        current_app.logger.info(f"用户 {user.username} 更新了个人信息")
        
        return jsonify({
            'success': True,
            'message': '用户信息更新成功',
            'data': user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"更新用户信息失败：{str(e)}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'update_user_info_failed',
                'message': '更新用户信息失败'
            }
        }), 500


@auth_bp.route('/refresh', methods=['POST'])
@token_required
def refresh_access_token():
    """
    刷新 Token 接口
    
    需要在 Authorization Header 中提供有效的 Token
    如果 Token 已过期但在宽限期内，也可以刷新
    
    Request Body (可选):
    {
        "expires_in": 86400  # 自定义新的过期时间（秒）
    }
    
    Response:
    {
        "success": true,
        "message": "Token 刷新成功",
        "data": {
            "access_token": "新的 JWT Token",
            "token_type": "Bearer",
            "expires_in": 86400,
            "user": {
                "id": 1,
                "username": "admin",
                "role": "admin",
                "user_type": "tenant"
            }
        }
    }
    """
    try:
        # 获取旧 Token
        old_token = get_token_from_request()
        
        if not old_token:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'token_missing',
                    'message': '未提供 Token'
                }
            }), 400
        
        # 获取请求参数
        data = request.get_json() or {}
        expires_in = data.get('expires_in')
        
        # 刷新 Token
        try:
            new_token = refresh_token(old_token, expires_in)
        except TokenInvalidError as e:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'token_invalid',
                    'message': str(e)
                }
            }), 400
        
        user = g.current_user
        
        # 默认过期时间
        if expires_in is None:
            expires_in = current_app.config.get('JWT_ACCESS_TOKEN_EXPIRES', 86400)
        
        current_app.logger.info(f"用户 {user.username} 刷新了 Token")
        
        return jsonify({
            'success': True,
            'message': 'Token 刷新成功',
            'data': create_token_response(new_token, {
                'user_id': user.id,
                'username': user.username,
                'role': user.role,
                'user_type': user.user_type
            }, expires_in)
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"刷新 Token 失败：{str(e)}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'refresh_token_failed',
                'message': '刷新 Token 失败'
            }
        }), 500


@auth_bp.route('/change-password', methods=['POST'])
@login_required
def change_password():
    """
    修改密码接口
    
    Request Body:
    {
        "old_password": "旧密码",
        "new_password": "新密码"
    }
    
    Response:
    {
        "success": true,
        "message": "密码修改成功"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'invalid_request',
                    'message': '请求数据不能为空'
                }
            }), 400
        
        old_password = data.get('old_password')
        new_password = data.get('new_password')
        
        if not old_password or not new_password:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'validation_error',
                    'message': '旧密码和新密码不能为空'
                }
            }), 400
        
        user = g.current_user
        
        # 验证旧密码
        if not user.check_password(old_password):
            return jsonify({
                'success': False,
                'error': {
                    'code': 'invalid_password',
                    'message': '旧密码错误'
                }
            }), 400
        
        # 验证新密码强度
        is_valid, message = validate_password_strength(new_password)
        if not is_valid:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'weak_password',
                    'message': message
                }
            }), 400
        
        # 新密码不能与旧密码相同
        if old_password == new_password:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'same_password',
                    'message': '新密码不能与旧密码相同'
                }
            }), 400
        
        # 更新密码
        user.set_password(new_password)
        db.session.commit()
        
        current_app.logger.info(f"用户 {user.username} 修改了密码")
        
        return jsonify({
            'success': True,
            'message': '密码修改成功，请重新登录'
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"修改密码失败：{str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': {
                'code': 'change_password_failed',
                'message': '修改密码失败'
            }
        }), 500


@auth_bp.route('/verify-token', methods=['POST'])
def verify_current_token():
    """
    验证当前 Token 是否有效
    
    需要在 Authorization Header 中提供 Token
    
    Response:
    {
        "success": true,
        "data": {
            "valid": true,
            "user": {
                "id": 1,
                "username": "admin",
                "role": "admin"
            },
            "expires_at": "2024-01-02T12:00:00Z"
        }
    }
    """
    try:
        token = get_token_from_request()
        
        if not token:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'token_missing',
                    'message': '未提供 Token'
                }
            }), 400
        
        try:
            payload = verify_token(token)
            user = User.query.get(payload['user_id'])
            
            if not user:
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'user_not_found',
                        'message': '用户不存在'
                    }
                }), 404
            
            return jsonify({
                'success': True,
                'data': {
                    'valid': True,
                    'user': {
                        'id': user.id,
                        'username': user.username,
                        'role': user.role,
                        'user_type': user.user_type
                    },
                    'expires_at': payload['exp'].isoformat() if 'exp' in payload else None
                }
            }), 200
            
        except TokenExpiredError:
            return jsonify({
                'success': True,
                'data': {
                    'valid': False,
                    'reason': 'token_expired',
                    'message': 'Token 已过期'
                }
            }), 200
            
        except TokenInvalidError:
            return jsonify({
                'success': True,
                'data': {
                    'valid': False,
                    'reason': 'token_invalid',
                    'message': 'Token 无效'
                }
            }), 200
        
    except Exception as e:
        current_app.logger.error(f"验证 Token 失败：{str(e)}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'verify_token_failed',
                'message': '验证 Token 失败'
            }
        }), 500


# ============================================================================
# 管理员专用接口
# ============================================================================

@auth_bp.route('/users/<int:user_id>/lock', methods=['POST'])
@login_required
def lock_user(user_id: int):
    """
    锁定用户（管理员专用）
    
    注意：此接口需要实现用户状态字段后才能完全工作
    """
    try:
        current_user = g.current_user
        
        # 检查是否为管理员
        if current_user.role != 'admin':
            return jsonify({
                'success': False,
                'error': {
                    'code': 'forbidden',
                    'message': '需要管理员权限'
                }
            }), 403
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'user_not_found',
                    'message': '用户不存在'
                }
            }), 404
        
        # TODO: 实现用户锁定逻辑
        # user.is_locked = True
        # db.session.commit()
        
        current_app.logger.info(f"管理员 {current_user.username} 锁定了用户 {user.username}")
        
        return jsonify({
            'success': True,
            'message': f'用户 {user.username} 已被锁定'
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"锁定用户失败：{str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': {
                'code': 'lock_user_failed',
                'message': '锁定用户失败'
            }
        }), 500


@auth_bp.route('/users/<int:user_id>/unlock', methods=['POST'])
@login_required
def unlock_user(user_id: int):
    """
    解锁用户（管理员专用）
    
    注意：此接口需要实现用户状态字段后才能完全工作
    """
    try:
        current_user = g.current_user
        
        # 检查是否为管理员
        if current_user.role != 'admin':
            return jsonify({
                'success': False,
                'error': {
                    'code': 'forbidden',
                    'message': '需要管理员权限'
                }
            }), 403
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'user_not_found',
                    'message': '用户不存在'
                }
            }), 404
        
        # TODO: 实现用户解锁逻辑
        # user.is_locked = False
        # db.session.commit()
        
        current_app.logger.info(f"管理员 {current_user.username} 解锁了用户 {user.username}")
        
        return jsonify({
            'success': True,
            'message': f'用户 {user.username} 已被解锁'
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"解锁用户失败：{str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': {
                'code': 'unlock_user_failed',
                'message': '解锁用户失败'
            }
        }), 500
