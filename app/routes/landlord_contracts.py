"""
承包合同管理路由模块
提供承包合同 CRUD、续签、终止、到期提醒等功能
"""
from flask import Blueprint, request, jsonify, g, current_app
from typing import Optional, Dict, Any
from datetime import datetime, date, timedelta

from app.models.landlord_contract import LandlordContract
from app.models.landlord import Landlord
from app.models.house import House
from app.models import db
from app.utils.decorators import login_required, admin_required, permission_required
from app.utils.responses import APIResponse, PaginationResponse

# 创建蓝图
landlord_contracts_bp = Blueprint('landlord_contracts', __name__, url_prefix='/api/landlord_contracts')


# ============================================================================
# 辅助函数
# ============================================================================

def validate_landlord_contract_data(data: Dict, is_update: bool = False) -> tuple:
    """
    验证承包合同数据
    
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
    
    # 房东 ID（必填）
    if not is_update or 'landlord_id' in data:
        if not data.get('landlord_id'):
            errors.append('房东 ID 不能为空')
        else:
            try:
                landlord_id = int(data['landlord_id'])
                landlord = Landlord.query.get(landlord_id)
                if not landlord:
                    errors.append('房东不存在')
                else:
                    validated_data['landlord_id'] = landlord_id
            except (ValueError, TypeError):
                errors.append('房东 ID 必须是有效的整数')
    
    # 房源 ID 列表（必填，支持多个房源）
    if not is_update or 'house_ids' in data:
        house_ids = data.get('house_ids', [])
        if not house_ids:
            errors.append('房源 ID 列表不能为空')
        else:
            try:
                if not isinstance(house_ids, list):
                    errors.append('房源 ID 列表必须是数组格式')
                else:
                    # 验证所有房源是否存在
                    valid_house_ids = []
                    for house_id in house_ids:
                        house = House.query.get(int(house_id))
                        if not house:
                            errors.append(f'房源 ID {house_id} 不存在')
                        else:
                            valid_house_ids.append(int(house_id))
                    
                    if valid_house_ids:
                        validated_data['house_ids'] = valid_house_ids
            except (ValueError, TypeError) as e:
                errors.append('房源 ID 必须是有效的整数')
    
    # 合同期限
    if not is_update or 'start_date' in data:
        if not data.get('start_date'):
            errors.append('开始日期不能为空')
        else:
            try:
                start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
                validated_data['start_date'] = start_date
            except (ValueError, TypeError):
                errors.append('开始日期格式不正确，应为 YYYY-MM-DD')
    
    if not is_update or 'end_date' in data:
        if not data.get('end_date'):
            errors.append('结束日期不能为空')
        else:
            try:
                end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
                # 验证结束日期必须晚于开始日期
                if 'start_date' in validated_data and end_date <= validated_data['start_date']:
                    errors.append('结束日期必须晚于开始日期')
                validated_data['end_date'] = end_date
            except (ValueError, TypeError):
                errors.append('结束日期格式不正确，应为 YYYY-MM-DD')
    
    # 合同金额（必填）
    if not is_update or 'contract_amount' in data:
        if not data.get('contract_amount'):
            errors.append('合同金额不能为空')
        else:
            try:
                contract_amount = float(data['contract_amount'])
                if contract_amount <= 0:
                    errors.append('合同金额必须大于 0')
                validated_data['contract_amount'] = contract_amount
            except (ValueError, TypeError):
                errors.append('合同金额必须是有效的数字')
    
    # 服务费率（必填）
    if not is_update or 'service_fee_rate' in data:
        if not data.get('service_fee_rate'):
            errors.append('服务费率不能为空')
        else:
            try:
                service_fee_rate = float(data['service_fee_rate'])
                if service_fee_rate < 0 or service_fee_rate > 100:
                    errors.append('服务费率必须在 0-100 之间')
                validated_data['service_fee_rate'] = service_fee_rate
            except (ValueError, TypeError):
                errors.append('服务费率必须是有效的数字')
    
    # 最低服务费（可选）
    if 'minimum_fee' in data:
        try:
            minimum_fee = float(data['minimum_fee']) if data['minimum_fee'] else None
            if minimum_fee is not None and minimum_fee < 0:
                errors.append('最低服务费不能为负数')
            validated_data['minimum_fee'] = minimum_fee
        except (ValueError, TypeError):
            errors.append('最低服务费必须是有效的数字')
    
    # 付款周期（可选）
    if 'payment_cycle' in data:
        try:
            payment_cycle = int(data['payment_cycle']) if data['payment_cycle'] else 1
            if payment_cycle <= 0:
                errors.append('付款周期必须大于 0')
            validated_data['payment_cycle'] = payment_cycle
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
        if data['status'] not in ['draft', 'active', 'expired', 'terminated']:
            errors.append('状态必须是：draft(草稿)、active(生效中)、expired(已过期)、terminated(已终止)')
        else:
            validated_data['status'] = data['status']
    
    if errors:
        return False, '; '.join(errors), None
    
    return True, None, validated_data


def format_landlord_contract_response(contract: LandlordContract, include_details: bool = False) -> Dict:
    """
    格式化承包合同响应数据
    
    Args:
        contract: 合同对象
        include_details: 是否包含详细信息
        
    Returns:
        dict: 合同响应数据
    """
    data = contract.to_dict()
    
    # 添加更多信息
    if include_details:
        # 获取关联房源详细信息
        houses = contract.get_houses()
        data['houses_detail'] = [house.to_dict(include_landlord=True) for house in houses]
    
    return data


# ============================================================================
# 承包合同 CRUD 接口
# ============================================================================

@landlord_contracts_bp.route('', methods=['GET'])
@login_required
def get_landlord_contracts():
    """
    获取承包合同列表（支持分页、筛选、搜索）
    
    Query Parameters:
        page: 页码，默认 1
        per_page: 每页数量，默认 20，最大 100
        keyword: 关键词搜索（合同编号、标题）
        contract_no: 合同编号搜索
        status: 状态筛选 (draft/active/expired/terminated)
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
        # 获取查询参数
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        
        # 构建查询
        query = LandlordContract.query
        
        # 关键词搜索
        keyword = request.args.get('keyword')
        if keyword:
            query = query.filter(
                db.or_(
                    LandlordContract.contract_no.ilike(f'%{keyword}%'),
                    LandlordContract.title.ilike(f'%{keyword}%')
                )
            )
        
        # 合同编号搜索
        contract_no = request.args.get('contract_no')
        if contract_no:
            query = query.filter(LandlordContract.contract_no.ilike(f'%{contract_no}%'))
        
        # 状态筛选
        status = request.args.get('status')
        if status:
            # 支持多个状态，用逗号分隔
            status_list = status.split(',')
            valid_statuses = ['draft', 'active', 'expired', 'terminated']
            # 验证所有状态值
            for s in status_list:
                if s not in valid_statuses:
                    return APIResponse.bad_request("状态必须是：draft、active、expired、terminated")
            query = query.filter(LandlordContract.status.in_(status_list))
        
        # 房东 ID 筛选
        landlord_id = request.args.get('landlord_id', type=int)
        if landlord_id:
            query = query.filter(LandlordContract.landlord_id == landlord_id)
        
        # 即将到期合同筛选
        is_expiring = request.args.get('is_expiring', 'false').lower() == 'true'
        if is_expiring:
            expiring_threshold = date.today() + timedelta(days=30)
            query = query.filter(
                LandlordContract.status == 'active',
                LandlordContract.end_date <= expiring_threshold,
                LandlordContract.end_date >= date.today()
            )
        
        # 排序
        order_by = request.args.get('order_by', 'created_at')
        order = request.args.get('order', 'desc')
        
        order_column = getattr(LandlordContract, order_by, LandlordContract.created_at)
        if order == 'asc':
            query = query.order_by(order_column.asc())
        else:
            query = query.order_by(order_column.desc())
        
        # 执行分页查询
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        # 格式化响应数据
        items = [format_landlord_contract_response(contract) for contract in pagination.items]
        
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
        }, "获取承包合同列表成功")
        
    except Exception as e:
        current_app.logger.error(f"获取承包合同列表失败：{str(e)}")
        return APIResponse.server_error("获取承包合同列表失败")


@landlord_contracts_bp.route('/<int:contract_id>', methods=['GET'])
@login_required
def get_landlord_contract(contract_id: int):
    """
    获取承包合同详情
    
    Path Parameters:
        contract_id: 合同 ID
        
    Response:
        {
            "success": true,
            "data": {
                "id": 1,
                "contract_no": "LC20240101ABC1234",
                "title": "承包合同",
                "landlord": {...},
                "houses": [...],
                "contract_amount": 100000,
                "service_fee_rate": 5.0,
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
        contract = LandlordContract.query.get(contract_id)
        
        if not contract:
            return APIResponse.not_found("合同不存在")
        
        # 格式化响应数据（包含详细信息）
        data = format_landlord_contract_response(contract, include_details=True)
        
        return APIResponse.success(data, "获取承包合同详情成功")
        
    except Exception as e:
        current_app.logger.error(f"获取承包合同详情失败：{str(e)}")
        return APIResponse.server_error("获取承包合同详情失败")


@landlord_contracts_bp.route('', methods=['POST'])
@login_required
@permission_required('create')
def create_landlord_contract():
    """
    创建承包合同
    
    Request Body:
        {
            "title": "承包合同",
            "landlord_id": 1,
            "house_ids": [1, 2, 3],
            "start_date": "2024-01-01",
            "end_date": "2025-01-01",
            "contract_amount": 100000,
            "service_fee_rate": 5.0,
            "minimum_fee": 5000,
            "payment_cycle": 3,
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
        is_valid, error_msg, validated_data = validate_landlord_contract_data(data, is_update=False)
        
        if not is_valid:
            return APIResponse.validation_error(error_msg)
        
        # 检查房源是否已被其他承包合同占用
        existing_contracts = LandlordContract.query.filter(
            LandlordContract.status == 'active',
            LandlordContract.id != validated_data.get('id', 0)
        ).all()
        
        for existing_contract in existing_contracts:
            if existing_contract.house_ids:
                # 检查是否有重叠的房源
                overlapping_houses = set(existing_contract.house_ids) & set(validated_data['house_ids'])
                if overlapping_houses:
                    return APIResponse.bad_request(
                        f"房源 {', '.join(map(str, overlapping_houses))} 已被其他生效中的承包合同占用"
                    )
        
        # 创建合同
        contract = LandlordContract(**validated_data)
        contract.contract_no = LandlordContract.generate_contract_no()
        
        db.session.add(contract)
        db.session.commit()
        
        # 刷新获取完整数据
        db.session.refresh(contract)
        
        # 格式化响应
        result = format_landlord_contract_response(contract)
        
        current_app.logger.info(f"用户 {g.username} 创建了承包合同 {contract.contract_no}")
        
        return APIResponse.success(result, "承包合同创建成功", 201)
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"创建承包合同失败：{str(e)}")
        return APIResponse.server_error("创建承包合同失败")


@landlord_contracts_bp.route('/<int:contract_id>', methods=['PUT'])
@login_required
@permission_required('edit')
def update_landlord_contract(contract_id: int):
    """
    更新承包合同信息
    
    Path Parameters:
        contract_id: 合同 ID
        
    Request Body:
        {
            "title": "新的合同标题",
            "contract_amount": 120000,
            "service_fee_rate": 6.0,
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
        contract = LandlordContract.query.get(contract_id)
        
        if not contract:
            return APIResponse.not_found("合同不存在")
        
        # 获取请求数据
        data = request.get_json()
        
        if not data:
            return APIResponse.bad_request("请求数据不能为空")
        
        # 已生效的合同不能随意修改关键信息
        if contract.status == 'active':
            restricted_fields = ['landlord_id', 'house_ids', 'start_date', 'end_date']
            for field in restricted_fields:
                if field in data:
                    return APIResponse.bad_request(f"已生效的合同不能修改{field}字段")
        
        # 验证数据
        is_valid, error_msg, validated_data = validate_landlord_contract_data(data, is_update=True)
        
        if not is_valid:
            return APIResponse.validation_error(error_msg)
        
        # 更新合同
        for key, value in validated_data.items():
            setattr(contract, key, value)
        
        db.session.commit()
        
        # 刷新获取完整数据
        db.session.refresh(contract)
        
        # 格式化响应
        result = format_landlord_contract_response(contract)
        
        current_app.logger.info(f"用户 {g.username} 更新了承包合同 {contract_id}")
        
        return APIResponse.success(result, "承包合同更新成功")
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"更新承包合同失败：{str(e)}")
        return APIResponse.server_error("更新承包合同失败")


@landlord_contracts_bp.route('/<int:contract_id>', methods=['DELETE'])
@login_required
@permission_required('delete')
def delete_landlord_contract(contract_id: int):
    """
    删除承包合同
    
    Path Parameters:
        contract_id: 合同 ID
        
    Response:
        {
            "success": true,
            "message": "合同删除成功"
        }
    """
    try:
        contract = LandlordContract.query.get(contract_id)
        
        if not contract:
            return APIResponse.not_found("合同不存在")
        
        # 只有草稿状态的合同才能删除
        if contract.status != 'draft':
            return APIResponse.bad_request("只能删除草稿状态的合同")
        
        contract_no = contract.contract_no
        
        # 删除合同
        db.session.delete(contract)
        db.session.commit()
        
        current_app.logger.info(f"用户 {g.username} 删除了承包合同 {contract_no}")
        
        return APIResponse.success(None, "承包合同删除成功")
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"删除承包合同失败：{str(e)}")
        return APIResponse.server_error("删除承包合同失败")


# ============================================================================
# 合同操作接口
# ============================================================================

@landlord_contracts_bp.route('/<int:contract_id>/activate', methods=['POST'])
@login_required
@permission_required('edit')
def activate_landlord_contract(contract_id: int):
    """
    激活承包合同
    
    Path Parameters:
        contract_id: 合同 ID
        
    Response:
        {
            "success": true,
            "message": "合同激活成功",
            "data": {...}
        }
    """
    try:
        contract = LandlordContract.query.get(contract_id)
        
        if not contract:
            return APIResponse.not_found("合同不存在")
        
        # 检查合同状态
        if contract.status != 'draft':
            return APIResponse.bad_request("只有草稿状态的合同才能激活")
        
        # 更新合同状态
        contract.status = 'active'
        
        db.session.commit()
        
        # 刷新获取完整数据
        db.session.refresh(contract)
        
        current_app.logger.info(f"用户 {g.username} 激活了承包合同 {contract.contract_no}")
        
        return APIResponse.success(contract.to_dict(), "承包合同激活成功")
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"激活承包合同失败：{str(e)}")
        return APIResponse.server_error("激活承包合同失败")


@landlord_contracts_bp.route('/<int:contract_id>/terminate', methods=['POST'])
@login_required
@permission_required('edit')
def terminate_landlord_contract(contract_id: int):
    """
    终止承包合同
    
    Path Parameters:
        contract_id: 合同 ID
        
    Request Body:
        {
            "reason": "终止原因",
            "terminate_date": "2024-06-01",  // 终止日期，默认为今天
            "settlement_amount": 5000  // 结算金额（可选）
        }
        
    Response:
        {
            "success": true,
            "message": "合同终止成功",
            "data": {...}
        }
    """
    try:
        contract = LandlordContract.query.get(contract_id)
        
        if not contract:
            return APIResponse.not_found("合同不存在")
        
        # 检查合同状态
        if contract.status != 'active':
            return APIResponse.bad_request("只有生效中的合同才能终止")
        
        # 获取请求数据
        data = request.get_json() or {}
        
        # 获取终止日期
        terminate_date_str = data.get('terminate_date')
        if terminate_date_str:
            try:
                terminate_date = datetime.strptime(terminate_date_str, '%Y-%m-%d').date()
            except (ValueError, TypeError):
                return APIResponse.bad_request("终止日期格式不正确")
        else:
            terminate_date = date.today()
        
        # 更新合同状态和备注
        contract.status = 'terminated'
        contract.remark = (contract.remark or '') + f"\n合同于{terminate_date}终止，原因：{data.get('reason', '无')}"
        
        db.session.commit()
        
        current_app.logger.info(f"用户 {g.username} 终止了承包合同 {contract.contract_no}")
        
        return APIResponse.success(contract.to_dict(), "承包合同终止成功")
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"终止承包合同失败：{str(e)}")
        return APIResponse.server_error("终止承包合同失败")


@landlord_contracts_bp.route('/<int:contract_id>/renew', methods=['POST'])
@login_required
@permission_required('edit')
def renew_landlord_contract(contract_id: int):
    """
    合同续签
    
    Path Parameters:
        contract_id: 合同 ID
        
    Request Body:
        {
            "end_date": "2026-01-01",  // 新的结束日期
            "contract_amount": 120000,  // 可选：新合同金额
            "service_fee_rate": 6.0,  // 可选：新服务费率
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
        contract = LandlordContract.query.get(contract_id)
        
        if not contract:
            return APIResponse.not_found("合同不存在")
        
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
        
        # 创建新合同
        new_contract = LandlordContract(
            contract_no=LandlordContract.generate_contract_no(),
            title=f"{contract.title} (续签)",
            landlord_id=contract.landlord_id,
            house_ids=contract.house_ids,
            start_date=contract.end_date,  # 从原合同结束日期开始
            end_date=new_end_date,
            contract_amount=data.get('contract_amount', contract.contract_amount),
            service_fee_rate=data.get('service_fee_rate', contract.service_fee_rate),
            minimum_fee=contract.minimum_fee,
            payment_cycle=contract.payment_cycle,
            description=contract.description,
            remark=data.get('remark', '合同续签')
        )
        
        # 标记原合同为已过期
        if contract.status == 'active':
            contract.status = 'expired'
        
        db.session.add(new_contract)
        db.session.commit()
        
        # 刷新获取完整数据
        db.session.refresh(new_contract)
        
        current_app.logger.info(f"用户 {g.username} 续签了承包合同 {contract.contract_no}")
        
        return APIResponse.success({
            'old_contract': contract.to_dict(),
            'new_contract': new_contract.to_dict()
        }, "承包合同续签成功")
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"合同续签失败：{str(e)}")
        return APIResponse.server_error("合同续签失败")


# ============================================================================
# 合同到期提醒接口
# ============================================================================

@landlord_contracts_bp.route('/expiring', methods=['GET'])
@login_required
def get_expiring_landlord_contracts():
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
        expiring_query = LandlordContract.query.filter(
            LandlordContract.status == 'active',
            LandlordContract.end_date >= today,
            LandlordContract.end_date <= threshold_date
        ).order_by(LandlordContract.end_date.asc())
        
        expiring_contracts = expiring_query.all()
        
        # 查询已过期合同
        expired_contracts = []
        if include_expired:
            expired_query = LandlordContract.query.filter(
                LandlordContract.status == 'active',
                LandlordContract.end_date < today
            ).order_by(LandlordContract.end_date.desc())
            expired_contracts = expired_query.all()
        
        # 格式化响应
        result = {
            'expiring_contracts': [contract.to_dict() for contract in expiring_contracts],
            'total_expiring': len(expiring_contracts)
        }
        
        if include_expired:
            result['expired_contracts'] = [contract.to_dict() for contract in expired_contracts]
            result['total_expired'] = len(expired_contracts)
        
        return APIResponse.success(result, "获取即将到期承包合同成功")
        
    except Exception as e:
        current_app.logger.error(f"获取即将到期承包合同失败：{str(e)}")
        return APIResponse.server_error("获取即将到期承包合同失败")


# ============================================================================
# 统计接口
# ============================================================================

@landlord_contracts_bp.route('/stats', methods=['GET'])
@login_required
def get_landlord_contract_stats():
    """
    获取承包合同统计信息
    
    Query Parameters:
        landlord_id: 房东 ID（可选，筛选特定房东的统计）
        
    Response:
        {
            "success": true,
            "data": {
                "total": 100,
                "by_status": {
                    "draft": 5,
                    "active": 60,
                    "expired": 20,
                    "terminated": 10
                },
                "expiring_soon": 10,
                "total_contract_amount": 5000000,
                "total_service_fee": 250000
            }
        }
    """
    try:
        # 构建查询
        query = LandlordContract.query
        
        # 房东筛选
        landlord_id = request.args.get('landlord_id', type=int)
        if landlord_id:
            query = query.filter(LandlordContract.landlord_id == landlord_id)
        
        # 统计总数
        total = query.count()
        
        # 按状态统计
        draft = query.filter(LandlordContract.status == 'draft').count()
        active = query.filter(LandlordContract.status == 'active').count()
        expired = query.filter(LandlordContract.status == 'expired').count()
        terminated = query.filter(LandlordContract.status == 'terminated').count()
        
        # 统计即将到期合同
        expiring_soon = query.filter(
            LandlordContract.status == 'active',
            LandlordContract.end_date >= date.today(),
            LandlordContract.end_date <= date.today() + timedelta(days=30)
        ).count()
        
        # 统计总合同金额和服务费
        active_contracts = query.filter(LandlordContract.status == 'active').all()
        total_contract_amount = sum(c.contract_amount for c in active_contracts)
        total_service_fee = sum(c.calculate_service_fee() for c in active_contracts)
        
        return APIResponse.success({
            'total': total,
            'by_status': {
                'draft': draft,
                'active': active,
                'expired': expired,
                'terminated': terminated
            },
            'expiring_soon': expiring_soon,
            'total_contract_amount': total_contract_amount,
            'total_service_fee': total_service_fee
        }, "获取承包合同统计信息成功")
        
    except Exception as e:
        current_app.logger.error(f"获取承包合同统计失败：{str(e)}")
        return APIResponse.server_error("获取承包合同统计失败")
