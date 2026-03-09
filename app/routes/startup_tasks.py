"""
启动任务状态查询 API

提供任务执行状态和日志查询接口
"""
from flask import Blueprint, jsonify, request
from app.utils.startup_tasks import get_task_manager
from app.utils.responses import APIResponse
from app.utils.decorators import admin_required, login_required


startup_tasks_bp = Blueprint('startup_tasks', __name__)


@startup_tasks_bp.route('/status', methods=['GET'])
@login_required
def get_task_status():
    """
    获取任务执行状态
    
    Query Parameters:
        task_name: 任务名称（可选）
        task_date: 任务日期（可选，格式：YYYY-MM-DD）
    
    Returns:
        任务状态列表
    """
    try:
        task_name = request.args.get('task_name')
        task_date = request.args.get('task_date')
        
        if task_date:
            from datetime import datetime
            try:
                task_date = datetime.strptime(task_date, '%Y-%m-%d').date()
            except ValueError:
                return APIResponse.error('validation_error', '日期格式错误，应为 YYYY-MM-DD', 400)
        
        manager = get_task_manager()
        status = manager.get_task_status(task_name=task_name, task_date=task_date)
        
        return APIResponse.success(data=status)
        
    except Exception as e:
        return APIResponse.error('server_error', f'获取任务状态失败: {str(e)}', 500)


@startup_tasks_bp.route('/logs', methods=['GET'])
@login_required
def get_task_logs():
    """
    获取任务执行日志
    
    Query Parameters:
        task_name: 任务名称（可选）
        limit: 返回记录数量限制（默认 100）
    
    Returns:
        任务日志列表
    """
    try:
        task_name = request.args.get('task_name')
        limit = request.args.get('limit', 100, type=int)
        
        if limit < 1 or limit > 1000:
            return APIResponse.error('validation_error', 'limit 参数应在 1-1000 之间', 400)
        
        manager = get_task_manager()
        logs = manager.get_task_logs(task_name=task_name, limit=limit)
        
        return APIResponse.success(data=logs)
        
    except Exception as e:
        return APIResponse.error('server_error', f'获取任务日志失败: {str(e)}', 500)


@startup_tasks_bp.route('/config', methods=['GET'])
@admin_required
def get_task_config():
    """
    获取任务配置信息（管理员）
    
    Returns:
        任务配置信息
    """
    try:
        manager = get_task_manager()
        
        config = {
            'enabled': manager.config.get('enabled'),
            'batch_size': manager.config.get('batch_size'),
            'timeout': manager.config.get('timeout'),
            'delay': manager.config.get('delay'),
            'tasks': list(manager.tasks.keys())
        }
        
        return APIResponse.success(data=config)
        
    except Exception as e:
        return APIResponse.error('server_error', f'获取任务配置失败: {str(e)}', 500)


@startup_tasks_bp.route('/summary', methods=['GET'])
@login_required
def get_task_summary():
    """
    获取任务执行摘要
    
    Returns:
        今日任务执行摘要
    """
    try:
        from datetime import date
        manager = get_task_manager()
        
        today = date.today()
        today_records = manager.get_task_status(task_date=today)
        
        total = len(today_records)
        completed = sum(1 for r in today_records if r.get('status') == 'completed')
        running = sum(1 for r in today_records if r.get('status') == 'running')
        failed = sum(1 for r in today_records if r.get('status') == 'failed')
        pending = sum(1 for r in today_records if r.get('status') == 'pending')
        
        summary = {
            'date': today.strftime('%Y-%m-%d'),
            'total': total,
            'completed': completed,
            'running': running,
            'failed': failed,
            'pending': pending,
            'tasks': today_records
        }
        
        return APIResponse.success(data=summary)
        
    except Exception as e:
        return APIResponse.error('server_error', f'获取任务摘要失败: {str(e)}', 500)
