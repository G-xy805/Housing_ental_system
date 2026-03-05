"""
对外房源管理路由模块
提供面向租客的房源查询接口（不含房东敏感信息）
"""
from flask import Blueprint, request, jsonify, g, current_app
from typing import Optional, Dict, Any
from datetime import datetime
import re

from app.models.house import House
from app.models.room import Room
from app.models.media import Media
from app.models import db
from app.utils.decorators import optional_login
from app.utils.responses import APIResponse, PaginationResponse

# 创建蓝图
public_houses_bp = Blueprint('public_houses', __name__, url_prefix='/api/public/houses')


# ============================================================================
# 辅助函数
# ============================================================================

def format_public_house_response(house: House, include_rooms: bool = False) -> Dict:
    """
    格式化对外房源响应数据（不含房东敏感信息）
    
    Args:
        house: 房源对象
        include_rooms: 是否包含房间信息
        
    Returns:
        dict: 房源响应数据
    """
    # 使用 is_internal=False 确保不返回房东敏感信息
    data = house.to_dict(include_landlord=False, is_internal=False)
    
    # 添加房间信息
    if include_rooms and house.rental_type == 'shared':
        # 房间信息也不包含房东信息
        room_list = []
        for room in house.rooms.order_by(Room.room_number).all():
            room_data = room.to_dict()
            room_list.append(room_data)
        data['rooms'] = room_list
    
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
# 对外房源查询接口
# ============================================================================

@public_houses_bp.route('', methods=['GET'])
@optional_login
def get_public_houses():
    """
    获取房源列表（对外接口，不含房东敏感信息）
    
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
        
    注意：
        - 此接口返回的房源信息不包含房东敏感信息
        - 房东姓名、电话、身份证号、银行卡号等都不会返回
        - 联系信息字段（contact_name, contact_phone, contact_wechat）均为 null
    """
    try:
        current_app.logger.info(f"获取对外房源列表请求参数：{request.args}")
        
        # 获取查询参数
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', type=int)
        per_page_arg = request.args.get('per_page', type=int)
        per_page = min(page_size or per_page_arg or 20, 100)
        
        current_app.logger.info(f"分页参数：page={page}, per_page={per_page}")
        
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
        
        # 格式化响应数据（使用对外版本，is_internal=False）
        items = [format_public_house_response(house) for house in pagination.items]
        
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
        current_app.logger.error(f"获取对外房源列表失败：{str(e)}")
        current_app.logger.exception(f"异常详情：{str(e)}")
        import traceback
        current_app.logger.error(f"堆栈跟踪：{traceback.format_exc()}")
        return APIResponse.server_error("获取房源列表失败")


@public_houses_bp.route('/<int:house_id>', methods=['GET'])
@optional_login
def get_public_house(house_id: int):
    """
    获取房源详情（对外接口，不含房东敏感信息）
    
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
        
    注意：
        - 此接口返回的房源信息不包含房东敏感信息
        - 房东姓名、电话、身份证号、银行卡号等都不会返回
        - 联系信息字段（contact_name, contact_phone, contact_wechat）均为 null
    """
    try:
        house = House.query.get(house_id)
        
        if not house:
            return APIResponse.not_found("房源不存在")
        
        # 格式化响应数据（包含房间信息，使用对外版本）
        data = format_public_house_response(house, include_rooms=True)
        
        return APIResponse.success(data, "获取房源详情成功")
        
    except Exception as e:
        current_app.logger.error(f"获取对外房源详情失败：{str(e)}")
        return APIResponse.server_error("获取房源详情失败")


@public_houses_bp.route('/<int:house_id>/rooms', methods=['GET'])
@optional_login
def get_public_rooms(house_id: int):
    """
    获取房间列表（对外接口，不含房东敏感信息）
    
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
        
    注意：
        - 此接口返回的房间信息不包含房东敏感信息
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
        current_app.logger.error(f"获取对外房间列表失败：{str(e)}")
        return APIResponse.server_error("获取房间列表失败")


# ============================================================================
# 对外统计接口
# ============================================================================

@public_houses_bp.route('/stats', methods=['GET'])
@optional_login
def get_public_house_stats():
    """
    获取房源统计信息（对外接口）
    
    Response:
        {
            "success": true,
            "data": {
                "total": 100,
                "by_status": {
                    "available": 60,
                    "rented": 30,
                    "maintenance": 10,
                    "partially_rented": 0
                },
                "by_rental_type": {
                    "whole": 70,
                    "shared": 30
                }
            }
        }
        
    注意：
        - 此接口仅返回基本统计信息，不包含房东相关统计
    """
    try:
        # 统计总数
        total = House.query.count()
        
        # 按状态统计
        available = House.query.filter(House.status == 'available').count()
        rented = House.query.filter(House.status == 'rented').count()
        maintenance = House.query.filter(House.status == 'maintenance').count()
        partially_rented = House.query.filter(House.status == 'partially_rented').count()
        
        # 按租赁类型统计
        whole_rental = House.query.filter(House.rental_type == 'whole').count()
        shared_rental = House.query.filter(House.rental_type == 'shared').count()
        
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
        current_app.logger.error(f"获取对外房源统计失败：{str(e)}")
        return APIResponse.server_error("获取房源统计失败")
