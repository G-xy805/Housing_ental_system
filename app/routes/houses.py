"""
房源管理路由模块
提供房源 CRUD、房间管理、房源状态管理等功能
"""
from flask import Blueprint, request, jsonify, g, current_app
from typing import Optional, Dict, Any
from datetime import datetime

from app.models.house import House
from app.models.room import Room
from app.models.user import User
from app.models.media import Media
from app.models import db
from app.utils.decorators import login_required, admin_required, permission_required
from app.utils.responses import APIResponse, PaginationResponse

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
    
    # 租金信息
    if not is_update or 'rent_price' in data:
        try:
            rent_price = float(data['rent_price']) if data.get('rent_price') else None
            if not is_update and (not rent_price or rent_price <= 0):
                errors.append('租金不能为空且必须大于 0')
            elif is_update and rent_price is not None and rent_price <= 0:
                errors.append('租金必须大于 0')
            validated_data['rent_price'] = rent_price
        except (ValueError, TypeError):
            errors.append('租金必须是有效的数字')
    
    if 'deposit' in data:
        try:
            validated_data['deposit'] = float(data['deposit']) if data['deposit'] else None
        except (ValueError, TypeError):
            errors.append('押金必须是有效的数字')
    
    if 'payment_method' in data:
        validated_data['payment_method'] = data.get('payment_method', '').strip()
    
    # 租赁类型
    if 'rental_type' in data:
        if data['rental_type'] not in ['whole', 'shared']:
            errors.append('租赁类型必须是 whole(整租) 或 shared(合租)')
        else:
            validated_data['rental_type'] = data['rental_type']
    
    # 状态（仅在更新时允许）
    if is_update and 'status' in data:
        if data['status'] not in ['available', 'rented', 'maintenance', 'partially_rented']:
            errors.append('状态必须是 available、rented、maintenance 或 partially_rented')
        else:
            validated_data['status'] = data['status']
    
    # 配套设施
    if 'facilities' in data:
        if isinstance(data['facilities'], dict):
            validated_data['facilities'] = data['facilities']
        elif isinstance(data['facilities'], str):
            import json
            try:
                validated_data['facilities'] = json.loads(data['facilities'])
            except json.JSONDecodeError:
                errors.append('配套设施必须是有效的 JSON 格式')
        else:
            errors.append('配套设施必须是对象或 JSON 字符串')
    
    # 封面图片
    if 'cover_image' in data:
        validated_data['cover_image'] = data.get('cover_image', '').strip()
    
    if errors:
        return False, '; '.join(errors), None
    
    return True, None, validated_data


def format_house_response(house: House, include_rooms: bool = False) -> Dict:
    """
    格式化房源响应数据
    
    Args:
        house: 房源对象
        include_rooms: 是否包含房间信息
        
    Returns:
        dict: 房源响应数据
    """
    data = house.to_dict()
    
    # 添加房间信息
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
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        
        current_app.logger.info(f"分页参数：page={page}, per_page={per_page}")
        
        # 构建查询
        query = House.query
        
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
        
        return APIResponse.success({
            'items': items,
            'pagination': pagination_info
        }, "获取房源列表成功")
        
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
        house = House.query.get(house_id)
        
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
        db.session.commit()
        
        # 刷新获取完整数据
        db.session.refresh(house)
        
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
        
        db.session.commit()
        
        # 刷新获取完整数据
        db.session.refresh(house)
        
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
        if 'name' in data:
            validated_data['name'] = data['name'].strip()
        
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
        if 'direction' in data:
            validated_data['direction'] = data.get('direction', '').strip()
        
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
        
        # 配套设施
        if 'facilities' in data:
            if isinstance(data['facilities'], dict):
                validated_data['facilities'] = data['facilities']
            elif isinstance(data['facilities'], str):
                import json
                try:
                    validated_data['facilities'] = json.loads(data['facilities'])
                except json.JSONDecodeError:
                    errors.append('配套设施必须是有效的 JSON 格式')
            else:
                errors.append('配套设施必须是对象或 JSON 字符串')
        
        if errors:
            return APIResponse.validation_error('; '.join(errors))
        
        # 创建房间
        room = Room(**validated_data)
        room.house_id = house_id
        
        db.session.add(room)
        db.session.commit()
        
        # 刷新获取完整数据
        db.session.refresh(room)
        
        # 自动更新房源状态
        house.update_status()
        db.session.commit()
        
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
        if 'name' in data:
            room.name = data['name'].strip()
        
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
        if 'direction' in data:
            room.direction = data.get('direction', '').strip()
        
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
        
        # 状态
        if 'status' in data:
            if data['status'] not in ['available', 'rented', 'maintenance']:
                errors.append('状态必须是 available、rented 或 maintenance')
            else:
                room.status = data['status']
        
        # 配套设施
        if 'facilities' in data:
            if isinstance(data['facilities'], dict):
                room.facilities = data['facilities']
            elif isinstance(data['facilities'], str):
                import json
                try:
                    room.facilities = json.loads(data['facilities'])
                except json.JSONDecodeError:
                    errors.append('配套设施必须是有效的 JSON 格式')
            else:
                errors.append('配套设施必须是对象或 JSON 字符串')
        
        if errors:
            return APIResponse.validation_error('; '.join(errors))
        
        db.session.commit()
        
        # 自动更新房源状态
        house.update_status()
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
def get_house_stats():
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
