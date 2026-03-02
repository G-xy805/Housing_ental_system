"""
房东管理路由模块
提供房东 CRUD、搜索、筛选、房源关联、合同关联等功能
"""
from flask import Blueprint, request, jsonify, g, current_app
from typing import Optional, Dict, Any
from datetime import datetime
import re

from app.models.landlord import Landlord
from app.models.house import House
from app.models.landlord_contract import LandlordContract
from app.models import db
from app.utils.decorators import login_required, admin_required, permission_required, landlord_access_log
from app.utils.responses import APIResponse, PaginationResponse
from app.utils.encryption import encrypt_sensitive_data

# 创建蓝图
landlords_bp = Blueprint('landlords', __name__, url_prefix='/api/landlords')


# ============================================================================
# 辅助函数
# ============================================================================

def validate_id_card(id_card: str) -> tuple:
    """
    验证身份证号格式
    
    Args:
        id_card: 身份证号
        
    Returns:
        tuple: (是否有效，错误消息)
    """
    if not id_card:
        return False, '身份证号不能为空'
    
    id_card = id_card.strip()
    
    # 18 位身份证号验证
    if len(id_card) != 18:
        return False, '身份证号必须是 18 位'
    
    # 前 17 位必须是数字
    if not id_card[:17].isdigit():
        return False, '身份证号前 17 位必须是数字'
    
    # 第 18 位可以是数字或 X/x
    if not (id_card[17].isdigit() or id_card[17].upper() == 'X'):
        return False, '身份证号最后一位必须是数字或 X'
    
    # 校验码验证（简化版，仅验证格式）
    # 完整的校验码验证需要按照 GB 11643-1989 标准计算
    return True, None


def validate_phone(phone: str) -> tuple:
    """
    验证手机号格式
    
    Args:
        phone: 手机号
        
    Returns:
        tuple: (是否有效，错误消息)
    """
    if not phone:
        return False, '手机号不能为空'
    
    phone = phone.strip()
    
    # 中国大陆手机号验证：11 位数字，以 1 开头，第二位是 3-9 之间的数字
    phone_pattern = r'^1[3-9]\d{9}$'
    if not re.match(phone_pattern, phone):
        return False, '手机号格式不正确，应为 11 位中国大陆手机号'
    
    return True, None


def validate_landlord_data(data: Dict, is_update: bool = False) -> tuple:
    """
    验证房东数据
    
    Args:
        data: 请求数据
        is_update: 是否为更新操作
        
    Returns:
        tuple: (是否有效，错误消息，验证后的数据)
    """
    errors = []
    validated_data = {}
    
    # 姓名（必填）
    if not is_update or 'name' in data:
        if not data.get('name'):
            errors.append('姓名不能为空')
        elif len(data.get('name', '')) > 50:
            errors.append('姓名不能超过 50 个字符')
        else:
            validated_data['name'] = data['name'].strip()
    
    # 身份证号（必填）
    if not is_update or 'id_card' in data:
        if not data.get('id_card'):
            errors.append('身份证号不能为空')
        else:
            id_card = data['id_card'].strip()
            is_valid, error_msg = validate_id_card(id_card)
            if not is_valid:
                errors.append(error_msg)
            else:
                validated_data['id_card'] = id_card
    
    # 手机号（必填）
    if not is_update or 'phone' in data:
        if not data.get('phone'):
            errors.append('手机号不能为空')
        else:
            phone = data['phone'].strip()
            is_valid, error_msg = validate_phone(phone)
            if not is_valid:
                errors.append(error_msg)
            else:
                validated_data['phone'] = phone
    
    # 银行卡信息（可选）
    if 'bank_card' in data:
        bank_card = data.get('bank_card', '').strip()
        if bank_card and not bank_card.isdigit():
            errors.append('银行卡号必须是数字')
        elif bank_card:
            validated_data['bank_card'] = bank_card
        else:
            validated_data['bank_card'] = None
    
    if 'bank_name' in data:
        bank_name = data.get('bank_name', '').strip()
        if bank_name and len(bank_name) > 100:
            errors.append('开户行名称不能超过 100 个字符')
        else:
            validated_data['bank_name'] = bank_name if bank_name else None
    
    # 房产信息（可选）
    if 'property_cert_no' in data:
        property_cert_no = data.get('property_cert_no', '').strip()
        if property_cert_no and len(property_cert_no) > 50:
            errors.append('房产证编号不能超过 50 个字符')
        else:
            validated_data['property_cert_no'] = property_cert_no if property_cert_no else None
    
    if 'address' in data:
        address = data.get('address', '').strip()
        if address and len(address) > 255:
            errors.append('房产地址不能超过 255 个字符')
        else:
            validated_data['address'] = address if address else None
    
    # 状态（仅在更新时允许）
    if is_update and 'status' in data:
        if data['status'] not in ['active', 'inactive', 'blacklisted']:
            errors.append('状态必须是 active(正常)、inactive(停用) 或 blacklisted(黑名单)')
        else:
            validated_data['status'] = data['status']
    
    # 备注（可选）
    if 'remark' in data:
        validated_data['remark'] = data.get('remark', '').strip()
    
    if errors:
        return False, '; '.join(errors), None
    
    return True, None, validated_data


def format_landlord_response(landlord: Landlord, include_details: bool = False) -> Dict:
    """
    格式化房东响应数据
    
    Args:
        landlord: 房东对象
        include_details: 是否包含详细信息（敏感字段）
        
    Returns:
        dict: 房东响应数据
    """
    data = landlord.to_dict(include_details=include_details)
    
    # 添加统计信息
    data['houses_count'] = landlord.houses.count()
    data['contracts_count'] = len(landlord.contracts) if hasattr(landlord, 'contracts') else 0
    
    # 添加负责员工信息
    if landlord.houses.count() > 0:
        first_house = landlord.houses.first()
        if first_house and first_house.owner:
            data['owner_name'] = first_house.owner.username
    
    return data


def check_id_card_duplicate(id_card: str, exclude_id: int = None) -> Optional[Landlord]:
    """
    检查身份证号是否已存在（使用加密存储）
    
    Args:
        id_card: 身份证号
        exclude_id: 排除的房东 ID（更新时使用）
        
    Returns:
        Landlord or None: 如果存在则返回房东对象
    """
    # 直接使用加密后的值查询
    encrypted_id_card = encrypt_sensitive_data(id_card)
    if not encrypted_id_card:
        return None
    
    query = Landlord.query.filter(Landlord.id_card_encrypted == encrypted_id_card)
    
    if exclude_id:
        query = query.filter(Landlord.id != exclude_id)
    
    return query.first()


# ============================================================================
# 房东 CRUD 接口
# ============================================================================

@landlords_bp.route('', methods=['GET'])
@login_required
@landlord_access_log
def get_landlords():
    """
    获取房东列表（支持分页、筛选、搜索）
    
    Query Parameters:
        page: 页码，默认 1
        per_page: 每页数量，默认 20，最大 100
        keyword: 关键词搜索（姓名、手机号、身份证号）
        name: 姓名搜索
        phone: 手机号搜索
        id_card: 身份证号搜索
        status: 状态筛选 (active/inactive/blacklisted)
        order_by: 排序字段 (created_at/updated_at/name)
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
        query = Landlord.query
        
        # 关键词搜索（姓名、手机号、身份证号）
        keyword = request.args.get('keyword')
        if keyword:
            query = query.filter(
                db.or_(
                    Landlord.name.ilike(f'%{keyword}%'),
                    Landlord.phone.ilike(f'%{keyword}%'),
                    Landlord.id_card.ilike(f'%{keyword}%')
                )
            )
        
        # 姓名搜索
        name = request.args.get('name')
        if name:
            query = query.filter(Landlord.name.ilike(f'%{name}%'))
        
        # 手机号搜索
        phone = request.args.get('phone')
        if phone:
            query = query.filter(Landlord.phone.ilike(f'%{phone}%'))
        
        # 身份证号搜索
        id_card = request.args.get('id_card')
        if id_card:
            query = query.filter(Landlord.id_card.ilike(f'%{id_card}%'))
        
        # 状态筛选
        status = request.args.get('status')
        if status:
            if status not in ['active', 'inactive', 'blacklisted']:
                return APIResponse.bad_request("状态必须是 active(正常)、inactive(停用) 或 blacklisted(黑名单)")
            query = query.filter(Landlord.status == status)
        
        # 排序
        order_by = request.args.get('order_by', 'created_at')
        order = request.args.get('order', 'desc')
        
        order_column = getattr(Landlord, order_by, Landlord.created_at)
        if order == 'asc':
            query = query.order_by(order_column.asc())
        else:
            query = query.order_by(order_column.desc())
        
        # 执行分页查询
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        # 格式化响应数据
        items = [format_landlord_response(landlord) for landlord in pagination.items]
        
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
        }, "获取房东列表成功")
        
    except Exception as e:
        current_app.logger.error(f"获取房东列表失败：{str(e)}")
        return APIResponse.server_error("获取房东列表失败")


@landlords_bp.route('/<int:landlord_id>', methods=['GET'])
@login_required
@landlord_access_log
def get_landlord(landlord_id: int):
    """
    获取房东详情（仅内部员工访问）
    
    Path Parameters:
        landlord_id: 房东 ID
        
    Response:
        {
            "success": true,
            "data": {
                "id": 1,
                "name": "张三",
                "phone": "13800138000",
                "bank_card": "6222001234567890123",
                "bank_name": "中国工商银行北京分行",
                "property_cert_no": "京房权证朝私字第 123456 号",
                "address": "北京市朝阳区某某小区 3 号楼",
                "status": "active",
                "houses_count": 5,
                "contracts_count": 2,
                "owner_name": "管理员"
            }
        }
    """
    try:
        landlord = Landlord.query.get(landlord_id)
        
        if not landlord:
            return APIResponse.not_found("房东不存在")
        
        # 格式化响应数据（包含详细信息）
        data = format_landlord_response(landlord, include_details=True)
        
        return APIResponse.success(data, "获取房东详情成功")
        
    except Exception as e:
        current_app.logger.error(f"获取房东详情失败：{str(e)}")
        return APIResponse.server_error("获取房东详情失败")


@landlords_bp.route('', methods=['POST'])
@login_required
@permission_required('create')
@landlord_access_log
def create_landlord():
    """
    创建房东（验证身份证号唯一性）
    
    Request Body:
        {
            "name": "张三",
            "id_card": "110101199001011234",
            "phone": "13800138000",
            "bank_card": "6222001234567890123",
            "bank_name": "中国工商银行北京分行",
            "property_cert_no": "京房权证朝私字第 123456 号",
            "address": "北京市朝阳区某某小区 3 号楼",
            "remark": "备注信息"
        }
        
    Response:
        {
            "success": true,
            "message": "房东创建成功",
            "data": {...}
        }
    """
    try:
        # 获取请求数据
        data = request.get_json()
        
        if not data:
            return APIResponse.bad_request("请求数据不能为空")
        
        # 验证数据
        is_valid, error_msg, validated_data = validate_landlord_data(data, is_update=False)
        
        if not is_valid:
            return APIResponse.validation_error(error_msg)
        
        # 检查身份证号是否重复
        existing_landlord = check_id_card_duplicate(validated_data['id_card'])
        if existing_landlord:
            return APIResponse.bad_request("该身份证号已登记在其他房东名下")
        
        # 创建房东（排除需要加密的字段）
        landlord_data = {k: v for k, v in validated_data.items() if k not in ['id_card', 'bank_card']}
        landlord = Landlord(**landlord_data)
        
        # 设置身份证号（会自动加密存储）
        if 'id_card' in validated_data:
            landlord.set_id_card(validated_data['id_card'])
        
        # 设置银行卡号（会自动加密存储）
        if 'bank_card' in validated_data and validated_data['bank_card']:
            landlord.set_bank_card(validated_data['bank_card'])
        
        db.session.add(landlord)
        db.session.commit()
        
        # 刷新获取完整数据
        db.session.refresh(landlord)
        
        # 格式化响应
        result = format_landlord_response(landlord, include_details=True)
        
        current_app.logger.info(f"用户 {g.username} 创建了房东 {landlord.id}: {landlord.name}")
        
        return APIResponse.success(result, "房东创建成功", 201)
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"创建房东失败：{str(e)}")
        return APIResponse.server_error("创建房东失败")


@landlords_bp.route('/<int:landlord_id>', methods=['PUT'])
@login_required
@permission_required('edit')
@landlord_access_log
def update_landlord(landlord_id: int):
    """
    更新房东信息
    
    Path Parameters:
        landlord_id: 房东 ID
        
    Request Body:
        {
            "name": "新的姓名",
            "phone": "新的手机号",
            "bank_card": "新的银行卡号",
            "bank_name": "新的开户行",
            "status": "active",
            ...
        }
        
    Response:
        {
            "success": true,
            "message": "房东信息更新成功",
            "data": {...}
        }
    """
    try:
        landlord = Landlord.query.get(landlord_id)
        
        if not landlord:
            return APIResponse.not_found("房东不存在")
        
        # 获取请求数据
        data = request.get_json()
        
        if not data:
            return APIResponse.bad_request("请求数据不能为空")
        
        # 验证数据
        is_valid, error_msg, validated_data = validate_landlord_data(data, is_update=True)
        
        if not is_valid:
            return APIResponse.validation_error(error_msg)
        
        # 检查身份证号是否重复（排除自己）
        if 'id_card' in validated_data:
            existing_landlord = check_id_card_duplicate(validated_data['id_card'], exclude_id=landlord_id)
            if existing_landlord:
                return APIResponse.bad_request("该身份证号已登记在其他房东名下")
            
            # 更新身份证号（自动加密）
            landlord.set_id_card(validated_data['id_card'])
        
        # 更新银行卡号（自动加密）
        if 'bank_card' in validated_data and validated_data['bank_card']:
            landlord.set_bank_card(validated_data['bank_card'])
        
        # 更新房东信息（排除需要加密的字段）
        for key, value in validated_data.items():
            if key not in ['id_card', 'bank_card']:  # 已通过加密方法处理
                setattr(landlord, key, value)
        
        db.session.commit()
        
        # 刷新获取完整数据
        db.session.refresh(landlord)
        
        # 格式化响应
        result = format_landlord_response(landlord, include_details=True)
        
        current_app.logger.info(f"用户 {g.username} 更新了房东 {landlord_id}: {landlord.name}")
        
        return APIResponse.success(result, "房东信息更新成功")
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"更新房东信息失败：{str(e)}")
        return APIResponse.server_error("更新房东信息失败")


@landlords_bp.route('/<int:landlord_id>', methods=['DELETE'])
@admin_required
@landlord_access_log
def delete_landlord(landlord_id: int):
    """
    删除房东（仅管理员）
    检查关联的房源和合同，有则不能删除
    
    Path Parameters:
        landlord_id: 房东 ID
        
    Response:
        {
            "success": true,
            "message": "房东删除成功"
        }
    """
    try:
        landlord = Landlord.query.get(landlord_id)
        
        if not landlord:
            return APIResponse.not_found("房东不存在")
        
        # 检查是否有房源
        houses_count = landlord.houses.count()
        if houses_count > 0:
            return APIResponse.bad_request(
                f"房东名下有 {houses_count} 个房源，无法删除",
                {"houses_count": houses_count}
            )
        
        # 检查是否有合同
        contracts_count = len(landlord.contracts) if hasattr(landlord, 'contracts') else 0
        if contracts_count > 0:
            return APIResponse.bad_request(
                f"房东有 {contracts_count} 个承包合同，无法删除",
                {"contracts_count": contracts_count}
            )
        
        landlord_name = landlord.name
        landlord_id_card = landlord.get_id_card() if hasattr(landlord, 'get_id_card') else None
        
        # 删除房东
        db.session.delete(landlord)
        db.session.commit()
        
        current_app.logger.info(f"管理员 {g.username} 删除了房东 {landlord_id}: {landlord_name}")
        
        return APIResponse.success(None, "房东删除成功")
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"删除房东失败：{str(e)}")
        return APIResponse.server_error("删除房东失败")


# ============================================================================
# 房东关联查询接口
# ============================================================================

@landlords_bp.route('/<int:landlord_id>/houses', methods=['GET'])
@login_required
@landlord_access_log
def get_landlord_houses(landlord_id: int):
    """
    获取房东名下所有房源
    
    Path Parameters:
        landlord_id: 房东 ID
        
    Query Parameters:
        status: 房源状态筛选 (available/rented/maintenance/partially_rented)
        rental_type: 租赁类型筛选 (whole/shared)
        page: 页码，默认 1
        per_page: 每页数量，默认 20，最大 100
        
    Response:
        {
            "success": true,
            "data": {
                "landlord_id": 1,
                "landlord_name": "张三",
                "houses": [...],
                "pagination": {...}
            }
        }
    """
    try:
        landlord = Landlord.query.get(landlord_id)
        
        if not landlord:
            return APIResponse.not_found("房东不存在")
        
        # 获取查询参数
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        
        # 构建查询
        query = House.query.filter(House.landlord_id == landlord_id)
        
        # 状态筛选
        status = request.args.get('status')
        if status:
            if status not in ['available', 'rented', 'maintenance', 'partially_rented']:
                return APIResponse.bad_request("状态必须是 available、rented、maintenance 或 partially_rented")
            query = query.filter(House.status == status)
        
        # 租赁类型筛选
        rental_type = request.args.get('rental_type')
        if rental_type:
            if rental_type not in ['whole', 'shared']:
                return APIResponse.bad_request("租赁类型必须是 whole(整租) 或 shared(合租)")
            query = query.filter(House.rental_type == rental_type)
        
        # 排序
        query = query.order_by(House.created_at.desc())
        
        # 执行分页查询
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        # 格式化响应数据
        houses_list = []
        for house in pagination.items:
            house_data = house.to_dict(include_landlord=False)
            houses_list.append(house_data)
        
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
            'landlord_id': landlord_id,
            'landlord_name': landlord.name,
            'houses': houses_list,
            'pagination': pagination_info
        }, "获取房东房源列表成功")
        
    except Exception as e:
        current_app.logger.error(f"获取房东房源列表失败：{str(e)}")
        return APIResponse.server_error("获取房东房源列表失败")


@landlords_bp.route('/<int:landlord_id>/contracts', methods=['GET'])
@login_required
@landlord_access_log
def get_landlord_contracts(landlord_id: int):
    """
    获取房东的所有承包合同
    
    Path Parameters:
        landlord_id: 房东 ID
        
    Query Parameters:
        status: 合同状态筛选 (draft/active/expired/terminated)
        include_expired: 是否包含已过期合同，默认 true
        
    Response:
        {
            "success": true,
            "data": {
                "landlord_id": 1,
                "landlord_name": "张三",
                "contracts": [...],
                "pagination": {...}
            }
        }
    """
    try:
        landlord = Landlord.query.get(landlord_id)
        
        if not landlord:
            return APIResponse.not_found("房东不存在")
        
        # 获取查询参数
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        
        # 构建查询
        query = LandlordContract.query.filter(LandlordContract.landlord_id == landlord_id)
        
        # 状态筛选
        status = request.args.get('status')
        if status:
            if status not in ['draft', 'active', 'expired', 'terminated']:
                return APIResponse.bad_request("状态必须是 draft、active、expired 或 terminated")
            query = query.filter(LandlordContract.status == status)
        
        # 是否包含已过期合同
        include_expired = request.args.get('include_expired', 'true').lower() == 'true'
        if not include_expired:
            from datetime import date
            query = query.filter(LandlordContract.end_date >= date.today())
        
        # 排序
        query = query.order_by(LandlordContract.created_at.desc())
        
        # 执行分页查询
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        # 格式化响应数据
        contracts_list = []
        for contract in pagination.items:
            contract_data = contract.to_dict()
            contracts_list.append(contract_data)
        
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
            'landlord_id': landlord_id,
            'landlord_name': landlord.name,
            'contracts': contracts_list,
            'pagination': pagination_info
        }, "获取房东合同列表成功")
        
    except Exception as e:
        current_app.logger.error(f"获取房东合同列表失败：{str(e)}")
        return APIResponse.server_error("获取房东合同列表失败")


# ============================================================================
# 统计接口
# ============================================================================

@landlords_bp.route('/stats', methods=['GET'])
@login_required
@landlord_access_log
def get_landlord_stats():
    """
    获取房东统计信息
    
    Response:
        {
            "success": true,
            "data": {
                "total": 100,
                "by_status": {
                    "active": 80,
                    "inactive": 15,
                    "blacklisted": 5
                },
                "with_houses": 60,
                "with_contracts": 50
            }
        }
    """
    try:
        # 统计总数
        total = Landlord.query.count()
        
        # 按状态统计
        active = Landlord.query.filter(Landlord.status == 'active').count()
        inactive = Landlord.query.filter(Landlord.status == 'inactive').count()
        blacklisted = Landlord.query.filter(Landlord.status == 'blacklisted').count()
        
        # 统计有房源的房东数
        landlords_with_houses = db.session.query(Landlord.id).join(
            House, Landlord.id == House.landlord_id
        ).distinct().count()
        
        # 统计有合同的房东数
        landlords_with_contracts = db.session.query(Landlord.id).join(
            LandlordContract, Landlord.id == LandlordContract.landlord_id
        ).distinct().count()
        
        return APIResponse.success({
            'total': total,
            'by_status': {
                'active': active,
                'inactive': inactive,
                'blacklisted': blacklisted
            },
            'with_houses': landlords_with_houses,
            'with_contracts': landlords_with_contracts
        }, "获取房东统计信息成功")
        
    except Exception as e:
        current_app.logger.error(f"获取房东统计失败：{str(e)}")
        return APIResponse.server_error("获取房东统计失败")


# ============================================================================
# 房东搜索接口（高级搜索）
# ============================================================================

@landlords_bp.route('/search', methods=['GET'])
@login_required
@landlord_access_log
def search_landlords():
    """
    高级搜索房东
    
    Query Parameters:
        name: 姓名
        phone: 手机号
        id_card: 身份证号
        city: 城市（通过房源地址）
        status: 状态
        page: 页码
        per_page: 每页数量
        
    Response:
        {
            "success": true,
            "data": {
                "items": [...],
                "pagination": {...}
            }
        }
    """
    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        
        query = Landlord.query
        
        # 姓名搜索
        name = request.args.get('name')
        if name:
            query = query.filter(Landlord.name.ilike(f'%{name}%'))
        
        # 手机号搜索
        phone = request.args.get('phone')
        if phone:
            query = query.filter(Landlord.phone.ilike(f'%{phone}%'))
        
        # 身份证号搜索
        id_card = request.args.get('id_card')
        if id_card:
            query = query.filter(Landlord.id_card.ilike(f'%{id_card}%'))
        
        # 状态筛选
        status = request.args.get('status')
        if status and status in ['active', 'inactive', 'blacklisted']:
            query = query.filter(Landlord.status == status)
        
        # 城市搜索（通过房源关联）
        city = request.args.get('city')
        if city:
            query = query.join(House, Landlord.id == House.landlord_id).filter(
                House.city.ilike(f'%{city}%')
            )
        
        # 排序
        query = query.order_by(Landlord.created_at.desc())
        
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        items = [format_landlord_response(landlord) for landlord in pagination.items]
        
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
        }, "搜索房东成功")
        
    except Exception as e:
        current_app.logger.error(f"搜索房东失败：{str(e)}")
        return APIResponse.server_error("搜索房东失败")
