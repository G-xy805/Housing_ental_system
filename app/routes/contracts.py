"""
合同管理路由模块
提供合同 CRUD、续签、终止、到期提醒、支付记录关联等功能
"""
from flask import Blueprint, request, jsonify, g, current_app
from typing import Optional, Dict, Any
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta

from app.models.contract import Contract, OptimisticLockError
from app.models.house import House
from app.models.room import Room
from app.models.tenant import Tenant
from app.models.payment import Payment
from app.models.deposit_refund import DepositRefund
from app.models import db
from app.utils.decorators import login_required, admin_required, permission_required
from app.utils.responses import APIResponse, PaginationResponse
from app.utils.file_lock import ContractLock, FileLockTimeoutError, FileLockError
from app.utils.retry import retry_call, RetryConfig
from app.utils.transaction import transactional, DatabaseException

# 创建蓝图
contracts_bp = Blueprint('contracts', __name__, url_prefix='/api/contracts')


# ============================================================================
# 辅助函数
# ============================================================================

def validate_contract_data(data: Dict, is_update: bool = False) -> tuple:
    """
    验证合同数据
    
    Args:
        data: 请求数据
        is_update: 是否为更新操作
        
    Returns:
        tuple: (是否有效，错误消息，验证后的数据)
    """
    errors = []
    validated_data = {}
    
    # 合同标题（必填）
    if not is_update or 'title' in data:
        if not data.get('title'):
            errors.append('合同标题不能为空')
        elif len(data.get('title', '')) > 100:
            errors.append('合同标题不能超过 100 个字符')
        else:
            validated_data['title'] = data['title'].strip()
    
    # 房源 ID（必填）
    if not is_update or 'house_id' in data:
        if not data.get('house_id'):
            errors.append('房源 ID 不能为空')
        else:
            try:
                house_id = int(data['house_id'])
                house = House.query.get(house_id)
                if not house:
                    errors.append('房源不存在')
                else:
                    validated_data['house_id'] = house_id
            except (ValueError, TypeError):
                errors.append('房源 ID 必须是有效的整数')
    
    # 房间 ID（合租房源必填）
    house_id = validated_data.get('house_id')
    if house_id:
        house = House.query.get(house_id)
        if data.get('room_id'):
            # 如果提供了房间 ID，无论房源类型如何，都需要验证
            try:
                room_id = int(data['room_id'])
                room = Room.query.get(room_id)
                if not room:
                    errors.append('房间不存在')
                elif room.house_id != house_id:
                    errors.append('所选房间不属于该房源')
                elif room.status != 'available':
                    errors.append('所选房间状态不是可租')
                else:
                    validated_data['room_id'] = room_id
                    # 合租房源默认使用房间租金
                    if house and house.rental_type == 'shared' and not data.get('rent_amount'):
                        validated_data['rent_amount'] = room.rent_price
            except (ValueError, TypeError):
                errors.append('房间 ID 必须是有效的整数')
        elif house and house.rental_type == 'shared':
            # 合租房源必须选择房间
            errors.append('合租房源必须选择房间')
        else:
            # 整租房源不需要房间 ID
            validated_data['room_id'] = None
    
    # 租客 ID（必填）
    if not is_update or 'tenant_id' in data:
        if not data.get('tenant_id'):
            errors.append('租客 ID 不能为空')
        else:
            try:
                tenant_id = int(data['tenant_id'])
                tenant = Tenant.query.get(tenant_id)
                if not tenant:
                    errors.append('租客不存在')
                else:
                    validated_data['tenant_id'] = tenant_id
            except (ValueError, TypeError):
                errors.append('租客 ID 必须是有效的整数')
    
    # 租赁日期（必填）
    if not is_update or 'start_date' in data:
        if not data.get('start_date'):
            errors.append('起租日期不能为空')
        else:
            try:
                start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
                validated_data['start_date'] = start_date
            except (ValueError, TypeError):
                errors.append('起租日期格式不正确，应为 YYYY-MM-DD')
    
    if not is_update or 'end_date' in data:
        if not data.get('end_date'):
            errors.append('结束日期不能为空')
        else:
            try:
                end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
                # 验证结束日期必须晚于起租日期
                if 'start_date' in validated_data and end_date <= validated_data['start_date']:
                    errors.append('结束日期必须晚于起租日期')
                validated_data['end_date'] = end_date
            except (ValueError, TypeError):
                errors.append('结束日期格式不正确，应为 YYYY-MM-DD')
    
    # 租金金额（必填）
    if not is_update or 'rent_amount' in data:
        if not data.get('rent_amount'):
            errors.append('租金金额不能为空')
        else:
            try:
                rent_amount = float(data['rent_amount'])
                if rent_amount <= 0:
                    errors.append('租金金额必须大于 0')
                validated_data['rent_amount'] = rent_amount
            except (ValueError, TypeError):
                errors.append('租金金额必须是有效的数字')
    
    # 押金金额（必填）
    # 支持 deposit 和 deposit_amount 两种字段名
    deposit_value = data.get('deposit') or data.get('deposit_amount')
    if not is_update or ('deposit' in data or 'deposit_amount' in data):
        if not deposit_value:
            errors.append('押金金额不能为空')
        else:
            try:
                deposit = float(deposit_value)
                if deposit < 0:
                    errors.append('押金金额不能为负数')
                validated_data['deposit'] = deposit
            except (ValueError, TypeError):
                errors.append('押金金额必须是有效的数字')
    
    # 付款类型（必填）
    if not is_update or 'payment_type' in data:
        payment_type = data.get('payment_type', '月付')
        if payment_type not in ['月付', '季付', '半年付', '年付']:
            errors.append('付款类型必须是：月付、季付、半年付、年付')
        else:
            validated_data['payment_type'] = payment_type
    
    # 付款周期（根据付款类型自动计算）
    payment_cycle_map = {
        '月付': 1,
        '季付': 3,
        '半年付': 6,
        '年付': 12
    }
    if 'payment_type' in validated_data:
        validated_data['payment_cycle'] = payment_cycle_map[validated_data['payment_type']]
    elif 'payment_cycle' in data:
        try:
            validated_data['payment_cycle'] = int(data['payment_cycle'])
        except (ValueError, TypeError):
            errors.append('付款周期必须是有效的整数')
    
    # 合同描述
    if 'description' in data:
        validated_data['description'] = data.get('description', '').strip()
    
    # 合同文件
    if 'contract_file' in data:
        validated_data['contract_file'] = data.get('contract_file', '').strip()
    
    # 备注
    if 'remark' in data:
        validated_data['remark'] = data.get('remark', '').strip()
    
    # 状态（仅在更新时允许）
    if is_update and 'status' in data:
        if data['status'] not in ['draft', 'active', 'expired', 'terminated', 'renewed']:
            errors.append('状态必须是：draft(草稿)、active(生效中)、expired(已过期)、terminated(已终止)、renewed(已续签)')
        else:
            validated_data['status'] = data['status']
    
    if errors:
        return False, '; '.join(errors), None
    
    return True, None, validated_data


def optimize_contract_detail_query(query):
    """
    优化合同详情查询，使用 eager loading 避免 N+1 问题
    
    Args:
        query: SQLAlchemy query 对象
        
    Returns:
        优化后的 query 对象
    """
    from sqlalchemy.orm import joinedload
    # 只加载 payments，不加载 tenant_rel 以避免 id_card_hash 字段问题
    return query.options(
        joinedload(Contract.payments)
    )


def format_contract_response(contract: Contract, include_payments: bool = False) -> Dict:
    """
    格式化合同响应数据
    
    Args:
        contract: 合同对象
        include_payments: 是否包含支付记录
        
    Returns:
        dict: 合同响应数据
    """
    # 使用contract.to_dict()，它已经有安全处理
    data = contract.to_dict()
    
    if include_payments:
        try:
            payments = contract.payments or []
            # 过滤掉没有 due_date 的支付记录，避免排序错误
            valid_payments = [p for p in payments if p.due_date]
            payments = sorted(valid_payments, key=lambda p: p.due_date)
            data['payments'] = [payment.to_dict() for payment in payments]
            data['total_paid'] = sum(p.paid_amount or 0 for p in payments if p.status == 'paid')
            data['total_due'] = sum(p.amount or 0 for p in payments)
            data['overdue_count'] = sum(1 for p in payments if p.is_overdue())
        except Exception:
            pass
    
    return data


def calculate_auto_deductions_for_refund(contract: Contract, terminate_date: date) -> list:
    """
    自动计算押金退款扣款项
    
    Args:
        contract: 合同对象
        terminate_date: 终止日期
        
    Returns:
        list: 扣款项列表
    """
    deductions = []
    
    unpaid_rents = Payment.query.filter(
        Payment.contract_id == contract.id,
        Payment.payment_type == 'rent',
        Payment.status.in_(['pending', 'overdue', 'partial']),
        Payment.due_date <= terminate_date
    ).all()
    
    if unpaid_rents:
        total_unpaid_rent = sum(p.amount - p.paid_amount for p in unpaid_rents)
        if total_unpaid_rent > 0:
            deductions.append({
                'type': 'unpaid_rent',
                'amount': total_unpaid_rent,
                'description': f'未付租金（共{len(unpaid_rents)}笔）'
            })
    
    overdue_payments = Payment.query.filter(
        Payment.contract_id == contract.id,
        Payment.status == 'overdue'
    ).all()
    
    if overdue_payments:
        total_late_fee = sum(p.late_fee or 0 for p in overdue_payments)
        if total_late_fee > 0:
            deductions.append({
                'type': 'late_fees',
                'amount': total_late_fee,
                'description': f'滞纳金（共{len(overdue_payments)}笔）'
            })
    
    return deductions


# ============================================================================
# 合同 CRUD 接口
# ============================================================================

@contracts_bp.route('', methods=['GET'])
@login_required
def get_contracts():
    """
    获取合同列表（支持分页、筛选、搜索）
    
    Query Parameters:
        page: 页码，默认 1
        per_page: 每页数量，默认 20，最大 100
        keyword: 关键词搜索（合同编号、标题）
        contract_no: 合同编号搜索
        status: 状态筛选 (draft/active/expired/terminated/renewed)
        tenant_id: 租客 ID 筛选
        house_id: 房源 ID 筛选
        room_id: 房间 ID 筛选
        landlord_id: 房东 ID 筛选
        is_expiring: 是否查询即将到期合同，默认 false
        order_by: 排序字段 (created_at/start_date/end_date)
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
        from sqlalchemy import func
        expired_contracts = Contract.query.filter(
            Contract.status == 'active',
            Contract.end_date < func.current_date()
        ).all()
        
        for contract in expired_contracts:
            contract.status = 'expired'
            if contract.house:
                contract.house.update_status()
            if contract.tenant_rel:
                contract.tenant_rel.update_status()
                
                from app.utils.credit_score import CreditEventType, CreditScoreConfig
                config = CreditScoreConfig.get_event_config(CreditEventType.CONTRACT_COMPLETE)
                contract.tenant_rel.add_credit_record(
                    event_type='contract_complete',
                    score_change=config['score_change'],
                    description=f"{config['description']}（合同编号: {contract.contract_no}）",
                    related_id=contract.id
                )
        
        if expired_contracts:
            db.session.commit()
        
        # 获取查询参数
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', type=int)
        per_page_arg = request.args.get('per_page', type=int)
        per_page = min(page_size or per_page_arg or 20, 100)
        
        # 构建查询（使用 db.session.query 避免 SoftDeleteQuery 的 paginate 问题）
        # 不使用 joinedload 以避免 id_card_hash 字段问题
        query = db.session.query(Contract).filter(Contract.deleted_at.is_(None))
        
        # 关键词搜索
        keyword = request.args.get('keyword')
        if keyword:
            query = query.filter(
                db.or_(
                    Contract.contract_no.ilike(f'%{keyword}%'),
                    Contract.title.ilike(f'%{keyword}%')
                )
            )
        
        # 合同编号搜索
        contract_no = request.args.get('contract_no')
        if contract_no:
            query = query.filter(Contract.contract_no.ilike(f'%{contract_no}%'))
        
        # 状态筛选
        status = request.args.get('status')
        if status:
            # 支持多个状态，用逗号分隔
            status_list = status.split(',')
            valid_statuses = ['draft', 'active', 'expired', 'terminated', 'renewed']
            # 验证所有状态值
            for s in status_list:
                if s not in valid_statuses:
                    return APIResponse.bad_request("状态必须是：draft、active、expired、terminated、renewed")
            query = query.filter(Contract.status.in_(status_list))
        
        # 租客 ID 筛选
        tenant_id = request.args.get('tenant_id', type=int)
        if tenant_id:
            query = query.filter(Contract.tenant_id == tenant_id)
        
        # 房源 ID 筛选
        house_id = request.args.get('house_id', type=int)
        if house_id:
            query = query.filter(Contract.house_id == house_id)
        
        # 房间 ID 筛选
        room_id = request.args.get('room_id', type=int)
        if room_id:
            query = query.filter(Contract.room_id == room_id)
        
        # 房东 ID 筛选（通过房源的房东ID筛选）
        landlord_id = request.args.get('landlord_id', type=int)
        if landlord_id:
            # 需要关联房源表来筛选房东
            query = query.join(Contract.house).filter(
                db.text('houses.landlord_id = :landlord_id')
            ).params(landlord_id=landlord_id)
        
        # 即将到期合同筛选
        is_expiring = request.args.get('is_expiring', 'false').lower() == 'true'
        if is_expiring:
            from sqlalchemy import func, and_
            from datetime import timedelta
            expiring_threshold = func.date(func.current_date() + timedelta(days=30))
            query = query.filter(
                Contract.status == 'active',
                Contract.end_date <= expiring_threshold,
                Contract.end_date >= func.current_date()
            )
        
        # 排序
        order_by = request.args.get('order_by', 'created_at')
        order = request.args.get('order', 'desc')
        
        order_column = getattr(Contract, order_by, Contract.created_at)
        if order == 'asc':
            query = query.order_by(order_column.asc())
        else:
            query = query.order_by(order_column.desc())
        
        # 执行分页查询
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        # 格式化响应数据
        items = [format_contract_response(contract) for contract in pagination.items]
        
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
        }, "获取合同列表成功")
        
    except Exception as e:
        current_app.logger.error(f"获取合同列表失败：{str(e)}")
        return APIResponse.server_error("获取合同列表失败")


@contracts_bp.route('/<int:contract_id>', methods=['GET'])
@login_required
def get_contract(contract_id: int):
    """
    获取合同详情
    
    Path Parameters:
        contract_id: 合同 ID
        
    Response:
        {
            "success": true,
            "data": {
                "id": 1,
                "contract_no": "HT20240101ABC12345",
                "title": "房屋租赁合同",
                "house_title": "温馨两居室",
                "house_address": "北京市朝阳区某某小区",
                "tenant_name": "张三",
                "rent_amount": 5000,
                "deposit": 10000,
                "payment_type": "季付",
                "start_date": "2024-01-01",
                "end_date": "2025-01-01",
                "status": "active",
                "is_expired": false,
                "is_expiring_soon": false,
                "days_until_expiry": 300
            }
        }
    """
    try:
        # 使用 eager loading 优化查询，避免 N+1 问题
        contract = optimize_contract_detail_query(Contract.query).filter_by(id=contract_id).first()
        
        if not contract:
            return APIResponse.not_found("合同不存在")
        
        # 格式化响应数据
        data = format_contract_response(contract, include_payments=False)
        
        return APIResponse.success(data, "获取合同详情成功")
        
    except Exception as e:
        current_app.logger.error(f"获取合同详情失败：{str(e)}")
        return APIResponse.server_error("获取合同详情失败")


@contracts_bp.route('', methods=['POST'])
@login_required
@permission_required('create')
def create_contract():
    """
    创建合同
    
    Request Body:
        {
            "title": "房屋租赁合同",
            "house_id": 1,
            "room_id": 2,  // 合租时填写
            "tenant_id": 1,
            "start_date": "2024-01-01",
            "end_date": "2025-01-01",
            "rent_amount": 5000,
            "deposit": 10000,
            "payment_type": "季付",
            "description": "合同描述",
            "remark": "备注信息"
        }
        
    Response:
        {
            "success": true,
            "message": "合同创建成功",
            "data": {...}
        }
    """
    try:
        # 获取请求数据
        data = request.get_json()
        
        if not data:
            return APIResponse.bad_request("请求数据不能为空")
        
        # 验证数据
        is_valid, error_msg, validated_data = validate_contract_data(data, is_update=False)
        
        if not is_valid:
            return APIResponse.validation_error(error_msg)
        
        # 检查租客状态（黑名单验证）
        tenant = Tenant.query.get(validated_data['tenant_id'])
        if tenant.status == 'blacklisted':
            return APIResponse.error(
                error_code='TENANT_BLACKLISTED',
                message=f'租客 {tenant.name} 已被列入黑名单，无法创建合同',
                status_code=403
            )
        
        # 检查租客信用评分
        credit_score = tenant.credit_score or 100
        credit_warning = None
        if credit_score < 60:
            credit_warning = {
                'warning_type': 'low_credit_score',
                'message': f'警告：租客 {tenant.name} 信用评分较低（{credit_score}分），建议谨慎签约',
                'credit_score': credit_score
            }
            current_app.logger.warning(
                f"用户 {g.username} 尝试为低信用评分租客 {tenant.name}（ID: {tenant.id}，信用分: {credit_score}）创建合同"
            )
        
        # 检查房源是否可租
        house = House.query.get(validated_data['house_id'])
        if house.status == 'maintenance':
            return APIResponse.bad_request("房源正在维护中，无法创建合同")
        
        # 字段名映射：将 deposit 映射为 deposit_amount
        if 'deposit' in validated_data:
            validated_data['deposit_amount'] = validated_data.pop('deposit')
        
        # 创建合同
        contract = Contract(**validated_data)
        contract.contract_no = Contract.generate_contract_no()
        
        db.session.add(contract)
        
        # 注意：创建合同时不改变房间状态和租客状态
        # 只有在合同激活后才改变状态，这样更加合理
        
        db.session.commit()
        
        # 刷新获取完整数据
        db.session.refresh(contract)
        
        # 取消自动生成支付计划，改为手动添加
        # generate_payment_plan(contract)
        
        # 格式化响应
        result = format_contract_response(contract)
        
        # 如果有信用警告，添加到响应中
        if credit_warning:
            result['credit_warning'] = credit_warning
            message = f"合同创建成功。{credit_warning['message']}"
        else:
            message = "合同创建成功"
        
        current_app.logger.info(f"用户 {g.username} 创建了合同 {contract.contract_no}")
        
        return APIResponse.success(result, message, 201)
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"创建合同失败：{str(e)}")
        return APIResponse.server_error("创建合同失败")


@contracts_bp.route('/<int:contract_id>', methods=['PUT'])
@login_required
@permission_required('edit')
def update_contract(contract_id: int):
    """
    更新合同信息
    
    Path Parameters:
        contract_id: 合同 ID
        
    Request Body:
        {
            "title": "新的合同标题",
            "rent_amount": 6000,
            "description": "新的描述",
            ...
        }
        
    Response:
        {
            "success": true,
            "message": "合同更新成功",
            "data": {...}
        }
    """
    try:
        contract = Contract.query.get(contract_id)
        
        if not contract:
            return APIResponse.not_found("合同不存在")
        
        # 检查权限
        if contract.house and contract.house.owner_id != g.user_id and g.user_role != 'admin':
            return APIResponse.forbidden("您没有权限编辑此合同")
        
        # 已生效的合同不能随意修改关键信息
        if contract.status == 'active':
            restricted_fields = ['house_id', 'tenant_id', 'start_date', 'end_date']
            data = request.get_json() or {}
            for field in restricted_fields:
                if field in data:
                    return APIResponse.bad_request(f"已生效的合同不能修改{field}字段")
        
        # 获取请求数据
        data = request.get_json()
        
        if not data:
            return APIResponse.bad_request("请求数据不能为空")
        
        # 验证数据
        is_valid, error_msg, validated_data = validate_contract_data(data, is_update=True)
        
        if not is_valid:
            return APIResponse.validation_error(error_msg)
        
        # 更新合同
        for key, value in validated_data.items():
            setattr(contract, key, value)
        
        db.session.commit()
        
        # 刷新获取完整数据
        db.session.refresh(contract)
        
        # 格式化响应
        result = format_contract_response(contract)
        
        current_app.logger.info(f"用户 {g.username} 更新了合同 {contract_id}")
        
        return APIResponse.success(result, "合同更新成功")
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"更新合同失败：{str(e)}")
        return APIResponse.server_error("更新合同失败")


@contracts_bp.route('/<int:contract_id>', methods=['DELETE'])
@admin_required
def delete_contract(contract_id: int):
    """
    删除合同（仅管理员）
    
    Path Parameters:
        contract_id: 合同 ID
        
    Response:
        {
            "success": true,
            "message": "合同删除成功"
        }
    """
    try:
        contract = Contract.query.get(contract_id)
        
        if not contract:
            return APIResponse.not_found("合同不存在")
        
        # 检查是否有未完成的支付记录
        unpaid_payments = [p for p in contract.payments if p.status in ['pending', 'overdue', 'partial']]
        
        if len(unpaid_payments) > 0:
            return APIResponse.bad_request(
                f"合同有 {len(unpaid_payments)} 个未完成的支付记录，无法删除",
                {"unpaid_payments": len(unpaid_payments)}
            )
        
        contract_no = contract.contract_no
        
        # 如果是合租房源，释放房间
        if contract.room_id:
            room = Room.query.get(contract.room_id)
            if room:
                room.status = 'available'
        
        if contract.house:
            contract.house.update_status()
        
        tenant_id = contract.tenant_id
        tenant = contract.tenant_rel
        
        db.session.delete(contract)
        
        if tenant:
            tenant.update_status()
        
        db.session.commit()
        
        current_app.logger.info(f"管理员 {g.username} 删除了合同 {contract_no}")
        
        return APIResponse.success(None, "合同删除成功")
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"删除合同失败：{str(e)}")
        return APIResponse.server_error("删除合同失败")


# ============================================================================
# 合同操作接口
# ============================================================================

@contracts_bp.route('/<int:contract_id>/renew', methods=['POST'])
@login_required
@permission_required('edit')
def renew_contract(contract_id: int):
    """
    合同续签
    
    Path Parameters:
        contract_id: 合同 ID
        
    Request Body:
        {
            "end_date": "2026-01-01",  // 新的结束日期
            "rent_amount": 5500,  // 可选：新租金
            "remark": "续签备注"
        }
        
    Response:
        {
            "success": true,
            "message": "合同续签成功",
            "data": {
                "old_contract": {...},
                "new_contract": {...}
            }
        }
    """
    try:
        contract = Contract.query.get(contract_id)
        
        if not contract:
            return APIResponse.not_found("合同不存在")
        
        # 检查权限
        if contract.house and contract.house.owner_id != g.user_id and g.user_role != 'admin':
            return APIResponse.forbidden("您没有权限操作此合同")
        
        # 检查合同状态
        if contract.status not in ['active', 'expired']:
            return APIResponse.bad_request("只有生效中或已到期的合同才能续签")
        
        # 获取请求数据
        data = request.get_json()
        
        if not data:
            return APIResponse.bad_request("请求数据不能为空")
        
        # 验证新结束日期
        if not data.get('end_date'):
            return APIResponse.bad_request("新的结束日期不能为空")
        
        try:
            new_end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
            if new_end_date <= contract.end_date:
                return APIResponse.bad_request("新的结束日期必须晚于原结束日期")
        except (ValueError, TypeError):
            return APIResponse.bad_request("结束日期格式不正确，应为 YYYY-MM-DD")
        
        # 检查原合同押金状态
        deposit_transferred = False
        deposit_message = ""
        
        if contract.can_transfer_deposit():
            # 原合同押金已支付且金额大于0，可以转移
            deposit_transferred = True
            deposit_message = "押金已从原合同转移"
        elif contract.deposit_amount > 0 and contract.deposit_status == 'pending':
            # 原合同押金未支付，需要提示
            deposit_message = "注意：原合同押金尚未支付，新合同需要重新收取押金"
        elif contract.deposit_amount == 0:
            # 原合同没有押金
            deposit_message = "原合同无押金"
        
        # 创建新合同
        new_contract = Contract(
            contract_no=Contract.generate_contract_no(),
            title=f"{contract.title} (续签)",
            house_id=contract.house_id,
            room_id=contract.room_id,
            tenant_id=contract.tenant_id,
            start_date=contract.end_date,  # 从原合同结束日期开始
            end_date=new_end_date,
            rent_amount=data.get('rent_amount', contract.rent_amount),
            deposit_amount=0 if deposit_transferred else contract.deposit_amount,  # 押金转移则为0
            payment_type=data.get('payment_type', contract.payment_type),
            payment_cycle=contract.payment_cycle,
            description=contract.description,
            remark=data.get('remark', '合同续签'),
            status='active',  # 续签合同直接激活
            original_contract_id=contract.id,  # 记录原合同ID
            deposit_status='paid' if deposit_transferred else 'pending'  # 押金状态
        )
        
        # 如果押金转移，更新原合同押金状态
        if deposit_transferred:
            try:
                contract.update_deposit_status('transferred')
                current_app.logger.info(
                    f"合同 {contract.contract_no} 押金已转移，"
                    f"金额: {contract.deposit_amount}元"
                )
            except ValueError as e:
                current_app.logger.warning(f"押金状态更新失败: {str(e)}")
        
        # 标记原合同为已续签
        contract.status = 'renewed'
        
        db.session.add(new_contract)
        db.session.flush()
        
        # 生成支付计划（只生成租金，押金已转移或沿用原合同）
        payment_summary = generate_payment_plan(new_contract)
        
        if contract.room_id:
            room = Room.query.get(contract.room_id)
            if room:
                room.status = 'rented'
        
        if contract.tenant_rel:
            contract.tenant_rel.update_status()
        
        db.session.commit()
        
        # 刷新获取完整数据
        db.session.refresh(new_contract)
        
        current_app.logger.info(
            f"用户 {g.username} 续签了合同 {contract.contract_no}，"
            f"生成 {payment_summary['rent_count']} 笔租金记录，押金{'已转移' if deposit_transferred else '沿用原合同'}"
        )
        
        result = {
            'old_contract': contract.to_dict(),
            'new_contract': new_contract.to_dict(),
            'payment_summary': payment_summary,
            'deposit_transferred': deposit_transferred,
            'original_deposit': float(contract.deposit_amount) if deposit_transferred else 0,
            'deposit_message': deposit_message
        }
        
        message = f"合同续签成功，已生成 {payment_summary['rent_count']} 笔租金记录"
        if deposit_transferred:
            message += f"，押金 {float(contract.deposit_amount)} 元已从原合同转移"
        else:
            message += f"，{deposit_message}"
        
        return APIResponse.success(result, message)
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"合同续签失败：{str(e)}")
        return APIResponse.server_error("合同续签失败")


@transactional()
def _do_activate_contract(contract_id: int, user_id: int, user_role: str) -> dict:
    """
    执行合同激活的核心业务逻辑（事务保护）
    
    Args:
        contract_id: 合同 ID
        user_id: 当前用户 ID
        user_role: 当前用户角色
        
    Returns:
        dict: 包含合同信息和支付计划摘要
        
    Raises:
        ValueError: 业务逻辑错误
        PermissionError: 权限错误
        DatabaseException: 数据库错误
    """
    contract = Contract.query.get(contract_id)
    
    if not contract:
        raise ValueError("合同不存在")
    
    # 检查权限
    if contract.house and contract.house.owner_id != user_id and user_role != 'admin':
        raise PermissionError("您没有权限操作此合同")
    
    # 检查合同状态
    if contract.status not in ['draft']:
        raise ValueError("只有草稿状态的合同才能激活")
    
    # 更新合同状态
    contract.status = 'active'
    
    # 生成支付计划（在同一事务中）
    payment_summary = generate_payment_plan(contract)
    
    # 如果租金记录为0，记录警告（可能是租期为0或其他原因）
    if payment_summary['rent_count'] == 0:
        current_app.logger.warning(
            f"合同 {contract.contract_no} 未生成租金记录，请检查合同租期设置"
        )
    
    # 如果是合租房源，更新房间状态
    if contract.room_id:
        room = Room.query.get(contract.room_id)
        if room:
            room.status = 'rented'
    
    if contract.house:
        contract.house.update_status()
    
    if contract.tenant_rel:
        contract.tenant_rel.update_status()
    
    return {
        "contract": contract.to_dict(),
        "payment_summary": payment_summary
    }


@contracts_bp.route('/<int:contract_id>/activate', methods=['POST'])
@login_required
@permission_required('edit')
def activate_contract(contract_id: int):
    """
    合同激活
    
    使用 @transactional 装饰器确保以下操作的原子性：
    1. 合同状态更新
    2. 支付计划生成
    3. 房间状态更新（合租房源）
    4. 房源状态更新
    5. 租客状态更新
    
    Path Parameters:
        contract_id: 合同 ID
        
    Response:
        {
            "success": true,
            "message": "合同激活成功，已生成 12 笔租金记录和 1 笔押金记录",
            "data": {
                "contract": {...},
                "payment_summary": {
                    "rent_count": 12,
                    "deposit_count": 1
                }
            }
        }
    """
    try:
        # 调用事务保护的核心业务函数
        result = _do_activate_contract(
            contract_id=contract_id,
            user_id=g.user_id,
            user_role=g.user_role
        )
        
        payment_summary = result['payment_summary']
        
        current_app.logger.info(
            f"用户 {g.username} 激活了合同 {result['contract']['contract_no']}，"
            f"生成 {payment_summary['rent_count']} 笔租金记录和 "
            f"{payment_summary['deposit_count']} 笔押金记录"
        )
        
        # 构建返回消息
        message = f"合同激活成功，已生成 {payment_summary['rent_count']} 笔租金记录"
        if payment_summary['deposit_count'] > 0:
            message += f"和 {payment_summary['deposit_count']} 笔押金记录"
        
        return APIResponse.success(result, message)
        
    except ValueError as e:
        if "合同不存在" in str(e):
            return APIResponse.not_found(str(e))
        return APIResponse.bad_request(str(e))
    except PermissionError as e:
        return APIResponse.forbidden(str(e))
    except DatabaseException as e:
        current_app.logger.error(f"合同激活数据库错误：{str(e)}")
        return APIResponse.server_error("合同激活失败，数据库操作错误")
    except Exception as e:
        current_app.logger.error(f"合同激活失败：{str(e)}", exc_info=True)
        return APIResponse.server_error("合同激活失败")


@contracts_bp.route('/<int:contract_id>/terminate', methods=['POST'])
@login_required
@permission_required('edit')
def terminate_contract(contract_id: int):
    """
    合同终止（带并发控制和事务保护）
    
    使用乐观锁和文件锁双重保护：
    1. 乐观锁：检查版本号，防止数据库层面的并发冲突
    2. 文件锁：保护关键操作，防止同一进程内的并发访问
    3. 事务装饰器：确保合同状态、房源状态、支付计划原子更新
    
    Path Parameters:
        contract_id: 合同 ID
        
    Request Body:
        {
            "reason": "终止原因",
            "terminate_date": "2024-06-01",  // 终止日期，默认为今天
            "settlement_amount": 5000,  // 结算金额（可选）
            "version": 0  // 乐观锁版本号（可选，用于并发控制）
        }
        
    Response:
        {
            "success": true,
            "message": "合同终止成功",
            "data": {...}
        }
        
    Error Codes:
        - 409: 版本冲突（乐观锁）
        - 423: 资源锁定中（文件锁）
    """
    try:
        # 获取请求数据
        data = request.get_json() or {}
        
        # 获取乐观锁版本号
        expected_version = data.get('version')
        
        # 使用文件锁保护关键操作
        try:
            with ContractLock.terminate_lock(contract_id, timeout=30.0):
                # 执行终止操作（带重试和事务保护）
                result = _execute_terminate_contract(
                    contract_id=contract_id,
                    data=data,
                    expected_version=expected_version
                )
                return result
                
        except FileLockTimeoutError as e:
            current_app.logger.warning(f"合同终止操作锁定超时: {contract_id}")
            return APIResponse.error(
                error_code='resource_locked',
                message='合同正在被其他操作处理，请稍后重试',
                status_code=423
            )
        except FileLockError as e:
            current_app.logger.error(f"合同终止操作锁定失败: {str(e)}")
            return APIResponse.error(
                error_code='lock_error',
                message='获取操作锁失败，请稍后重试',
                status_code=500
            )
            
    except OptimisticLockError as e:
        current_app.logger.warning(f"合同终止版本冲突: {str(e)}")
        return APIResponse.error(
            error_code='version_conflict',
            message='合同已被其他用户修改，请刷新后重试',
            status_code=409
        )
    except DatabaseException as e:
        current_app.logger.error(f"合同终止数据库错误：{str(e)}")
        return APIResponse.server_error("合同终止失败，数据库操作错误")
    except Exception as e:
        current_app.logger.error(f"合同终止失败：{str(e)}")
        return APIResponse.server_error("合同终止失败")


@transactional()
def _do_terminate_contract_core(
    contract_id: int,
    data: Dict,
    expected_version: Optional[int],
    user_id: int,
    user_role: str,
    username: str
) -> dict:
    """
    执行合同终止的核心业务逻辑（事务保护）
    
    确保以下操作的原子性：
    1. 合同状态更新
    2. 房间状态更新（合租房源）
    3. 房源状态更新
    4. 租客状态更新
    5. 支付计划更新
    6. 押金退款记录创建
    
    Args:
        contract_id: 合同 ID
        data: 请求数据
        expected_version: 期望的版本号（乐观锁）
        user_id: 当前用户 ID
        user_role: 当前用户角色
        username: 当前用户名
        
    Returns:
        dict: 包含合同信息和支付计划摘要
        
    Raises:
        ValueError: 业务逻辑错误
        PermissionError: 权限错误
        OptimisticLockError: 乐观锁冲突
        DatabaseException: 数据库错误
    """
    contract = Contract.query.get(contract_id)
    
    if not contract:
        raise ValueError("合同不存在")
    
    # 检查权限
    if contract.house and contract.house.owner_id != user_id and user_role != 'admin':
        raise PermissionError("您没有权限操作此合同")
    
    # 检查合同状态
    if contract.status not in ['active']:
        raise ValueError("只有生效中的合同才能终止")
    
    # 乐观锁检查
    if expected_version is not None:
        if not contract.check_version(expected_version):
            raise OptimisticLockError(
                f"合同版本冲突：期望版本 {expected_version}，实际版本 {contract.version}"
            )
    
    # 获取终止日期
    terminate_date_str = data.get('terminate_date')
    if terminate_date_str:
        try:
            terminate_date = datetime.strptime(terminate_date_str, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            raise ValueError("终止日期格式不正确")
    else:
        terminate_date = date.today()
    
    # 更新合同状态
    contract.status = 'terminated'
    contract.remark = (contract.remark or '') + f"\n合同于{terminate_date}终止，原因：{data.get('reason', '无')}"
    
    # 递增版本号（乐观锁）
    contract.increment_version()
    
    # 如果是合租房源，释放房间
    if contract.room_id:
        room = Room.query.get(contract.room_id)
        if room:
            room.status = 'available'
    
    if contract.house:
        contract.house.update_status()
    
    tenant = contract.tenant_rel
    
    if tenant:
        from app.utils.credit_score import CreditEventType, CreditScoreConfig
        config = CreditScoreConfig.get_event_config(CreditEventType.EARLY_TERMINATION)
        tenant.add_credit_record(
            event_type='early_termination',
            score_change=config['score_change'],
            description=f"{config['description']}（合同编号: {contract.contract_no}）",
            related_id=contract.id
        )
    
    unpaid_payments = [p for p in contract.payments if p.status in ['pending', 'overdue', 'partial']]
    cancelled_count = 0
    pending_count = 0
    
    for payment in unpaid_payments:
        if payment.due_date > terminate_date:
            payment.status = 'cancelled'
            payment.remark = (payment.remark or '') + '\n合同终止自动取消'
            cancelled_count += 1
        else:
            pending_count += 1
    
    deposit_refund = None
    # 只有押金已支付或已转移的合同才需要处理退款
    if contract.deposit_amount and contract.deposit_amount > 0 and contract.deposit_status in ['paid', 'transferred']:
        existing_refund = DepositRefund.query.filter_by(contract_id=contract.id).first()
        if not existing_refund:
            deposit_refund = DepositRefund(
                contract_id=contract.id,
                tenant_id=contract.tenant_id,
                house_id=contract.house_id,
                original_deposit=contract.deposit_amount,
                refund_amount=contract.deposit_amount,
                status='pending'
            )
            
            auto_deductions = calculate_auto_deductions_for_refund(contract, terminate_date)
            for deduction in auto_deductions:
                deposit_refund.add_deduction(
                    deduction['type'],
                    deduction['amount'],
                    deduction['description']
                )
            
            db.session.add(deposit_refund)
            
            current_app.logger.info(
                f"合同 {contract.contract_no} 终止，创建押金退款记录，"
                f"原押金: {contract.deposit_amount}元，押金状态: {contract.deposit_status}"
            )
    
    # 注意：事务装饰器会自动提交，不需要手动 commit
    
    # 更新租客状态（需要在主事务外单独处理）
    if tenant:
        tenant.update_status()
    
    current_app.logger.info(f"用户 {username} 终止了合同 {contract.contract_no}")
    
    result = contract.to_dict()
    result['payment_summary'] = {
        'cancelled_count': cancelled_count,
        'pending_count': pending_count,
        'message': f'已取消 {cancelled_count} 笔未来租金，{pending_count} 笔待结算租金需人工处理'
    }
    
    if deposit_refund:
        result['deposit_refund'] = deposit_refund.to_dict()
        result['deposit_refund']['message'] = f'已创建押金退款记录，原始押金 {deposit_refund.original_deposit} 元，扣款 {deposit_refund.total_deduction} 元，应退 {deposit_refund.refund_amount} 元'
    
    return result


def _execute_terminate_contract(
    contract_id: int,
    data: Dict,
    expected_version: Optional[int] = None
):
    """
    执行合同终止操作（内部函数）
    
    带有乐观锁检查和重试机制，调用事务保护的核心函数
    
    Args:
        contract_id: 合同 ID
        data: 请求数据
        expected_version: 期望的版本号（乐观锁）
        
    Returns:
        API 响应
    """
    # 定义重试配置
    retry_config = RetryConfig(
        max_retries=3,
        base_delay=0.1,
        max_delay=2.0,
        exponential_base=2.0,
        jitter=True
    )
    
    def _do_terminate():
        """执行终止操作的内部函数"""
        # 调用事务保护的核心业务函数
        return _do_terminate_contract_core(
            contract_id=contract_id,
            data=data,
            expected_version=expected_version,
            user_id=g.user_id,
            user_role=g.user_role,
            username=g.username
        )
    
    try:
        # 执行操作（带重试）
        result = retry_call(_do_terminate, config=retry_config)
        return APIResponse.success(result, "合同终止成功")
        
    except ValueError as e:
        if "合同不存在" in str(e):
            return APIResponse.not_found(str(e))
        return APIResponse.bad_request(str(e))
    except PermissionError as e:
        return APIResponse.forbidden(str(e))
    except OptimisticLockError as e:
        raise  # 向上抛出，由外层处理
    except DatabaseException as e:
        current_app.logger.error(f"合同终止数据库错误：{str(e)}")
        raise
    except Exception as e:
        current_app.logger.error(f"合同终止执行失败：{str(e)}")
        raise


@contracts_bp.route('/expiring', methods=['GET'])
@login_required
def get_expiring_contracts():
    """
    获取即将到期合同（30 天内）
    
    Query Parameters:
        days: 天数范围，默认 30
        include_expired: 是否包含已过期合同，默认 false
        
    Response:
        {
            "success": true,
            "data": {
                "expiring_contracts": [...],
                "expired_contracts": [...],
                "total_expiring": 10,
                "total_expired": 2
            }
        }
    """
    try:
        # 获取参数
        days = request.args.get('days', 30, type=int)
        include_expired = request.args.get('include_expired', 'false').lower() == 'true'
        
        # 计算日期范围
        today = date.today()
        threshold_date = today + timedelta(days=days)
        
        # 查询即将到期合同
        expiring_query = Contract.query.filter(
            Contract.status == 'active',
            Contract.end_date >= today,
            Contract.end_date <= threshold_date
        ).order_by(Contract.end_date.asc())
        
        expiring_contracts = expiring_query.all()
        
        # 查询已过期合同
        expired_contracts = []
        if include_expired:
            expired_query = Contract.query.filter(
                Contract.status == 'active',
                Contract.end_date < today
            ).order_by(Contract.end_date.desc())
            expired_contracts = expired_query.all()
        
        # 格式化响应
        result = {
            'expiring_contracts': [contract.to_dict() for contract in expiring_contracts],
            'total_expiring': len(expiring_contracts)
        }
        
        if include_expired:
            result['expired_contracts'] = [contract.to_dict() for contract in expired_contracts]
            result['total_expired'] = len(expired_contracts)
        
        return APIResponse.success(result, "获取即将到期合同成功")
        
    except Exception as e:
        current_app.logger.error(f"获取即将到期合同失败：{str(e)}")
        return APIResponse.server_error("获取即将到期合同失败")


@contracts_bp.route('/<int:contract_id>/payments', methods=['GET'])
@login_required
def get_contract_payments(contract_id: int):
    """
    获取合同支付记录列表
    
    Path Parameters:
        contract_id: 合同 ID
        
    Query Parameters:
        status: 支付状态筛选 (pending/paid/overdue/partial/refunded)
        
    Response:
        {
            "success": true,
            "data": {
                "contract_id": 1,
                "contract_no": "HT20240101ABC12345",
                "payments": [...]
            }
        }
    """
    try:
        contract = Contract.query.get(contract_id)
        
        if not contract:
            return APIResponse.not_found("合同不存在")
        
        # 构建查询
        query = Payment.query.filter_by(contract_id=contract_id)
        
        # 状态筛选
        status = request.args.get('status')
        if status:
            if status not in ['pending', 'paid', 'overdue', 'partial', 'refunded', 'cancelled']:
                return APIResponse.bad_request("状态参数不正确")
            query = query.filter(Payment.status == status)
        
        # 排序
        query = query.order_by(Payment.due_date.asc())
        
        # 获取所有支付记录
        payments = query.all()
        
        # 格式化响应
        payment_list = [payment.to_dict() for payment in payments]
        
        # 计算统计信息
        total_amount = sum(p.amount for p in payments if p.status != 'cancelled')
        paid_amount = sum(p.paid_amount for p in payments if p.status == 'paid')
        overdue_count = sum(1 for p in payments if p.is_overdue())
        
        return APIResponse.success({
            'contract_id': contract_id,
            'contract_no': contract.contract_no,
            'payments': payment_list,
            'statistics': {
                'total_amount': total_amount,
                'paid_amount': paid_amount,
                'pending_amount': total_amount - paid_amount,
                'overdue_count': overdue_count
            }
        }, "获取合同支付记录成功")
        
    except Exception as e:
        current_app.logger.error(f"获取合同支付记录失败：{str(e)}")
        return APIResponse.server_error("获取合同支付记录失败")


# ============================================================================
# 支付计划生成
# ============================================================================

def generate_payment_plan(contract: Contract) -> Dict[str, int]:
    """
    生成合同支付计划
    
    根据合同租期和付款周期，生成多笔租金记录和押金记录。
    
    Args:
        contract: 合同对象
        
    Returns:
        dict: 包含生成的租金记录数量和押金记录数量
              例如: {'rent_count': 12, 'deposit_count': 1}
    """
    # payment_type 到 payment_cycle 的映射（月数）
    PAYMENT_CYCLE_MAP = {
        '月付': 1,
        '季付': 3,
        '半年付': 6,
        '年付': 12
    }
    
    rent_count = 0
    deposit_count = 0
    
    try:
        start_date = contract.start_date
        end_date = contract.end_date
        
        # 验证日期有效性
        if not start_date or not end_date:
            current_app.logger.error(f"合同 {contract.contract_no} 缺少开始或结束日期")
            return {'rent_count': 0, 'deposit_count': 0}
        
        if end_date <= start_date:
            current_app.logger.error(f"合同 {contract.contract_no} 结束日期必须晚于开始日期")
            return {'rent_count': 0, 'deposit_count': 0}
        
        # 获取付款周期（月数）
        payment_type = contract.payment_type or '月付'
        cycle_months = PAYMENT_CYCLE_MAP.get(payment_type, 1)
        
        current_app.logger.info(
            f"开始为合同 {contract.contract_no} 生成支付计划，"
            f"租期: {start_date} 至 {end_date}，付款方式: {payment_type}（{cycle_months}个月/期）"
        )
        
        # 生成租金支付记录
        current_period_start = start_date
        
        while current_period_start < end_date:
            # 计算当前周期的结束日期（周期结束日期为下个周期开始日期的前一天）
            current_period_end = current_period_start + relativedelta(months=cycle_months) - timedelta(days=1)
            
            # 如果周期结束日期超过合同结束日期，则使用合同结束日期
            if current_period_end >= end_date:
                current_period_end = end_date
            
            # 计算该周期的实际月数（用于计算金额）
            # 使用 relativedelta 计算精确的月份差
            delta = relativedelta(current_period_end, current_period_start)
            actual_months = delta.years * 12 + delta.months
            
            # 如果不满一个月，按实际天数比例计算
            if actual_months == 0:
                # 计算实际天数
                actual_days = (current_period_end - current_period_start).days + 1
                # 按每月30天计算比例
                actual_months = actual_days / 30.0
            else:
                # 如果有剩余天数，也需要考虑
                if delta.days > 0:
                    # 将剩余天数转换为月的小数部分
                    actual_months += delta.days / 30.0
            
            # 计算该周期的租金金额
            # 注意：rent_amount 是 Decimal 类型，需要转换为 float 进行计算
            amount = float(contract.rent_amount) * actual_months
            
            # 创建租金支付记录
            payment = Payment(
                payment_no=Payment.generate_payment_no(),
                contract_id=contract.id,
                payment_type='rent',
                amount=round(amount, 2),  # 保留两位小数
                paid_amount=0,
                period_start=current_period_start,
                period_end=current_period_end,
                due_date=current_period_start,  # 应缴日期为周期开始日期
                status='pending',
                late_fee_rate=0.0005,  # 日利率 0.05%
                remark=f'租金（{current_period_start.strftime("%Y-%m-%d")} 至 {current_period_end.strftime("%Y-%m-%d")}）'
            )
            
            db.session.add(payment)
            rent_count += 1
            
            current_app.logger.debug(
                f"生成租金记录 #{rent_count}: {current_period_start} 至 {current_period_end}，"
                f"金额: {amount:.2f}元，周期月数: {actual_months:.2f}"
            )
            
            # 移动到下一个周期
            current_period_start = current_period_end + timedelta(days=1)
        
        # 生成押金支付记录
        if contract.deposit_amount and contract.deposit_amount > 0:
            deposit_payment = Payment(
                payment_no=Payment.generate_payment_no(),
                contract_id=contract.id,
                payment_type='deposit',
                amount=contract.deposit_amount,
                paid_amount=0,
                due_date=start_date,  # 押金应缴日期为合同开始日期
                status='pending',
                remark='押金'
            )
            db.session.add(deposit_payment)
            deposit_count = 1
            
            current_app.logger.info(f"生成押金记录: {contract.deposit_amount}元")
        
        # 不在函数内部 commit，由调用者控制事务
        current_app.logger.info(
            f"合同 {contract.contract_no} 支付计划生成完成: "
            f"{rent_count}笔租金记录，{deposit_count}笔押金记录"
        )
        
        return {
            'rent_count': rent_count,
            'deposit_count': deposit_count
        }
        
    except Exception as e:
        current_app.logger.error(f"生成支付计划失败: {str(e)}", exc_info=True)
        # 不在函数内部 rollback，由调用者控制事务
        return {
            'rent_count': 0,
            'deposit_count': 0
        }


# ============================================================================
# 统计接口
# ============================================================================

@contracts_bp.route('/stats', methods=['GET'])
@login_required
def get_contract_stats():
    """
    获取合同统计信息
    
    Query Parameters:
        landlord_id: 房东 ID（管理员可查看所有房东的统计）
        
    Response:
        {
            "success": true,
            "data": {
                "total": 100,
                "by_status": {
                    "draft": 5,
                    "active": 60,
                    "expired": 20,
                    "terminated": 10,
                    "renewed": 5
                },
                "expiring_soon": 10,
                "total_rent_amount": 500000
            }
        }
    """
    try:
        # 构建查询
        query = Contract.query
        
        # 权限筛选：非管理员只能查看自己负责的房源的合同
        if g.user_role != 'admin':
            # 通过房源负责人筛选（需要 join House 表）
            query = query.join(Contract.house).filter(
                db.text('houses.owner_id = :owner_id')
            ).params(owner_id=g.user_id)
        
        # 房东筛选（仅管理员可用）
        landlord_id = request.args.get('landlord_id', type=int)
        if landlord_id and g.user_role == 'admin':
            # 管理员可以通过房东ID筛选（通过房源的房东ID）
            query = query.join(Contract.house).filter(
                db.text('houses.landlord_id = :landlord_id')
            ).params(landlord_id=landlord_id)
        
        # 统计总数
        total = query.count()
        
        # 按状态统计
        draft = query.filter(Contract.status == 'draft').count()
        active = query.filter(Contract.status == 'active').count()
        expired = query.filter(Contract.status == 'expired').count()
        terminated = query.filter(Contract.status == 'terminated').count()
        renewed = query.filter(Contract.status == 'renewed').count()
        
        # 统计即将到期合同
        expiring_soon = query.filter(
            Contract.status == 'active',
            Contract.end_date >= date.today(),
            Contract.end_date <= date.today() + timedelta(days=30)
        ).count()
        
        # 统计总租金
        active_contracts = query.filter(Contract.status == 'active').all()
        total_rent_amount = sum(c.rent_amount for c in active_contracts)
        
        return APIResponse.success({
            'total': total,
            'by_status': {
                'draft': draft,
                'active': active,
                'expired': expired,
                'terminated': terminated,
                'renewed': renewed
            },
            'expiring_soon': expiring_soon,
            'total_rent_amount': total_rent_amount
        }, "获取合同统计信息成功")
        
    except Exception as e:
        current_app.logger.error(f"获取合同统计失败：{str(e)}")
        return APIResponse.server_error("获取合同统计失败")


@contracts_bp.route('/batch-update-status', methods=['POST'])
@login_required
@permission_required('edit')
def batch_update_contract_status():
    """
    批量更新合同状态
    
    Request Body:
        {
            "contract_ids": [1, 2, 3],
            "status": "terminated"
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
        
        contract_ids = data.get('contract_ids', [])
        status = data.get('status')
        
        if not contract_ids:
            return APIResponse.bad_request("合同 ID 列表不能为空")
        
        if not isinstance(contract_ids, list):
            return APIResponse.bad_request("contract_ids 必须是数组")
        
        if not status:
            return APIResponse.bad_request("状态不能为空")
        
        valid_statuses = ['draft', 'active', 'expired', 'terminated', 'renewed']
        if status not in valid_statuses:
            return APIResponse.bad_request(f"状态必须是：{', '.join(valid_statuses)}")
        
        updated_count = 0
        failed_count = 0
        details = []
        
        for contract_id in contract_ids:
            try:
                contract = Contract.query.get(contract_id)
                
                if not contract:
                    details.append({
                        'contract_id': contract_id,
                        'success': False,
                        'message': '合同不存在'
                    })
                    failed_count += 1
                    continue
                
                if contract.house and contract.house.owner_id != g.user_id and g.user_role != 'admin':
                    details.append({
                        'contract_id': contract_id,
                        'success': False,
                        'message': '没有权限操作此合同'
                    })
                    failed_count += 1
                    continue
                
                old_status = contract.status
                contract.status = status
                
                if status == 'terminated':
                    if contract.room_id:
                        room = Room.query.get(contract.room_id)
                        if room:
                            room.status = 'available'
                    
                    if contract.house:
                        contract.house.update_status()
                    
                    if contract.tenant_rel:
                        contract.tenant_rel.update_status()
                
                details.append({
                    'contract_id': contract_id,
                    'success': True,
                    'old_status': old_status,
                    'new_status': status,
                    'message': '更新成功'
                })
                updated_count += 1
                
            except Exception as e:
                details.append({
                    'contract_id': contract_id,
                    'success': False,
                    'message': str(e)
                })
                failed_count += 1
        
        if updated_count > 0:
            db.session.commit()
        
        current_app.logger.info(
            f"用户 {g.username} 批量更新合同状态：成功 {updated_count} 条，失败 {failed_count} 条"
        )
        
        return APIResponse.success({
            'updated_count': updated_count,
            'failed_count': failed_count,
            'details': details
        }, f"批量更新成功：{updated_count} 条记录已更新")
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"批量更新合同状态失败：{str(e)}")
        return APIResponse.server_error("批量更新合同状态失败")
