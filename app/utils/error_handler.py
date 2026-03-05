"""
全局错误处理中间件模块
提供统一的错误处理、日志记录和响应格式化
"""
import logging
import traceback
import json
from datetime import datetime
from functools import wraps
from flask import Flask, request, jsonify, g, current_app
from typing import Optional, Dict, Any, Callable
from sqlalchemy.exc import SQLAlchemyError

from app.utils.exceptions import BaseException as AppBaseException
from app.utils.responses import APIResponse


# ============================================================================
# 错误日志记录器配置
# ============================================================================

def setup_error_logger(app: Flask):
    """
    配置错误日志记录器
    
    Args:
        app: Flask 应用实例
    """
    # 创建错误日志记录器
    error_logger = logging.getLogger('error_handler')
    error_logger.setLevel(logging.ERROR)
    
    # 如果日志目录不存在，创建它
    import os
    log_dir = os.path.dirname(app.config.get('LOG_FILE', 'logs/app.log'))
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # 错误日志文件处理器
    from logging.handlers import RotatingFileHandler
    error_log_file = os.path.join(
        os.path.dirname(app.config.get('LOG_FILE', 'logs/app.log')),
        'errors.log'
    )
    
    file_handler = RotatingFileHandler(
        error_log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=10
    )
    file_handler.setLevel(logging.ERROR)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s\n'
        'Request ID: %(request_id)s\n'
        'User: %(user_info)s\n'
        'Endpoint: %(endpoint)s\n'
        'Method: %(method)s\n'
        'URL: %(url)s\n'
        'IP: %(ip)s\n'
        'Traceback:\n%(traceback)s\n'
        + '=' * 80 + '\n'
    ))
    
    error_logger.addHandler(file_handler)
    
    return error_logger


# ============================================================================
# 错误日志记录函数
# ============================================================================

def log_error(
    error: Exception,
    request_id: Optional[str] = None,
    user_info: Optional[str] = None,
    include_traceback: bool = True
):
    """
    记录错误日志
    
    Args:
        error: 异常对象
        request_id: 请求 ID
        user_info: 用户信息
        include_traceback: 是否包含堆栈跟踪
    """
    logger = logging.getLogger('error_handler')
    
    # 获取请求信息
    try:
        endpoint = request.endpoint or 'unknown'
        method = request.method or 'unknown'
        url = request.url or 'unknown'
        ip = request.remote_addr or 'unknown'
    except RuntimeError:
        # 在应用上下文之外
        endpoint = 'unknown'
        method = 'unknown'
        url = 'unknown'
        ip = 'unknown'
    
    # 构建日志信息
    log_data = {
        'request_id': request_id or getattr(g, 'request_id', 'N/A'),
        'user_info': user_info or getattr(g, 'username', 'anonymous'),
        'endpoint': endpoint,
        'method': method,
        'url': url,
        'ip': ip,
        'traceback': traceback.format_exc() if include_traceback else str(error)
    }
    
    # 记录错误
    logger.error(
        f"{error.__class__.__name__}: {str(error)}",
        extra=log_data
    )


def log_request_context():
    """
    记录请求上下文信息
    
    Returns:
        dict: 请求上下文信息
    """
    context = {
        'timestamp': datetime.utcnow().isoformat(),
        'request_id': getattr(g, 'request_id', None),
        'user_id': getattr(g, 'user_id', None),
        'username': getattr(g, 'username', None),
        'user_role': getattr(g, 'user_role', None),
        'endpoint': request.endpoint,
        'method': request.method,
        'url': request.url,
        'path': request.path,
        'query_string': request.query_string.decode('utf-8') if request.query_string else None,
        'ip_address': request.remote_addr,
        'user_agent': request.user_agent.string if request.user_agent else None,
        'referrer': request.referrer,
    }
    
    # 记录请求体（排除敏感信息）
    if request.is_json:
        try:
            body = request.get_json()
            # 移除敏感字段
            if isinstance(body, dict):
                body = body.copy()
                for field in ['password', 'token', 'secret', 'api_key']:
                    if field in body:
                        body[field] = '***REDACTED***'
            context['request_body'] = body
        except:
            context['request_body'] = 'Failed to parse JSON body'
    elif request.data:
        context['request_body_size'] = len(request.data)
    
    return context


# ============================================================================
# 错误处理器注册
# ============================================================================

def register_error_handlers(app: Flask):
    """
    注册全局错误处理器
    
    Args:
        app: Flask 应用实例
    """
    # 配置错误日志记录器
    error_logger = setup_error_logger(app)
    
    # 生成请求 ID
    @app.before_request
    def before_request():
        """请求前处理：生成请求 ID"""
        import uuid
        g.request_id = str(uuid.uuid4())
        g.request_start_time = datetime.utcnow()
    
    # 记录请求后处理
    @app.after_request
    def after_request(response):
        """请求后处理：记录请求日志"""
        # 计算请求处理时间
        if hasattr(g, 'request_start_time'):
            duration = (datetime.utcnow() - g.request_start_time).total_seconds()
            response.headers['X-Request-ID'] = g.request_id
            response.headers['X-Response-Time'] = f"{duration:.3f}s"
        
        return response
    
    # 处理应用自定义异常
    @app.errorhandler(AppBaseException)
    def handle_app_exception(error):
        """处理应用自定义异常"""
        # 记录错误日志
        log_error(
            error,
            request_id=getattr(g, 'request_id', None),
            user_info=getattr(g, 'username', None)
        )
        
        # 返回错误响应
        response = error.to_dict()
        response['error']['request_id'] = getattr(g, 'request_id', None)
        
        return jsonify(response), error.status_code
    
    # 处理 SQLAlchemy 异常
    @app.errorhandler(SQLAlchemyError)
    def handle_sqlalchemy_error(error):
        """处理 SQLAlchemy 数据库异常"""
        from app.utils.exceptions import DatabaseException
        
        # 记录详细错误日志
        log_error(
            error,
            request_id=getattr(g, 'request_id', None),
            user_info=getattr(g, 'username', None)
        )
        
        # 回滚事务
        from app.models import db
        try:
            db.session.rollback()
        except:
            pass
        
        # 返回通用数据库错误
        return jsonify({
            'success': False,
            'error': {
                'code': 'database_error',
                'message': '数据库操作失败',
                'request_id': getattr(g, 'request_id', None)
            }
        }), 500
    
    # 处理 400 错误
    @app.errorhandler(400)
    def handle_bad_request(error):
        """处理 400 错误"""
        log_error(
            error,
            request_id=getattr(g, 'request_id', None),
            user_info=getattr(g, 'username', None),
            include_traceback=False
        )
        
        return jsonify({
            'success': False,
            'error': {
                'code': 'bad_request',
                'message': str(error) or '请求参数错误',
                'request_id': getattr(g, 'request_id', None)
            }
        }), 400
    
    # 处理 401 错误
    @app.errorhandler(401)
    def handle_unauthorized(error):
        """处理 401 错误"""
        log_error(
            error,
            request_id=getattr(g, 'request_id', None),
            user_info=getattr(g, 'username', None),
            include_traceback=False
        )
        
        return jsonify({
            'success': False,
            'error': {
                'code': 'unauthorized',
                'message': '未授权访问，请先登录',
                'request_id': getattr(g, 'request_id', None)
            }
        }), 401
    
    # 处理 403 错误
    @app.errorhandler(403)
    def handle_forbidden(error):
        """处理 403 错误"""
        log_error(
            error,
            request_id=getattr(g, 'request_id', None),
            user_info=getattr(g, 'username', None),
            include_traceback=False
        )
        
        return jsonify({
            'success': False,
            'error': {
                'code': 'forbidden',
                'message': '禁止访问，权限不足',
                'request_id': getattr(g, 'request_id', None)
            }
        }), 403
    
    # 处理 404 错误
    @app.errorhandler(404)
    def handle_not_found(error):
        """处理 404 错误"""
        log_error(
            error,
            request_id=getattr(g, 'request_id', None),
            user_info=getattr(g, 'username', None),
            include_traceback=False
        )
        
        return jsonify({
            'success': False,
            'error': {
                'code': 'not_found',
                'message': f'请求的资源不存在：{request.path}',
                'request_id': getattr(g, 'request_id', None)
            }
        }), 404
    
    # 处理 405 错误
    @app.errorhandler(405)
    def handle_method_not_allowed(error):
        """处理 405 错误"""
        log_error(
            error,
            request_id=getattr(g, 'request_id', None),
            user_info=getattr(g, 'username', None),
            include_traceback=False
        )
        
        return jsonify({
            'success': False,
            'error': {
                'code': 'method_not_allowed',
                'message': f'请求方法 {request.method} 不允许',
                'request_id': getattr(g, 'request_id', None)
            }
        }), 405
    
    # 处理 422 错误
    @app.errorhandler(422)
    def handle_validation_error(error):
        """处理 422 验证错误"""
        log_error(
            error,
            request_id=getattr(g, 'request_id', None),
            user_info=getattr(g, 'username', None),
            include_traceback=False
        )
        
        return jsonify({
            'success': False,
            'error': {
                'code': 'validation_error',
                'message': '参数验证失败',
                'request_id': getattr(g, 'request_id', None)
            }
        }), 422
    
    # 处理 429 错误（请求过于频繁）
    @app.errorhandler(429)
    def handle_too_many_requests(error):
        """处理 429 错误"""
        log_error(
            error,
            request_id=getattr(g, 'request_id', None),
            user_info=getattr(g, 'username', None),
            include_traceback=False
        )
        
        return jsonify({
            'success': False,
            'error': {
                'code': 'too_many_requests',
                'message': '请求过于频繁，请稍后再试',
                'request_id': getattr(g, 'request_id', None)
            }
        }), 429
    
    # 处理 500 错误
    @app.errorhandler(500)
    def handle_internal_error(error):
        """处理 500 错误"""
        log_error(
            error,
            request_id=getattr(g, 'request_id', None),
            user_info=getattr(g, 'username', None)
        )
        
        # 回滚事务
        from app.models import db
        try:
            db.session.rollback()
        except:
            pass
        
        return jsonify({
            'success': False,
            'error': {
                'code': 'internal_server_error',
                'message': '服务器内部错误',
                'request_id': getattr(g, 'request_id', None)
            }
        }), 500
    
    # 处理所有其他异常
    @app.errorhandler(Exception)
    def handle_generic_error(error):
        """处理未分类的异常"""
        # 记录详细错误日志
        log_error(
            error,
            request_id=getattr(g, 'request_id', None),
            user_info=getattr(g, 'username', None)
        )
        
        # 回滚事务
        from app.models import db
        try:
            db.session.rollback()
        except:
            pass
        
        # 生产环境不返回详细错误信息
        if app.config.get('DEBUG'):
            error_message = str(error)
        else:
            error_message = '服务器内部错误'
        
        return jsonify({
            'success': False,
            'error': {
                'code': 'internal_error',
                'message': error_message,
                'request_id': getattr(g, 'request_id', None)
            }
        }), 500


# ============================================================================
# 错误处理装饰器
# ============================================================================

def handle_errors(f: Callable) -> Callable:
    """
    错误处理装饰器
    
    自动捕获异常并返回标准化的错误响应
    
    Args:
        f: 被装饰的函数
        
    Returns:
        装饰后的函数
        
    Example:
        @handle_errors
        def get_user(user_id):
            user = User.query.get(user_id)
            if not user:
                raise ResourceNotFoundException('用户', user_id)
            return user.to_dict()
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
            
        except AppBaseException as e:
            # 应用自定义异常
            log_error(
                e,
                request_id=getattr(g, 'request_id', None),
                user_info=getattr(g, 'username', None),
                include_traceback=False
            )
            
            response = e.to_dict()
            response['error']['request_id'] = getattr(g, 'request_id', None)
            
            return jsonify(response), e.status_code
            
        except SQLAlchemyError as e:
            # 数据库异常
            log_error(
                e,
                request_id=getattr(g, 'request_id', None),
                user_info=getattr(g, 'username', None)
            )
            
            # 回滚事务
            from app.models import db
            try:
                db.session.rollback()
            except:
                pass
            
            return jsonify({
                'success': False,
                'error': {
                    'code': 'database_error',
                    'message': '数据库操作失败',
                    'request_id': getattr(g, 'request_id', None)
                }
            }), 500
            
        except Exception as e:
            # 其他异常
            log_error(
                e,
                request_id=getattr(g, 'request_id', None),
                user_info=getattr(g, 'username', None)
            )
            
            # 回滚事务
            from app.models import db
            try:
                db.session.rollback()
            except:
                pass
            
            return jsonify({
                'success': False,
                'error': {
                    'code': 'internal_error',
                    'message': '操作失败',
                    'request_id': getattr(g, 'request_id', None)
                }
            }), 500
    
    return decorated_function


# ============================================================================
# 错误统计和分析
# ============================================================================

class ErrorStatistics:
    """错误统计类"""
    
    def __init__(self):
        self.errors = []
        self.max_errors = 1000  # 最多保存的错误数量
    
    def record_error(
        self,
        error_type: str,
        error_code: str,
        endpoint: str,
        user_id: Optional[int] = None
    ):
        """
        记录错误统计
        
        Args:
            error_type: 错误类型
            error_code: 错误代码
            endpoint: 端点
            user_id: 用户 ID
        """
        error_record = {
            'timestamp': datetime.utcnow().isoformat(),
            'error_type': error_type,
            'error_code': error_code,
            'endpoint': endpoint,
            'user_id': user_id
        }
        
        self.errors.append(error_record)
        
        # 限制错误数量
        if len(self.errors) > self.max_errors:
            self.errors = self.errors[-self.max_errors:]
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取错误统计信息
        
        Returns:
            dict: 统计信息
        """
        if not self.errors:
            return {
                'total_errors': 0,
                'errors_by_type': {},
                'errors_by_endpoint': {},
                'recent_errors': []
            }
        
        # 按错误类型统计
        errors_by_type = {}
        for error in self.errors:
            error_type = error['error_type']
            errors_by_type[error_type] = errors_by_type.get(error_type, 0) + 1
        
        # 按端点统计
        errors_by_endpoint = {}
        for error in self.errors:
            endpoint = error['endpoint']
            errors_by_endpoint[endpoint] = errors_by_endpoint.get(endpoint, 0) + 1
        
        return {
            'total_errors': len(self.errors),
            'errors_by_type': errors_by_type,
            'errors_by_endpoint': errors_by_endpoint,
            'recent_errors': self.errors[-10:]  # 最近 10 个错误
        }
    
    def clear_statistics(self):
        """清除统计信息"""
        self.errors = []


# 全局错误统计实例
error_statistics = ErrorStatistics()


def get_error_statistics() -> Dict[str, Any]:
    """
    获取错误统计信息
    
    Returns:
        dict: 错误统计信息
    """
    return error_statistics.get_statistics()


def clear_error_statistics():
    """清除错误统计信息"""
    error_statistics.clear_statistics()
