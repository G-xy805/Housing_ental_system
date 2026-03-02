"""
验证测试数据脚本
用于检查生成的测试数据是否符合规格要求
"""
import sys
import os

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

def verify_data():
    """验证测试数据"""
    app = create_app()
    
    with app.app_context():
        print("\n" + "="*60)
        print("测试数据验证报告")
        print("="*60)
        
        # 用户统计
        total_users = User.query.count()
        admin_users = User.query.filter_by(role='admin').count()
        staff_users = User.query.filter_by(role='staff').count()
        
        print(f"\n【用户数据】")
        print(f"  总数：{total_users} (规格：5-10)")
        print(f"  管理员：{admin_users} (规格：1-2)")
        print(f"  普通员工：{staff_users} (规格：3-8)")
        print(f"  ✓ 符合要求" if 5 <= total_users <= 10 and 1 <= admin_users <= 2 else "  ✗ 不符合要求")
        
        # 房东统计
        total_landlords = Landlord.query.count()
        print(f"\n【房东数据】")
        print(f"  总数：{total_landlords} (规格：10-20)")
        print(f"  ✓ 符合要求" if 10 <= total_landlords <= 20 else "  ✗ 不符合要求")
        
        # 房源统计
        total_houses = House.query.count()
        whole_houses = House.query.filter_by(rental_type='whole').count()
        shared_houses = House.query.filter_by(rental_type='shared').count()
        
        whole_pct = (whole_houses / total_houses * 100) if total_houses > 0 else 0
        shared_pct = (shared_houses / total_houses * 100) if total_houses > 0 else 0
        
        print(f"\n【房源数据】")
        print(f"  总数：{total_houses} (规格：30-50)")
        print(f"  整租：{whole_houses} ({whole_pct:.1f}%) (规格：~60%)")
        print(f"  合租：{shared_houses} ({shared_pct:.1f}%) (规格：~40%)")
        
        # 城市分布
        beijing = House.query.filter_by(city='北京').count()
        shanghai = House.query.filter_by(city='上海').count()
        guangzhou = House.query.filter_by(city='广州').count()
        shenzhen = House.query.filter_by(city='深圳').count()
        
        print(f"\n  城市分布:")
        print(f"    北京：{beijing} ({beijing/total_houses*100 if total_houses > 0 else 0:.1f}%) (规格：~40%)")
        print(f"    上海：{shanghai} ({shanghai/total_houses*100 if total_houses > 0 else 0:.1f}%) (规格：~30%)")
        print(f"    广州：{guangzhou} ({guangzhou/total_houses*100 if total_houses > 0 else 0:.1f}%) (规格：~15%)")
        print(f"    深圳：{shenzhen} ({shenzhen/total_houses*100 if total_houses > 0 else 0:.1f}%) (规格：~15%)")
        
        print(f"  ✓ 符合要求" if 30 <= total_houses <= 50 else "  ✗ 不符合要求")
        
        # 房间统计
        total_rooms = Room.query.count()
        avg_rooms_per_shared = (total_rooms / shared_houses) if shared_houses > 0 else 0
        
        print(f"\n【房间数据】")
        print(f"  总数：{total_rooms}")
        print(f"  平均每个合租房源房间数：{avg_rooms_per_shared:.1f} (规格：3-6)")
        print(f"  ✓ 符合要求" if 3 <= avg_rooms_per_shared <= 6 or shared_houses == 0 else "  ✗ 不符合要求")
        
        # 租客统计
        total_tenants = Tenant.query.count()
        print(f"\n【租客数据】")
        print(f"  总数：{total_tenants} (规格：50-80)")
        print(f"  ✓ 符合要求" if 50 <= total_tenants <= 80 else "  ✗ 不符合要求")
        
        # 合同统计
        total_contracts = Contract.query.count()
        active_contracts = Contract.query.filter_by(status='active').count()
        expired_contracts = Contract.query.filter_by(status='expired').count()
        draft_contracts = Contract.query.filter_by(status='draft').count()
        terminated_contracts = Contract.query.filter_by(status='terminated').count()
        
        print(f"\n【合同数据】")
        print(f"  总数：{total_contracts} (规格：60-100)")
        if total_contracts > 0:
            print(f"  生效中：{active_contracts} ({active_contracts/total_contracts*100:.1f}%) (规格：~60%)")
            print(f"  已过期：{expired_contracts} ({expired_contracts/total_contracts*100:.1f}%) (规格：~20%)")
            print(f"  草稿：{draft_contracts} ({draft_contracts/total_contracts*100:.1f}%) (规格：~10%)")
            print(f"  已终止：{terminated_contracts} ({terminated_contracts/total_contracts*100:.1f}%) (规格：~10%)")
        print(f"  ✓ 符合要求" if 60 <= total_contracts <= 100 else "  ✗ 不符合要求")
        
        # 支付记录统计
        total_payments = Payment.query.count()
        paid_payments = Payment.query.filter_by(status='paid').count()
        pending_payments = Payment.query.filter_by(status='pending').count()
        overdue_payments = Payment.query.filter_by(status='overdue').count()
        partial_payments = Payment.query.filter_by(status='partial').count()
        refunded_payments = Payment.query.filter_by(status='refunded').count()
        
        print(f"\n【支付记录】")
        print(f"  总数：{total_payments} (规格：200-300)")
        if total_payments > 0:
            print(f"  已支付：{paid_payments} ({paid_payments/total_payments*100:.1f}%) (规格：~60%)")
            print(f"  待支付：{pending_payments} ({pending_payments/total_payments*100:.1f}%) (规格：~20%)")
            print(f"  逾期：{overdue_payments} ({overdue_payments/total_payments*100:.1f}%) (规格：~10%)")
            print(f"  部分支付：{partial_payments} ({partial_payments/total_payments*100:.1f}%) (规格：~5%)")
            print(f"  已退款：{refunded_payments} ({refunded_payments/total_payments*100:.1f}%) (规格：~5%)")
        print(f"  ✓ 符合要求" if 200 <= total_payments <= 300 else "  ✗ 不符合要求")
        
        # 数据一致性检查
        print(f"\n【数据一致性检查】")
        
        # 检查合同关联
        contracts_without_house = Contract.query.filter(
            Contract.house_id.notin_(db.session.query(House.id))
        ).count()
        print(f"  无房源的合同：{contracts_without_house} (应为 0)")
        
        contracts_without_tenant = Contract.query.filter(
            Contract.tenant_id.notin_(db.session.query(Tenant.id))
        ).count()
        print(f"  无租客的合同：{contracts_without_tenant} (应为 0)")
        
        # 检查支付记录关联
        payments_without_contract = Payment.query.filter(
            Payment.contract_id.notin_(db.session.query(Contract.id))
        ).count()
        print(f"  无合同的支付记录：{payments_without_contract} (应为 0)")
        
        consistency_ok = (contracts_without_house == 0 and 
                         contracts_without_tenant == 0 and 
                         payments_without_contract == 0)
        print(f"  ✓ 数据一致性良好" if consistency_ok else "  ✗ 数据一致性问题")
        
        # 总结
        print("\n" + "="*60)
        all_ok = (
            5 <= total_users <= 10 and
            1 <= admin_users <= 2 and
            10 <= total_landlords <= 20 and
            30 <= total_houses <= 50 and
            50 <= total_tenants <= 80 and
            60 <= total_contracts <= 100 and
            200 <= total_payments <= 300 and
            consistency_ok
        )
        
        if all_ok:
            print("✓ 所有数据符合规格要求！")
        else:
            print("✗ 部分数据不符合规格要求，请检查")
        
        print("="*60 + "\n")

if __name__ == '__main__':
    verify_data()
