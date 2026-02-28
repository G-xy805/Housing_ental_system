"""
JWT 工具模块
提供 JWT Token 的生成、验证和刷新功能
"""
import jwt
from datetime import datetime, timedelta
from functools import wraps
from flask import current_app, request, jsonify, g
from typing import Optional, Dict, Any


class JWTError(Exception):
    """JWT 相关异常基类"""
    def __init__(self, message: str = "JWT 错误", code: str = "jwt_error"):
        self.message = message
        self.code = code
        super().__init__(self.message)


class TokenExpiredError(JWTError):
    """Token 过期异常"""
    def __init__(self, message: str = "Token 已过期"):
        super().__init__(message, "token_expired")


class TokenInvalidError(JWTError):
    """Token 无效异常"""
    def __init__(self, message: str = "Token 无效"):
        super().__init__(message, "token_invalid")


class TokenMissingError(JWTError):
    """Token 缺失异常"""
    def __init__(self, message: str = "未提供 Token"):
        super().__init__(message, "token_missing")


def generate_token(user_id: int, username: str, role: str = 'staff', 
                   user_type: str = 'tenant', expires_in: int = None) -> str:
    """
    生成 JWT Token
    
    Args:
        user_id: 用户 ID
        username: 用户名
        role: 用户角色 (admin/staff)
        user_type: 用户类型
        expires_in: 过期时间（秒），默认从配置读取
        
    Returns:
        str: JWT Token 字符串
    """
    if expires_in is None:
        expires_in = current_app.config.get('JWT_ACCESS_TOKEN_EXPIRES', 86400)  # 默认 24 小时
    
    payload = {
        'user_id': user_id,
        'username': username,
        'role': role,
        'user_type': user_type,
        'iat': datetime.utcnow(),
        'exp': datetime.utcnow() + timedelta(seconds=expires_in)
    }
    
    secret_key = current_app.config.get('JWT_SECRET_KEY')
    algorithm = current_app.config.get('JWT_ALGORITHM', 'HS256')
    
    token = jwt.encode(payload, secret_key, algorithm=algorithm)
    return token


def verify_token(token: str) -> Dict[str, Any]:
    """
    验证 JWT Token
    
    Args:
        token: JWT Token 字符串
        
    Returns:
        dict: Token 载荷信息
        
    Raises:
        TokenExpiredError: Token 已过期
        TokenInvalidError: Token 无效
    """
    try:
        secret_key = current_app.config.get('JWT_SECRET_KEY')
        algorithms = current_app.config.get('JWT_ALGORITHMS', ['HS256'])
        
        payload = jwt.decode(token, secret_key, algorithms=algorithms)
        return payload
        
    except jwt.ExpiredSignatureError:
        raise TokenExpiredError("Token 已过期，请重新登录")
    except jwt.InvalidTokenError as e:
        raise TokenInvalidError(f"Token 无效：{str(e)}")


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """
    解码 Token（不验证过期）
    
    Args:
        token: JWT Token 字符串
        
    Returns:
        dict: Token 载荷信息，失败返回 None
    """
    try:
        secret_key = current_app.config.get('JWT_SECRET_KEY')
        algorithms = current_app.config.get('JWT_ALGORITHMS', ['HS256'])
        
        # options 禁用过期验证
        payload = jwt.decode(token, secret_key, algorithms=algorithms, options={"verify_exp": False})
        return payload
    except jwt.InvalidTokenError:
        return None


def refresh_token(old_token: str, expires_in: int = None) -> str:
    """
    刷新 Token
    
    Args:
        old_token: 旧的 JWT Token
        expires_in: 新的过期时间（秒）
        
    Returns:
        str: 新的 JWT Token
        
    Raises:
        TokenInvalidError: 旧 Token 无效
    """
    payload = decode_token(old_token)
    if not payload:
        raise TokenInvalidError("无法刷新 Token，请重新登录")
    
    # 生成新 Token，保留用户信息
    return generate_token(
        user_id=payload['user_id'],
        username=payload['username'],
        role=payload.get('role', 'staff'),
        user_type=payload.get('user_type', 'tenant'),
        expires_in=expires_in
    )


def get_token_from_request() -> Optional[str]:
    """
    从请求中提取 Token
    
    支持以下格式：
    1. Authorization Header: Bearer <token>
    2. Query Parameter: token=<token>
    3. Form Data: token=<token>
    
    Returns:
        str: Token 字符串，未找到返回 None
    """
    # 1. 从 Authorization Header 获取
    auth_header = request.headers.get('Authorization')
    if auth_header:
        parts = auth_header.split()
        if len(parts) == 2 and parts[0].lower() == 'bearer':
            return parts[1]
    
    # 2. 从查询参数获取
    token = request.args.get('token')
    if token:
        return token
    
    # 3. 从表单数据获取
    token = request.form.get('token')
    if token:
        return token
    
    return None


def get_current_user() -> Optional[Dict[str, Any]]:
    """
    获取当前登录用户信息
    
    Returns:
        dict: 用户信息，未登录返回 None
    """
    token = get_token_from_request()
    if not token:
        return None
    
    try:
        payload = verify_token(token)
        return {
            'user_id': payload['user_id'],
            'username': payload['username'],
            'role': payload.get('role', 'staff'),
            'user_type': payload.get('user_type', 'tenant')
        }
    except JWTError:
        return None


def create_token_response(token: str, user: Dict[str, Any], expires_in: int = None) -> Dict[str, Any]:
    """
    创建统一的 Token 响应格式
    
    Args:
        token: JWT Token
        user: 用户信息
        expires_in: Token 过期时间（秒）
        
    Returns:
        dict: 响应数据
    """
    if expires_in is None:
        expires_in = current_app.config.get('JWT_ACCESS_TOKEN_EXPIRES', 86400)
    
    return {
        'access_token': token,
        'token_type': 'Bearer',
        'expires_in': expires_in,
        'user': {
            'id': user['user_id'],
            'username': user['username'],
            'role': user['role'],
            'user_type': user['user_type']
        }
    }
