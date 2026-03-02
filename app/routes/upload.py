"""
文件上传路由模块
提供图片、视频等文件的上传功能
"""
import os
import uuid
from datetime import datetime
from flask import Blueprint, request, jsonify, g, current_app
from werkzeug.utils import secure_filename

from app.models.media import Media
from app.models.house import House
from app.models import db
from app.utils.decorators import login_required, permission_required
from app.utils.responses import APIResponse

# 创建蓝图
upload_bp = Blueprint('upload', __name__, url_prefix='/api/upload')

# ============================================================================
# 常量定义
# ============================================================================

# 文件大小限制（字节）
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB
MAX_VIDEO_SIZE = 50 * 1024 * 1024  # 50MB
MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB (总上传限制)

# 允许的文件扩展名
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'mov', 'avi', 'webm'}

# 允许的 MIME 类型
ALLOWED_MIME_TYPES = {
    'image': [
        'image/jpeg',
        'image/png',
        'image/gif',
        'image/webp'
    ],
    'video': [
        'video/mp4',
        'video/quicktime',
        'video/x-msvideo',
        'video/webm'
    ]
}


# ============================================================================
# 辅助函数
# ============================================================================

def allowed_file(filename: str, file_type: str = None) -> bool:
    """
    检查文件扩展名是否允许
    
    Args:
        filename: 文件名
        file_type: 文件类型限制（image/video），不限制则为 None
        
    Returns:
        bool: 是否允许
    """
    if '.' not in filename:
        return False
    
    ext = filename.rsplit('.', 1)[1].lower()
    
    if file_type == 'image':
        return ext in ALLOWED_IMAGE_EXTENSIONS
    elif file_type == 'video':
        return ext in ALLOWED_VIDEO_EXTENSIONS
    else:
        return ext in ALLOWED_IMAGE_EXTENSIONS or ext in ALLOWED_VIDEO_EXTENSIONS


def get_file_type(mime_type: str) -> str:
    """
    根据 MIME 类型判断文件类型
    
    Args:
        mime_type: MIME 类型
        
    Returns:
        str: 文件类型（image/video）或 None
    """
    for file_type, mime_types in ALLOWED_MIME_TYPES.items():
        if mime_type in mime_types:
            return file_type
    return None


def validate_file(file, file_type: str = None) -> tuple:
    """
    验证文件
    
    Args:
        file: 文件对象
        file_type: 文件类型限制（image/video）
        
    Returns:
        tuple: (是否有效，错误消息，文件类型)
    """
    if not file or not file.filename:
        return False, "文件不能为空", None
    
    filename = secure_filename(file.filename)
    
    # 检查文件扩展名
    if not allowed_file(filename, file_type):
        if file_type == 'image':
            allowed_exts = ', '.join(ALLOWED_IMAGE_EXTENSIONS)
        elif file_type == 'video':
            allowed_exts = ', '.join(ALLOWED_VIDEO_EXTENSIONS)
        else:
            allowed_exts = ', '.join(ALLOWED_IMAGE_EXTENSIONS | ALLOWED_VIDEO_EXTENSIONS)
        return False, f"不允许的文件格式，支持的格式：{allowed_exts}", None
    
    # 获取文件扩展名
    ext = filename.rsplit('.', 1)[1].lower()
    
    # 根据扩展名确定文件类型
    if ext in ALLOWED_IMAGE_EXTENSIONS:
        detected_type = 'image'
        max_size = MAX_IMAGE_SIZE
    elif ext in ALLOWED_VIDEO_EXTENSIONS:
        detected_type = 'video'
        max_size = MAX_VIDEO_SIZE
    else:
        return False, "无法识别的文件类型", None
    
    # 如果指定了文件类型，检查是否匹配
    if file_type and detected_type != file_type:
        return False, f"文件类型不匹配，需要 {file_type} 类型", None
    
    # 检查文件大小
    file.seek(0, 2)  # 移动到文件末尾
    file_size = file.tell()
    file.seek(0)  # 重置文件指针
    
    if file_size == 0:
        return False, "文件不能为空", None
    
    if file_size > max_size:
        size_mb = max_size / (1024 * 1024)
        return False, f"文件大小超过限制（最大 {size_mb:.0f}MB）", None
    
    return True, None, detected_type


def generate_unique_filename(original_filename: str) -> str:
    """
    生成唯一的文件名
    
    Args:
        original_filename: 原始文件名
        
    Returns:
        str: 唯一文件名
    """
    # 获取文件扩展名
    ext = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else ''
    
    # 生成唯一文件名：UUID + 时间戳
    unique_name = f"{uuid.uuid4().hex}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    if ext:
        unique_name = f"{unique_name}.{ext}"
    
    return unique_name


def save_file(file, file_type: str, sub_folder: str = None) -> tuple:
    """
    保存文件到服务器
    
    Args:
        file: 文件对象
        file_type: 文件类型（image/video）
        sub_folder: 子文件夹名称
        
    Returns:
        tuple: (文件路径，文件 URL，错误消息)
    """
    try:
        # 获取原始文件名
        original_filename = secure_filename(file.filename)
        
        # 生成唯一文件名
        unique_filename = generate_unique_filename(original_filename)
        
        # 确定保存路径
        upload_folder = current_app.config['UPLOAD_FOLDER']
        
        if sub_folder:
            save_dir = os.path.join(upload_folder, file_type, sub_folder)
        else:
            save_dir = os.path.join(upload_folder, file_type)
        
        # 确保目录存在
        os.makedirs(save_dir, exist_ok=True)
        
        # 保存文件
        file_path = os.path.join(save_dir, unique_filename)
        file.save(file_path)
        
        # 生成访问 URL
        file_url = f"/uploads/{file_type}/{sub_folder + '/' if sub_folder else ''}{unique_filename}"
        
        return file_path, file_url, None
        
    except Exception as e:
        current_app.logger.error(f"保存文件失败：{str(e)}")
        return None, None, f"保存文件失败：{str(e)}"


def create_media_record(file_path: str, file_url: str, file_type: str, 
                       file_size: int, mime_type: str, house_id: int = None,
                       description: str = None, sort_order: int = 0,
                       is_cover: bool = False) -> Media:
    """
    创建媒体记录
    
    Args:
        file_path: 文件路径
        file_url: 文件 URL
        file_type: 文件类型
        file_size: 文件大小
        mime_type: MIME 类型
        house_id: 房源 ID
        description: 描述
        sort_order: 排序
        is_cover: 是否封面
        
    Returns:
        Media: 媒体对象
    """
    media = Media(
        file_name=os.path.basename(file_path),
        file_path=file_path,
        file_url=file_url,
        file_type=file_type,
        mime_type=mime_type,
        file_size=file_size,
        description=description,
        sort_order=sort_order,
        house_id=house_id,
        uploaded_by=g.user_id if g else None,
        is_cover=is_cover
    )
    
    db.session.add(media)
    return media


# ============================================================================
# 上传接口
# ============================================================================

@upload_bp.route('', methods=['POST'])
@login_required
@permission_required('create')
def upload_files():
    """
    上传文件接口（支持多文件上传）
    
    支持图片（最大 5MB）和视频（最大 50MB）
    支持的文件格式：
    - 图片：jpg, jpeg, png, gif, webp
    - 视频：mp4, mov, avi, webm
    
    Request:
        Content-Type: multipart/form-data
        FormData:
            files: 文件列表（可多选）
            house_id: 关联的房源 ID（可选）
            file_type: 文件类型限制（image/video，可选）
            descriptions: 文件描述列表（JSON 数组，可选）
            
    Response:
        {
            "success": true,
            "message": "上传成功",
            "data": {
                "uploaded_count": 3,
                "failed_count": 0,
                "files": [
                    {
                        "id": 1,
                        "file_name": "image.jpg",
                        "file_url": "/uploads/image/xxx.jpg",
                        "file_type": "image",
                        "file_size": 102400,
                        "mime_type": "image/jpeg"
                    }
                ],
                "failed_files": []
            }
        }
    """
    try:
        # 检查是否有文件
        if 'files' not in request.files:
            return APIResponse.bad_request("未找到上传文件")
        
        files = request.files.getlist('files')
        
        if not files or all(f.filename == '' for f in files):
            return APIResponse.bad_request("未选择任何文件")
        
        # 获取其他参数
        house_id = None
        house_id_str = request.form.get('house_id')
        if house_id_str:
            try:
                house_id = int(house_id_str)
            except (ValueError, TypeError):
                house_id = None
        
        file_type_filter = request.form.get('file_type')  # image/video
        descriptions_str = request.form.get('descriptions', '[]')
        
        try:
            descriptions = eval(descriptions_str) if descriptions_str else []
            if not isinstance(descriptions, list):
                descriptions = []
        except:
            descriptions = []
        
        # 验证房源 ID（如果提供）
        if house_id:
            house = House.query.get(house_id)
            if not house:
                return APIResponse.not_found("房源不存在")
            
            # 检查权限
            if house.owner_id != g.user_id and g.user_role != 'admin':
                return APIResponse.forbidden("您没有权限为此房源上传文件")
        
        uploaded_files = []
        failed_files = []
        
        # 处理每个文件
        for idx, file in enumerate(files):
            if not file or file.filename == '':
                continue
            
            # 验证文件
            is_valid, error_msg, detected_type = validate_file(file, file_type_filter)
            
            if not is_valid:
                failed_files.append({
                    'filename': file.filename,
                    'error': error_msg
                })
                continue
            
            # 获取 MIME 类型
            mime_type = file.content_type or 'application/octet-stream'
            
            # 再次验证 MIME 类型
            if not Media.is_allowed_type(mime_type):
                failed_files.append({
                    'filename': file.filename,
                    'error': '不支持的文件类型'
                })
                continue
            
            # 获取文件大小
            file.seek(0, 2)
            file_size = file.tell()
            file.seek(0)
            
            # 保存文件
            sub_folder = str(house_id) if house_id else datetime.now().strftime('%Y%m')
            file_path, file_url, save_error = save_file(file, detected_type, sub_folder)
            
            if save_error:
                failed_files.append({
                    'filename': file.filename,
                    'error': save_error
                })
                continue
            
            # 创建媒体记录
            description = descriptions[idx] if idx < len(descriptions) else None
            media = create_media_record(
                file_path=file_path,
                file_url=file_url,
                file_type=detected_type,
                file_size=file_size,
                mime_type=mime_type,
                house_id=house_id,
                description=description,
                sort_order=idx
            )
            
            db.session.flush()  # 获取 ID
            
            uploaded_files.append({
                'id': media.id,
                'file_name': media.file_name,
                'file_url': media.file_url,
                'file_type': media.file_type,
                'file_size': media.file_size,
                'file_size_formatted': media.get_file_size_formatted(),
                'mime_type': media.mime_type,
                'description': media.description,
                'house_id': media.house_id
            })
        
        # 提交数据库事务
        db.session.commit()
        
        # 记录日志
        current_app.logger.info(
            f"用户 {g.username} 上传了 {len(uploaded_files)} 个文件，"
            f"失败 {len(failed_files)} 个"
        )
        
        # 返回响应
        result = {
            'uploaded_count': len(uploaded_files),
            'failed_count': len(failed_files),
            'files': uploaded_files,
            'failed_files': failed_files
        }
        
        return APIResponse.success(result, "上传成功", 201)
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"上传文件失败：{str(e)}")
        return APIResponse.server_error("上传文件失败")


@upload_bp.route('/image', methods=['POST'])
@login_required
@permission_required('create')
def upload_images():
    """
    上传图片（专门接口）
    
    仅允许上传图片文件，最大 5MB
    
    Request:
        Content-Type: multipart/form-data
        FormData:
            files: 图片文件列表
            house_id: 关联的房源 ID（可选）
            
    Response:
        {
            "success": true,
            "data": {
                "uploaded_count": 2,
                "files": [...]
            }
        }
    """
    # 调用通用上传函数，传递文件类型限制
    from flask import request
    
    # 创建一个可变的表单数据副本
    form_data = dict(request.form)
    form_data['file_type'] = 'image'
    
    # 临时替换 request.form
    original_form = request.form
    request.form = form_data
    
    try:
        return upload_files()
    finally:
        # 恢复原始 request.form
        request.form = original_form


@upload_bp.route('/video', methods=['POST'])
@login_required
@permission_required('create')
def upload_videos():
    """
    上传视频（专门接口）
    
    仅允许上传视频文件，最大 50MB
    
    Request:
        Content-Type: multipart/form-data
        FormData:
            files: 视频文件列表
            house_id: 关联的房源 ID（可选）
            
    Response:
        {
            "success": true,
            "data": {
                "uploaded_count": 1,
                "files": [...]
            }
        }
    """
    # 调用通用上传函数，传递文件类型限制
    from flask import request
    
    # 创建一个可变的表单数据副本
    form_data = dict(request.form)
    form_data['file_type'] = 'video'
    
    # 临时替换 request.form
    original_form = request.form
    request.form = form_data
    
    try:
        return upload_files()
    finally:
        # 恢复原始 request.form
        request.form = original_form


@upload_bp.route('/house/<int:house_id>', methods=['POST'])
@login_required
@permission_required('create')
def upload_house_files(house_id: int):
    """
    为房源上传文件
    
    Path Parameters:
        house_id: 房源 ID
        
    Request:
        Content-Type: multipart/form-data
        FormData:
            files: 文件列表
            is_cover: 是否设为封面（true/false，可选）
            
    Response:
        {
            "success": true,
            "data": {
                "house_id": 1,
                "uploaded_count": 3,
                "files": [...],
                "cover_updated": true
            }
        }
    """
    try:
        # 验证房源
        house = House.query.get(house_id)
        
        if not house:
            return APIResponse.not_found("房源不存在")
        
        # 检查权限
        if house.owner_id != g.user_id and g.user_role != 'admin':
            return APIResponse.forbidden("您没有权限为此房源上传文件")
        
        # 检查是否有文件
        if 'files' not in request.files:
            return APIResponse.bad_request("未找到上传文件")
        
        files = request.files.getlist('files')
        
        if not files or all(f.filename == '' for f in files):
            return APIResponse.bad_request("未选择任何文件")
        
        # 获取是否设为封面
        is_cover = request.form.get('is_cover', 'false').lower() == 'true'
        
        # 如果设为封面，先取消其他封面
        if is_cover:
            Media.query.filter_by(house_id=house_id, is_cover=True).update({'is_cover': False})
        
        uploaded_files = []
        failed_files = []
        
        # 获取当前最大排序值
        max_sort = db.session.query(db.func.max(Media.sort_order)).filter_by(
            house_id=house_id
        ).scalar() or -1
        
        # 处理每个文件
        for idx, file in enumerate(files):
            if not file or file.filename == '':
                continue
            
            # 验证文件
            is_valid, error_msg, detected_type = validate_file(file)
            
            if not is_valid:
                failed_files.append({
                    'filename': file.filename,
                    'error': error_msg
                })
                continue
            
            # 获取 MIME 类型
            mime_type = file.content_type or 'application/octet-stream'
            
            # 验证 MIME 类型
            if not Media.is_allowed_type(mime_type):
                failed_files.append({
                    'filename': file.filename,
                    'error': '不支持的文件类型'
                })
                continue
            
            # 获取文件大小
            file.seek(0, 2)
            file_size = file.tell()
            file.seek(0)
            
            # 保存文件
            sub_folder = str(house_id)
            file_path, file_url, save_error = save_file(file, detected_type, sub_folder)
            
            if save_error:
                failed_files.append({
                    'filename': file.filename,
                    'error': save_error
                })
                continue
            
            # 创建媒体记录，直接传入 is_cover 参数
            media = create_media_record(
                file_path=file_path,
                file_url=file_url,
                file_type=detected_type,
                file_size=file_size,
                mime_type=mime_type,
                house_id=house_id,
                sort_order=max_sort + idx + 1,
                is_cover=(is_cover and idx == 0)  # 第一个文件且指定了 is_cover
            )
            
            db.session.flush()
            
            uploaded_files.append({
                'id': media.id,
                'file_name': media.file_name,
                'file_url': media.file_url,
                'file_type': media.file_type,
                'file_size': media.file_size,
                'is_cover': media.is_cover
            })
        
        db.session.commit()
        
        current_app.logger.info(
            f"用户 {g.username} 为房源 {house_id} 上传了 {len(uploaded_files)} 个文件"
        )
        
        return APIResponse.success({
            'house_id': house_id,
            'uploaded_count': len(uploaded_files),
            'failed_count': len(failed_files),
            'files': uploaded_files,
            'failed_files': failed_files,
            'cover_updated': is_cover
        }, "上传成功", 201)
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"为房源上传文件失败：{str(e)}")
        return APIResponse.server_error("上传文件失败")


# ============================================================================
# 文件管理接口
# ============================================================================

@upload_bp.route('/<int:media_id>', methods=['DELETE'])
@login_required
@permission_required('edit')
def delete_file(media_id: int):
    """
    删除文件
    
    Path Parameters:
        media_id: 媒体 ID
        
    Response:
        {
            "success": true,
            "message": "文件删除成功"
        }
    """
    try:
        media = Media.query.get(media_id)
        
        if not media:
            return APIResponse.not_found("文件不存在")
        
        # 检查权限
        if media.house_id:
            house = House.query.get(media.house_id)
            if house and house.owner_id != g.user_id and g.user_role != 'admin':
                return APIResponse.forbidden("您没有权限删除此文件")
        elif media.uploaded_by != g.user_id and g.user_role != 'admin':
            return APIResponse.forbidden("您没有权限删除此文件")
        
        # 获取文件路径
        file_path = media.file_path
        
        # 删除数据库记录
        db.session.delete(media)
        db.session.commit()
        
        # 删除物理文件
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                current_app.logger.info(f"删除物理文件：{file_path}")
        except Exception as e:
            current_app.logger.warning(f"删除物理文件失败：{str(e)}")
        
        current_app.logger.info(f"用户 {g.username} 删除了文件 {media_id}")
        
        return APIResponse.success(None, "文件删除成功")
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"删除文件失败：{str(e)}")
        return APIResponse.server_error("删除文件失败")


@upload_bp.route('/<int:media_id>/cover', methods=['PUT'])
@login_required
@permission_required('edit')
def set_cover_image(media_id: int):
    """
    设置封面图片
    
    Path Parameters:
        media_id: 媒体 ID
        
    Request Body:
        {
            "is_cover": true
        }
        
    Response:
        {
            "success": true,
            "message": "封面设置成功",
            "data": {...}
        }
    """
    try:
        media = Media.query.get(media_id)
        
        if not media:
            return APIResponse.not_found("文件不存在")
        
        # 检查是否为图片
        if media.file_type != 'image':
            return APIResponse.bad_request("只有图片可以设为封面")
        
        # 检查权限
        if media.house_id:
            house = House.query.get(media.house_id)
            if house and house.owner_id != g.user_id and g.user_role != 'admin':
                return APIResponse.forbidden("您没有权限操作此房源")
        
        # 获取请求数据
        data = request.get_json() or {}
        is_cover = data.get('is_cover', True)
        
        if is_cover:
            # 取消其他封面
            Media.query.filter_by(
                house_id=media.house_id,
                is_cover=True
            ).update({'is_cover': False})
            
            # 设置新封面
            media.is_cover = True
            db.session.commit()
            
            current_app.logger.info(f"用户 {g.username} 设置了房源 {media.house_id} 的封面图片")
        else:
            # 取消封面
            media.is_cover = False
            db.session.commit()
        
        return APIResponse.success(media.to_dict(), "封面设置成功")
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"设置封面失败：{str(e)}")
        return APIResponse.server_error("设置封面失败")


@upload_bp.route('/house/<int:house_id>/media', methods=['GET'])
@login_required
def get_house_media(house_id: int):
    """
    获取房源的媒体文件列表
    
    Path Parameters:
        house_id: 房源 ID
        
    Query Parameters:
        file_type: 文件类型筛选（image/video）
        
    Response:
        {
            "success": true,
            "data": {
                "house_id": 1,
                "media": [...]
            }
        }
    """
    try:
        house = House.query.get(house_id)
        
        if not house:
            return APIResponse.not_found("房源不存在")
        
        # 构建查询
        query = Media.query.filter_by(house_id=house_id)
        
        # 文件类型筛选
        file_type = request.args.get('file_type')
        if file_type:
            query = query.filter(Media.file_type == file_type)
        
        # 获取所有媒体文件
        media_list = query.order_by(Media.sort_order, Media.created_at).all()
        
        # 格式化响应
        media_data = [media.to_dict() for media in media_list]
        
        return APIResponse.success({
            'house_id': house_id,
            'media': media_data
        }, "获取媒体文件成功")
        
    except Exception as e:
        current_app.logger.error(f"获取媒体文件失败：{str(e)}")
        return APIResponse.server_error("获取媒体文件失败")
