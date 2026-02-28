"""
数据备份路由模块
提供数据库备份、恢复、备份管理等功能
支持手动备份和自动定时备份
"""
from flask import Blueprint, request, jsonify, g, current_app, send_file
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import os
import json
import zipfile
import shutil
import sqlite3
from pathlib import Path

from app.models import db
from app.utils.decorators import login_required, admin_required
from app.utils.responses import APIResponse

# 创建蓝图
backup_bp = Blueprint('backup', __name__, url_prefix='/api/backup')


# ============================================================================
# 辅助函数
# ============================================================================

def get_database_path() -> str:
    """获取数据库文件路径"""
    database_uri = current_app.config.get('SQLALCHEMY_DATABASE_URI', '')
    if database_uri.startswith('sqlite:///'):
        db_path = database_uri.replace('sqlite:///', '')
        if not os.path.isabs(db_path):
            db_path = os.path.join(current_app.instance_path or current_app.root_path, db_path)
        return os.path.abspath(db_path)
    return None


def get_backup_folder() -> str:
    """获取备份文件夹路径"""
    return current_app.config.get('BACKUP_FOLDER', 'backups')


def get_backup_settings() -> Dict:
    """获取备份设置"""
    settings_file = os.path.join(get_backup_folder(), 'backup_settings.json')
    
    default_settings = {
        'auto_backup_enabled': True,
        'backup_frequency': 'daily',  # daily, weekly
        'backup_retention_count': 10,  # 保留最近 10 个备份
        'backup_time': '02:00',  # 备份时间
        'backup_uploads': True,  # 是否备份上传文件
        'last_backup_time': None,
        'last_backup_size': 0
    }
    
    if os.path.exists(settings_file):
        try:
            with open(settings_file, 'r', encoding='utf-8') as f:
                settings = json.load(f)
                # 合并默认设置
                default_settings.update(settings)
        except Exception as e:
            current_app.logger.error(f"读取备份设置失败：{str(e)}")
    
    return default_settings


def save_backup_settings(settings: Dict) -> bool:
    """保存备份设置"""
    try:
        backup_folder = get_backup_folder()
        os.makedirs(backup_folder, exist_ok=True)
        
        settings_file = os.path.join(backup_folder, 'backup_settings.json')
        
        with open(settings_file, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=2, ensure_ascii=False)
        
        return True
    except Exception as e:
        current_app.logger.error(f"保存备份设置失败：{str(e)}")
        return False


def create_backup_metadata(backup_path: str, remark: str = None) -> Dict:
    """创建备份元数据"""
    file_size = os.path.getsize(backup_path)
    
    metadata = {
        'filename': os.path.basename(backup_path),
        'backup_time': datetime.now().isoformat(),
        'backup_type': 'manual',
        'file_size': file_size,
        'file_size_mb': round(file_size / (1024 * 1024), 2),
        'database_path': get_database_path(),
        'includes_uploads': get_backup_settings().get('backup_uploads', True),
        'remark': remark,
        'backup_by': g.username if hasattr(g, 'username') else 'system'
    }
    
    return metadata


def cleanup_old_backups(retention_count: int = 10):
    """清理旧备份，保留最近的 N 个"""
    try:
        backup_folder = get_backup_folder()
        
        # 获取所有备份文件
        backup_files = []
        for filename in os.listdir(backup_folder):
            if filename.startswith('housing_') and filename.endswith('.zip'):
                filepath = os.path.join(backup_folder, filename)
                backup_files.append({
                    'filename': filename,
                    'path': filepath,
                    'mtime': os.path.getmtime(filepath)
                })
        
        # 按修改时间排序
        backup_files.sort(key=lambda x: x['mtime'], reverse=True)
        
        # 删除超出保留数量的备份
        deleted_count = 0
        for backup_file in backup_files[retention_count:]:
            try:
                os.remove(backup_file['path'])
                # 同时删除元数据文件
                meta_file = backup_file['path'].replace('.zip', '.meta.json')
                if os.path.exists(meta_file):
                    os.remove(meta_file)
                deleted_count += 1
                current_app.logger.info(f"清理旧备份：{backup_file['filename']}")
            except Exception as e:
                current_app.logger.error(f"清理备份失败 {backup_file['filename']}: {str(e)}")
        
        return deleted_count
    except Exception as e:
        current_app.logger.error(f"清理备份失败：{str(e)}")
        return 0


# ============================================================================
# 创建备份接口
# ============================================================================

@backup_bp.route('/create', methods=['POST'])
@login_required
def create_backup():
    """
    创建备份
    
    Request Body (可选):
        {
            "remark": "备份备注",
            "backup_uploads": true  // 是否包含上传文件
        }
    
    Response:
        {
            "success": true,
            "message": "备份创建成功",
            "data": {
                "filename": "housing_20240101_120000.zip",
                "backup_time": "2024-01-01T12:00:00",
                "file_size": 1048576,
                "file_size_mb": 1.0,
                "includes_uploads": true,
                "remark": "备份备注"
            }
        }
    """
    try:
        # 获取请求数据
        data = request.get_json() or {}
        remark = data.get('remark', '')
        backup_uploads = data.get('backup_uploads', get_backup_settings().get('backup_uploads', True))
        
        # 获取路径
        database_path = get_database_path()
        backup_folder = get_backup_folder()
        upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
        
        if not database_path:
            return APIResponse.bad_request("无法获取数据库路径")
        
        if not os.path.exists(database_path):
            return APIResponse.bad_request("数据库文件不存在")
        
        # 确保备份目录存在
        os.makedirs(backup_folder, exist_ok=True)
        
        # 生成备份文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f'housing_{timestamp}.zip'
        backup_path = os.path.join(backup_folder, backup_filename)
        
        # 创建临时目录
        temp_dir = os.path.join(backup_folder, f'temp_{timestamp}')
        os.makedirs(temp_dir, exist_ok=True)
        
        try:
            # 1. 复制数据库文件
            db_backup_path = os.path.join(temp_dir, 'database.db')
            shutil.copy2(database_path, db_backup_path)
            
            # 2. 复制上传文件（如果启用）
            uploads_backup_path = None
            if backup_uploads and os.path.exists(upload_folder):
                uploads_backup_path = os.path.join(temp_dir, 'uploads')
                shutil.copytree(upload_folder, uploads_backup_path)
            
            # 3. 创建元数据文件
            metadata = {
                'backup_time': datetime.now().isoformat(),
                'backup_type': 'manual',
                'backup_by': g.username if hasattr(g, 'username') else 'unknown',
                'remark': remark,
                'includes_uploads': backup_uploads,
                'database_path': database_path,
                'upload_folder': upload_folder if backup_uploads else None
            }
            
            meta_file_path = os.path.join(temp_dir, 'metadata.json')
            with open(meta_file_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            # 4. 创建 ZIP 压缩包
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # 添加数据库文件
                zipf.write(db_backup_path, 'database.db')
                
                # 添加元数据文件
                zipf.write(meta_file_path, 'metadata.json')
                
                # 添加上传文件目录
                if uploads_backup_path and os.path.exists(uploads_backup_path):
                    for root, dirs, files in os.walk(uploads_backup_path):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.join('uploads', os.path.relpath(file_path, uploads_backup_path))
                            zipf.write(file_path, arcname)
            
            # 5. 清理临时目录
            shutil.rmtree(temp_dir)
            
            # 6. 更新备份设置
            settings = get_backup_settings()
            settings['last_backup_time'] = datetime.now().isoformat()
            settings['last_backup_size'] = os.path.getsize(backup_path)
            save_backup_settings(settings)
            
            # 7. 清理旧备份
            retention_count = settings.get('backup_retention_count', 10)
            deleted_count = cleanup_old_backups(retention_count)
            
            # 8. 准备响应数据
            backup_metadata = create_backup_metadata(backup_path, remark)
            
            current_app.logger.info(f"用户 {g.username} 创建了备份：{backup_filename}")
            
            return APIResponse.success({
                **backup_metadata,
                'deleted_old_backups': deleted_count
            }, "备份创建成功", 201)
            
        except Exception as e:
            # 清理临时目录
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            
            # 清理可能产生的不完整备份
            if os.path.exists(backup_path):
                os.remove(backup_path)
            
            raise e
            
    except Exception as e:
        current_app.logger.error(f"创建备份失败：{str(e)}")
        return APIResponse.server_error(f"创建备份失败：{str(e)}")


# ============================================================================
# 备份列表接口
# ============================================================================

@backup_bp.route('/list', methods=['GET'])
@login_required
def list_backups():
    """
    获取备份列表
    
    Query Parameters:
        page: 页码，默认 1
        per_page: 每页数量，默认 20
        
    Response:
        {
            "success": true,
            "data": {
                "items": [
                    {
                        "filename": "housing_20240101_120000.zip",
                        "backup_time": "2024-01-01T12:00:00",
                        "file_size": 1048576,
                        "file_size_mb": 1.0,
                        "backup_type": "manual",
                        "backup_by": "admin",
                        "remark": "月度备份"
                    }
                ],
                "pagination": {
                    "page": 1,
                    "per_page": 20,
                    "total": 10
                }
            }
        }
    """
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        backup_folder = get_backup_folder()
        
        if not os.path.exists(backup_folder):
            return APIResponse.success({
                'items': [],
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': 0,
                    'pages': 0
                }
            }, "获取备份列表成功")
        
        # 获取所有备份文件
        backup_files = []
        for filename in os.listdir(backup_folder):
            if filename.startswith('housing_') and filename.endswith('.zip'):
                filepath = os.path.join(backup_folder, filename)
                
                # 尝试读取元数据
                meta_file = filepath.replace('.zip', '.meta.json')
                metadata = {}
                
                if os.path.exists(meta_file):
                    try:
                        with open(meta_file, 'r', encoding='utf-8') as f:
                            metadata = json.load(f)
                    except:
                        pass
                
                # 如果没有元数据文件，从 ZIP 中读取
                if not metadata:
                    try:
                        with zipfile.ZipFile(filepath, 'r') as zipf:
                            if 'metadata.json' in zipf.namelist():
                                with zipf.open('metadata.json') as f:
                                    metadata = json.load(f)
                    except:
                        pass
                
                # 获取文件信息
                file_stat = os.stat(filepath)
                
                backup_files.append({
                    'filename': filename,
                    'filepath': filepath,
                    'backup_time': metadata.get('backup_time', datetime.fromtimestamp(file_stat.st_mtime).isoformat()),
                    'file_size': file_stat.st_size,
                    'file_size_mb': round(file_stat.st_size / (1024 * 1024), 2),
                    'backup_type': metadata.get('backup_type', 'unknown'),
                    'backup_by': metadata.get('backup_by', 'unknown'),
                    'remark': metadata.get('remark', ''),
                    'includes_uploads': metadata.get('includes_uploads', False)
                })
        
        # 按备份时间排序（最新的在前）
        backup_files.sort(key=lambda x: x['backup_time'], reverse=True)
        
        # 分页
        total = len(backup_files)
        pages = (total + per_page - 1) // per_page if per_page > 0 else 0
        
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_items = backup_files[start_idx:end_idx]
        
        return APIResponse.success({
            'items': paginated_items,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'pages': pages,
                'has_next': page < pages,
                'has_prev': page > 1,
                'next_num': page + 1 if page < pages else None,
                'prev_num': page - 1 if page > 1 else None
            }
        }, "获取备份列表成功")
        
    except Exception as e:
        current_app.logger.error(f"获取备份列表失败：{str(e)}")
        return APIResponse.server_error("获取备份列表失败")


# ============================================================================
# 下载备份接口
# ============================================================================

@backup_bp.route('/download/<filename>', methods=['GET'])
@login_required
def download_backup(filename: str):
    """
    下载备份文件
    
    Path Parameters:
        filename: 备份文件名
    
    Response:
        下载 ZIP 文件
    """
    try:
        # 验证文件名安全性
        if not filename.startswith('housing_') or not filename.endswith('.zip'):
            return APIResponse.bad_request("无效的备份文件名")
        
        backup_folder = get_backup_folder()
        backup_path = os.path.join(backup_folder, filename)
        
        if not os.path.exists(backup_path):
            return APIResponse.not_found("备份文件不存在")
        
        return send_file(
            backup_path,
            mimetype='application/zip',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        current_app.logger.error(f"下载备份失败：{str(e)}")
        return APIResponse.server_error(f"下载备份失败：{str(e)}")


# ============================================================================
# 恢复数据接口
# ============================================================================

@backup_bp.route('/restore', methods=['POST'])
@admin_required
def restore_backup():
    """
    恢复数据（仅管理员）
    
    Request Body:
        {
            "filename": "housing_20240101_120000.zip",
            "confirm": true  // 必须为 true 才执行恢复
        }
    
    Response:
        {
            "success": true,
            "message": "数据恢复成功",
            "data": {
                "backup_file": "housing_20240101_120000.zip",
                "restore_time": "2024-01-01T12:00:00",
                "pre_backup_file": "housing_20240101_120001.zip"
            }
        }
    """
    try:
        # 获取请求数据
        data = request.get_json()
        
        if not data:
            return APIResponse.bad_request("请求数据不能为空")
        
        filename = data.get('filename')
        confirm = data.get('confirm', False)
        
        if not filename:
            return APIResponse.bad_request("备份文件名不能为空")
        
        if not confirm:
            return APIResponse.bad_request("请确认恢复操作，设置 confirm=true")
        
        # 验证文件名安全性
        if not filename.startswith('housing_') or not filename.endswith('.zip'):
            return APIResponse.bad_request("无效的备份文件名")
        
        backup_folder = get_backup_folder()
        backup_path = os.path.join(backup_folder, filename)
        
        if not os.path.exists(backup_path):
            return APIResponse.not_found("备份文件不存在")
        
        # 获取当前数据库路径
        database_path = get_database_path()
        upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
        
        if not database_path:
            return APIResponse.bad_request("无法获取数据库路径")
        
        # 1. 创建当前数据的备份
        current_app.logger.info("恢复前自动备份当前数据...")
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        pre_backup_filename = f'housing_pre_restore_{timestamp}.zip'
        pre_backup_path = os.path.join(backup_folder, pre_backup_filename)
        
        try:
            # 创建临时目录
            temp_dir = os.path.join(backup_folder, f'temp_pre_{timestamp}')
            os.makedirs(temp_dir, exist_ok=True)
            
            # 复制当前数据库
            if os.path.exists(database_path):
                shutil.copy2(database_path, os.path.join(temp_dir, 'database.db'))
            
            # 复制上传文件
            if os.path.exists(upload_folder):
                shutil.copytree(upload_folder, os.path.join(temp_dir, 'uploads'))
            
            # 创建元数据
            pre_metadata = {
                'backup_time': datetime.now().isoformat(),
                'backup_type': 'auto_before_restore',
                'backup_by': g.username,
                'remark': f'恢复 {filename} 前的自动备份',
                'original_backup': filename
            }
            
            with open(os.path.join(temp_dir, 'metadata.json'), 'w', encoding='utf-8') as f:
                json.dump(pre_metadata, f, indent=2, ensure_ascii=False)
            
            # 创建 ZIP
            with zipfile.ZipFile(pre_backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(temp_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, temp_dir)
                        zipf.write(file_path, arcname)
            
            # 清理临时目录
            shutil.rmtree(temp_dir)
            
            current_app.logger.info(f"创建恢复前备份：{pre_backup_filename}")
            
        except Exception as e:
            current_app.logger.error(f"创建恢复前备份失败：{str(e)}")
            # 继续恢复流程，但记录错误
        
        # 2. 解压备份文件
        current_app.logger.info(f"开始恢复备份：{filename}")
        
        extract_dir = os.path.join(backup_folder, f'extract_{timestamp}')
        os.makedirs(extract_dir, exist_ok=True)
        
        try:
            with zipfile.ZipFile(backup_path, 'r') as zipf:
                zipf.extractall(extract_dir)
            
            # 3. 恢复数据库
            extracted_db = os.path.join(extract_dir, 'database.db')
            if os.path.exists(extracted_db):
                # 关闭数据库连接
                db.session.close()
                
                # 复制数据库文件
                shutil.copy2(extracted_db, database_path)
                
                current_app.logger.info("数据库恢复成功")
            
            # 4. 恢复上传文件（如果备份中包含）
            extracted_uploads = os.path.join(extract_dir, 'uploads')
            if os.path.exists(extracted_uploads):
                # 备份当前上传文件
                if os.path.exists(upload_folder):
                    current_uploads_backup = os.path.join(backup_folder, f'uploads_backup_{timestamp}')
                    shutil.move(upload_folder, current_uploads_backup)
                
                # 恢复上传文件
                shutil.move(extracted_uploads, upload_folder)
                
                current_app.logger.info("上传文件恢复成功")
            
            # 5. 清理临时目录
            shutil.rmtree(extract_dir)
            
            # 6. 更新备份设置
            settings = get_backup_settings()
            settings['last_restore_time'] = datetime.now().isoformat()
            settings['last_restore_file'] = filename
            save_backup_settings(settings)
            
            current_app.logger.info(f"用户 {g.username} 恢复了备份：{filename}")
            
            return APIResponse.success({
                'backup_file': filename,
                'restore_time': datetime.now().isoformat(),
                'pre_backup_file': pre_backup_filename if os.path.exists(pre_backup_path) else None
            }, "数据恢复成功")
            
        except Exception as e:
            current_app.logger.error(f"恢复失败：{str(e)}")
            
            # 清理临时目录
            if os.path.exists(extract_dir):
                shutil.rmtree(extract_dir)
            
            return APIResponse.server_error(f"数据恢复失败：{str(e)}")
        
    except Exception as e:
        current_app.logger.error(f"恢复数据失败：{str(e)}")
        return APIResponse.server_error(f"恢复数据失败：{str(e)}")


# ============================================================================
# 删除备份接口
# ============================================================================

@backup_bp.route('/<filename>', methods=['DELETE'])
@admin_required
def delete_backup(filename: str):
    """
    删除备份（仅管理员）
    
    Path Parameters:
        filename: 备份文件名
    
    Response:
        {
            "success": true,
            "message": "备份删除成功"
        }
    """
    try:
        # 验证文件名安全性
        if not filename.startswith('housing_') or not filename.endswith('.zip'):
            return APIResponse.bad_request("无效的备份文件名")
        
        backup_folder = get_backup_folder()
        backup_path = os.path.join(backup_folder, filename)
        
        if not os.path.exists(backup_path):
            return APIResponse.not_found("备份文件不存在")
        
        # 删除备份文件
        os.remove(backup_path)
        
        # 删除元数据文件（如果存在）
        meta_file = backup_path.replace('.zip', '.meta.json')
        if os.path.exists(meta_file):
            os.remove(meta_file)
        
        current_app.logger.info(f"管理员 {g.username} 删除了备份：{filename}")
        
        return APIResponse.success(None, "备份删除成功")
        
    except Exception as e:
        current_app.logger.error(f"删除备份失败：{str(e)}")
        return APIResponse.server_error(f"删除备份失败：{str(e)}")


# ============================================================================
# 备份设置接口
# ============================================================================

@backup_bp.route('/settings', methods=['GET'])
@login_required
def get_backup_settings_route():
    """
    获取备份设置
    
    Response:
        {
            "success": true,
            "data": {
                "auto_backup_enabled": true,
                "backup_frequency": "daily",
                "backup_retention_count": 10,
                "backup_time": "02:00",
                "backup_uploads": true,
                "last_backup_time": "2024-01-01T02:00:00",
                "last_backup_size": 1048576
            }
        }
    """
    try:
        settings = get_backup_settings()
        return APIResponse.success(settings, "获取备份设置成功")
    except Exception as e:
        current_app.logger.error(f"获取备份设置失败：{str(e)}")
        return APIResponse.server_error("获取备份设置失败")


@backup_bp.route('/settings', methods=['PUT'])
@admin_required
def update_backup_settings_route():
    """
    更新备份设置（仅管理员）
    
    Request Body:
        {
            "auto_backup_enabled": true,
            "backup_frequency": "daily",
            "backup_retention_count": 10,
            "backup_time": "02:00",
            "backup_uploads": true
        }
    
    Response:
        {
            "success": true,
            "message": "备份设置更新成功",
            "data": {...}
        }
    """
    try:
        # 获取请求数据
        data = request.get_json()
        
        if not data:
            return APIResponse.bad_request("请求数据不能为空")
        
        # 获取当前设置
        current_settings = get_backup_settings()
        
        # 更新允许的字段
        allowed_fields = [
            'auto_backup_enabled',
            'backup_frequency',
            'backup_retention_count',
            'backup_time',
            'backup_uploads'
        ]
        
        for field in allowed_fields:
            if field in data:
                current_settings[field] = data[field]
        
        # 验证字段值
        if current_settings['backup_frequency'] not in ['daily', 'weekly']:
            return APIResponse.bad_request("备份频率必须是 daily 或 weekly")
        
        if current_settings['backup_retention_count'] < 1 or current_settings['backup_retention_count'] > 100:
            return APIResponse.bad_request("备份保留数量必须在 1-100 之间")
        
        # 保存设置
        if save_backup_settings(current_settings):
            # 重新配置定时任务
            try:
                from app import scheduler
                from app.routes.backup import schedule_auto_backup
                
                # 移除旧任务
                if scheduler.get_job('auto_backup'):
                    scheduler.remove_job('auto_backup')
                
                # 添加新任务
                if current_settings['auto_backup_enabled']:
                    if current_settings['backup_frequency'] == 'daily':
                        hour, minute = map(int, current_settings['backup_time'].split(':'))
                        scheduler.add_job(
                            schedule_auto_backup,
                            'cron',
                            hour=hour,
                            minute=minute,
                            id='auto_backup',
                            replace_existing=True
                        )
                    elif current_settings['backup_frequency'] == 'weekly':
                        hour, minute = map(int, current_settings['backup_time'].split(':'))
                        scheduler.add_job(
                            schedule_auto_backup,
                            'cron',
                            hour=hour,
                            minute=minute,
                            day_of_week='mon',
                            id='auto_backup',
                            replace_existing=True
                        )
                    
                    current_app.logger.info("重新配置自动备份任务成功")
            except Exception as e:
                current_app.logger.error(f"重新配置定时任务失败：{str(e)}")
            
            return APIResponse.success(current_settings, "备份设置更新成功")
        else:
            return APIResponse.server_error("保存备份设置失败")
        
    except Exception as e:
        current_app.logger.error(f"更新备份设置失败：{str(e)}")
        return APIResponse.server_error("更新备份设置失败")


# ============================================================================
# 定时备份任务
# ============================================================================

def schedule_auto_backup():
    """定时自动备份任务"""
    try:
        current_app.logger.info("开始执行自动备份任务...")
        
        # 使用应用上下文
        with current_app.app_context():
            # 创建备份
            backup_folder = get_backup_folder()
            database_path = get_database_path()
            upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
            
            if not database_path or not os.path.exists(database_path):
                current_app.logger.error("数据库文件不存在，跳过自动备份")
                return
            
            # 生成备份文件名
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f'housing_auto_{timestamp}.zip'
            backup_path = os.path.join(backup_folder, backup_filename)
            
            # 创建临时目录
            temp_dir = os.path.join(backup_folder, f'temp_auto_{timestamp}')
            os.makedirs(temp_dir, exist_ok=True)
            
            try:
                # 复制数据库文件
                shutil.copy2(database_path, os.path.join(temp_dir, 'database.db'))
                
                # 复制上传文件
                settings = get_backup_settings()
                if settings.get('backup_uploads', True) and os.path.exists(upload_folder):
                    shutil.copytree(upload_folder, os.path.join(temp_dir, 'uploads'))
                
                # 创建元数据
                metadata = {
                    'backup_time': datetime.now().isoformat(),
                    'backup_type': 'auto',
                    'backup_by': 'system',
                    'remark': '系统自动备份',
                    'includes_uploads': settings.get('backup_uploads', True)
                }
                
                with open(os.path.join(temp_dir, 'metadata.json'), 'w', encoding='utf-8') as f:
                    json.dump(metadata, f, indent=2, ensure_ascii=False)
                
                # 创建 ZIP
                with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for root, dirs, files in os.walk(temp_dir):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, temp_dir)
                            zipf.write(file_path, arcname)
                
                # 清理临时目录
                shutil.rmtree(temp_dir)
                
                # 更新设置
                settings['last_backup_time'] = datetime.now().isoformat()
                settings['last_backup_size'] = os.path.getsize(backup_path)
                save_backup_settings(settings)
                
                # 清理旧备份
                retention_count = settings.get('backup_retention_count', 10)
                deleted_count = cleanup_old_backups(retention_count)
                
                current_app.logger.info(f"自动备份成功：{backup_filename}, 清理了 {deleted_count} 个旧备份")
                
            except Exception as e:
                current_app.logger.error(f"自动备份失败：{str(e)}")
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)
                
    except Exception as e:
        current_app.logger.error(f"自动备份任务执行失败：{str(e)}")


def init_auto_backup(app):
    """初始化自动备份任务"""
    try:
        # 在应用上下文中获取设置
        with app.app_context():
            settings = get_backup_settings()
            
            if not settings.get('auto_backup_enabled', True):
                app.logger.info("自动备份已禁用")
                return
            
            # 从 app 获取 scheduler
            from app import scheduler
            
            # 配置定时任务
            if settings['backup_frequency'] == 'daily':
                hour, minute = map(int, settings['backup_time'].split(':'))
                scheduler.add_job(
                    schedule_auto_backup,
                    'cron',
                    hour=hour,
                    minute=minute,
                    id='auto_backup',
                    replace_existing=True
                )
                app.logger.info(f"已配置每日自动备份任务：{settings['backup_time']}")
            
            elif settings['backup_frequency'] == 'weekly':
                hour, minute = map(int, settings['backup_time'].split(':'))
                scheduler.add_job(
                    schedule_auto_backup,
                    'cron',
                    hour=hour,
                    minute=minute,
                    day_of_week='mon',
                    id='auto_backup',
                    replace_existing=True
                )
                app.logger.info(f"已配置每周自动备份任务：周一 {settings['backup_time']}")
            
    except Exception as e:
        app.logger.error(f"初始化自动备份任务失败：{str(e)}")
