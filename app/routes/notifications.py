"""
通知管理路由模块
提供批量发送通知等功能
"""
from flask import Blueprint, request, jsonify, g, current_app
from typing import Dict, Any
from datetime import datetime

from app.models.tenant import Tenant
from app.models.contract import Contract
from app.models import db
from app.utils.decorators import login_required, admin_required, permission_required
from app.utils.responses import APIResponse

notifications_bp = Blueprint('notifications', __name__, url_prefix='/api/notifications')


@notifications_bp.route('/batch-send', methods=['POST'])
@login_required
@permission_required('edit')
def batch_send_notifications():
    """
    批量发送通知
    
    Request Body:
        {
            "tenant_ids": [1, 2, 3],
            "message": "催收通知内容"
        }
        
    Response:
        {
            "success": true,
            "message": "批量发送成功",
            "data": {
                "sent_count": 3,
                "failed_count": 0,
                "details": [...]
            }
        }
    """
    try:
        data = request.get_json()
        
        if not data:
            return APIResponse.bad_request("请求数据不能为空")
        
        tenant_ids = data.get('tenant_ids', [])
        message = data.get('message')
        
        if not tenant_ids:
            return APIResponse.bad_request("租客 ID 列表不能为空")
        
        if not isinstance(tenant_ids, list):
            return APIResponse.bad_request("tenant_ids 必须是数组")
        
        if not message:
            return APIResponse.bad_request("通知内容不能为空")
        
        if not isinstance(message, str):
            return APIResponse.bad_request("通知内容必须是字符串")
        
        if len(message) > 500:
            return APIResponse.bad_request("通知内容不能超过 500 个字符")
        
        sent_count = 0
        failed_count = 0
        details = []
        
        for tenant_id in tenant_ids:
            try:
                tenant = Tenant.query.get(tenant_id)
                
                if not tenant:
                    details.append({
                        'tenant_id': tenant_id,
                        'success': False,
                        'message': '租客不存在'
                    })
                    failed_count += 1
                    continue
                
                active_contracts = tenant.get_active_contracts()
                
                notification_data = {
                    'tenant_id': tenant_id,
                    'tenant_name': tenant.name,
                    'tenant_phone': tenant.phone,
                    'message': message,
                    'sent_at': datetime.now().isoformat(),
                    'active_contracts_count': len(active_contracts)
                }
                
                current_app.logger.info(
                    f"用户 {g.username} 向租客 {tenant.name}({tenant.phone}) 发送通知：{message}"
                )
                
                details.append({
                    'tenant_id': tenant_id,
                    'success': True,
                    'tenant_name': tenant.name,
                    'tenant_phone': tenant.phone,
                    'message': '发送成功'
                })
                sent_count += 1
                
            except Exception as e:
                details.append({
                    'tenant_id': tenant_id,
                    'success': False,
                    'message': str(e)
                })
                failed_count += 1
        
        current_app.logger.info(
            f"用户 {g.username} 批量发送通知：成功 {sent_count} 条，失败 {failed_count} 条"
        )
        
        return APIResponse.success({
            'sent_count': sent_count,
            'failed_count': failed_count,
            'details': details
        }, f"批量发送成功：{sent_count} 条通知已发送")
        
    except Exception as e:
        current_app.logger.error(f"批量发送通知失败：{str(e)}")
        return APIResponse.server_error("批量发送通知失败")


@notifications_bp.route('/send', methods=['POST'])
@login_required
@permission_required('edit')
def send_notification():
    """
    发送单个通知
    
    Request Body:
        {
            "tenant_id": 1,
            "message": "通知内容"
        }
        
    Response:
        {
            "success": true,
            "message": "发送成功",
            "data": {
                "tenant_id": 1,
                "tenant_name": "张三",
                "tenant_phone": "13800138000",
                "message": "通知内容",
                "sent_at": "2024-01-01T12:00:00"
            }
        }
    """
    try:
        data = request.get_json()
        
        if not data:
            return APIResponse.bad_request("请求数据不能为空")
        
        tenant_id = data.get('tenant_id')
        message = data.get('message')
        
        if not tenant_id:
            return APIResponse.bad_request("租客 ID 不能为空")
        
        if not message:
            return APIResponse.bad_request("通知内容不能为空")
        
        if not isinstance(message, str):
            return APIResponse.bad_request("通知内容必须是字符串")
        
        if len(message) > 500:
            return APIResponse.bad_request("通知内容不能超过 500 个字符")
        
        tenant = Tenant.query.get(tenant_id)
        
        if not tenant:
            return APIResponse.not_found("租客不存在")
        
        active_contracts = tenant.get_active_contracts()
        
        notification_data = {
            'tenant_id': tenant_id,
            'tenant_name': tenant.name,
            'tenant_phone': tenant.phone,
            'message': message,
            'sent_at': datetime.now().isoformat(),
            'active_contracts_count': len(active_contracts)
        }
        
        current_app.logger.info(
            f"用户 {g.username} 向租客 {tenant.name}({tenant.phone}) 发送通知：{message}"
        )
        
        return APIResponse.success(notification_data, "通知发送成功")
        
    except Exception as e:
        current_app.logger.error(f"发送通知失败：{str(e)}")
        return APIResponse.server_error("发送通知失败")
