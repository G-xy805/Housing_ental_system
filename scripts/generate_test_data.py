#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试数据生成脚本

用于生成完整的测试数据，包括用户、房东、房源、房间、租客、合同和支付记录
支持命令行参数控制是否清理旧数据

使用方法:
    python scripts/generate_test_data.py              # 清理旧数据并生成新数据
    python scripts/generate_test_data.py --no-clean   # 不清理旧数据，直接生成
    python scripts/generate_test_data.py --help       # 查看帮助
"""

import os
import sys
import random
import logging
import argparse
from datetime import datetime, timedelta, date
from decimal import Decimal
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models.user import User
from app.models.landlord import Landlord
from app.models.house import House
from app.models.room import Room
from app.models.tenant import Tenant
from app.models.contract import Contract
from app.models.payment import Payment

# ============================================================================
# 配置常量
# ============================================================================

# 数据生成数量配置
CONFIG = {
    'user': {
        'min': 5,
        'max': 10,
        'admin_ratio': 0.2,  # 管理员比例
    },
    'landlord': {
        'min': 10,
        'max': 20,
    },
    'house': {
        'min': 30,
        'max': 50,
        'whole_rent_ratio': 0.6,  # 整租比例 60%
        'cities': ['北京', '上海', '广州', '深圳'],  # 覆盖城市
    },
    'room': {
        'min_per_house': 3,
        'max_per_house': 6,
    },
    'tenant': {
        'min': 50,
        'max': 80,
    },
    'contract': {
        'min': 60,
        'max': 100,
        'status_distribution': {
            'active': 0.6,      # 60% 生效中
            'expired': 0.2,     # 20% 已过期
            'draft': 0.1,       # 10% 草稿
            'terminated': 0.1,  # 10% 已终止
        }
    },
    'payment': {
        'min': 200,
        'max': 300,
        'type_distribution': {
            'rent': 0.7,        # 70% 租金
            'deposit': 0.15,    # 15% 押金
            'utility': 0.1,     # 10% 水电费
            'other': 0.05,      # 5% 其他
        },
        'status_distribution': {
            'paid': 0.6,        # 60% 已支付
            'pending': 0.2,     # 20% 待支付
            'overdue': 0.15,    # 15% 逾期
            'partial': 0.05,    # 5% 部分支付
        }
    }
}

# 测试数据
FIRST_NAMES = ['张', '李', '王', '刘', '陈', '杨', '赵', '黄', '周', '吴', '徐', '孙', '马', '朱', '胡', '郭', '何', '高', '林', '罗']
LAST_NAMES = ['伟', '芳', '娜', '敏', '静', '丽', '强', '磊', '军', '洋', '勇', '艳', '杰', '涛', '明', '超', '秀英', '俊', '刚', '平']
COMPANIES = ['科技有限公司', '贸易有限公司', '咨询有限公司', '管理有限公司', '广告有限公司', '实业有限公司', '集团有限公司']
POSITIONS = ['软件工程师', '产品经理', '运营专员', '销售代表', '财务专员', '人事专员', '市场专员', '设计师']

# 城市数据
CITY_DATA = {
    '北京': {
        'districts': ['东城区', '西城区', '朝阳区', '海淀区', '丰台区', '石景山区', '通州区', '昌平区'],
        'area_range': (40, 150),
        'rent_range': (3000, 15000),
    },
    '上海': {
        'districts': ['黄浦区', '徐汇区', '长宁区', '静安区', '普陀区', '虹口区', '杨浦区', '浦东新区'],
        'area_range': (35, 140),
        'rent_range': (3500, 16000),
    },
    '广州': {
        'districts': ['越秀区', '海珠区', '荔湾区', '天河区', '白云区', '黄埔区', '番禺区'],
        'area_range': (40, 130),
        'rent_range': (2000, 10000),
    },
    '深圳': {
        'districts': ['福田区', '罗湖区', '南山区', '盐田区', '宝安区', '龙岗区', '龙华区'],
        'area_range': (30, 120),
        'rent_range': (2500, 12000),
    }
}

# 房源描述模板
HOUSE_DESCRIPTIONS = [
    '精装修，采光好，交通便利，近地铁站',
    '南北通透，户型方正，小区环境优美',
    '全新家电，拎包入住，周边配套设施齐全',
    '安静舒适，适合居住，近商圈',
    '豪华装修，视野开阔，高品质小区',
    '简约风格，干净整洁，交通便利',
    '温馨小屋，适合单身或情侣居住',
    '宽敞明亮，家庭首选，近学校医院',
]

ROOM_NAMES = ['主卧', '次卧 A', '次卧 B', '书房', '客房', '儿童房']
ROOM_DIRECTIONS = ['南', '北', '东', '西', '东南', '东北', '西南', '西北']

# ============================================================================
# 日志配置
# ============================================================================

def setup_logging():
    """配置日志系统"""
    log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    log_file = os.path.join(log_dir, f'generate_test_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    logger = logging.getLogger('TestDataGenerator')
    logger.info(f'日志文件：{log_file}')
    
    return logger

logger = setup_logging()

# ============================================================================
# 辅助函数
# ============================================================================

def random_date(start_date, end_date):
    """生成随机日期"""
    if start_date > end_date:
        # 如果开始日期晚于结束日期，返回开始日期
        return start_date
    
    delta = end_date - start_date
    if delta.days < 0:
        return start_date
    
    random_days = random.randint(0, delta.days)
    return start_date + timedelta(days=random_days)

def random_phone():
    """生成随机手机号"""
    prefixes = ['138', '139', '130', '131', '132', '133', '134', '135', '136', '137', '150', '151', '152', '158', '159', '186', '188', '189']
    prefix = random.choice(prefixes)
    suffix = ''.join(random.choices('0123456789', k=8))
    return f'{prefix}{suffix}'

def random_id_card():
    """生成随机身份证号（简化版，仅用于测试）"""
    # 格式：6 位地区码 + 8 位生日 + 4 位随机码
    provinces = ['110000', '310000', '440000', '440300']  # 北京、上海、广东、深圳
    province = random.choice(provinces)
    birth_year = random.randint(1970, 2000)
    birth_month = random.randint(1, 12)
    birth_day = random.randint(1, 28)
    birth = f'{birth_year:04d}{birth_month:02d}{birth_day:02d}'
    suffix = ''.join(random.choices('0123456789', k=3))
    check_digit = random.choice('0123456789X')
    return f'{province[:6]}{birth}{suffix}{check_digit}'

def random_bank_card():
    """生成随机银行卡号"""
    # 简化版银行卡号生成
    prefix = random.choice(['622202', '622848', '621226', '621700'])
    suffix = ''.join(random.choices('0123456789', k=10))
    return f'{prefix}{suffix}0'

def random_email(name=None):
    """生成随机邮箱"""
    if name:
        name_pinyin = name.replace(' ', '').lower()
        domains = ['qq.com', '163.com', 'gmail.com', 'outlook.com', 'sina.com']
        return f'{name_pinyin}{random.randint(1, 999)}@{random.choice(domains)}'
    else:
        domains = ['qq.com', '163.com', 'gmail.com', 'outlook.com']
        return f'user{random.randint(1, 9999)}@{random.choice(domains)}'

def generate_name():
    """生成随机姓名"""
    return random.choice(FIRST_NAMES) + random.choice(LAST_NAMES)

# ============================================================================
# 数据清理功能
# ============================================================================

def clean_existing_data():
    """清理现有测试数据"""
    logger.info('开始清理现有数据...')
    
    try:
        # 按依赖关系逆序删除
        payment_count = Payment.query.delete()
        logger.info(f'删除支付记录：{payment_count} 条')
        
        contract_count = Contract.query.delete()
        logger.info(f'删除合同：{contract_count} 份')
        
        tenant_count = Tenant.query.delete()
        logger.info(f'删除租客：{tenant_count} 个')
        
        room_count = Room.query.delete()
        logger.info(f'删除房间：{room_count} 个')
        
        house_count = House.query.delete()
        logger.info(f'删除房源：{house_count} 套')
        
        landlord_count = Landlord.query.delete()
        logger.info(f'删除房东：{landlord_count} 个')
        
        # 删除普通用户（保留管理员）
        user_count = User.query.filter(User.role != 'admin').delete()
        logger.info(f'删除普通用户：{user_count} 个')
        
        db.session.commit()
        logger.info('数据清理完成')
        
        return True
    except Exception as e:
        db.session.rollback()
        logger.error(f'数据清理失败：{str(e)}')
        return False

# ============================================================================
# 数据生成函数
# ============================================================================

def generate_users():
    """生成用户数据"""
    logger.info('开始生成用户数据...')
    
    num_users = random.randint(CONFIG['user']['min'], CONFIG['user']['max'])
    num_admins = max(1, int(num_users * CONFIG['user']['admin_ratio']))
    num_staff = num_users - num_admins
    
    users = []
    
    # 检查是否已有管理员
    existing_admins = User.query.filter_by(role='admin').all()
    start_admin_index = len(existing_admins)
    
    # 生成管理员
    for i in range(num_admins):
        if i < start_admin_index:
            # 已存在的管理员
            users.append(existing_admins[i])
            continue
            
        username = f'admin_{i+1}' if i > 0 else 'admin'
        
        # 检查用户名是否已存在
        if User.query.filter_by(username=username).first():
            logger.warning(f'  管理员 {username} 已存在，跳过')
            continue
        
        user = User(
            username=username,
            email=f'{username}{random.randint(1, 999)}@example.com',  # 避免邮箱冲突
            role='admin',
            user_type='admin',
            name=generate_name(),
            phone=random_phone(),
            position='管理员'
        )
        user.set_password('Admin@123')
        users.append(user)
        logger.info(f'  创建管理员：{username}')
    
    # 生成普通员工
    existing_staff_count = User.query.filter_by(role='staff').count()
    for i in range(num_staff):
        index = existing_staff_count + i + 1
        username = f'staff_{index:03d}'
        
        # 检查用户名是否已存在
        if User.query.filter_by(username=username).first():
            logger.warning(f'  员工 {username} 已存在，跳过')
            continue
        
        user = User(
            username=username,
            email=f'{username}{random.randint(1, 999)}@example.com',  # 避免邮箱冲突
            role='staff',
            user_type='staff',
            name=generate_name(),
            phone=random_phone(),
            id_card=random_id_card(),
            position=random.choice(POSITIONS),
            status='active'
        )
        user.set_password('Staff@123')
        users.append(user)
        logger.info(f'  创建员工：{username} - {user.position}')
    
    # 批量添加到数据库（只添加新创建的用户）
    new_users = [u for u in users if u.id is None]
    for user in new_users:
        db.session.add(user)
    
    try:
        db.session.commit()
        logger.info(f'用户数据生成完成：共 {len(users)} 个用户（管理员{len([u for u in users if u.role == "admin"])}个，员工{len([u for u in users if u.role == "staff"])}个）')
        return users
    except Exception as e:
        db.session.rollback()
        logger.error(f'用户数据生成失败：{str(e)}')
        return []

def generate_landlords():
    """生成房东数据"""
    logger.info('开始生成房东数据...')
    
    num_landlords = random.randint(CONFIG['landlord']['min'], CONFIG['landlord']['max'])
    landlords = []
    
    for i in range(num_landlords):
        name = generate_name()
        landlord = Landlord(
            name=name,
            phone=random_phone(),
            bank_name=random.choice(['中国工商银行', '中国建设银行', '中国农业银行', '中国银行', '招商银行', '交通银行']),
            property_cert_no=f'房产证{random.randint(100000, 999999)}号',
            status=random.choice(['active'] * 9 + ['inactive']),  # 90% 正常
            remark=f'测试房东{i+1}'
        )
        
        # 加密敏感信息
        landlord.set_id_card(random_id_card())
        landlord.set_bank_card(random_bank_card())
        
        landlords.append(landlord)
        logger.info(f'  创建房东：{name} - {landlord.phone}')
    
    # 批量添加
    for landlord in landlords:
        db.session.add(landlord)
    
    try:
        db.session.commit()
        logger.info(f'房东数据生成完成：共 {len(landlords)} 个房东')
        return landlords
    except Exception as e:
        db.session.rollback()
        logger.error(f'房东数据生成失败：{str(e)}')
        return []

def generate_houses(users, landlords):
    """生成房源数据"""
    logger.info('开始生成房源数据...')
    
    num_houses = random.randint(CONFIG['house']['min'], CONFIG['house']['max'])
    num_whole = int(num_houses * CONFIG['house']['whole_rent_ratio'])
    num_shared = num_houses - num_whole
    
    houses = []
    
    # 确保有足够的员工和房东
    if not users or not landlords:
        logger.error('员工或房东数据为空，无法生成房源')
        return []
    
    for i in range(num_houses):
        # 随机选择城市和区县
        city = random.choice(list(CITY_DATA.keys()))
        city_info = CITY_DATA[city]
        district = random.choice(city_info['districts'])
        
        # 确定租赁类型
        rental_type = 'whole' if i < num_whole else 'shared'
        
        # 生成面积和租金
        area = random.randint(city_info['area_range'][0], city_info['area_range'][1])
        rent_price = random.randint(city_info['rent_range'][0], city_info['rent_range'][1])
        
        # 调整合租价格
        if rental_type == 'shared':
            rent_price = int(rent_price * 0.6)  # 合租价格为整租的 60%
        
        house = House(
            title=f'{city}{district}{random.choice(["精装", "豪华", "温馨", "简约", "现代"])}{random.choice(["一居", "两居", "三居", "四居"])}',
            description=random.choice(HOUSE_DESCRIPTIONS),
            province=city,
            city=city,
            district=district,
            address=f'{district}街道{random.randint(1, 999)}号',
            area=area,
            room_count=random.randint(1, 4),
            hall_count=random.randint(1, 2),
            bathroom_count=random.randint(1, 2),
            floor=f'{random.randint(1, 20)}层',
            total_floors=random.randint(6, 30),
            rent_price=rent_price,
            deposit=random.randint(3000, 10000),
            payment_method=random.choice(['押一付三', '押一付一', '半年付', '年付']),
            rental_type=rental_type,
            status='available',
            facilities={
                'wifi': random.choice([True, False]),
                'ac': random.choice([True, False]),
                'heater': random.choice([True, False]),
                'washing_machine': random.choice([True, False]),
                'refrigerator': random.choice([True, False]),
            },
            owner_id=random.choice(users).id,
            landlord_id=random.choice(landlords).id,
            contact_name=generate_name(),
            contact_phone=random_phone(),
            contact_wechat=f'wx{random.randint(10000, 99999)}'
        )
        
        houses.append(house)
        logger.info(f'  创建房源：{house.title} - {city}{district} - {rental_type} - ¥{rent_price}/月')
    
    # 批量添加
    for house in houses:
        db.session.add(house)
    
    try:
        db.session.commit()
        logger.info(f'房源数据生成完成：共 {len(houses)} 套房源（整租{num_whole}套，合租{num_shared}套）')
        return houses
    except Exception as e:
        db.session.rollback()
        logger.error(f'房源数据生成失败：{str(e)}')
        return []

def generate_rooms(houses):
    """为合租房源生成房间数据"""
    logger.info('开始生成房间数据...')
    
    # 筛选合租房源
    shared_houses = [h for h in houses if h.rental_type == 'shared']
    
    if not shared_houses:
        logger.warning('没有合租房源，跳过房间生成')
        return []
    
    rooms = []
    
    for house in shared_houses:
        num_rooms = random.randint(CONFIG['room']['min_per_house'], CONFIG['room']['max_per_house'])
        
        for i in range(num_rooms):
            room = Room(
                house_id=house.id,
                room_number=f'{i+1:02d}',
                name=ROOM_NAMES[i % len(ROOM_NAMES)],
                description=f'{house.district}合租房源 - {ROOM_NAMES[i % len(ROOM_NAMES)]}',
                area=random.randint(10, 30),
                floor=house.floor,
                direction=random.choice(ROOM_DIRECTIONS),
                rent_price=int(house.rent_price / num_rooms * random.uniform(0.8, 1.2)),
                deposit=random.randint(1000, 3000),
                facilities={
                    'bed': True,
                    'desk': random.choice([True, False]),
                    'wardrobe': random.choice([True, False]),
                    'ac': random.choice([True, False]),
                },
                status='available'
            )
            rooms.append(room)
            logger.info(f'  创建房间：{house.title} - {room.name} - ¥{room.rent_price}/月')
    
    # 批量添加
    for room in rooms:
        db.session.add(room)
    
    try:
        db.session.commit()
        logger.info(f'房间数据生成完成：共 {len(rooms)} 个房间')
        return rooms
    except Exception as e:
        db.session.rollback()
        logger.error(f'房间数据生成失败：{str(e)}')
        return []

def generate_tenants():
    """生成租客数据"""
    logger.info('开始生成租客数据...')
    
    num_tenants = random.randint(CONFIG['tenant']['min'], CONFIG['tenant']['max'])
    tenants = []
    
    for i in range(num_tenants):
        name = generate_name()
        tenant = Tenant(
            name=name,
            phone=random_phone(),
            email=random_email(name),
            emergency_contact=generate_name(),
            emergency_phone=random_phone(),
            emergency_relation=random.choice(['父亲', '母亲', '配偶', '兄弟姐妹']),
            company=random.choice(COMPANIES),
            occupation=random.choice(POSITIONS),
            status=random.choice(['active'] * 9 + ['expired']),  # 90% 在租
            remark=f'测试租客{i+1}'
        )
        
        # 加密身份证号
        tenant.set_id_card(random_id_card())
        
        tenants.append(tenant)
        logger.info(f'  创建租客：{name} - {tenant.phone} - {tenant.occupation}')
    
    # 批量添加
    for tenant in tenants:
        db.session.add(tenant)
    
    try:
        db.session.commit()
        logger.info(f'租客数据生成完成：共 {len(tenants)} 个租客')
        return tenants
    except Exception as e:
        db.session.rollback()
        logger.error(f'租客数据生成失败：{str(e)}')
        return []

def generate_contracts(houses, rooms, tenants):
    """生成合同数据"""
    logger.info('开始生成合同数据...')
    
    num_contracts = random.randint(CONFIG['contract']['min'], CONFIG['contract']['max'])
    
    if not houses or not tenants:
        logger.error('房源或租客数据为空，无法生成合同')
        return []
    
    # 创建房间查找字典
    room_dict = {}
    for room in rooms:
        if room.house_id not in room_dict:
            room_dict[room.house_id] = []
        room_dict[room.house_id].append(room)
    
    contracts = []
    status_dist = CONFIG['contract']['status_distribution']
    
    for i in range(num_contracts):
        # 随机选择房源和租客
        house = random.choice(houses)
        tenant = random.choice(tenants)
        
        # 确定房间（如果是合租）
        room = None
        rent_amount = house.rent_price
        
        if house.rental_type == 'shared' and house.id in room_dict and room_dict[house.id]:
            room = random.choice(room_dict[house.id])
            rent_amount = room.rent_price
        
        # 生成合同日期
        start_date = random_date(date.today() - timedelta(days=365), date.today() + timedelta(days=30))
        contract_duration = random.randint(6, 24)  # 6-24 个月
        end_date = start_date + timedelta(days=contract_duration * 30)
        
        # 确定合同状态
        rand = random.random()
        if rand < status_dist['active']:
            status = 'active'
        elif rand < status_dist['active'] + status_dist['expired']:
            status = 'expired'
            end_date = date.today() - timedelta(days=random.randint(1, 180))
        elif rand < status_dist['active'] + status_dist['expired'] + status_dist['draft']:
            status = 'draft'
        else:
            status = 'terminated'
        
        contract = Contract(
            contract_no=Contract.generate_contract_no(),
            title=f'{house.city}{house.district}租赁合同',
            description=f'{house.title}租赁合同',
            start_date=start_date,
            end_date=end_date,
            rent_amount=rent_amount,
            deposit_amount=house.deposit,
            payment_type=random.choice(['月付', '季付', '半年付', '年付']),
            payment_cycle=random.choice([1, 3, 6, 12]),
            status=status,
            house_id=house.id,
            room_id=room.id if room else None,
            tenant_id=tenant.id,
            remark=f'测试合同{i+1}'
        )
        
        contracts.append(contract)
        logger.info(f'  创建合同：{contract.contract_no} - {house.title} - {tenant.name} - {status} - ¥{rent_amount}/月')
    
    # 批量添加
    for contract in contracts:
        db.session.add(contract)
    
    try:
        db.session.commit()
        logger.info(f'合同数据生成完成：共 {len(contracts)} 份合同')
        return contracts
    except Exception as e:
        db.session.rollback()
        logger.error(f'合同数据生成失败：{str(e)}')
        return []

def generate_payments(contracts, users):
    """生成支付记录"""
    logger.info('开始生成支付记录...')
    
    num_payments = random.randint(CONFIG['payment']['min'], CONFIG['payment']['max'])
    
    if not contracts:
        logger.error('合同数据为空，无法生成支付记录')
        return []
    
    if not users:
        logger.error('用户数据为空，无法生成支付记录')
        return []
    
    payments = []
    type_dist = CONFIG['payment']['type_distribution']
    status_dist = CONFIG['payment']['status_distribution']
    
    for i in range(num_payments):
        contract = random.choice(contracts)
        
        # 确定支付类型
        rand = random.random()
        if rand < type_dist['rent']:
            payment_type = 'rent'
        elif rand < type_dist['rent'] + type_dist['deposit']:
            payment_type = 'deposit'
        elif rand < type_dist['rent'] + type_dist['deposit'] + type_dist['utility']:
            payment_type = 'utility'
        else:
            payment_type = 'other'
        
        # 生成支付周期
        # 确保 start_date <= end_date
        effective_start = contract.start_date
        effective_end = min(contract.end_date, date.today())
        
        if effective_start > effective_end:
            # 如果合同已结束，使用合同结束日期作为基准
            effective_end = contract.end_date
            effective_start = max(contract.start_date, contract.end_date - timedelta(days=30))
        
        period_start = random_date(effective_start, effective_end)
        period_end = period_start + timedelta(days=30)
        
        # 确定到期日期
        due_date = period_start + timedelta(days=5)
        
        # 确定支付状态
        rand = random.random()
        if rand < status_dist['paid']:
            status = 'paid'
            # 支付日期在周期开始和今天之间
            payment_end = min(date.today(), period_end)
            if payment_end >= period_start:
                payment_date = random_date(period_start, payment_end)
            else:
                payment_date = period_start
            paid_amount = contract.rent_amount
        elif rand < status_dist['paid'] + status_dist['pending']:
            status = 'pending'
            payment_date = None
            paid_amount = 0
        elif rand < status_dist['paid'] + status_dist['pending'] + status_dist['overdue']:
            status = 'overdue'
            payment_date = None
            paid_amount = 0
            # 逾期记录需要设置较早的到期日期
            due_date = date.today() - timedelta(days=random.randint(1, 90))
        else:
            status = 'partial'
            # 部分支付日期在周期开始和今天之间
            payment_end = min(date.today(), period_end)
            if payment_end >= period_start:
                payment_date = random_date(period_start, payment_end)
            else:
                payment_date = period_start
            paid_amount = contract.rent_amount * random.uniform(0.3, 0.8)
        
        payment = Payment(
            payment_no=Payment.generate_payment_no(),
            amount=contract.rent_amount,
            paid_amount=paid_amount,
            payment_type=payment_type,
            payment_method=random.choice(['cash', 'bank', 'wechat', 'alipay']) if payment_date else None,
            period_start=period_start,
            period_end=period_end,
            payment_date=payment_date,
            due_date=due_date,
            confirmed_date=datetime.now() if status == 'paid' else None,
            status=status,
            contract_id=contract.id,
            operator_id=random.choice(users).id if users else None,
            remark=f'测试支付{i+1}'
        )
        
        # 计算滞纳金（针对逾期记录）
        if status in ['overdue', 'partial']:
            late_fee, overdue_days = payment.calculate_late_fee()
            payment.late_fee = late_fee
            payment.overdue_days = overdue_days
        
        payments.append(payment)
        logger.info(f'  创建支付：{payment.payment_no} - {payment_type} - ¥{payment.amount} - {status}' +
                   (f' - 滞纳金¥{payment.late_fee:.2f}' if payment.late_fee and payment.late_fee > 0 else ''))
    
    # 批量添加
    for payment in payments:
        db.session.add(payment)
    
    try:
        db.session.commit()
        logger.info(f'支付记录生成完成：共 {len(payments)} 条支付记录')
        return payments
    except Exception as e:
        db.session.rollback()
        logger.error(f'支付记录生成失败：{str(e)}')
        return []

def update_house_status():
    """更新房源状态（基于合同状态）"""
    logger.info('开始更新房源状态...')
    
    houses = House.query.all()
    updated_count = 0
    
    for house in houses:
        old_status = house.status
        new_status = house.update_status()
        
        if old_status != new_status:
            updated_count += 1
            logger.info(f'  更新房源状态：{house.title} - {old_status} -> {new_status}')
    
    try:
        db.session.commit()
        logger.info(f'房源状态更新完成：共更新 {updated_count} 套房源')
        return updated_count
    except Exception as e:
        db.session.rollback()
        logger.error(f'房源状态更新失败：{str(e)}')
        return 0

def verify_data_integrity():
    """验证数据一致性"""
    logger.info('开始验证数据一致性...')
    
    issues = []
    
    # 验证房源与房间关系
    shared_houses = House.query.filter_by(rental_type='shared').all()
    for house in shared_houses:
        room_count = house.rooms.count()
        if room_count == 0:
            issues.append(f'合租房源 {house.id} 没有房间')
    
    # 验证合同与房源/房间关系
    contracts = Contract.query.all()
    for contract in contracts:
        if not contract.house:
            issues.append(f'合同 {contract.contract_no} 没有关联房源')
        if not contract.tenant_rel:
            issues.append(f'合同 {contract.contract_no} 没有关联租客')
        if contract.room_id and not contract.room:
            issues.append(f'合同 {contract.contract_no} 关联了不存在的房间 {contract.room_id}')
    
    # 验证支付与合同关系
    payments = Payment.query.all()
    for payment in payments:
        if not payment.contract_rel:
            issues.append(f'支付 {payment.payment_no} 没有关联合同')
    
    # 报告结果
    if issues:
        logger.warning(f'发现 {len(issues)} 个数据一致性问题:')
        for issue in issues[:10]:  # 只显示前 10 个
            logger.warning(f'  - {issue}')
        if len(issues) > 10:
            logger.warning(f'  ... 还有 {len(issues) - 10} 个问题')
    else:
        logger.info('数据一致性验证通过，未发现问题')
    
    return len(issues) == 0

def generate_statistics():
    """生成统计报告"""
    logger.info('生成统计报告...')
    
    stats = {
        'users': User.query.count(),
        'landlords': Landlord.query.count(),
        'houses': House.query.count(),
        'rooms': Room.query.count(),
        'tenants': Tenant.query.count(),
        'contracts': Contract.query.count(),
        'payments': Payment.query.count(),
    }
    
    # 详细统计
    stats['houses_by_city'] = {}
    for city in CITY_DATA.keys():
        stats['houses_by_city'][city] = House.query.filter_by(city=city).count()
    
    stats['houses_by_rental_type'] = {
        'whole': House.query.filter_by(rental_type='whole').count(),
        'shared': House.query.filter_by(rental_type='shared').count(),
    }
    
    stats['contracts_by_status'] = {
        'active': Contract.query.filter_by(status='active').count(),
        'expired': Contract.query.filter_by(status='expired').count(),
        'draft': Contract.query.filter_by(status='draft').count(),
        'terminated': Contract.query.filter_by(status='terminated').count(),
    }
    
    stats['payments_by_status'] = {
        'paid': Payment.query.filter_by(status='paid').count(),
        'pending': Payment.query.filter_by(status='pending').count(),
        'overdue': Payment.query.filter_by(status='overdue').count(),
        'partial': Payment.query.filter_by(status='partial').count(),
    }
    
    stats['payments_by_type'] = {
        'rent': Payment.query.filter_by(payment_type='rent').count(),
        'deposit': Payment.query.filter_by(payment_type='deposit').count(),
        'utility': Payment.query.filter_by(payment_type='utility').count(),
        'other': Payment.query.filter_by(payment_type='other').count(),
    }
    
    # 计算总金额
    stats['total_rent'] = Payment.query.filter_by(payment_type='rent').with_entities(db.func.sum(Payment.amount)).scalar() or 0
    stats['total_paid'] = Payment.query.filter_by(status='paid').with_entities(db.func.sum(Payment.paid_amount)).scalar() or 0
    stats['total_late_fee'] = Payment.query.with_entities(db.func.sum(Payment.late_fee)).scalar() or 0
    
    return stats

def print_statistics(stats):
    """打印统计报告"""
    print('\n' + '=' * 80)
    print('测试数据生成统计报告'.center(80))
    print('=' * 80)
    
    print(f'\n【基础数据】')
    print(f'  用户数：{stats["users"]} 个')
    print(f'  房东数：{stats["landlords"]} 个')
    print(f'  房源数：{stats["houses"]} 套')
    print(f'  房间数：{stats["rooms"]} 个')
    print(f'  租客数：{stats["tenants"]} 个')
    print(f'  合同数：{stats["contracts"]} 份')
    print(f'  支付记录数：{stats["payments"]} 条')
    
    print(f'\n【房源分布 - 城市】')
    for city, count in stats['houses_by_city'].items():
        print(f'  {city}: {count} 套')
    
    print(f'\n【房源分布 - 租赁类型】')
    print(f'  整租：{stats["houses_by_rental_type"]["whole"]} 套')
    print(f'  合租：{stats["houses_by_rental_type"]["shared"]} 套')
    
    print(f'\n【合同状态分布】')
    for status, count in stats['contracts_by_status'].items():
        status_name = {'active': '生效中', 'expired': '已过期', 'draft': '草稿', 'terminated': '已终止'}
        print(f'  {status_name.get(status, status)}: {count} 份')
    
    print(f'\n【支付状态分布】')
    for status, count in stats['payments_by_status'].items():
        status_name = {'paid': '已支付', 'pending': '待支付', 'overdue': '逾期', 'partial': '部分支付'}
        print(f'  {status_name.get(status, status)}: {count} 条')
    
    print(f'\n【支付类型分布】')
    for ptype, count in stats['payments_by_type'].items():
        type_name = {'rent': '租金', 'deposit': '押金', 'utility': '水电费', 'other': '其他'}
        print(f'  {type_name.get(ptype, ptype)}: {count} 条')
    
    print(f'\n【金额统计】')
    print(f'  总租金：¥{stats["total_rent"]:,.2f}')
    print(f'  总实收：¥{stats["total_paid"]:,.2f}')
    print(f'  总滞纳金：¥{stats["total_late_fee"]:,.2f}')
    
    print('\n' + '=' * 80)

def print_test_accounts(users):
    """打印测试账号信息"""
    print('\n' + '=' * 80)
    print('测试账号信息'.center(80))
    print('=' * 80)
    
    print(f'\n【管理员账号】')
    admins = [u for u in users if u.role == 'admin']
    for admin in admins:
        print(f'  用户名：{admin.username:15} 密码：Admin@123  姓名：{admin.name}')
    
    print(f'\n【员工账号（前 5 个）】')
    staffs = [u for u in users if u.role == 'staff'][:5]
    for staff in staffs:
        print(f'  用户名：{staff.username:15} 密码：Staff@123  职位：{staff.position}')
    
    if len(staffs) < len([u for u in users if u.role == 'staff']):
        print(f'  ... 共 {len([u for u in users if u.role == "staff"])} 个员工账号，详见数据库')
    
    print('\n' + '=' * 80)
    print('提示：所有账号的初始密码已在上方列出，请及时修改密码')
    print('=' * 80 + '\n')

# ============================================================================
# 主函数
# ============================================================================

def main():
    """主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='测试数据生成脚本')
    parser.add_argument('--no-clean', action='store_true', help='不清理旧数据')
    parser.add_argument('--clean-only', action='store_true', help='仅清理数据，不生成')
    args = parser.parse_args()
    
    print('\n' + '=' * 80)
    print('房屋租赁系统 - 测试数据生成器'.center(80))
    print('=' * 80)
    
    # 创建应用上下文
    app = create_app(os.getenv('FLASK_ENV', 'development'))
    
    with app.app_context():
        logger.info('应用上下文创建成功')
        
        # 清理旧数据
        if not args.no_clean:
            if not clean_existing_data():
                logger.error('数据清理失败，终止执行')
                return 1
        else:
            logger.info('跳过数据清理（--no-clean 参数）')
        
        # 仅清理模式
        if args.clean_only:
            logger.info('仅清理模式，执行完成')
            return 0
        
        # 生成数据
        users = generate_users()
        if not users:
            logger.error('用户数据生成失败，终止执行')
            return 1
        
        landlords = generate_landlords()
        if not landlords:
            logger.error('房东数据生成失败，终止执行')
            return 1
        
        houses = generate_houses(users, landlords)
        if not houses:
            logger.error('房源数据生成失败，终止执行')
            return 1
        
        rooms = generate_rooms(houses)
        tenants = generate_tenants()
        if not tenants:
            logger.error('租客数据生成失败，终止执行')
            return 1
        
        contracts = generate_contracts(houses, rooms, tenants)
        if not contracts:
            logger.error('合同数据生成失败，终止执行')
            return 1
        
        payments = generate_payments(contracts, users)
        if not payments:
            logger.error('支付记录生成失败，终止执行')
            return 1
        
        # 更新房源状态
        update_house_status()
        
        # 验证数据一致性
        verify_data_integrity()
        
        # 生成并打印统计报告
        stats = generate_statistics()
        print_statistics(stats)
        
        # 打印测试账号
        print_test_accounts(users)
        
        logger.info('测试数据生成完成！')
        
        return 0

if __name__ == '__main__':
    sys.exit(main())
