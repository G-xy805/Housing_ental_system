"""
统一响应格式工具模块
提供标准化的 API 响应格式和错误处理
"""
from flask import jsonify, make_response
from typing import Optional, Dict, Any, Union
from datetime import datetime


# ============================================================================
# 统一响应格式
# ============================================================================

class APIResponse:
    """
    API 响应工具类
    提供统一的响应格式
    """
    
    @staticmethod
    def success(data: Any = None, message: str = "操作成功", status_code: int = 200) -> tuple:
        """
        成功响应
        
        Args:
            data: 响应数据
            message: 成功消息
            status_code: HTTP 状态码
            
        Returns:
            tuple: (response, status_code)
        """
        response = {
            'success': True,
            'message': message,
            'data': data,
            'timestamp': datetime.utcnow().isoformat()
        }
        return jsonify(response), status_code
    
    @staticmethod
    def error(error_code: str, message: str, status_code: int = 400, data: Any = None) -> tuple:
        """
        错误响应
        
        Args:
            error_code: 错误代码
            message: 错误消息
            status_code: HTTP 状态码
            data: 附加数据
            
        Returns:
            tuple: (response, status_code)
        """
        response = {
            'success': False,
            'error': {
                'code': error_code,
                'message': message
            },
            'data': data,
            'timestamp': datetime.utcnow().isoformat()
        }
        return jsonify(response), status_code
    
    @staticmethod
    def created(data: Any = None, message: str = "创建成功") -> tuple:
        """
        创建成功响应 (201)
        
        Args:
            data: 响应数据
            message: 成功消息
            
        Returns:
            tuple: (response, status_code)
        """
        return APIResponse.success(data, message, 201)
    
    @staticmethod
    def no_content(message: str = "操作成功") -> tuple:
        """
        无内容响应 (204)
        
        Args:
            message: 成功消息
            
        Returns:
            tuple: (response, status_code)
        """
        return APIResponse.success(None, message, 204)
    
    @staticmethod
    def unauthorized(message: str = "未授权访问") -> tuple:
        """
        未授权响应 (401)
        
        Args:
            message: 错误消息
            
        Returns:
            tuple: (response, status_code)
        """
        return APIResponse.error('unauthorized', message, 401)
    
    @staticmethod
    def forbidden(message: str = "禁止访问") -> tuple:
        """
        禁止访问响应 (403)
        
        Args:
            message: 错误消息
            
        Returns:
            tuple: (response, status_code)
        """
        return APIResponse.error('forbidden', message, 403)
    
    @staticmethod
    def not_found(message: str = "资源不存在") -> tuple:
        """
        资源不存在响应 (404)
        
        Args:
            message: 错误消息
            
        Returns:
            tuple: (response, status_code)
        """
        return APIResponse.error('not_found', message, 404)
    
    @staticmethod
    def bad_request(message: str = "请求参数错误", data: Any = None) -> tuple:
        """
        错误请求响应 (400)
        
        Args:
            message: 错误消息
            data: 附加数据（如验证错误详情）
            
        Returns:
            tuple: (response, status_code)
        """
        return APIResponse.error('bad_request', message, 400, data)
    
    @staticmethod
    def validation_error(message: str = "参数验证失败", errors: Dict = None) -> tuple:
        """
        参数验证错误响应 (422)
        
        Args:
            message: 错误消息
            errors: 详细验证错误信息
            
        Returns:
            tuple: (response, status_code)
        """
        return APIResponse.error('validation_error', message, 422, errors)
    
    @staticmethod
    def server_error(message: str = "服务器内部错误") -> tuple:
        """
        服务器错误响应 (500)
        
        Args:
            message: 错误消息
            
        Returns:
            tuple: (response, status_code)
        """
        return APIResponse.error('internal_server_error', message, 500)


# ============================================================================
# 认证相关错误响应
# ============================================================================

class AuthResponse:
    """
    认证相关响应工具类
    """
    
    @staticmethod
    def login_success(token: str, user: Dict, expires_in: int) -> tuple:
        """
        登录成功响应
        
        Args:
            token: JWT Token
            user: 用户信息
            expires_in: Token 过期时间（秒）
            
        Returns:
            tuple: (response, status_code)
        """
        data = {
            'access_token': token,
            'token_type': 'Bearer',
            'expires_in': expires_in,
            'user': user
        }
        return APIResponse.success(data, "登录成功", 200)
    
    @staticmethod
    def login_failed(message: str = "用户名或密码错误") -> tuple:
        """
        登录失败响应
        
        Args:
            message: 错误消息
            
        Returns:
            tuple: (response, status_code)
        """
        return APIResponse.error('invalid_credentials', message, 401)
    
    @staticmethod
    def logout_success() -> tuple:
        """
        登出成功响应
        
        Returns:
            tuple: (response, status_code)
        """
        return APIResponse.success(None, "登出成功", 200)
    
    @staticmethod
    def token_refreshed(token: str, user: Dict, expires_in: int) -> tuple:
        """
        Token 刷新成功响应
        
        Args:
            token: 新的 JWT Token
            user: 用户信息
            expires_in: Token 过期时间（秒）
            
        Returns:
            tuple: (response, status_code)
        """
        data = {
            'access_token': token,
            'token_type': 'Bearer',
            'expires_in': expires_in,
            'user': user
        }
        return APIResponse.success(data, "Token 刷新成功", 200)
    
    @staticmethod
    def token_expired(message: str = "Token 已过期") -> tuple:
        """
        Token 过期响应
        
        Args:
            message: 错误消息
            
        Returns:
            tuple: (response, status_code)
        """
        return APIResponse.error('token_expired', message, 401)
    
    @staticmethod
    def token_invalid(message: str = "Token 无效") -> tuple:
        """
        Token 无效响应
        
        Args:
            message: 错误消息
            
        Returns:
            tuple: (response, status_code)
        """
        return APIResponse.error('token_invalid', message, 401)
    
    @staticmethod
    def token_missing(message: str = "未提供 Token") -> tuple:
        """
        Token 缺失响应
        
        Args:
            message: 错误消息
            
        Returns:
            tuple: (response, status_code)
        """
        return APIResponse.error('token_missing', message, 401)
    
    @staticmethod
    def permission_denied(message: str = "没有权限访问此资源") -> tuple:
        """
        权限拒绝响应
        
        Args:
            message: 错误消息
            
        Returns:
            tuple: (response, status_code)
        """
        return APIResponse.error('permission_denied', message, 403)


# ============================================================================
# 分页响应
# ============================================================================

class PaginationResponse:
    """
    分页响应工具类
    """
    
    @staticmethod
    def paginated_success(data: list, pagination: Dict, message: str = "获取成功") -> tuple:
        """
        分页数据成功响应
        
        Args:
            data: 数据列表
            pagination: 分页信息 {page, per_page, total, pages}
            message: 成功消息
            
        Returns:
            tuple: (response, status_code)
        """
        response_data = {
            'items': data,
            'pagination': pagination
        }
        return APIResponse.success(response_data, message, 200)
    
    @staticmethod
    def from_query(query, page: int = 1, per_page: int = 20, message: str = "获取成功") -> tuple:
        """
        从 SQLAlchemy 查询对象创建分页响应
        
        Args:
            query: SQLAlchemy 查询对象
            page: 页码
            per_page: 每页数量
            message: 成功消息
            
        Returns:
            tuple: (response, status_code)
        """
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        data = [item.to_dict() for item in pagination.items]
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
        
        return PaginationResponse.paginated_success(data, pagination_info, message)


# ============================================================================
# 错误处理器注册
# ============================================================================

def register_error_handlers(app):
    """
    注册统一的错误处理器到 Flask 应用
    
    Args:
        app: Flask 应用实例
    """
    
    @app.errorhandler(400)
    def handle_bad_request(error):
        """处理 400 错误"""
        return APIResponse.bad_request(str(error) or "请求参数错误")
    
    @app.errorhandler(401)
    def handle_unauthorized(error):
        """处理 401 错误"""
        return APIResponse.unauthorized("未授权访问")
    
    @app.errorhandler(403)
    def handle_forbidden(error):
        """处理 403 错误"""
        return APIResponse.forbidden("禁止访问")
    
    @app.errorhandler(404)
    def handle_not_found(error):
        """处理 404 错误"""
        return APIResponse.not_found("资源不存在")
    
    @app.errorhandler(405)
    def handle_method_not_allowed(error):
        """处理 405 错误"""
        return APIResponse.bad_request("请求方法不允许")
    
    @app.errorhandler(422)
    def handle_validation_error(error):
        """处理 422 验证错误"""
        return APIResponse.validation_error("参数验证失败")
    
    @app.errorhandler(500)
    def handle_internal_error(error):
        """处理 500 错误"""
        app.logger.error(f"服务器内部错误：{str(error)}")
        return APIResponse.server_error()
    
    @app.errorhandler(Exception)
    def handle_generic_error(error):
        """处理未分类的异常"""
        app.logger.error(f"未处理的异常：{str(error)}")
        return APIResponse.server_error()


# ============================================================================
# 响应格式化辅助函数
# ============================================================================

def format_user_response(user) -> Dict:
    """
    格式化用户响应
    
    Args:
        user: 用户模型对象
        
    Returns:
        dict: 用户响应数据
    """
    return {
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'real_name': user.real_name,
        'phone': user.phone,
        'role': user.role,
        'user_type': user.user_type,
        'department': user.department,
        'avatar': user.avatar,
        'last_login': user.last_login.isoformat() if user.last_login else None,
        'created_at': user.created_at.isoformat() if user.created_at else None
    }


def format_error_response(error_code: str, message: str, details: Dict = None) -> Dict:
    """
    格式化错误响应
    
    Args:
        error_code: 错误代码
        message: 错误消息
        details: 详细错误信息
        
    Returns:
        dict: 错误响应数据
    """
    response = {
        'success': False,
        'error': {
            'code': error_code,
            'message': message
        },
        'timestamp': datetime.utcnow().isoformat()
    }
    
    if details:
        response['data'] = details
    
    return response
