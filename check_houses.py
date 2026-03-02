from app import create_app
from app.models.house import House
from app.models.room import Room

app = create_app()

with app.app_context():
    print('合租房源数量:', House.query.filter_by(rental_type='shared').count())
    print('房间数量:', Room.query.count())
    print('合租房源详情:')
    for house in House.query.filter_by(rental_type='shared').all():
        print(f'  ID: {house.id}, 标题: {house.title}, 房间数: {house.rooms.count()}')
        for room in house.rooms.all():
            print(f'    房间: {room.room_number}, 状态: {room.status}')
