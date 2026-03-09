"""
审计日志辅助模块

提供便捷的审计日志记录功能
"""
from functools import wraps
from flask import request, g, current_app
from typing import Optional, Callable, Any
from app.utils.sensitive_data_audit import SensitiveDataAuditLogger


def audit_operation(
    operation_type: str,
    model_name: str,
    field_name: str,
    field_display_name: str = None,
    get_record_id: Callable = None,
    get_old_value: Callable = None,
    get_new_value: Callable = None
):
    """
    审计操作装饰器
    
    自动记录敏感操作的审计日志
    
    Args:
        operation_type: 操作类型（create/update/delete/view/export）
        model_name: 模型名称
        field_name: 字段名称
        field_display_name: 字段显示名称
        get_record_id: 获取记录 ID 的函数，参数为 (data, result)
        get_old_value: 获取旧值的函数，参数为 (data, result)
        get_new_value: 获取新值的函数，参数为 (data, result)
    
    使用示例:
        @audit_operation(
            operation_type='update',
            model_name='Contract',
            field_name='rent_amount',
            field_display_name='租金金额',
            get_record_id=lambda data, result: result.id,
            get_old_value=lambda data, result: str(data.get('old_amount')),
            get_new_value=lambda data, result: str(data.get('rent_amount'))
        )
        def update_contract(contract_id):
            # 更新合同逻辑
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
                record_id = None
                if get_record_id:
                    record_id = get_record_id(kwargs, result)
                else:
                    # 尝试从参数中获取 ID
                    record_id = kwargs.get('id') or kwargs.get('record_id') or kwargs.get('contract_id') or kwargs.get('payment_id') or kwargs.get('tenant_id') or kwargs.get('landlord_id') or kwargs.get('house_id')
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
                    # 获取旧值和新值
                    old_value = None
                    new_value = None
                    
                    if get_old_value:
                        old_value = get_old_value(kwargs, result)
                    elif operation_type == 'update' and field_name:
                        # 尝试从请求体获取旧值
                        if request.is_json:
                            data = request.get_json()
                            if isinstance(data, dict) and f'old_{field_name}' in data:
                                old_value = str(data[f'old_{field_name}'])
                    
                    if get_new_value:
                        new_value = get_new_value(kwargs, result)
                    elif operation_type in ['create', 'update'] and field_name:
                        # 尝试从请求体获取新值
                        if request.is_json:
                            data = request.get_json()
                            if isinstance(data, dict) and field_name in data:
                                new_value = str(data[field_name])
                    
                    # 记录审计日志
                    SensitiveDataAuditLogger.log_sensitive_access(
                        operation_type=operation_type,
                        model_name=model_name,
                        record_id=record_id if isinstance(record_id, int) else int(record_id) if str(record_id).isdigit() else 0,
                        field_name=field_name or 'general',
                        field_display_name=field_display_name,
                        old_value=old_value,
                        new_value=new_value,
                        success=True
                    )
            except Exception as e:
                # 记录错误但不影响主流程
                current_app.logger.error(f"审计日志记录失败: {str(e)}")
            
            return result
        
        return decorated
    
    return decorator


def audit_create(model_name: str, field_name: str = None, field_display_name: str = None):
    """
    创建操作审计装饰器
    
    Args:
        model_name: 模型名称
        field_name: 字段名称
        field_display_name: 字段显示名称
    """
    return audit_operation('create', model_name, field_name, field_display_name)


def audit_update(model_name: str, field_name: str = None, field_display_name: str = None):
    """
    更新操作审计装饰器
    
    Args:
        model_name: 模型名称
        field_name: 字段名称
        field_display_name: 字段显示名称
    """
    return audit_operation('update', model_name, field_name, field_display_name)


def audit_delete(model_name: str, field_name: str = None, field_display_name: str = None):
    """
    删除操作审计装饰器
    
    Args:
        model_name: 模型名称
        field_name: 字段名称
        field_display_name: 字段显示名称
    """
    return audit_operation('delete', model_name, field_name, field_display_name)


def audit_amount_change(model_name: str, field_name: str, field_display_name: str, get_record_id: Callable = None):
    """
    金额变更审计装饰器
    
    专门用于记录金额类字段的变更
    
    Args:
        model_name: 模型名称
        field_name: 字段名称
        field_display_name: 字段显示名称
        get_record_id: 获取记录 ID 的函数
    """
    return audit_operation(
        operation_type='update',
        model_name=model_name,
        get_record_id=get_record_id,
        field_name=field_name,
        field_display_name=field_display_name
    )


class AuditContext:
    """
    审计上下文管理器
    
    用于在代码块中自动记录审计日志
    """
    
    def __init__(
        self,
        operation_type: str,
        model_name: str,
        record_id: int,
        field_name: str,
        field_display_name: str = None,
        old_value: str = None
    ):
        self.operation_type = operation_type
        self.model_name = model_name
        self.record_id = record_id
        self.field_name = field_name
        self.field_display_name = field_display_name
        self.old_value = old_value
        self.new_value = None
        self.success = True
        self.error_message = None
    
    def set_new_value(self, value: str):
        """设置新值"""
        self.new_value = value
    
    def set_error(self, error_message: str):
        """设置错误信息"""
        self.success = False
        self.error_message = error_message
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # 记录审计日志
        try:
            if exc_type:
                self.success = False
                self.error_message = str(exc_val)
            
            SensitiveDataAuditLogger.log_sensitive_access(
                operation_type=self.operation_type,
                model_name=self.model_name,
                record_id=self.record_id,
                field_name=self.field_name,
                field_display_name=self.field_display_name,
                old_value=self.old_value,
                new_value=self.new_value,
                success=self.success,
                error_message=self.error_message
            )
        except Exception as e:
            current_app.logger.error(f"审计上下文记录日志失败: {str(e)}")
        
        # 不抑制异常
        return False


def log_audit(
    operation_type: str,
    model_name: str,
    record_id: int,
    field_name: str,
    field_display_name: str = None,
    old_value: str = None,
    new_value: str = None,
    remark: str = None
):
    """
    便捷的审计日志记录函数
    
    Args:
        operation_type: 操作类型
        model_name: 模型名称
        record_id: 记录 ID
        field_name: 字段名称
        field_display_name: 字段显示名称
        old_value: 旧值
        new_value: 新值
        remark: 备注
    """
    try:
        SensitiveDataAuditLogger.log_sensitive_access(
            operation_type=operation_type,
            model_name=model_name,
            record_id=record_id,
            field_name=field_name,
            field_display_name=field_display_name,
            old_value=old_value,
            new_value=new_value,
            remark=remark
        )
    except Exception as e:
        current_app.logger.error(f"记录审计日志失败: {str(e)}")
