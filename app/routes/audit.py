"""
敏感数据访问审计日志 API 路由
提供审计日志查询、导出、统计等功能
"""
from flask import Blueprint, request, jsonify, g, current_app, make_response
from datetime import datetime, timedelta
from typing import Optional

from app.models.sensitive_data_audit import SensitiveDataAuditLog
from app.models.base import db
from app.utils.decorators import login_required, admin_required
from app.utils.sensitive_data_audit import (
    SensitiveDataAuditLogger,
    AuditLogExporter
)

# 创建蓝图
audit_bp = Blueprint('audit', __name__, url_prefix='/api/audit')

# 审计日志开关状态（默认关闭）
audit_enabled = False


# ============================================================================
# 审计日志开关接口
# ============================================================================

@audit_bp.route('/toggle', methods=['GET'])
@login_required
def get_audit_toggle():
    """
    获取审计日志开关状态
    
    Response:
    {
        "success": true,
        "data": {
            "enabled": false
        }
    }
    """
    try:
        return jsonify({
            'success': True,
            'data': {
                'enabled': audit_enabled
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"获取审计开关状态失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'get_audit_toggle_failed',
                'message': '获取审计开关状态失败'
            }
        }), 500


@audit_bp.route('/toggle', methods=['PUT'])
@admin_required
def update_audit_toggle():
    """
    更新审计日志开关状态（仅管理员）
    
    Request Body:
    {
        "enabled": true
    }
    
    Response:
    {
        "success": true,
        "data": {
            "enabled": true
        }
    }
    """
    global audit_enabled
    
    try:
        data = request.get_json()
        
        if not data or 'enabled' not in data:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'invalid_request',
                    'message': '请求参数无效，缺少 enabled 字段'
                }
            }), 400
        
        enabled = data['enabled']
        
        if not isinstance(enabled, bool):
            return jsonify({
                'success': False,
                'error': {
                    'code': 'invalid_request',
                    'message': 'enabled 字段必须为布尔值'
                }
            }), 400
        
        audit_enabled = enabled
        
        current_app.logger.info(f"审计日志开关已{'启用' if audit_enabled else '禁用'}")
        
        return jsonify({
            'success': True,
            'data': {
                'enabled': audit_enabled
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"更新审计开关状态失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'update_audit_toggle_failed',
                'message': '更新审计开关状态失败'
            }
        }), 500


# ============================================================================
# 审计日志查询接口
# ============================================================================

@audit_bp.route('/logs', methods=['GET'])
@login_required
def get_audit_logs():
    """
    获取审计日志列表
    
    Query Parameters:
        page: 页码（默认 1）
        per_page: 每页数量（默认 20，最大 100）
        user_id: 用户 ID（可选）
        model_name: 模型名称（可选）
        record_id: 记录 ID（可选）
        field_name: 字段名称（可选）
        operation_type: 操作类型（可选，view/modify/delete/export）
        success: 操作是否成功（可选，true/false）
        start_date: 开始日期（可选，格式：YYYY-MM-DD）
        end_date: 结束日期（可选，格式：YYYY-MM-DD）
        ip_address: IP 地址（可选）
    
    Response:
    {
        "success": true,
        "data": {
            "logs": [...],
            "pagination": {
                "page": 1,
                "per_page": 20,
                "total": 100,
                "pages": 5
            }
        }
    }
    """
    # 检查审计功能是否启用
    if not audit_enabled:
        return jsonify({
            'success': False,
            'error': {
                'code': 'audit_disabled',
                'message': '审计日志功能已禁用'
            }
        }), 403
    
    try:
        # 获取分页参数
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        per_page = min(per_page, 100)  # 限制最大每页数量
        
        # 构建查询（使用 db.session.query 避免 SoftDeleteQuery 的 paginate 问题）
        query = db.session.query(SensitiveDataAuditLog).filter(SensitiveDataAuditLog.deleted_at.is_(None))
        
        # 过滤条件
        user_id = request.args.get('user_id', type=int)
        if user_id:
            query = query.filter(SensitiveDataAuditLog.user_id == user_id)
        
        model_name = request.args.get('model_name')
        if model_name:
            query = query.filter(SensitiveDataAuditLog.model_name == model_name)
        
        record_id = request.args.get('record_id', type=int)
        if record_id:
            query = query.filter(SensitiveDataAuditLog.record_id == record_id)
        
        field_name = request.args.get('field_name')
        if field_name:
            query = query.filter(SensitiveDataAuditLog.field_name == field_name)
        
        operation_type = request.args.get('operation_type')
        if operation_type:
            query = query.filter(SensitiveDataAuditLog.operation_type == operation_type)
        
        success = request.args.get('success')
        if success is not None:
            success_bool = success.lower() == 'true'
            query = query.filter(SensitiveDataAuditLog.success == success_bool)
        
        ip_address = request.args.get('ip_address')
        if ip_address:
            query = query.filter(SensitiveDataAuditLog.ip_address.like(f'%{ip_address}%'))
        
        # 时间范围过滤
        start_date = request.args.get('start_date')
        if start_date:
            try:
                start_dt = datetime.strptime(start_date, '%Y-%m-%d')
                query = query.filter(SensitiveDataAuditLog.operation_time >= start_dt)
            except ValueError:
                pass
        
        end_date = request.args.get('end_date')
        if end_date:
            try:
                end_dt = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
                query = query.filter(SensitiveDataAuditLog.operation_time <= end_dt)
            except ValueError:
                pass
        
        # 排序和分页
        query = query.order_by(SensitiveDataAuditLog.operation_time.desc())
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        # 构建响应
        logs = [log.to_dict() for log in pagination.items]
        
        return jsonify({
            'success': True,
            'data': {
                'logs': logs,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': pagination.total,
                    'pages': pagination.pages
                }
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"获取审计日志失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'get_audit_logs_failed',
                'message': '获取审计日志失败'
            }
        }), 500


@audit_bp.route('/logs/<int:log_id>', methods=['GET'])
@login_required
def get_audit_log_detail(log_id: int):
    """
    获取审计日志详情
    
    Response:
    {
        "success": true,
        "data": {
            "id": 1,
            "operation_type": "view",
            "model_name": "Landlord",
            ...
        }
    }
    """
    try:
        log = SensitiveDataAuditLog.query.get(log_id)
        
        if not log:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'log_not_found',
                    'message': '审计日志不存在'
                }
            }), 404
        
        return jsonify({
            'success': True,
            'data': log.to_detail_dict()
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"获取审计日志详情失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'get_audit_log_detail_failed',
                'message': '获取审计日志详情失败'
            }
        }), 500


@audit_bp.route('/logs/user/<int:user_id>', methods=['GET'])
@login_required
def get_user_audit_logs(user_id: int):
    """
    获取指定用户的审计日志
    
    Query Parameters:
        limit: 返回数量限制（默认 50）
    
    Response:
    {
        "success": true,
        "data": {
            "logs": [...]
        }
    }
    """
    try:
        limit = request.args.get('limit', 50, type=int)
        limit = min(limit, 200)
        
        logs = SensitiveDataAuditLog.get_logs_by_user(user_id, limit)
        
        return jsonify({
            'success': True,
            'data': {
                'logs': [log.to_dict() for log in logs]
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"获取用户审计日志失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'get_user_audit_logs_failed',
                'message': '获取用户审计日志失败'
            }
        }), 500


@audit_bp.route('/logs/record/<model_name>/<int:record_id>', methods=['GET'])
@login_required
def get_record_audit_logs(model_name: str, record_id: int):
    """
    获取指定记录的审计日志
    
    Query Parameters:
        limit: 返回数量限制（默认 50）
    
    Response:
    {
        "success": true,
        "data": {
            "logs": [...]
        }
    }
    """
    try:
        limit = request.args.get('limit', 50, type=int)
        limit = min(limit, 200)
        
        logs = SensitiveDataAuditLog.get_logs_by_record(model_name, record_id, limit)
        
        return jsonify({
            'success': True,
            'data': {
                'logs': [log.to_dict() for log in logs]
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"获取记录审计日志失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'get_record_audit_logs_failed',
                'message': '获取记录审计日志失败'
            }
        }), 500


# ============================================================================
# 审计日志统计接口
# ============================================================================

@audit_bp.route('/statistics', methods=['GET'])
@admin_required
def get_audit_statistics():
    """
    获取审计日志统计信息
    
    Query Parameters:
        start_date: 开始日期（可选，格式：YYYY-MM-DD）
        end_date: 结束日期（可选，格式：YYYY-MM-DD）
    
    Response:
    {
        "success": true,
        "data": {
            "total_operations": 1000,
            "success_count": 950,
            "failed_count": 50,
            "success_rate": 95.0,
            "operation_statistics": [...],
            "model_statistics": [...],
            "user_statistics": [...],
            "hourly_statistics": [...]
        }
    }
    """
    # 检查审计功能是否启用
    if not audit_enabled:
        return jsonify({
            'success': True,
            'data': {
                'total_operations': 0,
                'success_count': 0,
                'failed_count': 0,
                'success_rate': 0.0,
                'operation_statistics': [],
                'model_statistics': [],
                'user_statistics': [],
                'hourly_statistics': [],
                'message': '审计日志功能已禁用'
            }
        }), 200
    
    try:
        # 时间范围
        start_date = None
        end_date = None
        
        start_date_str = request.args.get('start_date')
        if start_date_str:
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            except ValueError:
                pass
        
        end_date_str = request.args.get('end_date')
        if end_date_str:
            try:
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d') + timedelta(days=1)
            except ValueError:
                pass
        
        # 获取统计信息
        statistics = SensitiveDataAuditLog.get_statistics(start_date, end_date)
        
        return jsonify({
            'success': True,
            'data': statistics
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"获取审计统计信息失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'get_audit_statistics_failed',
                'message': '获取审计统计信息失败'
            }
        }), 500


@audit_bp.route('/statistics/user/<int:user_id>', methods=['GET'])
@login_required
def get_user_activity_summary(user_id: int):
    """
    获取用户活动摘要
    
    Query Parameters:
        days: 统计天数（默认 30）
    
    Response:
    {
        "success": true,
        "data": {
            "user_id": 1,
            "period_days": 30,
            "operations": [...],
            "models": [...],
            "recent_activities": [...]
        }
    }
    """
    try:
        days = request.args.get('days', 30, type=int)
        days = min(days, 365)  # 限制最大天数
        
        summary = SensitiveDataAuditLog.get_user_activity_summary(user_id, days)
        
        return jsonify({
            'success': True,
            'data': summary
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"获取用户活动摘要失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'get_user_activity_summary_failed',
                'message': '获取用户活动摘要失败'
            }
        }), 500


@audit_bp.route('/alerts', methods=['GET'])
@admin_required
def get_sensitive_access_alerts():
    """
    获取敏感数据访问预警
    
    检测短时间内频繁访问敏感数据的行为
    
    Query Parameters:
        threshold: 访问次数阈值（默认 10）
        hours: 时间窗口（小时，默认 1）
    
    Response:
    {
        "success": true,
        "data": {
            "alerts": [...]
        }
    }
    """
    try:
        threshold = request.args.get('threshold', 10, type=int)
        hours = request.args.get('hours', 1, type=int)
        
        alerts = SensitiveDataAuditLog.get_sensitive_access_alert(threshold, hours)
        
        return jsonify({
            'success': True,
            'data': {
                'alerts': alerts,
                'threshold': threshold,
                'time_window_hours': hours,
                'alert_count': len(alerts)
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"获取敏感数据访问预警失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'get_alerts_failed',
                'message': '获取敏感数据访问预警失败'
            }
        }), 500


# ============================================================================
# 审计日志导出接口
# ============================================================================

@audit_bp.route('/export', methods=['GET'])
@admin_required
def export_audit_logs():
    """
    导出审计日志
    
    Query Parameters:
        format: 导出格式（csv/json，默认 csv）
        include_details: 是否包含详细信息（默认 false）
        user_id: 用户 ID（可选）
        model_name: 模型名称（可选）
        operation_type: 操作类型（可选）
        start_date: 开始日期（可选，格式：YYYY-MM-DD）
        end_date: 结束日期（可选，格式：YYYY-MM-DD）
        limit: 导出数量限制（默认 1000，最大 5000）
    
    Response:
        CSV 或 JSON 文件下载
    """
    # 检查审计功能是否启用
    if not audit_enabled:
        return jsonify({
            'success': False,
            'error': {
                'code': 'audit_disabled',
                'message': '审计日志功能已禁用，无法导出'
            }
        }), 403
    
    try:
        # 获取导出参数
        export_format = request.args.get('format', 'csv').lower()
        include_details = request.args.get('include_details', 'false').lower() == 'true'
        limit = request.args.get('limit', 1000, type=int)
        limit = min(limit, 5000)
        
        # 构建查询（使用 db.session.query 避免 SoftDeleteQuery 的问题）
        query = db.session.query(SensitiveDataAuditLog).filter(SensitiveDataAuditLog.deleted_at.is_(None))
        
        # 过滤条件
        user_id = request.args.get('user_id', type=int)
        if user_id:
            query = query.filter(SensitiveDataAuditLog.user_id == user_id)
        
        model_name = request.args.get('model_name')
        if model_name:
            query = query.filter(SensitiveDataAuditLog.model_name == model_name)
        
        operation_type = request.args.get('operation_type')
        if operation_type:
            query = query.filter(SensitiveDataAuditLog.operation_type == operation_type)
        
        # 时间范围过滤
        start_date = request.args.get('start_date')
        if start_date:
            try:
                start_dt = datetime.strptime(start_date, '%Y-%m-%d')
                query = query.filter(SensitiveDataAuditLog.operation_time >= start_dt)
            except ValueError:
                pass
        
        end_date = request.args.get('end_date')
        if end_date:
            try:
                end_dt = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
                query = query.filter(SensitiveDataAuditLog.operation_time <= end_dt)
            except ValueError:
                pass
        
        # 获取数据
        logs = query.order_by(SensitiveDataAuditLog.operation_time.desc()).limit(limit).all()
        
        # 导出
        if export_format == 'json':
            content = AuditLogExporter.export_to_json(logs, include_details)
            filename = f'audit_logs_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
            mimetype = 'application/json'
        else:
            content = AuditLogExporter.export_to_csv(logs, include_details)
            filename = f'audit_logs_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
            mimetype = 'text/csv'
        
        # 创建响应
        response = make_response(content)
        response.headers['Content-Type'] = mimetype
        response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response
        
    except Exception as e:
        current_app.logger.error(f"导出审计日志失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'export_audit_logs_failed',
                'message': '导出审计日志失败'
            }
        }), 500


@audit_bp.route('/export/statistics', methods=['GET'])
@admin_required
def export_audit_statistics():
    """
    导出审计统计信息
    
    Query Parameters:
        start_date: 开始日期（可选，格式：YYYY-MM-DD）
        end_date: 结束日期（可选，格式：YYYY-MM-DD）
    
    Response:
        CSV 文件下载
    """
    try:
        # 时间范围
        start_date = None
        end_date = None
        
        start_date_str = request.args.get('start_date')
        if start_date_str:
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            except ValueError:
                pass
        
        end_date_str = request.args.get('end_date')
        if end_date_str:
            try:
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d') + timedelta(days=1)
            except ValueError:
                pass
        
        # 获取统计信息
        statistics = SensitiveDataAuditLog.get_statistics(start_date, end_date)
        
        # 导出为 CSV
        content = AuditLogExporter.export_statistics_to_csv(statistics)
        filename = f'audit_statistics_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        
        # 创建响应
        response = make_response(content)
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response
        
    except Exception as e:
        current_app.logger.error(f"导出审计统计信息失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'export_audit_statistics_failed',
                'message': '导出审计统计信息失败'
            }
        }), 500


# ============================================================================
# 敏感字段配置接口
# ============================================================================

@audit_bp.route('/sensitive-fields', methods=['GET'])
@login_required
def get_sensitive_fields():
    """
    获取敏感字段配置
    
    Response:
    {
        "success": true,
        "data": {
            "sensitive_fields": {
                "Landlord": {
                    "id_card": "身份证号",
                    "bank_card": "银行卡号"
                },
                ...
            }
        }
    }
    """
    try:
        return jsonify({
            'success': True,
            'data': {
                'sensitive_fields': SensitiveDataAuditLog.SENSITIVE_FIELDS
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"获取敏感字段配置失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'get_sensitive_fields_failed',
                'message': '获取敏感字段配置失败'
            }
        }), 500


# ============================================================================
# 操作类型配置接口
# ============================================================================

@audit_bp.route('/operation-types', methods=['GET'])
@login_required
def get_operation_types():
    """
    获取操作类型配置
    
    Response:
    {
        "success": true,
        "data": {
            "operation_types": {
                "view": "查看",
                "modify": "修改",
                "delete": "删除",
                "export": "导出"
            }
        }
    }
    """
    try:
        return jsonify({
            'success': True,
            'data': {
                'operation_types': SensitiveDataAuditLog.OPERATION_TYPES
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"获取操作类型配置失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'get_operation_types_failed',
                'message': '获取操作类型配置失败'
            }
        }), 500
