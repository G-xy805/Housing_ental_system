"""
认证装饰器模块
提供登录验证、权限验证等装饰器
"""
from functools import wraps
from flask import request, jsonify, g, current_app
from typing import Optional, List, Union

from .jwt import get_token_from_request, verify_token, JWTError, TokenExpiredError, TokenInvalidError, TokenMissingError
from app.models.user import User


def token_required(f):
    """
    Token 验证装饰器
    验证请求中的 JWT Token 是否有效，并将用户信息存入 Flask g 对象
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = get_token_from_request()
        
        if not token:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'token_missing',
                    'message': '未提供认证 Token，请在 Authorization Header 中添加 Bearer Token'
                }
            }), 401
        
        try:
            payload = verify_token(token)
            
            # 从数据库获取用户信息
            user = User.query.get(payload['user_id'])
            if not user:
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'user_not_found',
                        'message': '用户不存在'
                    }
                }), 401
            
            # 将用户信息存入 g 对象，供后续使用
            g.current_user = user
            g.user_id = user.id
            g.username = user.username
            g.user_role = user.role
            g.user_type = user.user_type
            
            return f(*args, **kwargs)
            
        except TokenExpiredError as e:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'token_expired',
                    'message': str(e)
                }
            }), 401
            
        except TokenInvalidError as e:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'token_invalid',
                    'message': str(e)
                }
            }), 401
            
        except JWTError as e:
            return jsonify({
                'success': False,
                'error': {
                    'code': e.code,
                    'message': e.message
                }
            }), 401
            
        except Exception as e:
            current_app.logger.error(f"Token 验证失败：{str(e)}")
            return jsonify({
                'success': False,
                'error': {
                    'code': 'token_verification_failed',
                    'message': 'Token 验证失败'
                }
            }), 500
    
    return decorated


def login_required(f):
    """
    登录验证装饰器
    要求用户必须登录才能访问
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = get_token_from_request()
        
        if not token:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'unauthorized',
                    'message': '请先登录'
                }
            }), 401
        
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
                }), 401
            
            g.current_user = user
            g.user_id = user.id
            g.username = user.username
            g.user_role = user.role
            g.user_type = user.user_type
            
            return f(*args, **kwargs)
            
        except TokenExpiredError:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'token_expired',
                    'message': '登录已过期，请重新登录'
                }
            }), 401
            
        except TokenInvalidError:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'token_invalid',
                    'message': '无效的登录凭证'
                }
            }), 401
    
    return decorated


def admin_required(f):
    """
    管理员权限装饰器
    要求用户必须是管理员才能访问
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = get_token_from_request()
        
        if not token:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'unauthorized',
                    'message': '请先登录'
                }
            }), 401
        
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
                }), 401
            
            # 检查是否为管理员
            if user.role != 'admin':
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'forbidden',
                        'message': '需要管理员权限才能访问此资源'
                    }
                }), 403
            
            g.current_user = user
            g.user_id = user.id
            g.username = user.username
            g.user_role = user.role
            g.user_type = user.user_type
            
            return f(*args, **kwargs)
            
        except TokenExpiredError:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'token_expired',
                    'message': '登录已过期，请重新登录'
                }
            }), 401
            
        except TokenInvalidError:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'token_invalid',
                    'message': '无效的登录凭证'
                }
            }), 401
    
    return decorated


def role_required(*roles: str):
    """
    角色权限装饰器
    要求用户必须具有指定角色之一才能访问
    
    Args:
        roles: 允许访问的角色列表，如 @role_required('admin', 'staff')
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            token = get_token_from_request()
            
            if not token:
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'unauthorized',
                        'message': '请先登录'
                    }
                }), 401
            
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
                    }), 401
                
                # 检查用户角色是否在允许的角色列表中
                if user.role not in roles:
                    return jsonify({
                        'success': False,
                        'error': {
                            'code': 'forbidden',
                            'message': f'需要以下角色权限才能访问：{", ".join(roles)}'
                        }
                    }), 403
                
                g.current_user = user
                g.user_id = user.id
                g.username = user.username
                g.user_role = user.role
                g.user_type = user.user_type
                
                return f(*args, **kwargs)
                
            except TokenExpiredError:
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'token_expired',
                        'message': '登录已过期，请重新登录'
                    }
                }), 401
                
            except TokenInvalidError:
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'token_invalid',
                        'message': '无效的登录凭证'
                    }
                }), 401
        
        return decorated
    return decorator


def permission_required(permission: str):
    """
    权限验证装饰器
    根据用户角色检查是否有指定权限
    
    Args:
        permission: 权限类型 ('view', 'create', 'edit', 'delete')
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            token = get_token_from_request()
            
            if not token:
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'unauthorized',
                        'message': '请先登录'
                    }
                }), 401
            
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
                    }), 401
                
                # 检查用户是否有指定权限
                if not user.has_permission(permission):
                    return jsonify({
                        'success': False,
                        'error': {
                            'code': 'forbidden',
                            'message': f'没有 {permission} 权限'
                        }
                    }), 403
                
                g.current_user = user
                g.user_id = user.id
                g.username = user.username
                g.user_role = user.role
                g.user_type = user.user_type
                
                return f(*args, **kwargs)
                
            except TokenExpiredError:
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'token_expired',
                        'message': '登录已过期，请重新登录'
                    }
                }), 401
                
            except TokenInvalidError:
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'token_invalid',
                        'message': '无效的登录凭证'
                    }
                }), 401
        
        return decorated
    return decorator


def optional_login(f):
    """
    可选登录装饰器
    如果用户已登录则加载用户信息，未登录也可以访问
    用于公开但登录后可见更多内容的接口
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = get_token_from_request()
        
        if token:
            try:
                payload = verify_token(token)
                user = User.query.get(payload['user_id'])
                
                if user:
                    g.current_user = user
                    g.user_id = user.id
                    g.username = user.username
                    g.user_role = user.role
                    g.user_type = user.user_type
            except (TokenExpiredError, TokenInvalidError):
                # Token 无效时忽略，作为未登录处理
                pass
        
        return f(*args, **kwargs)
    
    return decorated
