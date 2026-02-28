"""
数据库模型使用示例

本文件展示如何正确使用房屋租赁系统的数据库模型
"""
from datetime import datetime, date, timedelta
from decimal import Decimal
from app import create_app, db
from app.models import User, House, Room, Tenant, Contract, Payment, Media


def example_user_operations():
    """用户模型操作示例"""
    print("=" * 50)
    print("用户模型操作示例")
    print("=" * 50)
    
    # 创建管理员用户
    admin = User(
        username='admin',
        email='admin@example.com',
        phone='13800138000',
        role='admin',  # 管理员角色
        real_name='张管理员',
        department='管理部'
    )
    admin.set_password('admin123')
    db.session.add(admin)
    
    # 创建普通员工用户
    staff = User(
        username='staff001',
        email='staff@example.com',
        phone='13900139000',
        role='staff',  # 普通员工角色
        real_name='李员工',
        department='业务部'
    )
    staff.set_password('staff123')
    db.session.add(staff)
    
    # 权限检查
    print(f"管理员是否有删除权限：{admin.has_permission('delete')}")  # True
    print(f"普通员工是否有删除权限：{staff.has_permission('delete')}")  # False
    print(f"普通员工是否有查看权限：{staff.has_permission('view')}")  # True
    
    db.session.commit()
    return admin, staff


def example_house_and_room_operations():
    """房源和房间模型操作示例"""
    print("\n" + "=" * 50)
    print("房源和房间模型操作示例")
    print("=" * 50)
    
    # 获取管理员用户
    admin = User.query.filter_by(username='admin').first()
    
    # 创建整租房源
    house_whole = House(
        title='阳光花园整租两居室',
        description='精装修，拎包入住',
        province='北京市',
        city='北京市',
        district='朝阳区',
        address='阳光花园小区 1 号楼 2 单元 301',
        area=80.0,
        room_count=2,
        hall_count=1,
        bathroom_count=1,
        rent_price=8000.0,
        deposit=8000.0,
        payment_method='押一付三',
        rental_type='whole',  # 整租
        owner_id=admin.id,
        facilities={'wifi': True, 'ac': True, 'heater': True, 'washing_machine': True}
    )
    db.session.add(house_whole)
    
    # 创建合租房源
    house_shared = House(
        title='科技园区合租公寓',
        description='近地铁，交通便利',
        province='北京市',
        city='北京市',
        district='海淀区',
        address='科技园区 5 号楼 3 单元 502',
        area=120.0,
        room_count=3,
        hall_count=1,
        bathroom_count=2,
        rent_price=12000.0,  # 总租金
        deposit=6000.0,
        payment_method='押一付三',
        rental_type='shared',  # 合租
        owner_id=admin.id,
        facilities={'wifi': True, 'ac': True, 'kitchen': True, 'balcony': True}
    )
    db.session.add(house_shared)
    
    # 为合租房源添加房间
    room1 = Room(
        room_number='101',
        name='主卧',
        description='带独立卫生间，朝南',
        area=25.0,
        floor='5 层',
        direction='南',
        rent_price=4500.0,
        deposit=4500.0,
        facilities={'bed': True, 'desk': True, 'ac': True, 'private_bathroom': True},
        status='available',
        house_id=house_shared.id
    )
    db.session.add(room1)
    
    room2 = Room(
        room_number='102',
        name='次卧 A',
        description='次卧，朝北',
        area=18.0,
        floor='5 层',
        direction='北',
        rent_price=3500.0,
        deposit=3500.0,
        facilities={'bed': True, 'desk': True, 'ac': True},
        status='available',
        house_id=house_shared.id
    )
    db.session.add(room2)
    
    room3 = Room(
        room_number='103',
        name='次卧 B',
        description='小次卧，朝东',
        area=15.0,
        floor='5 层',
        direction='东',
        rent_price=3000.0,
        deposit=3000.0,
        facilities={'bed': True, 'desk': True},
        status='available',
        house_id=house_shared.id
    )
    db.session.add(room3)
    
    db.session.commit()
    
    # 更新房源状态
    house_shared.update_status()
    print(f"合租房源当前状态：{house_shared.status}")  # available
    print(f"房源房间数量：{house_shared.get_room_count()}")
    print(f"空闲房间数量：{len(house_shared.get_available_rooms())}")
    
    return house_whole, house_shared


def example_tenant_operations():
    """租客模型操作示例"""
    print("\n" + "=" * 50)
    print("租客模型操作示例")
    print("=" * 50)
    
    # 创建租客
    tenant = Tenant(
        name='王小明',
        phone='13700137000',
        email='wang@example.com',
        emergency_contact='王大明',
        emergency_phone='13600136000',
        emergency_relation='父亲',
        company='某某科技公司',
        occupation='工程师'
    )
    # 设置身份证号（会自动生成哈希）
    tenant.set_id_card('110101199001011234')
    db.session.add(tenant)
    
    db.session.commit()
    
    # 验证身份证号
    is_valid = tenant.verify_id_card('110101199001011234')
    print(f"身份证号验证：{is_valid}")  # True
    
    # 获取租客当前租住的房源
    current_houses = tenant.get_current_houses()
    print(f"当前租住房源数量：{len(current_houses)}")
    
    return tenant


def example_contract_operations(tenant, house, room=None):
    """合同模型操作示例"""
    print("\n" + "=" * 50)
    print("合同模型操作示例")
    print("=" * 50)
    
    # 获取房东
    landlord = User.query.filter_by(username='admin').first()
    
    # 创建租赁合同
    contract = Contract(
        contract_no=Contract.generate_contract_no(),
        title='房屋租赁合同',
        description='正规租赁合同，双方遵守',
        start_date=date.today(),
        end_date=date.today() + timedelta(days=365),
        rent_amount=room.rent_price if room else house.rent_price,
        deposit_amount=room.deposit if room else house.deposit,
        payment_type='月付',
        payment_cycle=1,
        status='active',
        house_id=house.id,
        room_id=room.id if room else None,  # 合租时填写房间 ID
        landlord_id=landlord.id,
        tenant_id=tenant.id
    )
    db.session.add(contract)
    db.session.commit()
    
    # 如果是合租，更新房间状态
    if room:
        room.status = 'rented'
        house.update_status()
    
    # 合同信息
    print(f"合同编号：{contract.contract_no}")
    print(f"合同是否过期：{contract.is_expired()}")
    print(f"合同是否即将到期：{contract.is_expiring_soon()}")
    print(f"距离到期天数：{contract.get_days_until_expiry()}")
    print(f"合同总租金：{contract.calculate_total_rent()}")
    
    return contract


def example_payment_operations(contract):
    """支付模型操作示例"""
    print("\n" + "=" * 50)
    print("支付模型操作示例")
    print("=" * 50)
    
    # 创建租金支付记录
    payment = Payment(
        payment_no=Payment.generate_payment_no(),
        amount=contract.rent_amount,
        payment_type='rent',
        payment_method='alipay',
        period_start=contract.start_date,
        period_end=contract.start_date + timedelta(days=30),
        due_date=contract.start_date + timedelta(days=7),  # 7 天内缴费
        status='pending',
        contract_id=contract.id
    )
    db.session.add(payment)
    db.session.commit()
    
    # 计算滞纳金
    late_fee, overdue_days = payment.calculate_late_fee()
    print(f"当前滞纳金：{late_fee}")
    print(f"逾期天数：{overdue_days}")
    print(f"应缴总额：{payment.get_total_amount()}")
    
    # 标记为已支付
    payment.mark_as_paid(
        paid_amount=payment.get_total_amount(),
        payment_method='alipay'
    )
    db.session.commit()
    
    print(f"支付状态：{payment.status}")
    
    return payment


def example_media_operations(house):
    """多媒体文件模型操作示例"""
    print("\n" + "=" * 50)
    print("多媒体文件模型操作示例")
    print("=" * 50)
    
    # 获取上传用户
    user = User.query.filter_by(username='admin').first()
    
    # 创建媒体文件记录
    media1 = Media(
        file_name='living_room.jpg',
        file_path='/uploads/houses/1/living_room.jpg',
        file_url='http://localhost:5000/uploads/houses/1/living_room.jpg',
        file_type='image',
        mime_type='image/jpeg',
        file_size=2048000,  # 2MB
        description='客厅照片',
        sort_order=1,
        is_cover=True,
        house_id=house.id,
        uploaded_by=user.id
    )
    db.session.add(media1)
    
    media2 = Media(
        file_name='bedroom.jpg',
        file_path='/uploads/houses/1/bedroom.jpg',
        file_url='http://localhost:5000/uploads/houses/1/bedroom.jpg',
        file_type='image',
        mime_type='image/jpeg',
        file_size=1536000,
        description='卧室照片',
        sort_order=2,
        house_id=house.id,
        uploaded_by=user.id
    )
    db.session.add(media2)
    
    db.session.commit()
    
    print(f"文件大小：{media1.get_file_size_formatted()}")
    print(f"房源媒体文件数量：{house.media.count()}")
    
    return media1, media2


def run_all_examples():
    """运行所有示例"""
    app = create_app()
    
    with app.app_context():
        # 创建所有表
        db.create_all()
        
        # 运行示例
        admin, staff = example_user_operations()
        house_whole, house_shared = example_house_and_room_operations()
        tenant = example_tenant_operations()
        contract = example_contract_operations(tenant, house_shared, room=house_shared.rooms.first())
        payment = example_payment_operations(contract)
        media1, media2 = example_media_operations(house_whole)
        
        print("\n" + "=" * 50)
        print("所有示例运行完成！")
        print("=" * 50)


if __name__ == '__main__':
    run_all_examples()
