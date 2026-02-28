"""
应用工具包
提供 JWT、认证装饰器、响应格式等工具模块
"""
from app.utils.jwt import (
    generate_token,
    verify_token,
    refresh_token,
    get_token_from_request,
    get_current_user,
    create_token_response,
    JWTError,
    TokenExpiredError,
    TokenInvalidError,
    TokenMissingError
)

from app.utils.decorators import (
    token_required,
    login_required,
    admin_required,
    role_required,
    permission_required,
    optional_login
)

from app.utils.responses import (
    APIResponse,
    AuthResponse,
    PaginationResponse,
    register_error_handlers,
    format_user_response,
    format_error_response
)

__all__ = [
    # JWT
    'generate_token',
    'verify_token',
    'refresh_token',
    'get_token_from_request',
    'get_current_user',
    'create_token_response',
    'JWTError',
    'TokenExpiredError',
    'TokenInvalidError',
    'TokenMissingError',
    
    # Decorators
    'token_required',
    'login_required',
    'admin_required',
    'role_required',
    'permission_required',
    'optional_login',
    
    # Responses
    'APIResponse',
    'AuthResponse',
    'PaginationResponse',
    'register_error_handlers',
    'format_user_response',
    'format_error_response'
]