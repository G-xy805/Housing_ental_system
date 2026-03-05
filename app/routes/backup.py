"""
数据备份路由模块
提供数据库备份、恢复、备份管理等功能
支持手动备份和自动定时备份

API 接口：
- POST /api/backup/create - 创建备份
- GET /api/backup/list - 获取备份列表
- GET /api/backup/download/<filename> - 下载备份文件
- POST /api/backup/restore - 恢复备份
- DELETE /api/backup/<filename> - 删除备份
- GET /api/backup/settings - 获取备份设置
- PUT /api/backup/settings - 更新备份设置
- GET /api/backup/stats - 获取备份统计信息
- GET /api/backup/health - 获取备份健康状态
- GET /api/backup/alerts - 获取告警列表
- POST /api/backup/verify/<filename> - 验证备份完整性
"""
from flask import Blueprint, request, jsonify, g, current_app, send_file
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import os
import json
import traceback

from app.models import db, BackupRecord
from app.utils.decorators import login_required, admin_required
from app.utils.responses import APIResponse
from app.utils.backup_manager import get_backup_manager
from app.utils.backup_monitor import get_backup_monitor

# 创建蓝图
backup_bp = Blueprint('backup', __name__, url_prefix='/api/backup')


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
            "backup_type": "full",  // full/incremental
            "remark": "备份备注",
            "include_uploads": true,  // 是否包含上传文件
            "encrypt": true,  // 是否加密
            "compress": true  // 是否压缩
        }
    
    Response:
        {
            "success": true,
            "message": "备份创建成功",
            "data": {
                "backup_id": "20240101_120000",
                "filename": "backup_full_20240101_120000.enc.zip",
                "backup_time": "2024-01-01T12:00:00",
                "file_size": 1048576,
                "file_size_mb": 1.0,
                "backup_type": "full",
                "encrypted": true,
                "compressed": true,
                "includes_uploads": true,
                "remark": "备份备注"
            }
        }
    """
    # 获取备份管理器和监控器
    backup_manager = get_backup_manager()
    backup_monitor = get_backup_monitor()
    
    # 记录备份开始
    backup_id = None
    
    try:
        # 获取请求数据
        data = request.get_json() or {}
        backup_type = data.get('backup_type', 'full')
        remark = data.get('remark', '')
        include_uploads = data.get('include_uploads', True)
        encrypt = data.get('encrypt')
        compress = data.get('compress')
        
        # 记录备份开始
        backup_id = backup_monitor.record_backup_start(backup_type)
        
        # 创建备份
        if backup_type == 'incremental':
            # 增量备份（需要上次备份时间）
            last_backup = BackupRecord.query.filter(
                BackupRecord.status == 'success',
                BackupRecord.deleted_at.is_(None)
            ).order_by(BackupRecord.start_time.desc()).first()
            
            last_backup_time = last_backup.start_time if last_backup else None
            
            backup_info = backup_manager.create_incremental_backup(
                last_backup_time=last_backup_time,
                remark=remark,
                encrypt=encrypt,
                compress=compress
            )
        else:
            # 完整备份
            backup_info = backup_manager.create_full_backup(
                remark=remark,
                include_uploads=include_uploads,
                encrypt=encrypt,
                compress=compress
            )
        
        # 记录备份成功
        backup_monitor.record_backup_success(backup_id, backup_info)
        
        # 保存到数据库
        record = BackupRecord.create_from_backup_info(
            backup_info=backup_info,
            backup_id=backup_id,
            backup_by=g.username if hasattr(g, 'username') else 'system'
        )
        record.backup_method = 'manual'
        record.trigger = 'api'
        db.session.add(record)
        db.session.commit()
        
        current_app.logger.info(f"用户 {g.username if hasattr(g, 'username') else 'unknown'} 创建了备份：{backup_info['filename']}")
        
        return APIResponse.success({
            'backup_id': backup_id,
            **backup_info
        }, "备份创建成功", 201)
        
    except Exception as e:
        # 记录备份失败
        if backup_id:
            backup_monitor.record_backup_failure(backup_id, str(e))
        
        current_app.logger.error(f"创建备份失败：{str(e)}\n{traceback.format_exc()}")
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
        backup_type: 备份类型过滤（full/incremental）
        status: 状态过滤（success/failed/running）
        
    Response:
        {
            "success": true,
            "data": {
                "items": [
                    {
                        "backup_id": "20240101_120000",
                        "filename": "backup_full_20240101_120000.enc.zip",
                        "backup_time": "2024-01-01T12:00:00",
                        "file_size": 1048576,
                        "file_size_mb": 1.0,
                        "backup_type": "full",
                        "status": "success",
                        "backup_by": "admin",
                        "remark": "月度备份"
                    }
                ],
                "pagination": {
                    "page": 1,
                    "per_page": 20,
                    "total": 10,
                    "pages": 1
                }
            }
        }
    """
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        backup_type = request.args.get('backup_type')
        status = request.args.get('status')
        
        # 构建查询（使用 db.session.query 避免 SoftDeleteQuery 的 paginate 问题）
        query = db.session.query(BackupRecord).filter(BackupRecord.deleted_at.is_(None))
        
        if backup_type:
            query = query.filter(BackupRecord.backup_type == backup_type)
        
        if status:
            query = query.filter(BackupRecord.status == status)
        
        # 排序和分页
        query = query.order_by(BackupRecord.start_time.desc())
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        items = [record.to_dict() for record in pagination.items]
        
        return APIResponse.success({
            'items': items,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
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
        下载备份文件
    """
    try:
        # 验证文件名安全性
        if not (filename.startswith('backup_') or filename.startswith('auto_backup_')) or not (
            filename.endswith('.db') or 
            filename.endswith('.zip') or 
            filename.endswith('.enc.zip') or
            filename.endswith('.enc')
        ):
            return APIResponse.bad_request("无效的备份文件名")
        
        backup_manager = get_backup_manager()
        backup_folder = backup_manager.backup_folder
        backup_path = os.path.join(backup_folder, filename)
        
        if not os.path.exists(backup_path):
            return APIResponse.not_found("备份文件不存在")
        
        current_app.logger.info(f"用户 {g.username if hasattr(g, 'username') else 'unknown'} 下载了备份：{filename}")
        
        return send_file(
            backup_path,
            mimetype='application/octet-stream',
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
            "filename": "backup_full_20240101_120000.enc.zip",
            "confirm": true  // 必须为 true 才执行恢复
        }
    
    Response:
        {
            "success": true,
            "message": "数据恢复成功",
            "data": {
                "backup_file": "backup_full_20240101_120000.enc.zip",
                "restore_time": "2024-01-01T12:00:00",
                "pre_backup_file": "backup_full_20240101_120001.enc.zip"
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
        if not (filename.startswith('backup_') or filename.startswith('auto_backup_')) or not (
            filename.endswith('.db') or 
            filename.endswith('.zip') or 
            filename.endswith('.enc.zip') or
            filename.endswith('.enc')
        ):
            return APIResponse.bad_request("无效的备份文件名")
        
        # 获取备份管理器
        backup_manager = get_backup_manager()
        backup_path = os.path.join(backup_manager.backup_folder, filename)
        
        if not os.path.exists(backup_path):
            return APIResponse.not_found("备份文件不存在")
        
        # 执行恢复
        restore_info = backup_manager.restore_backup(backup_path, create_pre_backup=True)
        
        current_app.logger.info(f"管理员 {g.username} 恢复了备份：{filename}")
        
        return APIResponse.success(restore_info, "数据恢复成功")
        
    except Exception as e:
        current_app.logger.error(f"恢复数据失败：{str(e)}\n{traceback.format_exc()}")
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
        if not (filename.startswith('backup_') or filename.startswith('auto_backup_')) or not (
            filename.endswith('.db') or 
            filename.endswith('.zip') or 
            filename.endswith('.enc.zip') or
            filename.endswith('.enc')
        ):
            return APIResponse.bad_request("无效的备份文件名")
        
        backup_manager = get_backup_manager()
        backup_path = os.path.join(backup_manager.backup_folder, filename)
        
        if not os.path.exists(backup_path):
            return APIResponse.not_found("备份文件不存在")
        
        # 删除备份文件
        os.remove(backup_path)
        
        # 更新数据库记录
        record = BackupRecord.query.filter(
            BackupRecord.filename == filename,
            BackupRecord.deleted_at.is_(None)
        ).first()
        
        if record:
            record.soft_delete()
        
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
                "enabled": true,
                "frequency": "daily",
                "backup_time": "02:00",
                "keep_count": 30,
                "backup_type": "full"
            }
        }
    """
    try:
        from app.models import BackupSettings
        db_settings = BackupSettings.get_settings()
        settings = db_settings.to_dict()
        
        return APIResponse.success(settings, "获取备份设置成功")
        
    except Exception as e:
        current_app.logger.error(f"获取备份设置失败：{str(e)}")
        return APIResponse.server_error("获取备份设置失败")


@backup_bp.route('/settings', methods=['PUT'])
@login_required
@admin_required
def update_backup_settings_route():
    """
    更新备份设置
    
    Request Body:
        {
            "enabled": true,
            "frequency": "daily",
            "backup_time": "02:00",
            "weekday": 1,
            "day_of_month": 1,
            "keep_count": 30,
            "backup_type": "full"
        }
        
    Response:
        {
            "success": true,
            "message": "备份设置更新成功"
        }
    """
    try:
        data = request.get_json()
        
        if not data:
            return APIResponse.bad_request("请求数据不能为空")
        
        from app.models import BackupSettings
        
        db_settings = BackupSettings.update_settings(data)
        
        enabled = db_settings.enabled
        frequency = db_settings.frequency
        backup_time = db_settings.backup_time
        keep_count = db_settings.keep_count
        
        config_updates = {
            'BACKUP_AUTO_ENABLED': enabled,
            'BACKUP_AUTO_TIME': backup_time,
            'BACKUP_RETENTION_DAYS': keep_count,
            'BACKUP_AUTO_FREQUENCY': frequency
        }
        
        for key, value in config_updates.items():
            current_app.config[key] = value
        
        # 重新配置调度器任务
        try:
            from app import scheduler
            from app.routes.backup import schedule_auto_backup_full
            
            # 移除旧任务
            scheduler.remove_job('auto_backup')
            
            # 解析新的备份时间
            hour, minute = map(int, backup_time.split(':'))
            
            # 添加新任务
            if frequency == 'daily':
                scheduler.add_job(
                    schedule_auto_backup_full,
                    'cron',
                    hour=hour,
                    minute=minute,
                    id='auto_backup',
                    replace_existing=True
                )
                current_app.logger.info(f"已重新配置每日自动备份任务：{backup_time}")
            elif frequency == 'weekly':
                scheduler.add_job(
                    schedule_auto_backup_full,
                    'cron',
                    hour=hour,
                    minute=minute,
                    day_of_week='mon',
                    id='auto_backup',
                    replace_existing=True
                )
                current_app.logger.info(f"已重新配置每周自动备份任务：周一 {backup_time}")
            elif frequency == 'monthly':
                scheduler.add_job(
                    schedule_auto_backup_full,
                    'cron',
                    hour=hour,
                    minute=minute,
                    day=1,
                    id='auto_backup',
                    replace_existing=True
                )
                current_app.logger.info(f"已重新配置每月自动备份任务：1日 {backup_time}")
        except Exception as e:
            current_app.logger.warning(f"重新配置调度器失败: {str(e)}")
        
        current_app.logger.info(f"管理员 {g.username} 更新了备份设置: {data}")
        
        return APIResponse.success(db_settings.to_dict(), "备份设置更新成功")
        
    except Exception as e:
        current_app.logger.error(f"更新备份设置失败：{str(e)}")
        return APIResponse.server_error("更新备份设置失败")


# ============================================================================
# 备份统计接口
# ============================================================================

@backup_bp.route('/stats', methods=['GET'])
@login_required
def get_backup_stats():
    """
    获取备份统计信息
    
    Query Parameters:
        days: 统计天数，默认 30
    
    Response:
        {
            "success": true,
            "data": {
                "total_backups": 100,
                "successful_backups": 95,
                "failed_backups": 5,
                "success_rate": 95.0,
                "average_size": 1048576,
                "average_size_mb": 1.0,
                "total_size": 104857600,
                "total_size_mb": 100.0,
                "average_duration": 5.5,
                "period_days": 30
            }
        }
    """
    try:
        days = request.args.get('days', 30, type=int)
        
        # 从数据库获取统计
        stats = BackupRecord.get_statistics(days)
        
        # 从监控器获取实时统计
        backup_monitor = get_backup_monitor()
        monitor_stats = backup_monitor.get_stats()
        
        # 合并统计信息
        result = {
            **stats,
            'backup_folder_size': monitor_stats.get('backup_folder_size', 0),
            'backup_folder_size_mb': monitor_stats.get('backup_folder_size_mb', 0),
            'disk_usage': monitor_stats.get('disk_usage'),
            'last_backup_time': monitor_stats.get('last_backup_time'),
            'last_backup_status': monitor_stats.get('last_backup_status')
        }
        
        return APIResponse.success(result, "获取备份统计信息成功")
        
    except Exception as e:
        current_app.logger.error(f"获取备份统计信息失败：{str(e)}")
        return APIResponse.server_error("获取备份统计信息失败")


# ============================================================================
# 备份健康状态接口
# ============================================================================

@backup_bp.route('/health', methods=['GET'])
@login_required
def get_backup_health():
    """
    获取备份健康状态
    
    Response:
        {
            "success": true,
            "data": {
                "status": "healthy",
                "issues": [],
                "recommendations": []
            }
        }
    """
    try:
        backup_monitor = get_backup_monitor()
        health = backup_monitor.get_health_status()
        
        return APIResponse.success(health, "获取备份健康状态成功")
        
    except Exception as e:
        current_app.logger.error(f"获取备份健康状态失败：{str(e)}")
        return APIResponse.server_error("获取备份健康状态失败")


# ============================================================================
# 备份告警接口
# ============================================================================

@backup_bp.route('/alerts', methods=['GET'])
@login_required
def get_backup_alerts():
    """
    获取备份告警列表
    
    Query Parameters:
        level: 告警级别过滤（info/warning/error/critical）
        acknowledged: 是否已确认（true/false）
        limit: 返回数量限制，默认 50
    
    Response:
        {
            "success": true,
            "data": {
                "alerts": [
                    {
                        "id": "20240101_120000_123456",
                        "level": "error",
                        "message": "备份失败",
                        "backup_id": "20240101_120000",
                        "timestamp": "2024-01-01T12:00:00",
                        "acknowledged": false
                    }
                ]
            }
        }
    """
    try:
        level = request.args.get('level')
        acknowledged = request.args.get('acknowledged', type=lambda x: x.lower() == 'true' if x else None)
        limit = request.args.get('limit', 50, type=int)
        
        backup_monitor = get_backup_monitor()
        alerts = backup_monitor.get_alerts(level=level, acknowledged=acknowledged, limit=limit)
        
        return APIResponse.success({
            'alerts': alerts
        }, "获取备份告警列表成功")
        
    except Exception as e:
        current_app.logger.error(f"获取备份告警列表失败：{str(e)}")
        return APIResponse.server_error("获取备份告警列表失败")


@backup_bp.route('/alerts/<alert_id>/acknowledge', methods=['POST'])
@admin_required
def acknowledge_alert(alert_id: str):
    """
    确认告警（仅管理员）
    
    Path Parameters:
        alert_id: 告警 ID
    
    Response:
        {
            "success": true,
            "message": "告警已确认"
        }
    """
    try:
        backup_monitor = get_backup_monitor()
        success = backup_monitor.acknowledge_alert(alert_id)
        
        if success:
            return APIResponse.success(None, "告警已确认")
        else:
            return APIResponse.not_found("告警不存在")
        
    except Exception as e:
        current_app.logger.error(f"确认告警失败：{str(e)}")
        return APIResponse.server_error("确认告警失败")


# ============================================================================
# 备份验证接口
# ============================================================================

@backup_bp.route('/verify/<filename>', methods=['POST'])
@login_required
def verify_backup(filename: str):
    """
    验证备份完整性
    
    Path Parameters:
        filename: 备份文件名
    
    Response:
        {
            "success": true,
            "data": {
                "valid": true,
                "backup_path": "/path/to/backup",
                "errors": [],
                "metadata": {}
            }
        }
    """
    try:
        # 验证文件名安全性
        if not filename.startswith('backup_') or not (
            filename.endswith('.db') or 
            filename.endswith('.zip') or 
            filename.endswith('.enc')
        ):
            return APIResponse.bad_request("无效的备份文件名")
        
        backup_manager = get_backup_manager()
        backup_path = os.path.join(backup_manager.backup_folder, filename)
        
        if not os.path.exists(backup_path):
            return APIResponse.not_found("备份文件不存在")
        
        # 验证备份
        result = backup_manager.verify_backup(backup_path)
        
        if result['valid']:
            return APIResponse.success(result, "备份验证通过")
        else:
            return APIResponse.success(result, "备份验证失败")
        
    except Exception as e:
        current_app.logger.error(f"验证备份失败：{str(e)}")
        return APIResponse.server_error(f"验证备份失败：{str(e)}")


# ============================================================================
# 定时备份任务
# ============================================================================

def schedule_auto_backup():
    """定时自动备份任务"""
    import os
    import sqlite3
    import shutil
    from datetime import datetime
    
    print("开始执行自动备份任务...")
    
    try:
        # 获取项目根目录
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        # 数据库路径
        db_path = os.path.join(base_dir, 'instance', 'housing_rental.db')
        
        # 备份目录
        backup_dir = os.path.join(base_dir, 'backups')
        os.makedirs(backup_dir, exist_ok=True)
        
        # 生成备份文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f'auto_backup_{timestamp}.db'
        backup_path = os.path.join(backup_dir, backup_filename)
        
        # 复制数据库文件（基础备份）
        if os.path.exists(db_path):
            shutil.copy2(db_path, backup_path)
            print(f"自动备份成功：{backup_filename}")
            
            # 记录到数据库
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # 检查 backup_records 表是否存在
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='backup_records'")
            if cursor.fetchone():
                backup_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                cursor.execute("""
                    INSERT INTO backup_records 
                    (backup_id, backup_type, status, start_time, end_time, filename, file_path, file_size, backup_by, backup_method, trigger, created_at, is_active)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    backup_id,
                    'full',
                    'success',
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    backup_filename,
                    backup_path,
                    os.path.getsize(backup_path),
                    'system',
                    'auto',
                    'scheduled',
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    1
                ))
                conn.commit()
            
            conn.close()
        else:
            print(f"数据库文件不存在：{db_path}")
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"自动备份任务执行失败：{str(e)}")


def schedule_auto_backup_full():
    """
    完整自动备份任务（推荐使用）
    
    使用 BackupManager 创建与手动备份相同格式的备份：
    - 加密压缩
    - 包含上传文件
    - 完整元数据
    """
    import os
    from datetime import datetime
    
    print("开始执行完整自动备份任务...")
    
    try:
        # 获取项目根目录
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        # 数据库路径
        db_path = os.path.join(base_dir, 'instance', 'housing_rental.db')
        
        # 导入备份管理器
        from app.utils.backup_manager import get_backup_manager
        
        # 获取全局备份管理器实例
        backup_manager = get_backup_manager()
        
        # 创建完整备份
        backup_info = backup_manager.create_full_backup(
            remark='系统自动备份',
            include_uploads=True
        )
        
        print(f"完整自动备份成功：{backup_info['filename']}")
        
        # 记录到数据库
        import sqlite3
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='backup_records'")
        if cursor.fetchone():
            backup_id = datetime.now().strftime('%Y%m%d_%H%M%S')
            import json
            cursor.execute("""
                INSERT INTO backup_records 
                (backup_id, backup_type, status, start_time, end_time, filename, file_path, file_size, 
                 file_hash, encrypted, compressed, includes_uploads, backup_by, backup_method, trigger, 
                 backup_metadata, created_at, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                backup_id,
                'full',
                'success',
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                backup_info.get('filename'),
                backup_info.get('backup_path'),
                backup_info.get('file_size'),
                backup_info.get('file_hash'),
                1 if backup_info.get('encrypted') else 0,
                1 if backup_info.get('compressed') else 0,
                1 if backup_info.get('includes_uploads') else 0,
                'system',
                'auto',
                'scheduled',
                json.dumps(backup_info),
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                1
            ))
            conn.commit()
        
        conn.close()
        
        # 清理过期备份
        deleted_count = backup_manager.cleanup_old_backups()
        if deleted_count > 0:
            print(f"清理了 {deleted_count} 个过期备份")
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"完整自动备份任务执行失败：{str(e)}")


def init_auto_backup(app):
    """
    初始化自动备份任务
    在调度器启动前添加定时任务
    """
    from app import scheduler
    
    try:
        backup_time = '02:00'
        backup_frequency = 'daily'
        weekday = 1
        
        with app.app_context():
            from app.models import BackupSettings
            
            db_settings = BackupSettings.get_settings()
            
            if not db_settings.enabled:
                app.logger.info("自动备份已禁用")
                return
            
            backup_time = db_settings.backup_time
            backup_frequency = db_settings.frequency
            weekday = db_settings.weekday
        
        hour, minute = map(int, backup_time.split(':'))
        
        if backup_frequency == 'daily':
            scheduler.add_job(
                schedule_auto_backup,
                'cron',
                hour=hour,
                minute=minute,
                id='auto_backup',
                replace_existing=True
            )
            app.logger.info(f"已配置每日自动备份任务：{backup_time}")
        
        elif backup_frequency == 'weekly':
            weekday_map = {0: 'sun', 1: 'mon', 2: 'tue', 3: 'wed', 4: 'thu', 5: 'fri', 6: 'sat'}
            day_of_week = weekday_map.get(weekday, 'mon')
            scheduler.add_job(
                schedule_auto_backup,
                'cron',
                hour=hour,
                minute=minute,
                day_of_week=day_of_week,
                id='auto_backup',
                replace_existing=True
            )
            weekday_names = {0: '周日', 1: '周一', 2: '周二', 3: '周三', 4: '周四', 5: '周五', 6: '周六'}
            app.logger.info(f"已配置每周自动备份任务：{weekday_names.get(weekday, '周一')} {backup_time}")
        
        elif backup_frequency == 'monthly':
            scheduler.add_job(
                schedule_auto_backup,
                'cron',
                hour=hour,
                minute=minute,
                day=1,
                id='auto_backup',
                replace_existing=True
            )
            app.logger.info(f"已配置每月自动备份任务：1日 {backup_time}")
            
    except Exception as e:
        app.logger.error(f"初始化自动备份任务失败：{str(e)}")
