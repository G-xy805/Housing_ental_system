"""
租金管理路由模块
提供支付记录 CRUD、确认收款、逾期管理、还款计划等功能
"""
from flask import Blueprint, request, jsonify, g, current_app
from typing import Optional, Dict, Any
from datetime import datetime, date, timedelta
from decimal import Decimal

from app.models.payment import Payment, LATE_FEE_RATE, LATE_FEE_MAX_RATE
from app.models.contract import Contract
from app.models import db
from app.utils.decorators import login_required, admin_required, permission_required
from app.utils.responses import APIResponse, PaginationResponse
from app.utils.query_optimizer import (
    optimize_payment_query,
    optimize_payment_detail_query
)
from app.utils.transaction import transactional, DatabaseException

# 创建蓝图
payments_bp = Blueprint('payments', __name__, url_prefix='/api/payments')


# ============================================================================
# 辅助函数
# ============================================================================

def validate_payment_data(data: Dict, is_update: bool = False) -> tuple:
    """
    验证支付数据
    
    Args:
        data: 请求数据
        is_update: 是否为更新操作
        
    Returns:
        tuple: (是否有效，错误消息，验证后的数据)
    """
    errors = []
    validated_data = {}
    
    # 合同 ID（必填）
    if not is_update or 'contract_id' in data:
        if not data.get('contract_id'):
            errors.append('合同 ID 不能为空')
        else:
            try:
                contract_id = int(data['contract_id'])
                contract = Contract.query.get(contract_id)
                if not contract:
                    errors.append('合同不存在')
                else:
                    validated_data['contract_id'] = contract_id
            except (ValueError, TypeError):
                errors.append('合同 ID 必须是有效的整数')
    
    # 支付类型（必填）
    if not is_update or 'payment_type' in data:
        if not data.get('payment_type'):
            errors.append('支付类型不能为空')
        elif data['payment_type'] not in ['rent', 'deposit', 'utility', 'other']:
            errors.append('支付类型必须是：rent(租金)、deposit(押金)、utility(水电费)、other(其他)')
        else:
            validated_data['payment_type'] = data['payment_type']
    
    # 金额（必填）
    if not is_update or 'amount' in data:
        if not data.get('amount'):
            errors.append('金额不能为空')
        else:
            try:
                amount = float(data['amount'])
                if amount <= 0:
                    errors.append('金额必须大于 0')
                validated_data['amount'] = amount
            except (ValueError, TypeError):
                errors.append('金额必须是有效的数字')
    
    # 应缴日期（必填）
    if not is_update or 'due_date' in data:
        if not data.get('due_date'):
            errors.append('应缴日期不能为空')
        else:
            try:
                due_date = datetime.strptime(data['due_date'], '%Y-%m-%d').date()
                validated_data['due_date'] = due_date
            except (ValueError, TypeError):
                errors.append('应缴日期格式不正确，应为 YYYY-MM-DD')
    
    # 支付周期
    if 'period_start' in data:
        try:
            period_start = datetime.strptime(data['period_start'], '%Y-%m-%d').date() if data['period_start'] else None
            validated_data['period_start'] = period_start
        except (ValueError, TypeError):
            errors.append('周期开始日期格式不正确')
    
    if 'period_end' in data:
        try:
            period_end = datetime.strptime(data['period_end'], '%Y-%m-%d').date() if data['period_end'] else None
            if 'period_start' in validated_data and period_end and period_end < validated_data['period_start']:
                errors.append('周期结束日期不能早于周期开始日期')
            validated_data['period_end'] = period_end
        except (ValueError, TypeError):
            errors.append('周期结束日期格式不正确')
    
    # 支付方式
    if 'payment_method' in data:
        if data['payment_method'] not in ['cash', 'bank', 'wechat', 'alipay']:
            errors.append('支付方式必须是：cash(现金)、bank(银行转账)、wechat(微信)、alipay(支付宝)')
        else:
            validated_data['payment_method'] = data['payment_method']
    
    # 实缴金额
    if 'paid_amount' in data:
        try:
            paid_amount = float(data['paid_amount'])
            if paid_amount < 0:
                errors.append('实缴金额不能为负数')
            validated_data['paid_amount'] = paid_amount
        except (ValueError, TypeError):
            errors.append('实缴金额必须是有效的数字')
    
    # 实际支付日期
    if 'payment_date' in data:
        try:
            payment_date = datetime.strptime(data['payment_date'], '%Y-%m-%d').date() if data['payment_date'] else None
            validated_data['payment_date'] = payment_date
        except (ValueError, TypeError):
            errors.append('实际支付日期格式不正确')
    
    # 备注
    if 'remark' in data:
        validated_data['remark'] = data.get('remark', '').strip()
    
    # 凭证文件
    if 'receipt_file' in data:
        validated_data['receipt_file'] = data.get('receipt_file', '').strip()
    
    # 状态（仅在更新时允许）
    if is_update and 'status' in data:
        if data['status'] not in ['pending', 'paid', 'overdue', 'partial', 'refunded', 'cancelled']:
            errors.append('状态必须是：pending、paid、overdue、partial、refunded、cancelled')
        else:
            validated_data['status'] = data['status']
    
    if errors:
        return False, '; '.join(errors), None
    
    return True, None, validated_data


def format_payment_response(payment: Payment) -> Dict:
    """
    格式化支付记录响应数据
    
    Args:
        payment: 支付记录对象
        
    Returns:
        dict: 支付记录响应数据
    """
    data = payment.to_dict()
    
    # 计算滞纳金
    late_fee, overdue_days = payment.calculate_late_fee()
    data['current_late_fee'] = float(late_fee) if isinstance(late_fee, Decimal) else late_fee
    data['current_overdue_days'] = overdue_days
    # 确保 amount 和 late_fee 类型一致
    amount = float(payment.amount) if isinstance(payment.amount, (int, float, Decimal)) else 0.0
    data['total_amount_with_late_fee'] = amount + float(late_fee) if isinstance(late_fee, Decimal) else amount + late_fee
    
    return data


# ============================================================================
# 支付记录 CRUD 接口
# ============================================================================

@payments_bp.route('', methods=['GET'])
@login_required
def get_payments():
    """
    获取支付记录列表（支持分页、筛选、搜索）
    
    Query Parameters:
        page: 页码，默认 1
        per_page: 每页数量，默认 20，最大 100
        contract_id: 合同 ID 筛选
        payment_type: 支付类型筛选 (rent/deposit/utility/other)
        status: 支付状态筛选 (pending/paid/overdue/partial/refunded)
        payment_method: 支付方式筛选 (cash/bank/wechat/alipay)
        start_date: 开始日期筛选
        end_date: 结束日期筛选
        is_overdue: 是否逾期，默认 false
        order_by: 排序字段 (created_at/due_date/payment_date)
        order: 排序方向 (asc/desc)，默认 desc
        
    Response:
        {
            "success": true,
            "message": "获取成功",
            "data": {
                "items": [...],
                "pagination": {
                    "page": 1,
                    "per_page": 20,
                    "total": 100,
                    "pages": 5,
                    "has_next": true,
                    "has_prev": false
                }
            }
        }
    """
    try:
        # 获取查询参数
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', type=int)
        per_page_arg = request.args.get('per_page', type=int)
        per_page = min(page_size or per_page_arg or 20, 100)
        
        # 构建查询（使用 db.session.query 避免 SoftDeleteQuery 的 paginate 问题）
        query = db.session.query(Payment).filter(Payment.deleted_at.is_(None))
        
        # 合同 ID 筛选
        contract_id = request.args.get('contract_id', type=int)
        if contract_id:
            query = query.filter(Payment.contract_id == contract_id)
        
        # 支付类型筛选
        payment_type = request.args.get('payment_type')
        if payment_type:
            if payment_type not in ['rent', 'deposit', 'utility', 'other']:
                return APIResponse.bad_request("支付类型参数不正确")
            query = query.filter(Payment.payment_type == payment_type)
        
        # 支付状态筛选
        status = request.args.get('status')
        if status:
            if status not in ['pending', 'paid', 'overdue', 'partial', 'refunded', 'cancelled']:
                return APIResponse.bad_request("支付状态参数不正确")
            query = query.filter(Payment.status == status)
        
        # 支付方式筛选
        payment_method = request.args.get('payment_method')
        if payment_method:
            if payment_method not in ['cash', 'bank', 'wechat', 'alipay']:
                return APIResponse.bad_request("支付方式参数不正确")
            query = query.filter(Payment.payment_method == payment_method)
        
        # 是否逾期
        is_overdue = request.args.get('is_overdue', 'false').lower() == 'true'
        if is_overdue:
            query = query.filter(
                Payment.status.in_(['pending', 'partial', 'overdue']),
                Payment.due_date < date.today()
            )
        
        # 日期范围筛选
        start_date = request.args.get('start_date')
        if start_date:
            try:
                start = datetime.strptime(start_date, '%Y-%m-%d').date()
                query = query.filter(Payment.due_date >= start)
            except (ValueError, TypeError):
                pass
        
        end_date = request.args.get('end_date')
        if end_date:
            try:
                end = datetime.strptime(end_date, '%Y-%m-%d').date()
                query = query.filter(Payment.due_date <= end)
            except (ValueError, TypeError):
                pass
        
        # 排序
        order_by = request.args.get('order_by', 'due_date')
        order = request.args.get('order', 'desc')
        
        order_column = getattr(Payment, order_by, Payment.due_date)
        if order == 'asc':
            query = query.order_by(order_column.asc())
        else:
            query = query.order_by(order_column.desc())
        
        # 执行分页查询
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        # 格式化响应数据
        items = [format_payment_response(payment) for payment in pagination.items]
        
        pagination_info = {
            'page': pagination.page,
            'per_page': pagination.per_page,
            'total': pagination.total,
            'pages': pagination.pages,
            'has_next': pagination.has_next,
            'has_prev': pagination.has_prev,
            'next_num': pagination.next_num if pagination.has_next else None,
            'prev_num': pagination.prev_num if pagination.has_prev else None
        }
        
        return APIResponse.success({
            'items': items,
            'pagination': pagination_info
        }, "获取支付记录列表成功")
        
    except Exception as e:
        current_app.logger.error(f"获取支付记录列表失败：{str(e)}")
        return APIResponse.server_error("获取支付记录列表失败")


@payments_bp.route('/<int:payment_id>', methods=['GET'])
@login_required
def get_payment(payment_id: int):
    """
    获取支付记录详情
    
    Path Parameters:
        payment_id: 支付记录 ID
        
    Response:
        {
            "success": true,
            "data": {
                "id": 1,
                "payment_no": "PY20240101ABC12345",
                "contract_no": "HT20240101ABC12345",
                "payment_type": "rent",
                "payment_type_name": "租金",
                "amount": 5000,
                "paid_amount": 0,
                "late_fee": 0,
                "overdue_days": 0,
                "due_date": "2024-01-01",
                "status": "pending",
                "is_overdue": false,
                "days_until_due": 10,
                "total_amount_with_late_fee": 5000
            }
        }
    """
    try:
        # 使用 eager loading 优化查询，避免 N+1 问题
        payment = optimize_payment_detail_query(Payment.query).filter_by(id=payment_id).first()
        
        if not payment:
            return APIResponse.not_found("支付记录不存在")
        
        # 格式化响应数据
        data = format_payment_response(payment)
        
        return APIResponse.success(data, "获取支付记录详情成功")
        
    except Exception as e:
        current_app.logger.error(f"获取支付记录详情失败：{str(e)}")
        return APIResponse.server_error("获取支付记录详情失败")


@payments_bp.route('', methods=['POST'])
@login_required
@permission_required('create')
def create_payment():
    """
    创建支付记录
    
    Request Body:
        {
            "contract_id": 1,
            "payment_type": "rent",
            "amount": 5000,
            "due_date": "2024-01-01",
            "period_start": "2024-01-01",
            "period_end": "2024-01-31",
            "remark": "备注信息"
        }
        
    Response:
        {
            "success": true,
            "message": "支付记录创建成功",
            "data": {...}
        }
    """
    try:
        # 获取请求数据
        data = request.get_json()
        
        if not data:
            return APIResponse.bad_request("请求数据不能为空")
        
        # 验证数据
        is_valid, error_msg, validated_data = validate_payment_data(data, is_update=False)
        
        if not is_valid:
            return APIResponse.validation_error(error_msg)
        
        # 创建支付记录
        payment = Payment(**validated_data)
        payment.payment_no = Payment.generate_payment_no()
        payment.operator_id = g.user_id
        
        db.session.add(payment)
        db.session.commit()
        
        # 刷新获取完整数据
        db.session.refresh(payment)
        
        # 格式化响应
        result = format_payment_response(payment)
        
        current_app.logger.info(f"用户 {g.username} 创建了支付记录 {payment.payment_no}")
        
        return APIResponse.success(result, "支付记录创建成功", 201)
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"创建支付记录失败：{str(e)}")
        return APIResponse.server_error("创建支付记录失败")


@payments_bp.route('/<int:payment_id>', methods=['PUT'])
@login_required
@permission_required('edit')
def update_payment(payment_id: int):
    """
    更新支付记录
    
    Path Parameters:
        payment_id: 支付记录 ID
        
    Request Body:
        {
            "amount": 6000,
            "remark": "新的备注",
            ...
        }
        
    Response:
        {
            "success": true,
            "message": "支付记录更新成功",
            "data": {...}
        }
    """
    try:
        payment = Payment.query.get(payment_id)
        
        if not payment:
            return APIResponse.not_found("支付记录不存在")
        
        # 已支付的记录不能修改关键信息
        if payment.status == 'paid':
            restricted_fields = ['amount', 'due_date', 'period_start', 'period_end', 'payment_type']
            data = request.get_json() or {}
            for field in restricted_fields:
                if field in data:
                    return APIResponse.bad_request(f"已支付的记录不能修改{field}字段")
        
        # 获取请求数据
        data = request.get_json()
        
        if not data:
            return APIResponse.bad_request("请求数据不能为空")
        
        # 验证数据
        is_valid, error_msg, validated_data = validate_payment_data(data, is_update=True)
        
        if not is_valid:
            return APIResponse.validation_error(error_msg)
        
        # 更新支付记录
        for key, value in validated_data.items():
            setattr(payment, key, value)
        
        # 如果状态变为已支付，设置确认日期
        if validated_data.get('status') == 'paid' and not payment.confirmed_date:
            payment.confirmed_date = datetime.now()
        
        db.session.commit()
        
        # 刷新获取完整数据
        db.session.refresh(payment)
        
        # 格式化响应
        result = format_payment_response(payment)
        
        current_app.logger.info(f"用户 {g.username} 更新了支付记录 {payment_id}")
        
        return APIResponse.success(result, "支付记录更新成功")
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"更新支付记录失败：{str(e)}")
        return APIResponse.server_error("更新支付记录失败")


@payments_bp.route('/<int:payment_id>', methods=['DELETE'])
@admin_required
def delete_payment(payment_id: int):
    """
    删除支付记录（仅管理员）
    
    Path Parameters:
        payment_id: 支付记录 ID
        
    Response:
        {
            "success": true,
            "message": "支付记录删除成功"
        }
    """
    try:
        payment = Payment.query.get(payment_id)
        
        if not payment:
            return APIResponse.not_found("支付记录不存在")
        
        # 已支付的记录不能删除
        if payment.status == 'paid':
            return APIResponse.bad_request("已支付的记录不能删除")
        
        payment_no = payment.payment_no
        
        # 删除支付记录
        db.session.delete(payment)
        db.session.commit()
        
        current_app.logger.info(f"管理员 {g.username} 删除了支付记录 {payment_no}")
        
        return APIResponse.success(None, "支付记录删除成功")
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"删除支付记录失败：{str(e)}")
        return APIResponse.server_error("删除支付记录失败")


# ============================================================================
# 支付操作接口
# ============================================================================

@transactional()
def _do_verify_payment(
    payment_id: int,
    paid_amount: float,
    payment_method: Optional[str],
    payment_date: date,
    remark: Optional[str],
    user_id: int,
    username: str,
    user_role: str
) -> dict:
    """
    执行支付确认的核心业务逻辑（事务保护）
    
    确保以下操作的原子性：
    1. 支付状态更新
    2. 滞纳金计算
    3. 租客信用记录更新
    4. 押金状态更新（如果是押金支付）
    
    Args:
        payment_id: 支付记录 ID
        paid_amount: 实付金额
        payment_method: 支付方式
        payment_date: 实际支付日期
        remark: 备注
        user_id: 当前用户 ID
        username: 当前用户名
        user_role: 当前用户角色
        
    Returns:
        dict: 包含支付确认结果
        
    Raises:
        ValueError: 业务逻辑错误
        PermissionError: 权限错误
        DatabaseException: 数据库错误
    """
    payment = Payment.query.get(payment_id)
    
    if not payment:
        raise ValueError("支付记录不存在")
    
    # 检查权限（管理员或房源负责人）
    contract = Contract.query.get(payment.contract_id)
    if contract and contract.house and user_role != 'admin':
        # 检查当前员工是否为房源负责人
        if contract.house.owner_id != user_id:
            raise PermissionError("您没有权限操作此支付记录")
    
    # 计算滞纳金
    late_fee, overdue_days = payment.calculate_late_fee(payment_date)
    
    # 标记为已支付
    payment.mark_as_paid(
        paid_amount=paid_amount,
        payment_date=payment_date,
        payment_method=payment_method
    )
    
    # 添加备注
    if remark:
        payment.remark = (payment.remark or '') + f"\n{remark}"
    
    payment.operator_id = user_id
    
    # 如果是押金支付，更新合同押金状态
    if payment.payment_type == 'deposit' and payment.status == 'paid':
        if contract:
            try:
                # 检查押金是否全额支付
                total_deposit_paid = sum(
                    p.paid_amount for p in contract.payments 
                    if p.payment_type == 'deposit' and p.status == 'paid'
                )
                
                # 如果押金全额支付，更新合同押金状态
                if total_deposit_paid >= contract.deposit_amount:
                    contract.update_deposit_status('paid')
                    current_app.logger.info(
                        f"合同 {contract.contract_no} 押金已全额支付，"
                        f"金额: {total_deposit_paid}元"
                    )
            except ValueError as e:
                current_app.logger.warning(f"押金状态更新失败: {str(e)}")
    
    # 更新租客信用记录
    if payment.contract_id and payment.contract_rel and payment.contract_rel.tenant_id:
        from app.models.tenant import Tenant
        from app.utils.credit_score import CreditEventType, CreditScoreConfig
        
        tenant = Tenant.query.get(payment.contract_rel.tenant_id)
        if tenant and payment_date <= payment.due_date:
            config = CreditScoreConfig.get_event_config(CreditEventType.ON_TIME_PAYMENT)
            tenant.add_credit_record(
                event_type='on_time_payment',
                score_change=config['score_change'],
                description=f"{config['description']}（支付记录ID: {payment.id}）",
                related_id=payment.id
            )
            db.session.add(tenant)
    
    # 注意：事务装饰器会自动提交，不需要手动 commit
    
    current_app.logger.info(f"用户 {username} 确认了收款 {payment.payment_no}，金额：{paid_amount}")
    
    return {
        'payment_id': payment.id,
        'payment_no': payment.payment_no,
        'status': payment.status,
        'paid_amount': payment.paid_amount,
        'late_fee': payment.late_fee,
        'total_amount': float(payment.get_total_amount()),
        'deposit_status_updated': payment.payment_type == 'deposit' and payment.status == 'paid'
    }


@payments_bp.route('/<int:payment_id>/verify', methods=['POST'])
@login_required
@permission_required('edit')
def verify_payment(payment_id: int):
    """
    确认收款
    
    使用 @transactional 装饰器确保以下操作的原子性：
    1. 支付状态更新
    2. 滞纳金计算
    3. 租客信用记录更新
    
    Path Parameters:
        payment_id: 支付记录 ID
        
    Request Body:
        {
            "paid_amount": 5000,  // 实付金额
            "payment_method": "wechat",  // 支付方式
            "payment_date": "2024-01-01",  // 实际支付日期，默认今天
            "remark": "备注"
        }
        
    Response:
        {
            "success": true,
            "message": "收款确认成功",
            "data": {
                "payment_id": 1,
                "status": "paid",
                "paid_amount": 5000,
                "late_fee": 0,
                "total_amount": 5000
            }
        }
    """
    try:
        # 获取请求数据
        data = request.get_json()
        
        if not data:
            return APIResponse.bad_request("请求数据不能为空")
        
        # 验证实付金额
        paid_amount = data.get('paid_amount')
        if paid_amount is None:
            return APIResponse.bad_request("实付金额不能为空")
        
        try:
            paid_amount = float(paid_amount)
            if paid_amount <= 0:
                return APIResponse.bad_request("实付金额必须大于 0")
        except (ValueError, TypeError):
            return APIResponse.bad_request("实付金额必须是有效的数字")
        
        # 验证支付方式
        payment_method = data.get('payment_method')
        if payment_method and payment_method not in ['cash', 'bank', 'wechat', 'alipay']:
            return APIResponse.bad_request("支付方式不正确")
        
        # 验证实际支付日期
        payment_date_str = data.get('payment_date')
        if payment_date_str:
            try:
                payment_date = datetime.strptime(payment_date_str, '%Y-%m-%d').date()
            except (ValueError, TypeError):
                return APIResponse.bad_request("实际支付日期格式不正确")
        else:
            payment_date = date.today()
        
        # 调用事务保护的核心业务函数
        result = _do_verify_payment(
            payment_id=payment_id,
            paid_amount=paid_amount,
            payment_method=payment_method,
            payment_date=payment_date,
            remark=data.get('remark'),
            user_id=g.user_id,
            username=g.username,
            user_role=g.user_role
        )
        
        return APIResponse.success(result, "收款确认成功")
        
    except ValueError as e:
        if "支付记录不存在" in str(e):
            return APIResponse.not_found(str(e))
        return APIResponse.bad_request(str(e))
    except PermissionError as e:
        return APIResponse.forbidden(str(e))
    except DatabaseException as e:
        current_app.logger.error(f"确认收款数据库错误：{str(e)}")
        return APIResponse.server_error("确认收款失败，数据库操作错误")
    except Exception as e:
        current_app.logger.error(f"确认收款失败：{str(e)}")
        return APIResponse.server_error("确认收款失败")


@payments_bp.route('/overdue', methods=['GET'])
@login_required
def get_overdue_payments():
    """
    获取逾期支付记录
    
    Query Parameters:
        page: 页码，默认 1
        per_page: 每页数量，默认 20，最大 100
        contract_id: 合同 ID 筛选
        min_overdue_days: 最小逾期天数，默认 1
        max_overdue_days: 最大逾期天数
        include_partial: 是否包含部分支付记录，默认 true
        
    Response:
        {
            "success": true,
            "data": {
                "items": [...],
                "pagination": {...},
                "statistics": {
                    "total_overdue": 10,
                    "total_overdue_amount": 50000,
                    "total_late_fee": 500
                }
            }
        }
    """
    try:
        # 获取查询参数
        page = request.args.get('page', 1, type=int)
        per_page = min(
            request.args.get('page_size', request.args.get('per_page', 20), type=int),
            100
        )
        
        # 构建查询（使用 db.session.query 避免 SoftDeleteQuery 的 paginate 问题）
        query = db.session.query(Payment).filter(
            Payment.deleted_at.is_(None),
            Payment.status.in_(['pending', 'partial', 'overdue']),
            Payment.due_date < date.today()
        )
        
        # 合同 ID 筛选
        contract_id = request.args.get('contract_id', type=int)
        if contract_id:
            query = query.filter(Payment.contract_id == contract_id)
        
        # 最小逾期天数
        min_overdue_days = request.args.get('min_overdue_days', 1, type=int)
        
        # 最大逾期天数
        max_overdue_days = request.args.get('max_overdue_days', type=int)
        if max_overdue_days:
            min_date = date.today() - timedelta(days=max_overdue_days)
            query = query.filter(Payment.due_date >= min_date)
        else:
            min_date = date.today() - timedelta(days=min_overdue_days)
            query = query.filter(Payment.due_date <= min_date)
        
        # 是否包含部分支付记录
        include_partial = request.args.get('include_partial', 'true').lower() == 'true'
        if not include_partial:
            query = query.filter(Payment.status != 'partial')
        
        # 排序
        query = query.order_by(Payment.due_date.asc())
        
        # 执行分页查询
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        # 格式化响应数据并计算滞纳金
        items = []
        total_overdue_amount = 0
        total_late_fee = 0
        
        for payment in pagination.items:
            payment_data = format_payment_response(payment)
            items.append(payment_data)
            total_overdue_amount += payment.amount - payment.paid_amount
            total_late_fee += payment.late_fee
        
        pagination_info = {
            'page': pagination.page,
            'per_page': pagination.per_page,
            'total': pagination.total,
            'pages': pagination.pages,
            'has_next': pagination.has_next,
            'has_prev': pagination.has_prev,
            'next_num': pagination.next_num if pagination.has_next else None,
            'prev_num': pagination.prev_num if pagination.has_prev else None
        }
        
        return APIResponse.success({
            'items': items,
            'pagination': pagination_info,
            'statistics': {
                'total_overdue': pagination.total,
                'total_overdue_amount': total_overdue_amount,
                'total_late_fee': total_late_fee
            }
        }, "获取逾期支付记录成功")
        
    except Exception as e:
        current_app.logger.error(f"获取逾期支付记录失败：{str(e)}")
        return APIResponse.server_error("获取逾期支付记录失败")


# ============================================================================
# 还款计划接口
# ============================================================================

@payments_bp.route('/contracts/<int:contract_id>/payment-plan', methods=['GET'])
@login_required
def get_contract_payment_plan(contract_id: int):
    """
    获取合同的还款计划
    
    Path Parameters:
        contract_id: 合同 ID
        
    Response:
        {
            "success": true,
            "data": {
                "contract_id": 1,
                "contract_no": "HT20240101ABC12345",
                "payment_plan": [...],
                "statistics": {
                    "total_amount": 60000,
                    "paid_amount": 20000,
                    "pending_amount": 40000,
                    "overdue_count": 1,
                    "paid_count": 4,
                    "pending_count": 8
                }
            }
        }
    """
    try:
        contract = Contract.query.get(contract_id)
        
        if not contract:
            return APIResponse.not_found("合同不存在")
        
        # 获取所有支付记录
        payments = Payment.query.filter_by(contract_id=contract_id).order_by(Payment.due_date.asc()).all()
        
        # 格式化支付计划
        payment_plan = []
        total_amount = 0
        paid_amount = 0
        pending_amount = 0
        overdue_count = 0
        paid_count = 0
        pending_count = 0
        
        for payment in payments:
            payment_data = format_payment_response(payment)
            payment_plan.append(payment_data)
            
            if payment.status != 'cancelled':
                total_amount += payment.amount
                pending_amount += payment.amount - payment.paid_amount
            
            if payment.status == 'paid':
                paid_amount += payment.paid_amount
                paid_count += 1
            elif payment.is_overdue():
                overdue_count += 1
                pending_count += 1
            elif payment.status in ['pending', 'partial']:
                pending_count += 1
        
        return APIResponse.success({
            'contract_id': contract_id,
            'contract_no': contract.contract_no,
            'payment_plan': payment_plan,
            'statistics': {
                'total_amount': total_amount,
                'paid_amount': paid_amount,
                'pending_amount': pending_amount,
                'overdue_count': overdue_count,
                'paid_count': paid_count,
                'pending_count': pending_count
            }
        }, "获取还款计划成功")
        
    except Exception as e:
        current_app.logger.error(f"获取还款计划失败：{str(e)}")
        return APIResponse.server_error("获取还款计划失败")


# ============================================================================
# 统计接口
# ============================================================================

@payments_bp.route('/stats', methods=['GET'])
@login_required
def get_payment_stats():
    """
    获取支付统计信息
    
    Query Parameters:
        contract_id: 合同 ID 筛选
        start_date: 开始日期
        end_date: 结束日期
        
    Response:
        {
            "success": true,
            "data": {
                "total_payments": 100,
                "by_status": {
                    "pending": 20,
                    "paid": 70,
                    "overdue": 5,
                    "partial": 3,
                    "refunded": 2
                },
                "total_amount": 500000,
                "total_paid": 350000,
                "total_overdue": 50000,
                "total_late_fee": 500
            }
        }
    """
    try:
        # 构建查询
        query = Payment.query
        
        # 合同 ID 筛选
        contract_id = request.args.get('contract_id', type=int)
        if contract_id:
            query = query.filter(Payment.contract_id == contract_id)
        
        # 日期范围筛选
        start_date = request.args.get('start_date')
        if start_date:
            try:
                start = datetime.strptime(start_date, '%Y-%m-%d').date()
                query = query.filter(Payment.due_date >= start)
            except (ValueError, TypeError):
                pass
        
        end_date = request.args.get('end_date')
        if end_date:
            try:
                end = datetime.strptime(end_date, '%Y-%m-%d').date()
                query = query.filter(Payment.due_date <= end)
            except (ValueError, TypeError):
                pass
        
        # 统计总数
        total_payments = query.count()
        
        # 按状态统计
        pending = query.filter(Payment.status == 'pending').count()
        paid = query.filter(Payment.status == 'paid').count()
        overdue = query.filter(Payment.status == 'overdue').count()
        partial = query.filter(Payment.status == 'partial').count()
        refunded = query.filter(Payment.status == 'refunded').count()
        
        # 统计金额
        all_payments = query.all()
        total_amount = sum(p.amount for p in all_payments if p.status != 'cancelled')
        total_paid = sum(p.paid_amount for p in all_payments if p.status == 'paid')
        
        # 统计逾期金额
        overdue_payments = query.filter(
            Payment.status.in_(['pending', 'partial', 'overdue']),
            Payment.due_date < date.today()
        ).all()
        total_overdue = sum(p.amount - p.paid_amount for p in overdue_payments)
        
        # 统计滞纳金
        total_late_fee = sum(p.late_fee for p in all_payments)
        
        return APIResponse.success({
            'total_payments': total_payments,
            'by_status': {
                'pending': pending,
                'paid': paid,
                'overdue': overdue,
                'partial': partial,
                'refunded': refunded
            },
            'total_amount': total_amount,
            'total_paid': total_paid,
            'total_overdue': total_overdue,
            'total_late_fee': total_late_fee
        }, "获取支付统计信息成功")
        
    except Exception as e:
        current_app.logger.error(f"获取支付统计失败：{str(e)}")
        return APIResponse.server_error("获取支付统计失败")


# ============================================================================
# 滞纳金更新接口（供定时任务调用）
# ============================================================================

@payments_bp.route('/update-late-fees', methods=['POST'])
@login_required
@admin_required
def update_late_fees():
    """
    批量更新滞纳金（供定时任务调用）
    
    Response:
        {
            "success": true,
            "data": {
                "updated_count": 10,
                "total_late_fee": 500
            }
        }
    """
    try:
        # 查询所有未支付的逾期记录
        overdue_payments = Payment.query.filter(
            Payment.status.in_(['pending', 'partial', 'overdue']),
            Payment.due_date < date.today()
        ).all()
        
        updated_count = 0
        total_late_fee = Decimal('0.00')
        
        for payment in overdue_payments:
            old_late_fee = payment.late_fee
            late_fee, overdue_days = payment.calculate_late_fee()
            
            if late_fee != old_late_fee:
                payment.status = 'overdue'
                updated_count += 1
                total_late_fee += late_fee if isinstance(late_fee, Decimal) else Decimal(str(late_fee))
        
        if updated_count > 0:
            db.session.commit()
        
        current_app.logger.info(f"批量更新滞纳金：{updated_count} 条记录，总滞纳金：{float(total_late_fee)}")
        
        return APIResponse.success({
            'updated_count': updated_count,
            'total_late_fee': float(total_late_fee)
        }, "滞纳金更新成功")
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"更新滞纳金失败：{str(e)}")
        return APIResponse.server_error("更新滞纳金失败")


@payments_bp.route('/batch-update-status', methods=['POST'])
@login_required
@permission_required('edit')
def batch_update_payment_status():
    """
    批量更新支付状态
    
    Request Body:
        {
            "payment_ids": [1, 2, 3],
            "status": "paid"
        }
        
    Response:
        {
            "success": true,
            "message": "批量更新成功",
            "data": {
                "updated_count": 3,
                "failed_count": 0,
                "details": [...]
            }
        }
    """
    try:
        data = request.get_json()
        
        if not data:
            return APIResponse.bad_request("请求数据不能为空")
        
        payment_ids = data.get('payment_ids', [])
        status = data.get('status')
        
        if not payment_ids:
            return APIResponse.bad_request("支付记录 ID 列表不能为空")
        
        if not isinstance(payment_ids, list):
            return APIResponse.bad_request("payment_ids 必须是数组")
        
        if not status:
            return APIResponse.bad_request("状态不能为空")
        
        valid_statuses = ['pending', 'paid', 'overdue', 'partial', 'refunded', 'cancelled']
        if status not in valid_statuses:
            return APIResponse.bad_request(f"状态必须是：{', '.join(valid_statuses)}")
        
        updated_count = 0
        failed_count = 0
        details = []
        
        for payment_id in payment_ids:
            try:
                payment = Payment.query.get(payment_id)
                
                if not payment:
                    details.append({
                        'payment_id': payment_id,
                        'success': False,
                        'message': '支付记录不存在'
                    })
                    failed_count += 1
                    continue
                
                old_status = payment.status
                
                if status == 'paid':
                    payment_date = payment.payment_date or date.today()
                    late_fee, overdue_days = payment.calculate_late_fee(payment_date)
                    total_amount = payment.get_total_amount()
                    paid_amount = payment.paid_amount or total_amount
                    payment.mark_as_paid(
                        paid_amount=paid_amount,
                        payment_date=payment_date,
                        payment_method=payment.payment_method
                    )
                    payment.operator_id = g.user_id
                    
                    # 如果是押金支付，更新合同押金状态
                    if payment.payment_type == 'deposit':
                        contract = payment.contract_rel
                        if contract:
                            try:
                                # 检查押金是否全额支付
                                total_deposit_paid = sum(
                                    p.paid_amount for p in contract.payments 
                                    if p.payment_type == 'deposit' and p.status == 'paid'
                                )
                                
                                # 如果押金全额支付，更新合同押金状态
                                if total_deposit_paid >= contract.deposit_amount:
                                    contract.update_deposit_status('paid')
                            except ValueError as e:
                                current_app.logger.warning(f"押金状态更新失败: {str(e)}")
                    
                    if payment.contract_id and payment.contract_rel and payment.contract_rel.tenant_id:
                        from app.models.tenant import Tenant
                        from app.utils.credit_score import CreditEventType, CreditScoreConfig
                        
                        tenant = Tenant.query.get(payment.contract_rel.tenant_id)
                        if tenant and payment_date <= payment.due_date:
                            config = CreditScoreConfig.get_event_config(CreditEventType.ON_TIME_PAYMENT)
                            tenant.add_credit_record(
                                event_type='on_time_payment',
                                score_change=config['score_change'],
                                description=f"{config['description']}（支付记录ID: {payment.id}）",
                                related_id=payment.id
                            )
                            db.session.add(tenant)
                else:
                    payment.status = status
                
                details.append({
                    'payment_id': payment_id,
                    'success': True,
                    'old_status': old_status,
                    'new_status': status,
                    'message': '更新成功'
                })
                updated_count += 1
                
            except Exception as e:
                details.append({
                    'payment_id': payment_id,
                    'success': False,
                    'message': str(e)
                })
                failed_count += 1
        
        if updated_count > 0:
            db.session.commit()
        
        current_app.logger.info(
            f"用户 {g.username} 批量更新支付状态：成功 {updated_count} 条，失败 {failed_count} 条"
        )
        
        return APIResponse.success({
            'updated_count': updated_count,
            'failed_count': failed_count,
            'details': details
        }, f"批量更新成功：{updated_count} 条记录已更新")
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"批量更新支付状态失败：{str(e)}")
        return APIResponse.server_error("批量更新支付状态失败")
