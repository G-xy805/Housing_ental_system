"""
常用工具函数
"""
import os
import uuid
from datetime import datetime
from functools import wraps
from flask import request, jsonify, current_app, g
import jwt


def generate_unique_id(prefix=''):
    """
    生成唯一 ID
    
    Args:
        prefix: ID 前缀
    
    Returns:
        唯一 ID 字符串
    """
    unique_id = f"{prefix}{datetime.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:8].upper()}"
    return unique_id


def allowed_file(filename, allowed_extensions=None):
    """
    检查文件扩展名是否允许
    
    Args:
        filename: 文件名
        allowed_extensions: 允许的扩展名集合
    
    Returns:
        bool
    """
    if allowed_extensions is None:
        allowed_extensions = current_app.config.get('ALLOWED_EXTENSIONS', set())
    
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions


def save_uploaded_file(file, folder='uploads'):
    """
    保存上传的文件
    
    Args:
        file: 文件对象
        folder: 保存文件夹
    
    Returns:
        文件路径或 None
    """
    if file and allowed_file(file.filename):
        # 生成安全的文件名
        ext = file.filename.rsplit('.', 1)[1].lower()
        filename = f"{uuid.uuid4().hex}.{ext}"
        
        # 确保目录存在
        folder_path = os.path.join(current_app.config['UPLOAD_FOLDER'], folder)
        os.makedirs(folder_path, exist_ok=True)
        
        # 保存文件
        file_path = os.path.join(folder_path, filename)
        file.save(file_path)
        
        return os.path.join(folder, filename)
    
    return None


def login_required(f):
    """
    登录验证装饰器
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = None
        
        # 从 Authorization header 获取 token
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(' ')[1]  # Bearer <token>
            except IndexError:
                return jsonify({'error': '无效的 Authorization header'}), 401
        
        if not token:
            return jsonify({'error': '未提供认证 token'}), 401
        
        # 验证 token
        try:
            payload = jwt.decode(token, current_app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
            g.current_user = payload
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token 已过期'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': '无效的 Token'}), 401
        
        return f(*args, **kwargs)
    
    return decorated_function


def admin_required(f):
    """
    管理员权限验证装饰器
    """
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if g.current_user.get('user_type') != 'admin':
            return jsonify({'error': '需要管理员权限'}), 403
        return f(*args, **kwargs)
    
    return decorated_function


def paginate(query, page=1, per_page=20):
    """
    分页查询
    
    Args:
        query: SQLAlchemy 查询对象
        page: 页码
        per_page: 每页数量
    
    Returns:
        分页结果字典
    """
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return {
        'items': [item.to_dict() for item in pagination.items],
        'total': pagination.total,
        'page': page,
        'per_page': per_page,
        'pages': pagination.pages,
        'has_next': pagination.has_next,
        'has_prev': pagination.has_prev
    }


def parse_date(date_str, default=None):
    """
    解析日期字符串
    
    Args:
        date_str: 日期字符串 (YYYY-MM-DD)
        default: 默认值
    
    Returns:
        date 对象或 None
    """
    if not date_str:
        return default
    
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return default


def format_currency(amount):
    """
    格式化货币金额
    
    Args:
        amount: 金额
    
    Returns:
        格式化后的字符串
    """
    if amount is None:
        return '¥0.00'
    return f"¥{float(amount):,.2f}"
