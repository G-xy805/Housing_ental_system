"""
租客管理路由模块
提供租客 CRUD、搜索、筛选、合同关联等功能
"""
from flask import Blueprint, request, jsonify, g, current_app
from typing import Optional, Dict, Any
from datetime import datetime

from app.models.tenant import Tenant
from app.models.contract import Contract
from app.models import db
from app.utils.decorators import login_required, admin_required, permission_required
from app.utils.responses import APIResponse, PaginationResponse

# 创建蓝图
tenants_bp = Blueprint('tenants', __name__, url_prefix='/api/tenants')


# ============================================================================
# 辅助函数
# ============================================================================

def validate_tenant_data(data: Dict, is_update: bool = False) -> tuple:
    """
    验证租客数据
    
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
        elif len(data.get('id_card', '')) not in [15, 18]:
            errors.append('身份证号格式不正确')
        else:
            validated_data['id_card'] = data['id_card'].strip()
    
    # 手机号（必填）
    if not is_update or 'phone' in data:
        if not data.get('phone'):
            errors.append('手机号不能为空')
        elif len(data.get('phone', '')) > 20:
            errors.append('手机号格式不正确')
        else:
            validated_data['phone'] = data['phone'].strip()
    
    # 邮箱
    if 'email' in data:
        email = data.get('email', '').strip()
        if email and '@' not in email:
            errors.append('邮箱格式不正确')
        else:
            validated_data['email'] = email
    
    # 紧急联系人
    if 'emergency_contact' in data:
        validated_data['emergency_contact'] = data.get('emergency_contact', '').strip()
    
    if 'emergency_phone' in data:
        validated_data['emergency_phone'] = data.get('emergency_phone', '').strip()
    
    if 'emergency_relation' in data:
        validated_data['emergency_relation'] = data.get('emergency_relation', '').strip()
    
    # 职业
    if 'occupation' in data:
        validated_data['occupation'] = data.get('occupation', '').strip()
    
    if 'company' in data:
        validated_data['company'] = data.get('company', '').strip()
    
    # 状态（仅在更新时允许）
    if is_update and 'status' in data:
        if data['status'] not in ['active', 'expired', 'blacklisted']:
            errors.append('状态必须是 active(在租)、expired(已退租) 或 blacklisted(黑名单)')
        else:
            validated_data['status'] = data['status']
    
    # 备注
    if 'remark' in data:
        validated_data['remark'] = data.get('remark', '').strip()
    
    if errors:
        return False, '; '.join(errors), None
    
    return True, None, validated_data


def format_tenant_response(tenant: Tenant, include_contracts: bool = False) -> Dict:
    """
    格式化租客响应数据
    
    Args:
        tenant: 租客对象
        include_contracts: 是否包含合同信息
        
    Returns:
        dict: 租客响应数据
    """
    data = tenant.to_dict()
    
    # 添加合同统计
    active_contracts = tenant.get_active_contracts()
    data['active_contracts_count'] = len(active_contracts)
    data['contracts_count'] = tenant.contracts.count()
    
    # 添加当前租住房源信息
    if include_contracts and active_contracts:
        data['current_houses'] = []
        for contract in active_contracts:
            if contract.house:
                house_info = {
                    'house_id': contract.house.id,
                    'house_title': contract.house.title,
                    'house_address': contract.house.address,
                    'contract_no': contract.contract_no,
                    'contract_end_date': contract.end_date.isoformat() if contract.end_date else None
                }
                data['current_houses'].append(house_info)
    
    return data


def check_id_card_duplicate(id_card: str, exclude_id: int = None) -> Optional[Tenant]:
    """
    检查身份证号是否已存在
    
    Args:
        id_card: 身份证号
        exclude_id: 排除的租客 ID（更新时使用）
        
    Returns:
        Tenant or None: 如果存在则返回租客对象
    """
    # 由于身份证号是加密存储的，我们需要检查所有租客的身份证号
    # 注意：这种方法在租客数量较多时可能会影响性能
    tenants = Tenant.query.all()
    for tenant in tenants:
        if tenant.get_id_card() == id_card:
            if exclude_id and tenant.id == exclude_id:
                continue
            return tenant
    return None


# ============================================================================
# 租客 CRUD 接口
# ============================================================================

@tenants_bp.route('', methods=['GET'])
@login_required
def get_tenants():
    """
    获取租客列表（支持分页、筛选、搜索）
    
    Query Parameters:
        page: 页码，默认 1
        per_page: 每页数量，默认 20，最大 100
        keyword: 关键词搜索（姓名、手机号、身份证号）
        name: 姓名搜索
        phone: 手机号搜索
        id_card: 身份证号搜索
        status: 状态筛选 (active/expired/blacklisted)
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
        query = Tenant.query
        
        # 关键词搜索（姓名、手机号、身份证号）
        keyword = request.args.get('keyword')
        if keyword:
            query = query.filter(
                db.or_(
                    Tenant.name.ilike(f'%{keyword}%'),
                    Tenant.phone.ilike(f'%{keyword}%'),
                    Tenant.id_card.ilike(f'%{keyword}%')
                )
            )
        
        # 姓名搜索
        name = request.args.get('name')
        if name:
            query = query.filter(Tenant.name.ilike(f'%{name}%'))
        
        # 手机号搜索
        phone = request.args.get('phone')
        if phone:
            query = query.filter(Tenant.phone.ilike(f'%{phone}%'))
        
        # 身份证号搜索
        id_card = request.args.get('id_card')
        if id_card:
            query = query.filter(Tenant.id_card.ilike(f'%{id_card}%'))
        
        # 状态筛选
        status = request.args.get('status')
        if status:
            if status not in ['active', 'expired', 'blacklisted']:
                return APIResponse.bad_request("状态必须是 active(在租)、expired(已退租) 或 blacklisted(黑名单)")
            query = query.filter(Tenant.status == status)
        
        # 排序
        order_by = request.args.get('order_by', 'created_at')
        order = request.args.get('order', 'desc')
        
        order_column = getattr(Tenant, order_by, Tenant.created_at)
        if order == 'asc':
            query = query.order_by(order_column.asc())
        else:
            query = query.order_by(order_column.desc())
        
        # 执行分页查询
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        # 格式化响应数据
        items = [format_tenant_response(tenant) for tenant in pagination.items]
        
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
        }, "获取租客列表成功")
        
    except Exception as e:
        current_app.logger.error(f"获取租客列表失败：{str(e)}")
        return APIResponse.server_error("获取租客列表失败")


@tenants_bp.route('/<int:tenant_id>', methods=['GET'])
@login_required
def get_tenant(tenant_id: int):
    """
    获取租客详情
    
    Path Parameters:
        tenant_id: 租客 ID
        
    Response:
        {
            "success": true,
            "data": {
                "id": 1,
                "name": "张三",
                "phone": "13800138000",
                "email": "zhangsan@example.com",
                "emergency_contact": "李四",
                "emergency_phone": "13900139000",
                "occupation": "工程师",
                "status": "active",
                "active_contracts_count": 1,
                "total_contracts_count": 2,
                "current_houses": [...]
            }
        }
    """
    try:
        tenant = Tenant.query.get(tenant_id)
        
        if not tenant:
            return APIResponse.not_found("租客不存在")
        
        # 格式化响应数据（包含合同信息）
        data = format_tenant_response(tenant, include_contracts=True)
        
        return APIResponse.success(data, "获取租客详情成功")
        
    except Exception as e:
        current_app.logger.error(f"获取租客详情失败：{str(e)}")
        return APIResponse.server_error("获取租客详情失败")


@tenants_bp.route('', methods=['POST'])
@login_required
@permission_required('create')
def create_tenant():
    """
    创建租客
    
    Request Body:
        {
            "name": "张三",
            "id_card": "110101199001011234",
            "phone": "13800138000",
            "email": "zhangsan@example.com",
            "emergency_contact": "李四",
            "emergency_phone": "13900139000",
            "emergency_relation": "配偶",
            "occupation": "工程师",
            "company": "某某科技公司",
            "remark": "备注信息"
        }
        
    Response:
        {
            "success": true,
            "message": "租客创建成功",
            "data": {...}
        }
    """
    try:
        # 获取请求数据
        data = request.get_json()
        
        if not data:
            return APIResponse.bad_request("请求数据不能为空")
        
        # 验证数据
        is_valid, error_msg, validated_data = validate_tenant_data(data, is_update=False)
        
        if not is_valid:
            return APIResponse.validation_error(error_msg)
        
        # 检查身份证号是否重复
        existing_tenant = check_id_card_duplicate(validated_data['id_card'])
        if existing_tenant:
            return APIResponse.bad_request("该身份证号已登记在其他租客名下")
        
        # 创建租客（排除 id_card 字段，因为模型中没有这个字段）
        tenant_data = {k: v for k, v in validated_data.items() if k != 'id_card'}
        tenant = Tenant(**tenant_data)
        
        # 设置身份证号（会自动加密存储）
        if 'id_card' in validated_data:
            tenant.set_id_card(validated_data['id_card'])
        
        db.session.add(tenant)
        db.session.commit()
        
        # 刷新获取完整数据
        db.session.refresh(tenant)
        
        # 格式化响应
        result = format_tenant_response(tenant)
        
        current_app.logger.info(f"用户 {g.username} 创建了租客 {tenant.id}: {tenant.name}")
        
        return APIResponse.success(result, "租客创建成功", 201)
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"创建租客失败：{str(e)}")
        return APIResponse.server_error("创建租客失败")


@tenants_bp.route('/<int:tenant_id>', methods=['PUT'])
@login_required
@permission_required('edit')
def update_tenant(tenant_id: int):
    """
    更新租客信息
    
    Path Parameters:
        tenant_id: 租客 ID
        
    Request Body:
        {
            "name": "新的姓名",
            "phone": "新的手机号",
            "email": "新的邮箱",
            "occupation": "新的职业",
            ...
        }
        
    Response:
        {
            "success": true,
            "message": "租客信息更新成功",
            "data": {...}
        }
    """
    try:
        tenant = Tenant.query.get(tenant_id)
        
        if not tenant:
            return APIResponse.not_found("租客不存在")
        
        # 获取请求数据
        data = request.get_json()
        
        if not data:
            return APIResponse.bad_request("请求数据不能为空")
        
        # 验证数据
        is_valid, error_msg, validated_data = validate_tenant_data(data, is_update=True)
        
        if not is_valid:
            return APIResponse.validation_error(error_msg)
        
        # 检查身份证号是否重复（排除自己）
        if 'id_card' in validated_data:
            existing_tenant = check_id_card_duplicate(validated_data['id_card'], exclude_id=tenant_id)
            if existing_tenant:
                return APIResponse.bad_request("该身份证号已登记在其他租客名下")
            
            # 更新身份证号
            tenant.set_id_card(validated_data['id_card'])
        
        # 更新租客信息
        for key, value in validated_data.items():
            if key != 'id_card':  # 身份证号已通过 set_id_card 处理
                setattr(tenant, key, value)
        
        db.session.commit()
        
        # 刷新获取完整数据
        db.session.refresh(tenant)
        
        # 格式化响应
        result = format_tenant_response(tenant)
        
        current_app.logger.info(f"用户 {g.username} 更新了租客 {tenant_id}: {tenant.name}")
        
        return APIResponse.success(result, "租客信息更新成功")
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"更新租客信息失败：{str(e)}")
        return APIResponse.server_error("更新租客信息失败")


@tenants_bp.route('/<int:tenant_id>', methods=['DELETE'])
@admin_required
def delete_tenant(tenant_id: int):
    """
    删除租客（仅管理员）
    
    Path Parameters:
        tenant_id: 租客 ID
        
    Response:
        {
            "success": true,
            "message": "租客删除成功"
        }
    """
    try:
        tenant = Tenant.query.get(tenant_id)
        
        if not tenant:
            return APIResponse.not_found("租客不存在")
        
        # 检查是否有活跃合同
        active_contracts = tenant.get_active_contracts()
        if active_contracts:
            return APIResponse.bad_request(
                f"租客有 {len(active_contracts)} 个活跃合同，无法删除",
                {"active_contracts": len(active_contracts)}
            )
        
        tenant_name = tenant.name
        tenant_id_card = tenant.id_card
        
        # 删除租客
        db.session.delete(tenant)
        db.session.commit()
        
        current_app.logger.info(f"管理员 {g.username} 删除了租客 {tenant_id}: {tenant_name}")
        
        return APIResponse.success(None, "租客删除成功")
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"删除租客失败：{str(e)}")
        return APIResponse.server_error("删除租客失败")


# ============================================================================
# 租客合同关联接口
# ============================================================================

@tenants_bp.route('/<int:tenant_id>/contracts', methods=['GET'])
@login_required
def get_tenant_contracts(tenant_id: int):
    """
    获取租客合同列表
    
    Path Parameters:
        tenant_id: 租客 ID
        
    Query Parameters:
        status: 合同状态筛选 (active/expired/terminated/renewed)
        include_expired: 是否包含已过期合同，默认 true
        
    Response:
        {
            "success": true,
            "data": {
                "tenant_id": 1,
                "tenant_name": "张三",
                "contracts": [...]
            }
        }
    """
    try:
        tenant = Tenant.query.get(tenant_id)
        
        if not tenant:
            return APIResponse.not_found("租客不存在")
        
        # 构建查询
        query = Contract.query.filter_by(tenant_id=tenant_id)
        
        # 状态筛选
        status = request.args.get('status')
        if status:
            if status not in ['active', 'expired', 'terminated', 'renewed', 'draft']:
                return APIResponse.bad_request("状态必须是 active、expired、terminated、renewed 或 draft")
            query = query.filter(Contract.status == status)
        
        # 是否包含已过期合同
        include_expired = request.args.get('include_expired', 'true').lower() == 'true'
        if not include_expired:
            from datetime import date
            query = query.filter(Contract.end_date >= date.today())
        
        # 排序
        query = query.order_by(Contract.created_at.desc())
        
        # 获取所有合同
        contracts = query.all()
        
        # 格式化响应
        contract_list = []
        for contract in contracts:
            contract_data = contract.to_dict()
            contract_list.append(contract_data)
        
        return APIResponse.success({
            'tenant_id': tenant_id,
            'tenant_name': tenant.name,
            'contracts': contract_list
        }, "获取租客合同列表成功")
        
    except Exception as e:
        current_app.logger.error(f"获取租客合同列表失败：{str(e)}")
        return APIResponse.server_error("获取租客合同列表失败")


# ============================================================================
# 统计接口
# ============================================================================

@tenants_bp.route('/stats', methods=['GET'])
@login_required
def get_tenant_stats():
    """
    获取租客统计信息
    
    Response:
        {
            "success": true,
            "data": {
                "total": 100,
                "by_status": {
                    "active": 60,
                    "expired": 30,
                    "blacklisted": 10
                },
                "with_active_contracts": 50
            }
        }
    """
    try:
        # 统计总数
        total = Tenant.query.count()
        
        # 按状态统计
        active = Tenant.query.filter(Tenant.status == 'active').count()
        expired = Tenant.query.filter(Tenant.status == 'expired').count()
        blacklisted = Tenant.query.filter(Tenant.status == 'blacklisted').count()
        
        # 统计有活跃合同的租客数
        from datetime import date
        tenants_with_contracts = db.session.query(Tenant.id).join(
            Contract, Tenant.id == Contract.tenant_id
        ).filter(
            Contract.status.in_(['active', 'draft']),
            Contract.end_date >= date.today()
        ).distinct().count()
        
        return APIResponse.success({
            'total': total,
            'by_status': {
                'active': active,
                'expired': expired,
                'blacklisted': blacklisted
            },
            'with_active_contracts': tenants_with_contracts
        }, "获取租客统计信息成功")
        
    except Exception as e:
        current_app.logger.error(f"获取租客统计失败：{str(e)}")
        return APIResponse.server_error("获取租客统计失败")


# ============================================================================
# 租客搜索接口（高级搜索）
# ============================================================================

@tenants_bp.route('/search', methods=['GET'])
@login_required
def search_tenants():
    """
    高级搜索租客
    
    Query Parameters:
        name: 姓名
        phone: 手机号
        id_card: 身份证号
        house_address: 房源地址
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
        
        query = Tenant.query
        
        # 姓名搜索
        name = request.args.get('name')
        if name:
            query = query.filter(Tenant.name.ilike(f'%{name}%'))
        
        # 手机号搜索
        phone = request.args.get('phone')
        if phone:
            query = query.filter(Tenant.phone.ilike(f'%{phone}%'))
        
        # 身份证号搜索
        id_card = request.args.get('id_card')
        if id_card:
            query = query.filter(Tenant.id_card.ilike(f'%{id_card}%'))
        
        # 状态筛选
        status = request.args.get('status')
        if status and status in ['active', 'expired', 'blacklisted']:
            query = query.filter(Tenant.status == status)
        
        # 房源地址搜索（通过合同关联）
        house_address = request.args.get('house_address')
        if house_address:
            query = query.join(Contract, Tenant.id == Contract.tenant_id).join(
                House, Contract.house_id == House.id
            ).filter(House.address.ilike(f'%{house_address}%'))
        
        # 排序
        query = query.order_by(Tenant.created_at.desc())
        
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        items = [format_tenant_response(tenant) for tenant in pagination.items]
        
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
        }, "搜索租客成功")
        
    except Exception as e:
        current_app.logger.error(f"搜索租客失败：{str(e)}")
        return APIResponse.server_error("搜索租客失败")
