"""
敏感数据访问审计工具模块
提供审计日志记录、查询、导出等功能
"""
from datetime import datetime
from functools import wraps
from flask import request, g, current_app
from typing import Optional, Dict, Any, List
import csv
import io
import json


class SensitiveDataAuditLogger:
    """
    敏感数据访问审计日志记录器
    
    提供便捷的审计日志记录方法，支持：
    - 自动获取用户信息
    - 自动获取请求信息
    - 记录数据变更
    - 异步日志记录（不影响主流程）
    """
    
    @staticmethod
    def get_current_user_info() -> Dict[str, Any]:
        """
        获取当前用户信息
        
        Returns:
            dict: 用户信息字典
        """
        user_info = {
            'user_id': None,
            'username': 'anonymous',
            'user_role': None
        }
        
        # 从 Flask g 对象获取用户信息
        if hasattr(g, 'current_user') and g.current_user:
            user_info['user_id'] = g.current_user.id
            user_info['username'] = g.current_user.username
            user_info['user_role'] = getattr(g.current_user, 'role', None)
        elif hasattr(g, 'user_id'):
            user_info['user_id'] = g.user_id
            user_info['username'] = getattr(g, 'username', 'unknown')
            user_info['user_role'] = getattr(g, 'user_role', None)
        
        return user_info
    
    @staticmethod
    def get_request_info() -> Dict[str, Any]:
        """
        获取请求信息
        
        Returns:
            dict: 请求信息字典
        """
        request_info = {
            'ip_address': None,
            'user_agent': None,
            'request_path': None,
            'request_method': None
        }
        
        try:
            # 获取真实 IP（支持代理）
            if request:
                # 优先从 X-Forwarded-For 获取
                forwarded_for = request.headers.get('X-Forwarded-For')
                if forwarded_for:
                    request_info['ip_address'] = forwarded_for.split(',')[0].strip()
                else:
                    request_info['ip_address'] = request.remote_addr
                
                request_info['user_agent'] = request.headers.get('User-Agent', '')[:500]
                request_info['request_path'] = request.path
                request_info['request_method'] = request.method
        except Exception:
            pass
        
        return request_info
    
    @staticmethod
    def mask_value(value: str, show_last: int = 4) -> str:
        """
        脱敏敏感数据
        
        Args:
            value: 原始值
            show_last: 显示最后几位
            
        Returns:
            str: 脱敏后的值
        """
        if not value:
            return None
        
        if len(value) <= show_last:
            return '*' * len(value)
        
        return '*' * (len(value) - show_last) + value[-show_last:]
    
    @staticmethod
    def log_sensitive_access(
        operation_type: str,
        model_name: str,
        record_id: int,
        field_name: str,
        field_display_name: str = None,
        old_value: str = None,
        new_value: str = None,
        success: bool = True,
        error_message: str = None,
        user_id: int = None,
        username: str = None,
        user_role: str = None,
        ip_address: str = None,
        remark: str = None
    ):
        """
        记录敏感数据访问日志（异步方式）
        
        Args:
            operation_type: 操作类型（view/modify/delete/export）
            model_name: 模型名称
            record_id: 记录 ID
            field_name: 字段名称
            field_display_name: 字段显示名称
            old_value: 变更前的值（脱敏）
            new_value: 变更后的值（脱敏）
            success: 操作是否成功
            error_message: 错误信息
            user_id: 用户 ID（可选，自动获取）
            username: 用户名（可选，自动获取）
            user_role: 用户角色（可选，自动获取）
            ip_address: IP 地址（可选，自动获取）
            remark: 备注信息
        """
        try:
            # 检查审计开关是否启用
            from app.routes.audit import audit_enabled
            if not audit_enabled:
                return
            
            # 检查是否启用了审计
            from flask import current_app
            if current_app and not current_app.config.get('ENCRYPTION_AUDIT_ENABLED', True):
                return
            
            from app.utils.async_audit import queue_sensitive_audit
            
            queue_sensitive_audit(
                operation_type=operation_type,
                model_name=model_name,
                record_id=record_id,
                field_name=field_name,
                field_display_name=field_display_name,
                old_value=old_value,
                new_value=new_value,
                success=success,
                error_message=error_message,
                user_id=user_id,
                username=username,
                user_role=user_role,
                ip_address=ip_address,
                remark=remark
            )
                
        except Exception as e:
            import logging
            logging.error(f"记录敏感数据访问审计日志失败: {str(e)}")
    
    @staticmethod
    def log_view(
        model_name: str,
        record_id: int,
        field_name: str,
        field_display_name: str = None,
        user_id: int = None,
        username: str = None,
        ip_address: str = None,
        remark: str = None
    ):
        """
        记录查看敏感数据操作
        
        Args:
            model_name: 模型名称
            record_id: 记录 ID
            field_name: 字段名称
            field_display_name: 字段显示名称
            user_id: 用户 ID
            username: 用户名
            ip_address: IP 地址
            remark: 备注信息
        """
        SensitiveDataAuditLogger.log_sensitive_access(
            operation_type='view',
            model_name=model_name,
            record_id=record_id,
            field_name=field_name,
            field_display_name=field_display_name,
            user_id=user_id,
            username=username,
            ip_address=ip_address,
            remark=remark
        )
    
    @staticmethod
    def log_modify(
        model_name: str,
        record_id: int,
        field_name: str,
        old_value: str = None,
        new_value: str = None,
        field_display_name: str = None,
        user_id: int = None,
        username: str = None,
        ip_address: str = None,
        remark: str = None
    ):
        """
        记录修改敏感数据操作
        
        Args:
            model_name: 模型名称
            record_id: 记录 ID
            field_name: 字段名称
            old_value: 变更前的值
            new_value: 变更后的值
            field_display_name: 字段显示名称
            user_id: 用户 ID
            username: 用户名
            ip_address: IP 地址
            remark: 备注信息
        """
        SensitiveDataAuditLogger.log_sensitive_access(
            operation_type='modify',
            model_name=model_name,
            record_id=record_id,
            field_name=field_name,
            field_display_name=field_display_name,
            old_value=old_value,
            new_value=new_value,
            user_id=user_id,
            username=username,
            ip_address=ip_address,
            remark=remark
        )
    
    @staticmethod
    def log_delete(
        model_name: str,
        record_id: int,
        field_name: str,
        old_value: str = None,
        field_display_name: str = None,
        user_id: int = None,
        username: str = None,
        ip_address: str = None,
        remark: str = None
    ):
        """
        记录删除敏感数据操作
        
        Args:
            model_name: 模型名称
            record_id: 记录 ID
            field_name: 字段名称
            old_value: 删除前的值
            field_display_name: 字段显示名称
            user_id: 用户 ID
            username: 用户名
            ip_address: IP 地址
            remark: 备注信息
        """
        SensitiveDataAuditLogger.log_sensitive_access(
            operation_type='delete',
            model_name=model_name,
            record_id=record_id,
            field_name=field_name,
            field_display_name=field_display_name,
            old_value=old_value,
            user_id=user_id,
            username=username,
            ip_address=ip_address,
            remark=remark
        )
    
    @staticmethod
    def log_export(
        model_name: str,
        record_ids: List[int],
        field_name: str,
        field_display_name: str = None,
        user_id: int = None,
        username: str = None,
        ip_address: str = None,
        remark: str = None
    ):
        """
        记录导出敏感数据操作
        
        Args:
            model_name: 模型名称
            record_ids: 记录 ID 列表
            field_name: 字段名称
            field_display_name: 字段显示名称
            user_id: 用户 ID
            username: 用户名
            ip_address: IP 地址
            remark: 备注信息
        """
        # 为每个记录创建一条日志
        for record_id in record_ids:
            SensitiveDataAuditLogger.log_sensitive_access(
                operation_type='export',
                model_name=model_name,
                record_id=record_id,
                field_name=field_name,
                field_display_name=field_display_name,
                user_id=user_id,
                username=username,
                ip_address=ip_address,
                remark=remark
            )


# ==================== 装饰器 ====================

def audit_sensitive_access(model_name: str, field_name: str, operation_type: str = 'view'):
    """
    敏感数据访问审计装饰器
    
    自动记录敏感数据访问操作
    
    Args:
        model_name: 模型名称
        field_name: 字段名称
        operation_type: 操作类型（view/modify/delete/export）
    
    使用示例:
        @audit_sensitive_access('Landlord', 'id_card', 'view')
        def get_landlord_id_card(landlord_id):
            # 获取房东身份证号
            pass
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            # 执行原函数
            result = f(*args, **kwargs)
            
            # 记录审计日志
            try:
                # 尝试从参数中获取 record_id
                record_id = kwargs.get('id') or kwargs.get('record_id') or kwargs.get('landlord_id') or kwargs.get('tenant_id')
                if not record_id and args:
                    # 尝试从位置参数获取
                    for arg in args:
                        if isinstance(arg, int):
                            record_id = arg
                            break
                        elif hasattr(arg, 'id'):
                            record_id = arg.id
                            break
                
                if record_id:
                    # 获取字段显示名称
                    from app.models.sensitive_data_audit import SensitiveDataAuditLog
                    field_display_name = None
                    if model_name in SensitiveDataAuditLog.SENSITIVE_FIELDS:
                        field_display_name = SensitiveDataAuditLog.SENSITIVE_FIELDS[model_name].get(field_name)
                    
                    # 记录日志
                    SensitiveDataAuditLogger.log_sensitive_access(
                        operation_type=operation_type,
                        model_name=model_name,
                        record_id=record_id,
                        field_name=field_name,
                        field_display_name=field_display_name
                    )
            except Exception as e:
                current_app.logger.error(f"审计装饰器记录日志失败: {str(e)}")
            
            return result
        
        return decorated
    
    return decorator


def audit_sensitive_view(model_name: str, field_name: str):
    """
    敏感数据查看审计装饰器
    
    Args:
        model_name: 模型名称
        field_name: 字段名称
    """
    return audit_sensitive_access(model_name, field_name, 'view')


def audit_sensitive_modify(model_name: str, field_name: str):
    """
    敏感数据修改审计装饰器
    
    Args:
        model_name: 模型名称
        field_name: 字段名称
    """
    return audit_sensitive_access(model_name, field_name, 'modify')


def audit_sensitive_delete(model_name: str, field_name: str):
    """
    敏感数据删除审计装饰器
    
    Args:
        model_name: 模型名称
        field_name: 字段名称
    """
    return audit_sensitive_access(model_name, field_name, 'delete')


# ==================== 导出工具 ====================

class AuditLogExporter:
    """
    审计日志导出工具
    
    支持导出为 CSV、JSON 格式
    """
    
    @staticmethod
    def export_to_csv(logs: List[Any], include_details: bool = False) -> str:
        """
        导出审计日志为 CSV 格式
        
        Args:
            logs: 审计日志列表
            include_details: 是否包含详细信息
            
        Returns:
            str: CSV 内容
        """
        if not logs:
            return ''
        
        output = io.StringIO()
        
        # CSV 表头
        fieldnames = [
            'ID', '操作类型', '模型名称', '记录ID', '字段名称', '字段显示名称',
            '用户ID', '用户名', '用户角色', 'IP地址', '操作时间',
            '是否成功', '错误信息', '请求路径', '请求方法'
        ]
        
        if include_details:
            fieldnames.extend(['变更前值', '变更后值', '备注'])
        
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        
        # 写入数据
        for log in logs:
            log_dict = log.to_detail_dict() if include_details else log.to_dict()
            
            row = {
                'ID': log_dict.get('id'),
                '操作类型': log_dict.get('operation_type_name'),
                '模型名称': log_dict.get('model_name'),
                '记录ID': log_dict.get('record_id'),
                '字段名称': log_dict.get('field_name'),
                '字段显示名称': log_dict.get('field_display_name'),
                '用户ID': log_dict.get('user_id'),
                '用户名': log_dict.get('username'),
                '用户角色': log_dict.get('user_role'),
                'IP地址': log_dict.get('ip_address'),
                '操作时间': log_dict.get('operation_time'),
                '是否成功': '成功' if log_dict.get('success') else '失败',
                '错误信息': log_dict.get('error_message'),
                '请求路径': log_dict.get('request_path'),
                '请求方法': log_dict.get('request_method')
            }
            
            if include_details:
                row['变更前值'] = log_dict.get('old_value')
                row['变更后值'] = log_dict.get('new_value')
                row['备注'] = log_dict.get('remark')
            
            writer.writerow(row)
        
        return output.getvalue()
    
    @staticmethod
    def export_to_json(logs: List[Any], include_details: bool = False) -> str:
        """
        导出审计日志为 JSON 格式
        
        Args:
            logs: 审计日志列表
            include_details: 是否包含详细信息
            
        Returns:
            str: JSON 内容
        """
        if not logs:
            return '[]'
        
        if include_details:
            data = [log.to_detail_dict() for log in logs]
        else:
            data = [log.to_dict() for log in logs]
        
        return json.dumps(data, ensure_ascii=False, indent=2)
    
    @staticmethod
    def export_statistics_to_csv(statistics: Dict[str, Any]) -> str:
        """
        导出统计信息为 CSV 格式
        
        Args:
            statistics: 统计信息字典
            
        Returns:
            str: CSV 内容
        """
        output = io.StringIO()
        writer = csv.writer(output)
        
        # 总体统计
        writer.writerow(['总体统计'])
        writer.writerow(['总操作数', statistics.get('total_operations', 0)])
        writer.writerow(['成功数', statistics.get('success_count', 0)])
        writer.writerow(['失败数', statistics.get('failed_count', 0)])
        writer.writerow(['成功率', f"{statistics.get('success_rate', 0):.2f}%"])
        writer.writerow([])
        
        # 按操作类型统计
        writer.writerow(['按操作类型统计'])
        writer.writerow(['操作类型', '操作数量'])
        for op in statistics.get('operation_statistics', []):
            writer.writerow([op.get('operation_type_name'), op.get('count')])
        writer.writerow([])
        
        # 按模型统计
        writer.writerow(['按模型统计'])
        writer.writerow(['模型名称', '操作数量'])
        for model in statistics.get('model_statistics', []):
            writer.writerow([model.get('model_name'), model.get('count')])
        writer.writerow([])
        
        # 按用户统计
        writer.writerow(['用户操作统计（Top 10）'])
        writer.writerow(['用户ID', '用户名', '操作数量'])
        for user in statistics.get('user_statistics', []):
            writer.writerow([user.get('user_id'), user.get('username'), user.get('count')])
        
        return output.getvalue()
