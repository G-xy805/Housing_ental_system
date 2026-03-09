"""
房源管理路由模块
提供房源 CRUD、房间管理、房源状态管理等功能
"""
from flask import Blueprint, request, jsonify, g, current_app
from typing import Optional, Dict, Any
from datetime import datetime
import re

from app.models.house import House
from app.models.room import Room
from app.models.user import User
from app.models.media import Media
from app.models import db
from app.utils.decorators import login_required, admin_required, permission_required
from app.utils.responses import APIResponse, PaginationResponse
from app.utils.redis_cache import (
    get_cache_manager, 
    invalidate_cache_pattern, 
    CacheEventEmitter,
    generate_cache_key
)
from app.utils.query_optimizer import (
    optimize_house_query,
    optimize_house_detail_query
)
from app.utils.json_validator import (
    validate_facilities,
    validate_facilities_detailed,
    sanitize_facilities,
    ValidationResult
)

# 创建蓝图
houses_bp = Blueprint('houses', __name__, url_prefix='/api/houses')


# ============================================================================
# 辅助函数
# ============================================================================

def validate_house_data(data: Dict, is_update: bool = False) -> tuple:
    """
    验证房源数据
    
    Args:
        data: 请求数据
        is_update: 是否为更新操作
        
    Returns:
        tuple: (是否有效，错误消息，验证后的数据)
    """
    errors = []
    validated_data = {}
    
    # 必填字段验证
    if not is_update or 'title' in data:
        if not data.get('title'):
            errors.append('房源标题不能为空')
        elif len(data.get('title', '')) > 100:
            errors.append('房源标题不能超过 100 个字符')
        else:
            validated_data['title'] = data['title'].strip()
    
    if 'description' in data:
        validated_data['description'] = data.get('description', '').strip()
    
    # 地址信息
    if not is_update or 'city' in data:
        if not data.get('city'):
            errors.append('城市不能为空')
        else:
            validated_data['city'] = data['city'].strip()
    
    if 'district' in data:
        validated_data['district'] = data.get('district', '').strip()
    
    if 'province' in data:
        validated_data['province'] = data.get('province', '').strip()
    
    if 'address' in data:
        validated_data['address'] = data.get('address', '').strip()
    
    # 坐标
    if 'latitude' in data:
        try:
            validated_data['latitude'] = float(data['latitude']) if data['latitude'] else None
        except (ValueError, TypeError):
            errors.append('纬度必须是有效的数字')
    
    if 'longitude' in data:
        try:
            validated_data['longitude'] = float(data['longitude']) if data['longitude'] else None
        except (ValueError, TypeError):
            errors.append('经度必须是有效的数字')
    
    # 房源属性
    if 'area' in data:
        try:
            area = float(data['area']) if data['area'] else None
            if area and area <= 0:
                errors.append('面积必须大于 0')
            validated_data['area'] = area
        except (ValueError, TypeError):
            errors.append('面积必须是有效的数字')
    
    if 'room_count' in data:
        try:
            room_count = int(data['room_count']) if data['room_count'] else None
            if room_count and room_count <= 0:
                errors.append('房间数必须大于 0')
            validated_data['room_count'] = room_count
        except (ValueError, TypeError):
            errors.append('房间数必须是有效的整数')
    
    if 'hall_count' in data:
        try:
            validated_data['hall_count'] = int(data['hall_count']) if data['hall_count'] else None
        except (ValueError, TypeError):
            errors.append('客厅数必须是有效的整数')
    
    if 'bathroom_count' in data:
        try:
            validated_data['bathroom_count'] = int(data['bathroom_count']) if data['bathroom_count'] else None
        except (ValueError, TypeError):
            errors.append('卫生间数必须是有效的整数')
    
    if 'floor' in data:
        # 处理可能是整数或字符串的情况
        floor_value = data.get('floor')
        if floor_value is not None:
            validated_data['floor'] = str(floor_value).strip() if floor_value else ''
        else:
            validated_data['floor'] = ''
    
    if 'total_floors' in data:
        try:
            validated_data['total_floors'] = int(data['total_floors']) if data['total_floors'] else None
        except (ValueError, TypeError):
            errors.append('总楼层必须是有效的整数')
    
    # 朝向
    if 'orientation' in data:
        validated_data['orientation'] = data.get('orientation', '').strip()
    
    # 装修情况
    if 'decoration' in data:
        validated_data['decoration'] = data.get('decoration', '').strip()
    
    # 租金信息（仅整租需要）
    rental_type = data.get('rental_type', 'whole')
    if not is_update or 'rent_price' in data:
        try:
            rent_price = float(data['rent_price']) if data.get('rent_price') else None
            # 整租类型必须设置租金，合租类型租金可选（因为房间级别会设置）
            if rental_type == 'whole':
                if not is_update and (not rent_price or rent_price <= 0):
                    errors.append('租金不能为空且必须大于 0')
                elif is_update and rent_price is not None and rent_price <= 0:
                    errors.append('租金必须大于 0')
            validated_data['rent_price'] = rent_price
        except (ValueError, TypeError):
            errors.append('租金必须是有效的数字')
    
    # 押金和付款方式（仅整租需要）
    if rental_type == 'whole':
        if 'deposit' in data:
            try:
                validated_data['deposit'] = float(data['deposit']) if data['deposit'] else None
            except (ValueError, TypeError):
                errors.append('押金必须是有效的数字')
        
        if 'payment_method' in data:
            validated_data['payment_method'] = data.get('payment_method', '').strip()
    else:
        # 合租类型允许为空
        if 'deposit' in data:
            try:
                validated_data['deposit'] = float(data['deposit']) if data.get('deposit') else None
            except (ValueError, TypeError):
                errors.append('押金必须是有效的数字')
        
        if 'payment_method' in data:
            validated_data['payment_method'] = data.get('payment_method', '').strip()
    
    # 租赁类型（支持整租和合租）
    if 'rental_type' in data:
        if data['rental_type'] not in ['whole', 'shared']:
            errors.append('租赁类型只能是 whole(整租) 或 shared(合租)')
        else:
            validated_data['rental_type'] = data['rental_type']
    else:
        # 默认设置为整租
        validated_data['rental_type'] = 'whole'
    
    # 状态（仅在更新时允许）
    if is_update and 'status' in data:
        if data['status'] not in ['available', 'rented', 'maintenance', 'partially_rented']:
            errors.append('状态必须是 available、rented、maintenance 或 partially_rented')
        else:
            validated_data['status'] = data['status']
    
    # 配套设施（使用 JSON 字段验证器）
    if 'facilities' in data:
        facilities_data = None
        
        # 解析 JSON 字符串
        if isinstance(data['facilities'], str):
            import json
            try:
                facilities_data = json.loads(data['facilities'])
            except json.JSONDecodeError:
                errors.append('配套设施必须是有效的 JSON 格式')
        elif isinstance(data['facilities'], dict):
            facilities_data = data['facilities']
        elif data['facilities'] is not None:
            errors.append('配套设施必须是对象或 JSON 字符串')
        
        # 验证设施数据
        if facilities_data is not None:
            is_valid, facility_errors, validated_facilities = validate_facilities(
                facilities_data, 
                strict=False  # 非严格模式，保留未知字段
            )
            
            if not is_valid:
                errors.extend(facility_errors)
            else:
                # 使用验证后的数据（包含默认值填充）
                validated_data['facilities'] = validated_facilities
    elif not is_update:
        # 创建时如果没有提供 facilities，使用默认值
        validated_data['facilities'] = {}
    
    # 封面图片
    if 'cover_image' in data:
        validated_data['cover_image'] = data.get('cover_image', '').strip()
    
    # 房东 ID
    if 'landlord_id' in data:
        try:
            landlord_id = int(data['landlord_id']) if data['landlord_id'] else None
            validated_data['landlord_id'] = landlord_id
        except (ValueError, TypeError):
            errors.append('房东 ID 必须是有效的整数')
    
    # 联系信息字段（可选）
    if 'contact_name' in data:
        contact_name = data.get('contact_name')
        if contact_name is None:
            validated_data['contact_name'] = None
        else:
            contact_name = contact_name.strip()
            if contact_name and len(contact_name) > 50:
                errors.append('联系人姓名不能超过 50 个字符')
            else:
                validated_data['contact_name'] = contact_name
    
    if 'contact_phone' in data:
        contact_phone = data.get('contact_phone')
        if contact_phone is None:
            validated_data['contact_phone'] = None
        else:
            contact_phone = contact_phone.strip()
            if contact_phone:
                # 中国大陆手机号验证：11 位数字，以 1 开头，第二位是 3-9 之间的数字
                phone_pattern = r'^1[3-9]\d{9}$'
                if not re.match(phone_pattern, contact_phone):
                    errors.append('手机号格式不正确，应为 11 位中国大陆手机号')
                else:
                    validated_data['contact_phone'] = contact_phone
            else:
                validated_data['contact_phone'] = None
    
    if 'contact_wechat' in data:
        contact_wechat = data.get('contact_wechat')
        if contact_wechat is None:
            validated_data['contact_wechat'] = None
        else:
            contact_wechat = contact_wechat.strip()
            if contact_wechat and len(contact_wechat) > 50:
                errors.append('微信号不能超过 50 个字符')
            else:
                validated_data['contact_wechat'] = contact_wechat
    
    if errors:
        return False, '; '.join(errors), None
    
    return True, None, validated_data


def format_house_response(house: House, include_rooms: bool = False, is_internal: bool = True) -> Dict:
    """
    格式化房源响应数据
    
    Args:
        house: 房源对象
        include_rooms: 是否包含房间信息
        is_internal: 是否为内部接口（默认 True，返回完整信息）
        
    Returns:
        dict: 房源响应数据
    """
    data = house.to_dict(include_landlord=is_internal, is_internal=is_internal)
    
    # 合租类型返回房间信息
    if include_rooms and house.rental_type == 'shared':
        data['rooms'] = [room.to_dict() for room in house.rooms.order_by(Room.room_number).all()]
    
    # 添加媒体文件信息
    media_list = Media.query.filter_by(house_id=house.id).order_by(Media.sort_order, Media.created_at).all()
    if media_list:
        data['media'] = [media.to_dict() for media in media_list]
        # 设置封面图片
        cover_media = next((m for m in media_list if m.is_cover), None)
        if cover_media:
            data['cover_image'] = cover_media.file_url
    
    return data


# ============================================================================
# 房源 CRUD 接口
# ============================================================================

@houses_bp.route('', methods=['GET'])
@login_required
def get_houses():
    """
    获取房源列表（支持分页、筛选、搜索）
    
    Query Parameters:
        page: 页码，默认 1
        per_page: 每页数量，默认 20，最大 100
        city: 城市筛选
        district: 区县筛选
        status: 状态筛选 (available/rented/maintenance/partially_rented)
        rental_type: 租赁类型筛选 (whole/shared)
        min_price: 最低租金
        max_price: 最高租金
        keyword: 关键词搜索（地址、小区名称）
        owner_id: 房东 ID 筛选
        order_by: 排序字段 (created_at/rent_price/updated_at)，默认 created_at
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
        current_app.logger.info(f"获取房源列表请求参数：{request.args}")
        
        # 获取查询参数
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', type=int)
        per_page_arg = request.args.get('per_page', type=int)
        per_page = min(page_size or per_page_arg or 20, 100)
        
        current_app.logger.info(f"分页参数：page={page}, per_page={per_page}")
        
        # 尝试从缓存获取数据
        cache_manager = get_cache_manager()
        cache_key_params = {
            'page': page,
            'per_page': per_page,
            'city': request.args.get('city', ''),
            'district': request.args.get('district', ''),
            'status': request.args.get('status', ''),
            'rental_type': request.args.get('rental_type') or request.args.get('type', ''),
            'min_price': request.args.get('min_price', ''),
            'max_price': request.args.get('max_price', ''),
            'keyword': request.args.get('keyword', ''),
            'owner_id': request.args.get('owner_id', ''),
            'order_by': request.args.get('order_by', 'created_at'),
            'order': request.args.get('order', 'desc')
        }
        
        # 生成缓存键
        cache_key_suffix = generate_cache_key(**cache_key_params)
        key_prefix = current_app.config.get('CACHE_KEY_PREFIX', 'housing_rental:')
        cache_key = f"{key_prefix}houses:list:{cache_key_suffix}"
        
        # 尝试从缓存获取
        cached_result = cache_manager.get(cache_key)
        if cached_result is not None:
            current_app.logger.info(f"从缓存获取房源列表数据: {cache_key}")
            return APIResponse.success(cached_result, "获取房源列表成功（缓存）")
        
        # 构建查询（使用 db.session.query 避免 SoftDeleteQuery 的 paginate 问题）
        query = db.session.query(House).filter(House.deleted_at.is_(None))
        
        # 城市筛选
        city = request.args.get('city')
        if city and city.strip():
            query = query.filter(House.city.ilike(f'%{city.strip()}%'))
        
        # 区县筛选
        district = request.args.get('district')
        if district and district.strip():
            query = query.filter(House.district.ilike(f'%{district.strip()}%'))
        
        # 状态筛选
        status = request.args.get('status')
        if status and status.strip():
            query = query.filter(House.status == status.strip())
        
        # 租赁类型筛选（支持 type 和 rental_type 两种参数名）
        rental_type = request.args.get('rental_type') or request.args.get('type')
        if rental_type and rental_type.strip():
            query = query.filter(House.rental_type == rental_type.strip())
        
        # 租金范围筛选
        min_price = request.args.get('min_price', type=float)
        max_price = request.args.get('max_price', type=float)
        if min_price is not None and min_price >= 0:
            query = query.filter(House.rent_price >= min_price)
        if max_price is not None and max_price >= 0:
            query = query.filter(House.rent_price <= max_price)
        
        # 关键词搜索
        keyword = request.args.get('keyword')
        if keyword and keyword.strip():
            keyword = keyword.strip()
            query = query.filter(
                db.or_(
                    House.title.ilike(f'%{keyword}%'),
                    House.address.ilike(f'%{keyword}%'),
                    House.district.ilike(f'%{keyword}%')
                )
            )
        
        # 房东 ID 筛选
        owner_id = request.args.get('owner_id', type=int)
        if owner_id:
            query = query.filter(House.owner_id == owner_id)
        
        # 排序
        order_by = request.args.get('order_by', 'created_at')
        order = request.args.get('order', 'desc')
        
        order_column = getattr(House, order_by, House.created_at)
        if order == 'asc':
            query = query.order_by(order_column.asc())
        else:
            query = query.order_by(order_column.desc())
        
        # 执行分页查询
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        # 格式化响应数据
        items = [format_house_response(house) for house in pagination.items]
        
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
        
        result = {
            'items': items,
            'pagination': pagination_info
        }
        
        # 缓存结果（缓存 5 分钟）
        cache_manager.set(cache_key, result, timeout=300)
        current_app.logger.info(f"房源列表数据已缓存: {cache_key}")
        
        return APIResponse.success(result, "获取房源列表成功")
        
    except Exception as e:
        current_app.logger.error(f"获取房源列表失败：{str(e)}")
        current_app.logger.exception(f"异常详情：{str(e)}")
        import traceback
        current_app.logger.error(f"堆栈跟踪：{traceback.format_exc()}")
        return APIResponse.server_error("获取房源列表失败")


@houses_bp.route('/<int:house_id>', methods=['GET'])
@login_required
def get_house(house_id: int):
    """
    获取房源详情
    
    Path Parameters:
        house_id: 房源 ID
        
    Response:
        {
            "success": true,
            "data": {
                "id": 1,
                "title": "温馨两居室",
                "description": "...",
                "city": "北京",
                "district": "朝阳区",
                "address": "某某小区 3 号楼",
                "rent_price": 5000,
                "rooms": [...],  // 合租房源包含房间信息
                "media": [...]
            }
        }
    """
    try:
        # 使用 eager loading 优化查询，避免 N+1 问题
        house = optimize_house_detail_query(House.query).filter_by(id=house_id).first()
        
        if not house:
            return APIResponse.not_found("房源不存在")
        
        # 格式化响应数据（包含房间信息）
        data = format_house_response(house, include_rooms=True)
        
        return APIResponse.success(data, "获取房源详情成功")
        
    except Exception as e:
        current_app.logger.error(f"获取房源详情失败：{str(e)}")
        return APIResponse.server_error("获取房源详情失败")


@houses_bp.route('', methods=['POST'])
@login_required
@permission_required('create')
def create_house():
    """
    创建房源（所有登录用户可创建）
    
    Request Body:
        {
            "title": "房源标题",
            "description": "房源描述",
            "province": "省份",
            "city": "城市",
            "district": "区县",
            "address": "详细地址",
            "latitude": 39.9042,
            "longitude": 116.4074,
            "area": 80.5,
            "room_count": 2,
            "hall_count": 1,
            "bathroom_count": 1,
            "floor": "中层",
            "total_floors": 18,
            "rent_price": 5000,
            "deposit": 10000,
            "payment_method": "押一付三",
            "rental_type": "whole",  // whole-整租，shared-合租
            "facilities": {"wifi": true, "ac": true},
            "cover_image": "cover.jpg"
        }
        
    Response:
        {
            "success": true,
            "message": "房源创建成功",
            "data": {...}
        }
    """
    try:
        # 获取请求数据
        data = request.get_json()
        
        if not data:
            return APIResponse.bad_request("请求数据不能为空")
        
        # 验证数据
        is_valid, error_msg, validated_data = validate_house_data(data, is_update=False)
        
        if not is_valid:
            return APIResponse.validation_error(error_msg)
        
        # 创建房源
        house = House(**validated_data)
        house.owner_id = g.user_id
        
        db.session.add(house)
        db.session.flush()  # 获取房源 ID，并绑定到 session
        
        # 计算初始状态（需要在 add 和 flush 之后，因为 update_status 会访问关系属性）
        house.update_status()
        
        # 处理封面图片和图片集逻辑
        current_app.logger.info(f"处理图片逻辑：cover_image={validated_data.get('cover_image')}, images={data.get('images', [])}")
        
        # 收集所有需要关联的图片 URL
        all_image_urls = []
        if validated_data.get('cover_image'):
            all_image_urls.append(validated_data['cover_image'])
        if data.get('images'):
            for img in data['images']:
                if isinstance(img, str):
                    all_image_urls.append(img)
                elif isinstance(img, dict) and img.get('file_url'):
                    all_image_urls.append(img.get('file_url'))
        
        # 去重
        all_image_urls = list(set(all_image_urls))
        current_app.logger.info(f"需要关联的图片 URL：{all_image_urls}")
        
        if all_image_urls:
            # 查找所有匹配的媒体记录（house_id 为 None 或已关联的）
            media_records = Media.query.filter(
                Media.file_url.in_(all_image_urls)
            ).all()
            
            current_app.logger.info(f"找到 {len(media_records)} 个媒体记录")
            
            for media in media_records:
                media.house_id = house.id
                current_app.logger.info(f"关联媒体 {media.id} 到房源 {house.id}")
            
            # 设置封面图片
            if validated_data.get('cover_image'):
                # 查找封面图片并设为封面
                cover_media = next((m for m in media_records if m.file_url == validated_data['cover_image']), None)
                if cover_media:
                    cover_media.is_cover = True
                    current_app.logger.info(f"设置媒体 {cover_media.id} 为封面")
            elif media_records:
                # 如果没有指定封面，将第一张设为封面
                first_media = media_records[0]
                first_media.is_cover = True
                current_app.logger.info(f"自动设置媒体 {first_media.id} 为封面")
        
        db.session.commit()
        
        # 刷新获取完整数据
        db.session.refresh(house)
        
        # 失效房源列表缓存
        CacheEventEmitter.emit('house_created')
        
        # 格式化响应
        result = format_house_response(house)
        
        current_app.logger.info(f"用户 {g.username} 创建了房源 {house.id}")
        
        return APIResponse.success(result, "房源创建成功", 201)
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"创建房源失败：{str(e)}")
        return APIResponse.server_error("创建房源失败")


@houses_bp.route('/<int:house_id>', methods=['PUT'])
@login_required
@permission_required('edit')
def update_house(house_id: int):
    """
    更新房源（所有登录用户可编辑自己创建的房源）
    
    Path Parameters:
        house_id: 房源 ID
        
    Request Body:
        {
            "title": "新的房源标题",
            "rent_price": 6000,
            ...
        }
        
    Response:
        {
            "success": true,
            "message": "房源更新成功",
            "data": {...}
        }
    """
    try:
        house = House.query.get(house_id)
        
        if not house:
            return APIResponse.not_found("房源不存在")
        
        # 检查权限：只有房东或管理员可以编辑
        if house.owner_id != g.user_id and g.user_role != 'admin':
            return APIResponse.forbidden("您没有权限编辑此房源")
        
        # 获取请求数据
        data = request.get_json()
        
        current_app.logger.info(f"更新房源 {house_id}，接收到的数据：{data}")
        
        if not data:
            return APIResponse.bad_request("请求数据不能为空")
        
        # 验证数据
        is_valid, error_msg, validated_data = validate_house_data(data, is_update=True)
        
        current_app.logger.info(f"验证结果：is_valid={is_valid}, error_msg={error_msg}, validated_data={validated_data}")
        
        if not is_valid:
            return APIResponse.validation_error(error_msg)
        
        # 更新房源
        for key, value in validated_data.items():
            setattr(house, key, value)
        
        # 处理封面图片和图片集逻辑
        current_app.logger.info(f"处理图片逻辑：cover_image={validated_data.get('cover_image')}, images={data.get('images', [])}")
        
        # 收集所有需要关联的图片 URL
        all_image_urls = []
        if validated_data.get('cover_image'):
            all_image_urls.append(validated_data['cover_image'])
        if data.get('images'):
            for img in data['images']:
                if isinstance(img, str):
                    all_image_urls.append(img)
                elif isinstance(img, dict) and img.get('file_url'):
                    all_image_urls.append(img.get('file_url'))
        
        # 去重
        all_image_urls = list(set(all_image_urls))
        current_app.logger.info(f"需要关联的图片 URL：{all_image_urls}")
        
        if all_image_urls:
            # 查找所有匹配的媒体记录（house_id 为 None 或已关联的）
            media_records = Media.query.filter(
                Media.file_url.in_(all_image_urls)
            ).all()
            
            current_app.logger.info(f"找到 {len(media_records)} 个媒体记录")
            
            for media in media_records:
                media.house_id = house.id
                current_app.logger.info(f"关联媒体 {media.id} 到房源 {house.id}")
            
            # 设置封面图片
            if validated_data.get('cover_image'):
                # 查找封面图片并设为封面
                cover_media = next((m for m in media_records if m.file_url == validated_data['cover_image']), None)
                if cover_media:
                    # 取消其他封面
                    Media.query.filter_by(house_id=house.id, is_cover=True).update({'is_cover': False})
                    cover_media.is_cover = True
                    current_app.logger.info(f"设置媒体 {cover_media.id} 为封面")
            elif media_records:
                # 如果没有指定封面，将第一张设为封面
                # 取消其他封面
                Media.query.filter_by(house_id=house.id, is_cover=True).update({'is_cover': False})
                first_media = media_records[0]
                first_media.is_cover = True
                current_app.logger.info(f"自动设置媒体 {first_media.id} 为封面")
        
        db.session.commit()
        
        # 刷新获取完整数据
        db.session.refresh(house)
        
        # 失效房源缓存
        CacheEventEmitter.emit('house_updated')
        
        # 格式化响应
        result = format_house_response(house, include_rooms=True)
        
        current_app.logger.info(f"用户 {g.username} 更新了房源 {house.id}")
        
        return APIResponse.success(result, "房源更新成功")
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"更新房源失败：{str(e)}")
        current_app.logger.exception(f"更新房源异常详情：{str(e)}")
        import traceback
        current_app.logger.error(f"堆栈跟踪：{traceback.format_exc()}")
        return APIResponse.server_error("更新房源失败")


@houses_bp.route('/<int:house_id>', methods=['DELETE'])
@admin_required
def delete_house(house_id: int):
    """
    删除房源（仅管理员）
    
    Path Parameters:
        house_id: 房源 ID
        
    Response:
        {
            "success": true,
            "message": "房源删除成功"
        }
    """
    try:
        house = House.query.get(house_id)
        
        if not house:
            return APIResponse.not_found("房源不存在")
        
        # 检查是否有活跃合同
        from app.models.contract import Contract
        active_contracts = house.contracts.filter(
            Contract.status.in_(['active', 'pending'])
        ).count()
        
        if active_contracts > 0:
            return APIResponse.bad_request(
                f"房源有 {active_contracts} 个活跃合同，无法删除",
                {"active_contracts": active_contracts}
            )
        
        # 删除房源（级联删除房间和媒体）
        house_title = house.title
        db.session.delete(house)
        db.session.commit()
        
        # 失效房源缓存
        CacheEventEmitter.emit('house_deleted')
        
        current_app.logger.info(f"管理员 {g.username} 删除了房源 {house_id}: {house_title}")
        
        return APIResponse.success(None, "房源删除成功")
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"删除房源失败：{str(e)}")
        return APIResponse.server_error("删除房源失败")


# ============================================================================
# 房间管理接口
# ============================================================================

@houses_bp.route('/<int:house_id>/rooms', methods=['GET'])
@login_required
def get_rooms(house_id: int):
    """
    获取房间列表
    
    Path Parameters:
        house_id: 房源 ID
        
    Query Parameters:
        status: 房间状态筛选 (available/rented/maintenance)
        
    Response:
        {
            "success": true,
            "data": {
                "house_id": 1,
                "house_title": "温馨两居室",
                "rooms": [...]
            }
        }
    """
    try:
        house = House.query.get(house_id)
        
        if not house:
            return APIResponse.not_found("房源不存在")
        
        # 检查是否为合租房源
        if house.rental_type != 'shared':
            return APIResponse.bad_request("该房源不是合租房源")
        
        # 构建查询
        query = Room.query.filter_by(house_id=house_id)
        
        # 状态筛选
        status = request.args.get('status')
        if status:
            query = query.filter(Room.status == status)
        
        # 获取所有房间
        rooms = query.order_by(Room.room_number).all()
        
        # 格式化响应
        room_list = [room.to_dict() for room in rooms]
        
        return APIResponse.success({
            'house_id': house_id,
            'house_title': house.title,
            'rooms': room_list
        }, "获取房间列表成功")
        
    except Exception as e:
        current_app.logger.error(f"获取房间列表失败：{str(e)}")
        return APIResponse.server_error("获取房间列表失败")


@houses_bp.route('/<int:house_id>/rooms', methods=['POST'])
@login_required
@permission_required('create')
def create_room(house_id: int):
    """
    创建房间（所有登录用户可为自己的房源创建房间）
    
    Path Parameters:
        house_id: 房源 ID
        
    Request Body:
        {
            "room_number": "101",
            "name": "主卧",
            "description": "朝南主卧，带阳台",
            "area": 20.5,
            "floor": "1 层",
            "direction": "南",
            "rent_price": 2500,
            "deposit": 5000,
            "facilities": {"bed": true, "ac": true, "desk": true}
        }
        
    Response:
        {
            "success": true,
            "message": "房间创建成功",
            "data": {...}
        }
    """
    try:
        house = House.query.get(house_id)
        
        if not house:
            return APIResponse.not_found("房源不存在")
        
        # 检查权限
        if house.owner_id != g.user_id and g.user_role != 'admin':
            return APIResponse.forbidden("您没有权限为此房源创建房间")
        
        # 检查是否为合租房源
        if house.rental_type != 'shared':
            return APIResponse.bad_request("只有合租房源才能创建房间")
        
        # 获取请求数据
        data = request.get_json()
        
        if not data:
            return APIResponse.bad_request("请求数据不能为空")
        
        # 验证必填字段
        errors = []
        validated_data = {}
        
        # 房间编号（必填）
        if not data.get('room_number'):
            errors.append('房间编号不能为空')
        else:
            room_number = str(data['room_number']).strip()
            # 检查房间编号是否重复
            existing_room = Room.query.filter_by(
                house_id=house_id,
                room_number=room_number
            ).first()
            if existing_room:
                errors.append(f'房间编号 {room_number} 已存在')
            else:
                validated_data['room_number'] = room_number
        
        # 房间名称
        if 'room_name' in data:
            validated_data['room_name'] = data['room_name'].strip()
        
        # 描述
        if 'description' in data:
            validated_data['description'] = data.get('description', '').strip()
        
        # 面积
        if 'area' in data:
            try:
                area = float(data['area']) if data['area'] else None
                if area and area <= 0:
                    errors.append('面积必须大于 0')
                validated_data['area'] = area
            except (ValueError, TypeError):
                errors.append('面积必须是有效的数字')
        
        # 楼层
        if 'floor' in data:
            # 处理可能是整数或字符串的情况
            floor_value = data.get('floor')
            if floor_value is not None:
                validated_data['floor'] = str(floor_value).strip() if floor_value else ''
            else:
                validated_data['floor'] = ''
        
        # 朝向
        if 'orientation' in data:
            validated_data['orientation'] = data.get('orientation', '').strip()
        
        # 租金（必填）
        if not data.get('rent_price'):
            errors.append('房间租金不能为空')
        else:
            try:
                rent_price = float(data['rent_price'])
                if rent_price <= 0:
                    errors.append('租金必须大于 0')
                validated_data['rent_price'] = rent_price
            except (ValueError, TypeError):
                errors.append('租金必须是有效的数字')
        
        # 押金
        if 'deposit' in data:
            try:
                validated_data['deposit'] = float(data['deposit']) if data['deposit'] else 0
            except (ValueError, TypeError):
                errors.append('押金必须是有效的数字')
        
        # 付款方式
        if 'payment_method' in data:
            validated_data['payment_method'] = data.get('payment_method', 'press1_pay3').strip()
        
        # 是否主卧
        if 'is_master' in data:
            validated_data['is_master'] = bool(data['is_master'])
        
        # 配套设施（使用 JSON 字段验证器）
        if 'facilities' in data and data['facilities'] is not None:
            facilities_data = None
            
            # 解析 JSON 字符串
            if isinstance(data['facilities'], dict):
                facilities_data = data['facilities']
            elif isinstance(data['facilities'], str) and data['facilities'].strip():
                import json
                try:
                    facilities_data = json.loads(data['facilities'])
                except json.JSONDecodeError:
                    errors.append('配套设施必须是有效的 JSON 格式')
            
            # 验证设施数据
            if facilities_data is not None:
                is_valid, facility_errors, validated_facilities = validate_facilities(
                    facilities_data,
                    strict=False
                )
                
                if not is_valid:
                    errors.extend(facility_errors)
                else:
                    validated_data['facilities'] = validated_facilities
            else:
                # 默认为空对象
                validated_data['facilities'] = {}
        else:
            # 默认为空对象
            validated_data['facilities'] = {}
        
        if errors:
            return APIResponse.validation_error('; '.join(errors))
        
        # 创建房间
        room = Room(**validated_data)
        room.house_id = house_id
        
        db.session.add(room)
        
        # 自动更新房源状态（在同一个事务中）
        house.update_status()
        
        # 统一提交所有更改
        db.session.commit()
        
        # 刷新获取完整数据
        db.session.refresh(room)
        
        current_app.logger.info(f"用户 {g.username} 为房源 {house_id} 创建了房间 {room.id}")
        
        return APIResponse.success(room.to_dict(), "房间创建成功", 201)
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"创建房间失败：{str(e)}")
        return APIResponse.server_error("创建房间失败")


@houses_bp.route('/rooms/<int:room_id>', methods=['PUT'])
@login_required
@permission_required('edit')
def update_room(room_id: int):
    """
    更新房间
    
    Path Parameters:
        room_id: 房间 ID
        
    Request Body:
        {
            "name": "新的房间名称",
            "rent_price": 3000,
            "status": "available"
        }
        
    Response:
        {
            "success": true,
            "message": "房间更新成功",
            "data": {...}
        }
    """
    try:
        room = Room.query.get(room_id)
        
        if not room:
            return APIResponse.not_found("房间不存在")
        
        # 检查权限
        house = room.house
        if house.owner_id != g.user_id and g.user_role != 'admin':
            return APIResponse.forbidden("您没有权限编辑此房间")
        
        # 获取请求数据
        data = request.get_json()
        
        if not data:
            return APIResponse.bad_request("请求数据不能为空")
        
        # 验证并更新字段
        errors = []
        
        # 房间名称
        if 'room_name' in data:
            room.room_name = data['room_name'].strip()
        
        # 描述
        if 'description' in data:
            room.description = data.get('description', '').strip()
        
        # 面积
        if 'area' in data:
            try:
                room.area = float(data['area']) if data['area'] else None
            except (ValueError, TypeError):
                errors.append('面积必须是有效的数字')
        
        # 楼层
        if 'floor' in data:
            # 处理可能是整数或字符串的情况
            floor_value = data.get('floor')
            if floor_value is not None:
                room.floor = str(floor_value).strip() if floor_value else ''
            else:
                room.floor = ''
        
        # 朝向
        if 'orientation' in data:
            room.orientation = data.get('orientation', '').strip()
        
        # 租金
        if 'rent_price' in data:
            try:
                rent_price = float(data['rent_price'])
                if rent_price <= 0:
                    errors.append('租金必须大于 0')
                room.rent_price = rent_price
            except (ValueError, TypeError):
                errors.append('租金必须是有效的数字')
        
        # 押金
        if 'deposit' in data:
            try:
                room.deposit = float(data['deposit']) if data['deposit'] else 0
            except (ValueError, TypeError):
                errors.append('押金必须是有效的数字')
        
        # 付款方式
        if 'payment_method' in data:
            room.payment_method = data.get('payment_method', 'press1_pay3').strip()
        
        # 是否主卧
        if 'is_master' in data:
            room.is_master = bool(data['is_master'])
        
        # 状态
        if 'status' in data:
            if data['status'] not in ['available', 'rented', 'maintenance']:
                errors.append('状态必须是 available、rented 或 maintenance')
            else:
                room.status = data['status']
        
        # 配套设施（使用 JSON 字段验证器）
        if 'facilities' in data and data['facilities'] is not None:
            facilities_data = None
            
            # 解析 JSON 字符串
            if isinstance(data['facilities'], dict):
                facilities_data = data['facilities']
            elif isinstance(data['facilities'], str) and data['facilities'].strip():
                import json
                try:
                    facilities_data = json.loads(data['facilities'])
                except json.JSONDecodeError:
                    errors.append('配套设施必须是有效的 JSON 格式')
            
            # 验证设施数据
            if facilities_data is not None:
                is_valid, facility_errors, validated_facilities = validate_facilities(
                    facilities_data,
                    strict=False
                )
                
                if not is_valid:
                    errors.extend(facility_errors)
                else:
                    room.facilities = validated_facilities
        
        if errors:
            return APIResponse.validation_error('; '.join(errors))
        
        # 自动更新房源状态（在同一个事务中）
        house.update_status()
        
        # 统一提交所有更改
        db.session.commit()
        
        current_app.logger.info(f"用户 {g.username} 更新了房间 {room_id}")
        
        return APIResponse.success(room.to_dict(), "房间更新成功")
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"更新房间失败：{str(e)}")
        return APIResponse.server_error("更新房间失败")


@houses_bp.route('/rooms/<int:room_id>', methods=['DELETE'])
@admin_required
def delete_room(room_id: int):
    """
    删除房间（仅管理员）
    
    Path Parameters:
        room_id: 房间 ID
        
    Response:
        {
            "success": true,
            "message": "房间删除成功"
        }
    """
    try:
        room = Room.query.get(room_id)
        
        if not room:
            return APIResponse.not_found("房间不存在")
        
        # 检查是否有活跃合同
        from app.models.contract import Contract
        active_contracts = room.contracts.filter(
            Contract.status.in_(['active', 'pending'])
        ).count()
        
        if active_contracts > 0:
            return APIResponse.bad_request(
                f"房间有 {active_contracts} 个活跃合同，无法删除",
                {"active_contracts": active_contracts}
            )
        
        house = room.house
        room_number = room.room_number
        
        # 删除房间
        db.session.delete(room)
        
        # 自动更新房源状态
        house.update_status()
        
        db.session.commit()
        
        current_app.logger.info(f"管理员 {g.username} 删除了房源 {house.id} 的房间 {room_number}")
        
        return APIResponse.success(None, "房间删除成功")
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"删除房间失败：{str(e)}")
        return APIResponse.server_error("删除房间失败")


@houses_bp.route('/<int:house_id>/rooms/batch', methods=['POST'])
@login_required
@permission_required('create')
def batch_create_rooms(house_id: int):
    """
    批量创建房间
    
    Path Parameters:
        house_id: 房源 ID
        
    Request Body:
        {
            "rooms": [
                {
                    "room_number": "101",
                    "name": "主卧",
                    "description": "朝南主卧，带阳台",
                    "area": 20.5,
                    "floor": "1 层",
                    "direction": "南",
                    "rent_price": 2500,
                    "deposit": 5000,
                    "facilities": {"bed": true, "ac": true, "desk": true}
                },
                {
                    "room_number": "102",
                    "name": "次卧",
                    "description": "朝北次卧",
                    "area": 15.5,
                    "floor": "1 层",
                    "direction": "北",
                    "rent_price": 2000,
                    "deposit": 4000,
                    "facilities": {"bed": true, "desk": true}
                }
            ]
        }
        
    Response:
        {
            "success": true,
            "message": "批量创建房间成功",
            "data": {
                "created_count": 2,
                "rooms": [...]
            }
        }
    """
    try:
        house = House.query.get(house_id)
        
        if not house:
            return APIResponse.not_found("房源不存在")
        
        # 检查权限
        if house.owner_id != g.user_id and g.user_role != 'admin':
            return APIResponse.forbidden("您没有权限为此房源创建房间")
        
        # 检查是否为合租房源
        if house.rental_type != 'shared':
            return APIResponse.bad_request("只有合租房源才能创建房间")
        
        # 获取请求数据
        data = request.get_json()
        
        if not data or not isinstance(data.get('rooms'), list):
            return APIResponse.bad_request("请求数据必须包含 rooms 数组")
        
        rooms_data = data['rooms']
        if not rooms_data:
            return APIResponse.bad_request("rooms 数组不能为空")
        
        # 验证并创建房间
        created_rooms = []
        errors = []
        
        # 首先检查所有房间编号是否重复
        existing_room_numbers = set(
            room.room_number for room in Room.query.filter_by(house_id=house_id).all()
        )
        
        # 检查批量创建的房间编号是否内部重复
        batch_room_numbers = set()
        for i, room_data in enumerate(rooms_data):
            room_number = str(room_data.get('room_number', '')).strip()
            if not room_number:
                errors.append(f"第 {i+1} 个房间：房间编号不能为空")
            elif room_number in existing_room_numbers:
                errors.append(f"第 {i+1} 个房间：房间编号 {room_number} 已存在")
            elif room_number in batch_room_numbers:
                errors.append(f"第 {i+1} 个房间：房间编号 {room_number} 在批量创建中重复")
            else:
                batch_room_numbers.add(room_number)
        
        if errors:
            return APIResponse.validation_error('; '.join(errors))
        
        # 批量创建房间
        for room_data in rooms_data:
            validated_data = {}
            
            # 房间编号
            validated_data['room_number'] = str(room_data['room_number']).strip()
            
            # 房间名称（API 使用 name，模型使用 room_name）
            if 'name' in room_data:
                validated_data['room_name'] = room_data.get('name', '').strip()
            
            # 描述
            if 'description' in room_data:
                validated_data['description'] = room_data.get('description', '').strip()
            
            # 面积
            if 'area' in room_data:
                try:
                    area = float(room_data['area']) if room_data['area'] else None
                    if area and area <= 0:
                        errors.append('面积必须大于 0')
                    validated_data['area'] = area
                except (ValueError, TypeError):
                    errors.append('面积必须是有效的数字')
            
            # 楼层
            if 'floor' in room_data:
                floor_value = room_data.get('floor')
                if floor_value is not None:
                    validated_data['floor'] = str(floor_value).strip() if floor_value else ''
                else:
                    validated_data['floor'] = ''
            
            # 朝向（API 使用 direction，模型使用 orientation）
            if 'direction' in room_data:
                validated_data['orientation'] = room_data.get('direction', '').strip()
            
            # 租金（必填）
            if not room_data.get('rent_price'):
                errors.append('房间租金不能为空')
            else:
                try:
                    rent_price = float(room_data['rent_price'])
                    if rent_price <= 0:
                        errors.append('租金必须大于 0')
                    validated_data['rent_price'] = rent_price
                except (ValueError, TypeError):
                    errors.append('租金必须是有效的数字')
            
            # 押金
            if 'deposit' in room_data:
                try:
                    validated_data['deposit'] = float(room_data['deposit']) if room_data['deposit'] else 0
                except (ValueError, TypeError):
                    errors.append('押金必须是有效的数字')
            
            # 配套设施（使用 JSON 字段验证器）
            if 'facilities' in room_data:
                facilities_data = None
                
                # 解析 JSON 字符串
                if isinstance(room_data['facilities'], dict):
                    facilities_data = room_data['facilities']
                elif isinstance(room_data['facilities'], str):
                    import json
                    try:
                        facilities_data = json.loads(room_data['facilities'])
                    except json.JSONDecodeError:
                        errors.append('配套设施必须是有效的 JSON 格式')
                else:
                    errors.append('配套设施必须是对象或 JSON 字符串')
                
                # 验证设施数据
                if facilities_data is not None:
                    is_valid, facility_errors, validated_facilities = validate_facilities(
                        facilities_data,
                        strict=False
                    )
                    
                    if not is_valid:
                        errors.extend(facility_errors)
                    else:
                        validated_data['facilities'] = validated_facilities
            
            if errors:
                break
            
            # 创建房间
            room = Room(**validated_data)
            room.house_id = house_id
            db.session.add(room)
            created_rooms.append(room)
        
        if errors:
            db.session.rollback()
            return APIResponse.validation_error('; '.join(errors))
        
        # 自动更新房源状态（在同一个事务中）
        house.update_status()
        
        # 统一提交所有更改
        db.session.commit()
        
        # 刷新获取完整数据
        for room in created_rooms:
            db.session.refresh(room)
        
        current_app.logger.info(f"用户 {g.username} 为房源 {house_id} 批量创建了 {len(created_rooms)} 个房间")
        
        return APIResponse.success({
            'created_count': len(created_rooms),
            'rooms': [room.to_dict() for room in created_rooms]
        }, "批量创建房间成功", 201)
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"批量创建房间失败：{str(e)}")
        return APIResponse.server_error("批量创建房间失败")


@houses_bp.route('/<int:house_id>/rooms/available', methods=['GET'])
@login_required
def get_available_rooms(house_id: int):
    """
    获取可租房间列表
    
    Path Parameters:
        house_id: 房源 ID
        
    Response:
        {
            "success": true,
            "data": {
                "house_id": 1,
                "house_title": "温馨两居室",
                "available_rooms": [...]
            }
        }
    """
    try:
        house = House.query.get(house_id)
        
        if not house:
            return APIResponse.not_found("房源不存在")
        
        # 检查是否为合租房源
        if house.rental_type != 'shared':
            return APIResponse.bad_request("该房源不是合租房源")
        
        # 获取所有可租房间
        available_rooms = Room.query.filter_by(
            house_id=house_id,
            status='available'
        ).order_by(Room.room_number).all()
        
        # 格式化响应
        room_list = [room.to_dict() for room in available_rooms]
        
        return APIResponse.success({
            'house_id': house_id,
            'house_title': house.title,
            'available_rooms': room_list
        }, "获取可租房间列表成功")
        
    except Exception as e:
        current_app.logger.error(f"获取可租房间列表失败：{str(e)}")
        return APIResponse.server_error("获取可租房间列表失败")


@houses_bp.route('/<int:house_id>/stats', methods=['GET'])
@login_required
def get_house_stats(house_id: int):
    """
    获取合租房源统计信息
    
    Path Parameters:
        house_id: 房源 ID
        
    Response:
        {
            "success": true,
            "data": {
                "house_id": 1,
                "house_title": "温馨两居室",
                "total_rooms": 3,
                "rented_rooms": 1,
                "available_rooms": 2,
                "maintenance_rooms": 0
            }
        }
    """
    try:
        house = House.query.get(house_id)
        
        if not house:
            return APIResponse.not_found("房源不存在")
        
        # 检查是否为合租房源
        if house.rental_type != 'shared':
            return APIResponse.bad_request("该房源不是合租房源")
        
        # 统计房间状态
        total_rooms = house.rooms.count()
        rented_rooms = house.rooms.filter(Room.status == 'rented').count()
        available_rooms = house.rooms.filter(Room.status == 'available').count()
        maintenance_rooms = house.rooms.filter(Room.status == 'maintenance').count()
        
        # 格式化响应
        stats_data = {
            'house_id': house_id,
            'house_title': house.title,
            'total_rooms': total_rooms,
            'rented_rooms': rented_rooms,
            'available_rooms': available_rooms,
            'maintenance_rooms': maintenance_rooms
        }
        
        return APIResponse.success(stats_data, "获取房源统计信息成功")
        
    except Exception as e:
        current_app.logger.error(f"获取房源统计信息失败：{str(e)}")
        return APIResponse.server_error("获取房源统计信息失败")


# ============================================================================
# 房源状态管理接口
# ============================================================================

@houses_bp.route('/<int:house_id>/status', methods=['PUT'])
@login_required
@permission_required('edit')
def update_house_status(house_id: int):
    """
    更新房源状态
    
    Path Parameters:
        house_id: 房源 ID
        
    Request Body:
        {
            "status": "available"  // available/rented/maintenance/partially_rented
        }
        
    Response:
        {
            "success": true,
            "message": "房源状态更新成功",
            "data": {
                "id": 1,
                "status": "available",
                "rental_type": "whole"
            }
        }
    """
    try:
        house = House.query.get(house_id)
        
        if not house:
            return APIResponse.not_found("房源不存在")
        
        # 检查权限
        if house.owner_id != g.user_id and g.user_role != 'admin':
            return APIResponse.forbidden("您没有权限更新此房源状态")
        
        # 获取请求数据
        data = request.get_json()
        
        if not data:
            return APIResponse.bad_request("请求数据不能为空")
        
        # 获取新状态
        new_status = data.get('status')
        
        if not new_status:
            return APIResponse.bad_request("状态不能为空")
        
        # 验证状态值
        valid_statuses = ['available', 'rented', 'maintenance', 'partially_rented']
        if new_status not in valid_statuses:
            return APIResponse.bad_request(
                f"状态必须是以下值之一：{', '.join(valid_statuses)}"
            )
        
        # 对于合租房源，自动计算状态
        if house.rental_type == 'shared':
            # 合租模式下，状态由系统自动计算
            actual_status = house.update_status()
            if actual_status != new_status:
                current_app.logger.warning(
                    f"合租房源 {house_id} 的状态由系统自动计算为 {actual_status}，"
                    f"忽略请求的状态 {new_status}"
                )
                new_status = actual_status
        else:
            # 整租模式，允许手动设置
            house.status = new_status
        
        house.status = new_status
        db.session.commit()
        
        current_app.logger.info(f"用户 {g.username} 更新了房源 {house_id} 的状态为 {new_status}")
        
        return APIResponse.success({
            'id': house.id,
            'status': house.status,
            'rental_type': house.rental_type,
            'auto_calculated': house.rental_type == 'shared'
        }, "房源状态更新成功")
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"更新房源状态失败：{str(e)}")
        return APIResponse.server_error("更新房源状态失败")


@houses_bp.route('/<int:house_id>/auto-status', methods=['POST'])
@login_required
def recalculate_house_status(house_id: int):
    """
    重新计算房源状态（基于房间状态）
    
    Path Parameters:
        house_id: 房源 ID
        
    Response:
        {
            "success": true,
            "data": {
                "id": 1,
                "old_status": "available",
                "new_status": "partially_rented",
                "rental_type": "shared"
            }
        }
    """
    try:
        house = House.query.get(house_id)
        
        if not house:
            return APIResponse.not_found("房源不存在")
        
        # 检查权限
        if house.owner_id != g.user_id and g.user_role != 'admin':
            return APIResponse.forbidden("您没有权限操作此房源")
        
        # 保存旧状态
        old_status = house.status
        
        # 重新计算状态
        new_status = house.update_status()
        
        # 如果状态有变化，保存到数据库
        if old_status != new_status:
            house.status = new_status
            db.session.commit()
            
            current_app.logger.info(
                f"房源 {house_id} 状态从 {old_status} 变更为 {new_status}"
            )
        
        return APIResponse.success({
            'id': house.id,
            'old_status': old_status,
            'new_status': new_status,
            'rental_type': house.rental_type,
            'changed': old_status != new_status
        }, "房源状态重新计算成功")
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"重新计算房源状态失败：{str(e)}")
        return APIResponse.server_error("重新计算房源状态失败")


# ============================================================================
# 统计接口
# ============================================================================

@houses_bp.route('/stats', methods=['GET'])
@login_required
def get_houses_stats():
    """
    获取房源统计信息
    
    Query Parameters:
        owner_id: 房东 ID（管理员可查看所有房东的统计）
        
    Response:
        {
            "success": true,
            "data": {
                "total": 100,
                "available": 60,
                "rented": 30,
                "maintenance": 10,
                "whole_rental": 70,
                "shared_rental": 30
            }
        }
    """
    try:
        # 构建查询
        query = House.query
        
        # 房东筛选
        owner_id = request.args.get('owner_id', type=int)
        if owner_id:
            # 非管理员只能查看自己的统计
            if g.user_role != 'admin':
                owner_id = g.user_id
            query = query.filter(House.owner_id == owner_id)
        elif g.user_role != 'admin':
            # 非管理员默认查看自己的统计
            query = query.filter(House.owner_id == g.user_id)
        
        # 统计总数
        total = query.count()
        
        # 按状态统计
        available = query.filter(House.status == 'available').count()
        rented = query.filter(House.status == 'rented').count()
        maintenance = query.filter(House.status == 'maintenance').count()
        partially_rented = query.filter(House.status == 'partially_rented').count()
        
        # 按租赁类型统计
        whole_rental = query.filter(House.rental_type == 'whole').count()
        shared_rental = query.filter(House.rental_type == 'shared').count()
        
        return APIResponse.success({
            'total': total,
            'by_status': {
                'available': available,
                'rented': rented,
                'maintenance': maintenance,
                'partially_rented': partially_rented
            },
            'by_rental_type': {
                'whole': whole_rental,
                'shared': shared_rental
            }
        }, "获取统计信息成功")
        
    except Exception as e:
        current_app.logger.error(f"获取房源统计失败：{str(e)}")
        return APIResponse.server_error("获取房源统计失败")


# ============================================================================
# 设施配置接口
# ============================================================================

@houses_bp.route('/facilities/config', methods=['GET'])
@login_required
def get_facilities_config():
    """
    获取设施配置信息
    
    返回所有支持的设施字段及其描述，供前端使用
    
    Response:
        {
            "success": true,
            "data": {
                "facilities": {
                    "wifi": {"type": "bool", "description": "无线网络", "default": false},
                    "ac": {"type": "bool", "description": "空调", "default": false},
                    ...
                },
                "default_facilities": {...}
            }
        }
    """
    try:
        from app.utils.json_validator import get_all_facilities, get_default_facilities
        
        facilities = get_all_facilities()
        default_facilities = get_default_facilities()
        
        # 格式化设施数据
        formatted_facilities = {}
        for key, config in facilities.items():
            formatted_facilities[key] = {
                'type': config['type'].__name__,
                'description': config['description'],
                'default': config['default']
            }
        
        return APIResponse.success({
            'facilities': formatted_facilities,
            'default_facilities': default_facilities
        }, "获取设施配置成功")
        
    except Exception as e:
        current_app.logger.error(f"获取设施配置失败：{str(e)}")
        return APIResponse.server_error("获取设施配置失败")


@houses_bp.route('/facilities/validate', methods=['POST'])
@login_required
def validate_facilities_endpoint():
    """
    验证设施数据
    
    用于前端实时验证设施数据
    
    Request Body:
        {
            "facilities": {"wifi": true, "ac": true, ...},
            "strict": false  // 可选，是否严格模式
        }
        
    Response:
        {
            "success": true,
            "data": {
                "is_valid": true,
                "errors": [],
                "warnings": ["未知字段 'custom_field'"],
                "validated_data": {...}
            }
        }
    """
    try:
        data = request.get_json()
        
        if not data:
            return APIResponse.bad_request("请求数据不能为空")
        
        facilities = data.get('facilities')
        strict = data.get('strict', False)
        
        if facilities is None:
            return APIResponse.bad_request("facilities 字段不能为空")
        
        # 使用详细验证
        result = validate_facilities_detailed(facilities, strict=strict)
        
        return APIResponse.success({
            'is_valid': result.is_valid,
            'errors': result.errors,
            'warnings': result.warnings,
            'validated_data': result.data
        }, "验证完成")
        
    except Exception as e:
        current_app.logger.error(f"验证设施数据失败：{str(e)}")
        return APIResponse.server_error("验证设施数据失败")
