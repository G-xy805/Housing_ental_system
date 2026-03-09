"""
押金退款路由模块
提供退款列表、详情、处理、完成、取消等功能
"""
from flask import Blueprint, request, g, current_app
from datetime import datetime
from typing import Dict

from app.models.deposit_refund import DepositRefund
from app.models.contract import Contract
from app.models import db
from app.utils.decorators import login_required, admin_required, permission_required
from app.utils.responses import APIResponse

deposit_refunds_bp = Blueprint('deposit_refunds', __name__, url_prefix='/api/deposit-refunds')


@deposit_refunds_bp.route('', methods=['GET'])
@login_required
def get_deposit_refunds():
    """
    获取退款列表（支持分页、筛选）
    
    Query Parameters:
        page: 页码，默认 1
        per_page: 每页数量，默认 20，最大 100
        status: 状态筛选 (pending/processed/completed/cancelled)
        contract_id: 合同 ID 筛选
        tenant_id: 租客 ID 筛选
        house_id: 房源 ID 筛选
        
    Response:
        {
            "success": true,
            "message": "获取成功",
            "data": {
                "items": [...],
                "pagination": {...}
            }
        }
    """
    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        
        query = DepositRefund.query.filter(DepositRefund.deleted_at.is_(None))
        
        status = request.args.get('status')
        if status and status.strip():
            valid_statuses = ['pending', 'processed', 'completed', 'cancelled']
            if status not in valid_statuses:
                return APIResponse.bad_request("状态必须是：pending、processed、completed、cancelled")
            query = query.filter(DepositRefund.status == status)
        
        contract_id = request.args.get('contract_id', type=int)
        if contract_id:
            query = query.filter(DepositRefund.contract_id == contract_id)
        
        tenant_id = request.args.get('tenant_id', type=int)
        if tenant_id:
            query = query.filter(DepositRefund.tenant_id == tenant_id)
        
        house_id = request.args.get('house_id', type=int)
        if house_id:
            query = query.filter(DepositRefund.house_id == house_id)
        
        query = query.order_by(DepositRefund.created_at.desc())
        
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        items = [refund.to_dict() for refund in pagination.items]
        
        pagination_info = {
            'page': pagination.page,
            'per_page': pagination.per_page,
            'total': pagination.total,
            'pages': pagination.pages,
            'has_next': pagination.has_next,
            'has_prev': pagination.has_prev
        }
        
        return APIResponse.success({
            'items': items,
            'pagination': pagination_info
        }, "获取退款列表成功")
        
    except Exception as e:
        import traceback
        current_app.logger.error(f"获取退款列表失败：{str(e)}")
        current_app.logger.error(traceback.format_exc())
        return APIResponse.server_error("获取退款列表失败")


@deposit_refunds_bp.route('/<int:refund_id>', methods=['GET'])
@login_required
def get_deposit_refund(refund_id: int):
    """
    获取退款详情
    
    Path Parameters:
        refund_id: 退款 ID
        
    Response:
        {
            "success": true,
            "data": {...}
        }
    """
    try:
        refund = DepositRefund.query.get(refund_id)
        
        if not refund:
            return APIResponse.not_found("退款记录不存在")
        
        return APIResponse.success(refund.to_dict(), "获取退款详情成功")
        
    except Exception as e:
        current_app.logger.error(f"获取退款详情失败：{str(e)}")
        return APIResponse.server_error("获取退款详情失败")


@deposit_refunds_bp.route('/<int:refund_id>/process', methods=['POST'])
@login_required
@permission_required('edit')
def process_deposit_refund(refund_id: int):
    """
    处理退款
    
    Path Parameters:
        refund_id: 退款 ID
        
    Request Body:
        {
            "deductions": [  // 可选，更新扣款项
                {
                    "type": "unpaid_rent",
                    "amount": 1000,
                    "description": "未付租金"
                }
            ],
            "remark": "备注信息"
        }
        
    Response:
        {
            "success": true,
            "message": "退款处理成功",
            "data": {...}
        }
    """
    try:
        refund = DepositRefund.query.get(refund_id)
        
        if not refund:
            return APIResponse.not_found("退款记录不存在")
        
        if refund.status != 'pending':
            return APIResponse.bad_request("只有待处理状态的退款才能处理")
        
        data = request.get_json() or {}
        
        if 'deductions' in data:
            refund.deductions = []
            for deduction in data['deductions']:
                deduction_type = deduction.get('type')
                amount = deduction.get('amount')
                description = deduction.get('description', '')
                
                if not deduction_type or deduction_type not in DepositRefund.DEDUCTION_TYPES:
                    return APIResponse.bad_request(f"扣款类型必须是：{', '.join(DepositRefund.DEDUCTION_TYPES.keys())}")
                
                if not amount or amount <= 0:
                    return APIResponse.bad_request("扣款金额必须大于 0")
                
                refund.add_deduction(deduction_type, amount, description)
        
        if 'remark' in data:
            refund.remark = data['remark']
        
        refund.process(g.user_id)
        
        db.session.commit()
        
        current_app.logger.info(f"用户 {g.username} 处理了退款记录 {refund_id}")
        
        return APIResponse.success(refund.to_dict(), "退款处理成功")
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"处理退款失败：{str(e)}")
        return APIResponse.server_error("处理退款失败")


@deposit_refunds_bp.route('/<int:refund_id>/complete', methods=['POST'])
@login_required
@permission_required('edit')
def complete_deposit_refund(refund_id: int):
    """
    完成退款
    
    Path Parameters:
        refund_id: 退款 ID
        
    Request Body:
        {
            "remark": "备注信息"
        }
        
    Response:
        {
            "success": true,
            "message": "退款完成",
            "data": {...}
        }
    """
    try:
        refund = DepositRefund.query.get(refund_id)
        
        if not refund:
            return APIResponse.not_found("退款记录不存在")
        
        # 检查是否可以完成退款
        can_complete, error_msg = refund.can_complete()
        if not can_complete:
            return APIResponse.bad_request(error_msg)
        
        data = request.get_json() or {}
        
        if 'remark' in data:
            if refund.remark:
                refund.remark += f"\n{data['remark']}"
            else:
                refund.remark = data['remark']
        
        # 完成退款
        refund.complete()
        
        # 更新合同押金状态为已退款
        from app.models.contract import Contract
        contract = Contract.query.get(refund.contract_id)
        if contract:
            try:
                contract.update_deposit_status('refunded')
                current_app.logger.info(
                    f"合同 {contract.contract_no} 押金已退款，"
                    f"金额: {refund.refund_amount}元"
                )
            except ValueError as e:
                current_app.logger.warning(f"押金状态更新失败: {str(e)}")
        
        db.session.commit()
        
        current_app.logger.info(f"用户 {g.username} 完成了退款记录 {refund_id}")
        
        return APIResponse.success(refund.to_dict(), "退款完成")
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"完成退款失败：{str(e)}")
        return APIResponse.server_error("完成退款失败")


@deposit_refunds_bp.route('/<int:refund_id>/cancel', methods=['POST'])
@login_required
@permission_required('edit')
def cancel_deposit_refund(refund_id: int):
    """
    取消退款
    
    Path Parameters:
        refund_id: 退款 ID
        
    Request Body:
        {
            "reason": "取消原因"
        }
        
    Response:
        {
            "success": true,
            "message": "退款已取消",
            "data": {...}
        }
    """
    try:
        refund = DepositRefund.query.get(refund_id)
        
        if not refund:
            return APIResponse.not_found("退款记录不存在")
        
        if refund.status not in ['pending', 'processed']:
            return APIResponse.bad_request("只有待处理或已处理状态的退款才能取消")
        
        data = request.get_json() or {}
        reason = data.get('reason', '无')
        
        refund.cancel(reason)
        
        db.session.commit()
        
        current_app.logger.info(f"用户 {g.username} 取消了退款记录 {refund_id}，原因：{reason}")
        
        return APIResponse.success(refund.to_dict(), "退款已取消")
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"取消退款失败：{str(e)}")
        return APIResponse.server_error("取消退款失败")
