"""
统计管理路由模块
提供房源、收入、租客、合同等各类统计功能
支持数据导出为 Excel 和 PDF 格式
"""
from flask import Blueprint, request, jsonify, g, current_app, send_file
from typing import Optional, Dict, Any
from datetime import datetime, date, timedelta
from sqlalchemy import func, extract, case, cast, Numeric
from sqlalchemy.sql import label
import io
import os
import json

from app.models.house import House
from app.models.room import Room
from app.models.tenant import Tenant
from app.models.contract import Contract
from app.models.payment import Payment
from app.models.user import User
from app.models import db
from app.utils.decorators import login_required, admin_required
from app.utils.responses import APIResponse

# 创建蓝图
statistics_bp = Blueprint('statistics', __name__, url_prefix='/api/statistics')


# ============================================================================
# 辅助函数
# ============================================================================

def get_date_range(period: str, months: int = 12) -> tuple:
    """
    获取日期范围
    
    Args:
        period: 时间周期 (monthly/quarterly/yearly)
        months: 月数
        
    Returns:
        tuple: (开始日期，结束日期)
    """
    end_date = date.today()
    
    if period == 'monthly':
        start_date = end_date - timedelta(days=30 * months)
    elif period == 'quarterly':
        start_date = end_date - timedelta(days=90 * months)
    elif period == 'yearly':
        start_date = end_date - timedelta(days=365 * months)
    else:
        start_date = end_date - timedelta(days=30)
    
    return start_date, end_date


def format_currency(amount: float) -> str:
    """格式化货币显示"""
    return f"¥{amount:,.2f}"


# ============================================================================
# 概览统计接口
# ============================================================================

@statistics_bp.route('/overview', methods=['GET'])
@login_required
def get_overview_statistics():
    """
    获取概览统计
    
    Query Parameters:
        period: 统计周期 (today/week/month/year)，默认 month
        
    Response:
        {
            "success": true,
            "data": {
                "houses": {
                    "total": 100,
                    "available": 60,
                    "rented": 35,
                    "maintenance": 5,
                    "occupancy_rate": 0.70
                },
                "income": {
                    "current_period": 150000.00,
                    "previous_period": 130000.00,
                    "growth_rate": 0.1538
                },
                "contracts": {
                    "total": 150,
                    "active": 80,
                    "expiring_soon": 12
                },
                "tenants": {
                    "total": 200,
                    "active": 120
                }
            }
        }
    """
    try:
        # 获取周期参数
        period = request.args.get('period', 'month')
        
        # 计算日期范围
        end_date = date.today()
        if period == 'today':
            start_date = end_date
        elif period == 'week':
            start_date = end_date - timedelta(days=7)
        elif period == 'month':
            start_date = end_date - timedelta(days=30)
        elif period == 'year':
            start_date = end_date - timedelta(days=365)
        else:
            start_date = end_date - timedelta(days=30)
        
        # 上一个周期
        period_days = (end_date - start_date).days
        prev_start_date = start_date - timedelta(days=period_days)
        prev_end_date = start_date - timedelta(days=1)
        
        # 房源统计
        total_houses = House.query.count()
        available_houses = House.query.filter(House.status == 'available').count()
        rented_houses = House.query.filter(House.status == 'rented').count()
        maintenance_houses = House.query.filter(House.status == 'maintenance').count()
        
        # 上一个周期的房源数量
        prev_total_houses = House.query.filter(
            House.created_at < prev_start_date
        ).count()
        
        # 出租率
        occupancy_rate = rented_houses / total_houses if total_houses > 0 else 0
        
        # 收入统计（当前周期）
        current_income_query = db.session.query(
            func.sum(Payment.paid_amount).label('total')
        ).filter(
            Payment.status == 'paid',
            Payment.payment_date >= start_date,
            Payment.payment_date <= end_date
        )
        current_income = current_income_query.scalar() or 0.0
        
        # 收入统计（上一周期）
        prev_income_query = db.session.query(
            func.sum(Payment.paid_amount).label('total')
        ).filter(
            Payment.status == 'paid',
            Payment.payment_date >= prev_start_date,
            Payment.payment_date <= prev_end_date
        )
        prev_income = prev_income_query.scalar() or 0.0
        
        # 收入增长率
        income_growth = (current_income - prev_income) / prev_income if prev_income > 0 else 0
        
        # 合同统计
        total_contracts = Contract.query.count()
        active_contracts = Contract.query.filter(Contract.status == 'active').count()
        
        # 上一个周期的合同数量
        prev_total_contracts = Contract.query.filter(
            Contract.created_at < prev_start_date
        ).count()
        
        # 即将到期合同（30 天内）
        expiring_soon = Contract.query.filter(
            Contract.status == 'active',
            Contract.end_date >= end_date,
            Contract.end_date <= end_date + timedelta(days=30)
        ).count()
        
        # 租客统计
        total_tenants = Tenant.query.count()
        active_tenants = Tenant.query.filter(Tenant.status == 'active').count()
        
        # 上一个周期的租客数量
        prev_total_tenants = Tenant.query.filter(
            Tenant.created_at < prev_start_date
        ).count()
        
        # 计算增长率
        houses_growth = (total_houses - prev_total_houses) / prev_total_houses if prev_total_houses > 0 else 0
        tenants_growth = (total_tenants - prev_total_tenants) / prev_total_tenants if prev_total_tenants > 0 else 0
        contracts_growth = (total_contracts - prev_total_contracts) / prev_total_contracts if prev_total_contracts > 0 else 0
        
        return APIResponse.success({
            'houses': {
                'total': total_houses,
                'available': available_houses,
                'rented': rented_houses,
                'maintenance': maintenance_houses,
                'occupancy_rate': round(occupancy_rate, 4),
                'growth_rate': round(houses_growth, 4)
            },
            'income': {
                'current_period': round(current_income, 2),
                'previous_period': round(prev_income, 2),
                'growth_rate': round(income_growth, 4),
                'period': period
            },
            'contracts': {
                'total': total_contracts,
                'active': active_contracts,
                'expiring_soon': expiring_soon,
                'growth_rate': round(contracts_growth, 4)
            },
            'tenants': {
                'total': total_tenants,
                'active': active_tenants,
                'growth_rate': round(tenants_growth, 4)
            },
            'period': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            }
        }, "获取概览统计成功")
        
    except Exception as e:
        current_app.logger.error(f"获取概览统计失败：{str(e)}")
        return APIResponse.server_error("获取概览统计失败")


# ============================================================================
# 房源统计接口
# ============================================================================

@statistics_bp.route('/houses', methods=['GET'])
@login_required
def get_house_statistics():
    """
    获取房源统计
    
    Query Parameters:
        group_by: 分组维度 (status/city/district/layout)，默认 status
        include_trend: 是否包含趋势数据，默认 true
        
    Response:
        {
            "success": true,
            "data": {
                "by_status": {
                    "available": 60,
                    "rented": 35,
                    "maintenance": 5
                },
                "by_city": {
                    "北京": 50,
                    "上海": 30,
                    "广州": 20
                },
                "by_district": {
                    "朝阳区": 20,
                    "海淀区": 15,
                    ...
                },
                "by_layout": {
                    "1 室 1 厅": 30,
                    "2 室 1 厅": 40,
                    "3 室 1 厅": 30
                },
                "occupancy_trend": [
                    {"month": "2024-01", "rate": 0.65},
                    {"month": "2024-02", "rate": 0.68},
                    ...
                ]
            }
        }
    """
    try:
        group_by = request.args.get('group_by', 'status')
        include_trend = request.args.get('include_trend', 'true').lower() == 'true'
        
        result = {}
        
        # 按状态分类
        if group_by == 'status':
            status_stats = db.session.query(
                House.status,
                func.count(House.id).label('count')
            ).group_by(House.status).all()
            
            result['by_status'] = {
                stat.status: stat.count for stat in status_stats
            }
        
        # 按城市分布
        if group_by == 'city' or group_by == 'all':
            city_stats = db.session.query(
                House.city,
                func.count(House.id).label('count')
            ).filter(
                House.city.isnot(None)
            ).group_by(House.city).all()
            
            result['by_city'] = {
                stat.city: stat.count for stat in city_stats
            }
        
        # 按区县分布
        if group_by == 'district' or group_by == 'all':
            district_stats = db.session.query(
                House.district,
                func.count(House.id).label('count')
            ).filter(
                House.district.isnot(None)
            ).group_by(House.district).all()
            
            result['by_district'] = {
                stat.district: stat.count for stat in district_stats
            }
        
        # 按户型分布
        if group_by == 'layout' or group_by == 'all':
            # 根据 room_count 和 hall_count 组合成户型
            layout_stats = db.session.query(
                House.room_count,
                House.hall_count,
                func.count(House.id).label('count')
            ).filter(
                House.room_count.isnot(None),
                House.hall_count.isnot(None)
            ).group_by(House.room_count, House.hall_count).all()
            
            result['by_layout'] = {
                f"{stat.room_count}室{stat.hall_count}厅": stat.count 
                for stat in layout_stats
            }
        
        # 出租率趋势（近 12 个月）
        if include_trend:
            occupancy_trend = []
            end_date = date.today()
            
            for i in range(11, -1, -1):
                month_date = end_date - timedelta(days=30 * i)
                month_start = month_date.replace(day=1)
                month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
                
                # 查询该月的出租房源数
                rented_count = db.session.query(func.count(House.id)).filter(
                    House.status == 'rented',
                    func.strftime('%Y-%m', House.created_at) == month_date.strftime('%Y-%m')
                ).scalar() or 0
                
                # 查询该月总房源数
                total_count = db.session.query(func.count(House.id)).filter(
                    func.strftime('%Y-%m', House.created_at) <= month_date.strftime('%Y-%m')
                ).scalar() or 1
                
                occupancy_rate = rented_count / total_count if total_count > 0 else 0
                
                occupancy_trend.append({
                    'month': month_date.strftime('%Y-%m'),
                    'rate': round(occupancy_rate, 4),
                    'rented_count': rented_count,
                    'total_count': total_count
                })
            
            result['occupancy_trend'] = occupancy_trend
        
        # 总体统计
        total_houses = House.query.count()
        result['summary'] = {
            'total': total_houses,
            'available': House.query.filter(House.status == 'available').count(),
            'rented': House.query.filter(House.status == 'rented').count(),
            'maintenance': House.query.filter(House.status == 'maintenance').count(),
            'occupancy_rate': round(House.query.filter(House.status == 'rented').count() / total_houses, 4) if total_houses > 0 else 0
        }
        
        return APIResponse.success(result, "获取房源统计成功")
        
    except Exception as e:
        current_app.logger.error(f"获取房源统计失败：{str(e)}")
        return APIResponse.server_error("获取房源统计失败")


# ============================================================================
# 收入统计接口
# ============================================================================

@statistics_bp.route('/income', methods=['GET'])
@login_required
def get_income_statistics():
    """
    获取收入统计
    
    Query Parameters:
        period: 时间周期 (monthly/quarterly/yearly)，默认 monthly
        months: 统计月数，默认 12
        payment_type: 支付类型筛选 (rent/deposit/utility/other)
        
    Response:
        {
            "success": true,
            "data": {
                "monthly_trend": [
                    {"month": "2024-01", "income": 50000, "paid_count": 120},
                    ...
                ],
                "yearly_comparison": [
                    {"year": 2022, "income": 500000},
                    {"year": 2023, "income": 600000},
                    {"year": 2024, "income": 700000}
                ],
                "by_type": {
                    "rent": 450000,
                    "deposit": 100000,
                    "utility": 50000,
                    "other": 20000
                },
                "summary": {
                    "total_income": 620000,
                    "total_paid": 580,
                    "total_pending": 50,
                    "total_overdue": 20
                }
            }
        }
    """
    try:
        period = request.args.get('period', 'monthly')
        months = request.args.get('months', 12, type=int)
        payment_type = request.args.get('payment_type')
        
        result = {}
        
        # 月度收入趋势（近 12 个月）
        if period == 'monthly' or period == 'all':
            monthly_trend = []
            end_date = date.today()
            
            for i in range(months - 1, -1, -1):
                month_date = end_date - timedelta(days=30 * i)
                month_start = month_date.replace(day=1)
                month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
                
                # 查询该月的收入
                income_query = db.session.query(
                    func.sum(Payment.paid_amount).label('total')
                ).filter(
                    Payment.status == 'paid',
                    Payment.payment_date >= month_start,
                    Payment.payment_date <= month_end
                )
                
                if payment_type:
                    income_query = income_query.filter(Payment.payment_type == payment_type)
                
                income = income_query.scalar() or 0.0
                
                # 查询该月的支付笔数
                paid_count = db.session.query(func.count(Payment.id)).filter(
                    Payment.status == 'paid',
                    Payment.payment_date >= month_start,
                    Payment.payment_date <= month_end
                ).scalar() or 0
                
                monthly_trend.append({
                    'month': month_date.strftime('%Y-%m'),
                    'income': round(income, 2),
                    'paid_count': paid_count
                })
            
            result['monthly_trend'] = monthly_trend
        
        # 年度收入对比（近 3 年）
        if period == 'yearly' or period == 'all':
            yearly_comparison = []
            current_year = datetime.now().year
            
            for i in range(2, -1, -1):
                year = current_year - i
                
                # 查询该年的收入
                income_query = db.session.query(
                    func.sum(Payment.paid_amount).label('total')
                ).filter(
                    Payment.status == 'paid',
                    extract('year', Payment.payment_date) == year
                )
                
                if payment_type:
                    income_query = income_query.filter(Payment.payment_type == payment_type)
                
                income = income_query.scalar() or 0.0
                
                yearly_comparison.append({
                    'year': year,
                    'income': round(income, 2),
                    'growth_rate': None  # 需要上一年数据才能计算
                })
            
            # 计算增长率
            for i in range(1, len(yearly_comparison)):
                prev_income = yearly_comparison[i-1]['income']
                curr_income = yearly_comparison[i]['income']
                if prev_income > 0:
                    yearly_comparison[i]['growth_rate'] = round((curr_income - prev_income) / prev_income, 4)
            
            result['yearly_comparison'] = yearly_comparison
        
        # 收入构成
        by_type_query = db.session.query(
            Payment.payment_type,
            func.sum(Payment.paid_amount).label('total')
        ).filter(
            Payment.status == 'paid'
        ).group_by(Payment.payment_type).all()
        
        result['by_type'] = {
            stat.payment_type: round(stat.total, 2) for stat in by_type_query
        }
        
        # 汇总统计
        total_income_query = db.session.query(
            func.sum(Payment.paid_amount).label('total')
        ).filter(
            Payment.status == 'paid'
        )
        
        if payment_type:
            total_income_query = total_income_query.filter(Payment.payment_type == payment_type)
        
        total_income = total_income_query.scalar() or 0.0
        
        total_paid = db.session.query(func.count(Payment.id)).filter(
            Payment.status == 'paid'
        ).scalar() or 0
        
        total_pending = db.session.query(func.count(Payment.id)).filter(
            Payment.status == 'pending'
        ).scalar() or 0
        
        total_overdue = db.session.query(func.count(Payment.id)).filter(
            Payment.status == 'overdue'
        ).scalar() or 0
        
        result['summary'] = {
            'total_income': round(total_income, 2),
            'total_paid': total_paid,
            'total_pending': total_pending,
            'total_overdue': total_overdue,
            'collection_rate': round(total_paid / (total_paid + total_pending + total_overdue), 4) if (total_paid + total_pending + total_overdue) > 0 else 0
        }
        
        return APIResponse.success(result, "获取收入统计成功")
        
    except Exception as e:
        current_app.logger.error(f"获取收入统计失败：{str(e)}")
        return APIResponse.server_error("获取收入统计失败")


# ============================================================================
# 租客分析接口
# ============================================================================

@statistics_bp.route('/tenants', methods=['GET'])
@login_required
def get_tenant_statistics():
    """
    获取租客分析统计
    
    Query Parameters:
        include_demographics: 是否包含人口统计信息，默认 true
        
    Response:
        {
            "success": true,
            "data": {
                "summary": {
                    "total": 200,
                    "active": 120,
                    "expired": 70,
                    "blacklisted": 10
                },
                "by_source": {
                    "线上": 80,
                    "中介": 50,
                    "朋友介绍": 40,
                    "其他": 30
                },
                "by_contract_type": {
                    "short_term": 30,
                    "long_term": 90
                },
                "age_distribution": {
                    "18-25": 40,
                    "26-35": 60,
                    "36-45": 30,
                    "46+": 20
                },
                "contract_renewal_rate": 0.65
            }
        }
    """
    try:
        include_demographics = request.args.get('include_demographics', 'true').lower() == 'true'
        
        result = {}
        
        # 租客总数和状态统计
        total_tenants = Tenant.query.count()
        active_tenants = Tenant.query.filter(Tenant.status == 'active').count()
        expired_tenants = Tenant.query.filter(Tenant.status == 'expired').count()
        blacklisted_tenants = Tenant.query.filter(Tenant.status == 'blacklisted').count()
        
        result['summary'] = {
            'total': total_tenants,
            'active': active_tenants,
            'expired': expired_tenants,
            'blacklisted': blacklisted_tenants
        }
        
        # 租客来源渠道（需要从合同或其他地方获取，这里假设从备注中分析）
        # 实际项目中应该有专门的 source 字段
        result['by_source'] = {
            '线上': 0,
            '中介': 0,
            '朋友介绍': 0,
            '其他': 0
        }
        
        # 租期分布（通过合同分析）
        current_year = datetime.now().year
        
        # 获取所有活跃合同
        active_contracts = Contract.query.filter(
            Contract.status == 'active'
        ).all()
        
        short_term = 0  # 小于 6 个月
        medium_term = 0  # 6-12 个月
        long_term = 0  # 大于 12 个月
        
        for contract in active_contracts:
            if not contract.end_date or not contract.start_date:
                continue
            duration_months = (contract.end_date.year - contract.start_date.year) * 12 + \
                            (contract.end_date.month - contract.start_date.month)
            
            if duration_months < 6:
                short_term += 1
            elif duration_months <= 12:
                medium_term += 1
            else:
                long_term += 1
        
        result['by_contract_type'] = {
            'short_term': short_term,
            'medium_term': medium_term,
            'long_term': long_term
        }
        
        # 年龄分布（从身份证号推算，这里简化处理）
        # 实际项目中应该从身份证解析出生日期
        if include_demographics:
            result['age_distribution'] = {
                '18-25': 0,
                '26-35': 0,
                '36-45': 0,
                '46+': 0
            }
        
        # 合同续签率
        # 计算有过期合同的租客中有多少续签了新合同
        expired_contracts = Contract.query.filter(
            Contract.status == 'expired'
        ).all()
        
        renewed_count = 0
        for contract in expired_contracts:
            # 检查该租客是否有后续合同
            if not contract.end_date or not contract.tenant_id:
                continue
            subsequent_contract = Contract.query.filter(
                Contract.tenant_id == contract.tenant_id,
                Contract.start_date > contract.end_date,
                Contract.status.in_(['active', 'expired'])
            ).first()
            
            if subsequent_contract:
                renewed_count += 1
        
        renewal_rate = renewed_count / len(expired_contracts) if expired_contracts else 0
        
        result['contract_renewal_rate'] = round(renewal_rate, 4)
        
        # 平均租期
        avg_duration_query = db.session.query(
            func.avg(
                (func.julianday(Contract.end_date) - 
                 func.julianday(Contract.start_date)) / 30
            )
        ).filter(
            Contract.status.in_(['active', 'expired'])
        )
        
        avg_duration = avg_duration_query.scalar() or 0
        
        result['average_lease_duration'] = round(avg_duration, 2)
        
        return APIResponse.success(result, "获取租客分析统计成功")
        
    except Exception as e:
        current_app.logger.error(f"获取租客分析统计失败：{str(e)}")
        return APIResponse.server_error("获取租客分析统计失败")


# ============================================================================
# 合同统计接口
# ============================================================================

@statistics_bp.route('/contracts', methods=['GET'])
@login_required
def get_contract_statistics():
    """
    获取合同统计
    
    Response:
        {
            "success": true,
            "data": {
                "summary": {
                    "total": 150,
                    "active": 80,
                    "draft": 10,
                    "expired": 50,
                    "terminated": 10
                },
                "expiring_soon": {
                    "count": 12,
                    "contracts": [...]
                },
                "by_status": {
                    "active": 80,
                    "draft": 10,
                    "expired": 50,
                    "terminated": 10
                },
                "renewal_rate": 0.65,
                "average_duration": 12.5,
                "average_rent": 5000.00
            }
        }
    """
    try:
        result = {}
        
        # 合同总数和状态统计
        total_contracts = Contract.query.count()
        active_contracts = Contract.query.filter(Contract.status == 'active').count()
        draft_contracts = Contract.query.filter(Contract.status == 'draft').count()
        expired_contracts = Contract.query.filter(Contract.status == 'expired').count()
        terminated_contracts = Contract.query.filter(Contract.status == 'terminated').count()
        
        result['summary'] = {
            'total': total_contracts,
            'active': active_contracts,
            'draft': draft_contracts,
            'expired': expired_contracts,
            'terminated': terminated_contracts
        }
        
        result['by_status'] = {
            'active': active_contracts,
            'draft': draft_contracts,
            'expired': expired_contracts,
            'terminated': terminated_contracts
        }
        
        # 即将到期合同（30 天内）
        end_date = date.today()
        expiring_date = end_date + timedelta(days=30)
        
        expiring_contracts = Contract.query.filter(
            Contract.status == 'active',
            Contract.end_date >= end_date,
            Contract.end_date <= expiring_date
        ).all()
        
        expiring_list = []
        for contract in expiring_contracts:
            expiring_list.append({
                'id': contract.id,
                'contract_no': contract.contract_no,
                'title': contract.title,
                'tenant_name': contract.tenant_rel.name if contract.tenant_rel else None,
                'end_date': contract.end_date.isoformat() if contract.end_date else None,
                'days_until_expiry': (contract.end_date - end_date).days if contract.end_date else None
            })
        
        result['expiring_soon'] = {
            'count': len(expiring_contracts),
            'contracts': expiring_list
        }
        
        # 合同续签率
        # 查询所有已过期的合同对象
        expired_contracts_list = Contract.query.filter(Contract.status == 'expired').all()
        
        renewed_count = 0
        for contract in expired_contracts_list:
            # 检查该租客是否有后续合同
            if not contract.end_date or not contract.tenant_id:
                continue
            subsequent_contract = Contract.query.filter(
                Contract.tenant_id == contract.tenant_id,
                Contract.start_date > contract.end_date,
                Contract.status.in_(['active', 'expired'])
            ).first()
            
            if subsequent_contract:
                renewed_count += 1
        
        renewal_rate = renewed_count / len(expired_contracts_list) if len(expired_contracts_list) > 0 else 0
        result['renewal_rate'] = round(renewal_rate, 4)
        
        # 平均租期（月）
        avg_duration_query = db.session.query(
            func.avg(
                (func.julianday(Contract.end_date) - 
                 func.julianday(Contract.start_date)) / 30
            )
        ).filter(
            Contract.status.in_(['active', 'expired'])
        )
        
        avg_duration = avg_duration_query.scalar() or 0
        result['average_duration'] = round(avg_duration, 2)
        
        # 平均租金
        avg_rent_query = db.session.query(
            func.avg(Contract.rent_amount)
        ).filter(
            Contract.status == 'active'
        )
        
        avg_rent = avg_rent_query.scalar() or 0
        result['average_rent'] = round(avg_rent, 2)
        
        # 总租金收入（合同期内）
        total_rent_query = db.session.query(
            func.sum(Contract.rent_amount)
        ).filter(
            Contract.status == 'active'
        )
        
        total_rent = total_rent_query.scalar() or 0
        result['total_active_rent'] = round(total_rent, 2)
        
        return APIResponse.success(result, "获取合同统计成功")
        
    except Exception as e:
        current_app.logger.error(f"获取合同统计失败：{str(e)}")
        return APIResponse.server_error("获取合同统计失败")


# ============================================================================
# Excel 导出接口
# ============================================================================

@statistics_bp.route('/export/excel', methods=['GET'])
@login_required
def export_statistics_excel():
    """
    导出 Excel 报表
    
    Query Parameters:
        report_type: 报表类型 (overview/houses/income/tenants/contracts/all)
        start_date: 开始日期 (YYYY-MM-DD)
        end_date: 结束日期 (YYYY-MM-DD)
        
    Response:
        下载 Excel 文件
    """
    try:
        # 检查是否安装了 openpyxl
        try:
            from openpyxl import Workbook
            from openpyxl.styles import Font, Alignment, Border, Side, PatternFill
            from openpyxl.utils import get_column_letter
        except ImportError:
            return APIResponse.server_error("未安装 openpyxl 库，请运行：pip install openpyxl")
        
        report_type = request.args.get('report_type', 'all')
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        
        # 解析日期
        if start_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        else:
            start_date = date.today() - timedelta(days=30)
        
        if end_date_str:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        else:
            end_date = date.today()
        
        # 创建工作簿
        wb = Workbook()
        wb.title = "房屋租赁统计报表"
        
        # 定义样式
        header_font = Font(bold=True, size=12, color="FFFFFF")
        header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
        header_alignment = Alignment(horizontal="center", vertical="center")
        
        thin_border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )
        
        # 创建概览工作表
        if report_type in ['overview', 'all']:
            ws_overview = wb.active
            ws_overview.title = "概览统计"
            
            # 添加标题
            ws_overview.merge_cells('A1:D1')
            title_cell = ws_overview['A1']
            title_cell.value = f"房屋租赁统计报表 ({start_date} 至 {end_date})"
            title_cell.font = Font(bold=True, size=16)
            title_cell.alignment = Alignment(horizontal="center")
            
            # 获取概览数据
            total_houses = House.query.count()
            rented_houses = House.query.filter(House.status == 'rented').count()
            total_income = db.session.query(func.sum(Payment.paid_amount)).filter(
                Payment.status == 'paid',
                Payment.payment_date >= start_date,
                Payment.payment_date <= end_date
            ).scalar() or 0
            
            total_contracts = Contract.query.count()
            active_contracts = Contract.query.filter(Contract.status == 'active').count()
            
            total_tenants = Tenant.query.count()
            active_tenants = Tenant.query.filter(Tenant.status == 'active').count()
            
            # 添加数据
            overview_data = [
                ["指标", "数值", "说明", ""],
                ["房源总数", total_houses, "", ""],
                ["出租房源数", rented_houses, f"出租率：{rented_houses/total_houses*100:.1f}%" if total_houses > 0 else "N/A", ""],
                ["维护中房源", House.query.filter(House.status == 'maintenance').count(), "", ""],
                ["", "", "", ""],
                ["期间总收入", f"¥{total_income:,.2f}", f"{start_date} 至 {end_date}", ""],
                ["", "", "", ""],
                ["合同总数", total_contracts, "", ""],
                ["活跃合同数", active_contracts, "", ""],
                ["即将到期合同", Contract.query.filter(
                    Contract.status == 'active',
                    Contract.end_date >= end_date,
                    Contract.end_date <= end_date + timedelta(days=30)
                ).count(), "30 天内到期", ""],
                ["", "", "", ""],
                ["租客总数", total_tenants, "", ""],
                ["活跃租客数", active_tenants, "", ""],
            ]
            
            for row_idx, row_data in enumerate(overview_data, start=3):
                for col_idx, value in enumerate(row_data, start=1):
                    cell = ws_overview.cell(row=row_idx, column=col_idx, value=value)
                    if row_idx == 3:  # 表头
                        cell.font = header_font
                        cell.fill = header_fill
                        cell.alignment = header_alignment
                        cell.border = thin_border
                    else:
                        cell.border = thin_border
                        cell.alignment = Alignment(horizontal="left", vertical="center")
            
            # 调整列宽
            ws_overview.column_dimensions['A'].width = 20
            ws_overview.column_dimensions['B'].width = 20
            ws_overview.column_dimensions['C'].width = 30
            ws_overview.column_dimensions['D'].width = 10
        
        # 创建房源统计工作表
        if report_type in ['houses', 'all']:
            ws_houses = wb.create_sheet(title="房源统计")
            
            # 按状态统计
            status_stats = db.session.query(
                House.status,
                func.count(House.id).label('count')
            ).group_by(House.status).all()
            
            ws_houses['A1'] = "房源状态分布"
            ws_houses['A1'].font = Font(bold=True, size=14)
            
            ws_houses['A3'] = "状态"
            ws_houses['B3'] = "数量"
            ws_houses['A3'].font = header_font
            ws_houses['B3'].font = header_font
            ws_houses['A3'].fill = header_fill
            ws_houses['B3'].fill = header_fill
            
            for idx, stat in enumerate(status_stats, start=4):
                ws_houses.cell(row=idx, column=1, value=stat.status).border = thin_border
                ws_houses.cell(row=idx, column=2, value=stat.count).border = thin_border
            
            # 按城市统计
            city_stats = db.session.query(
                House.city,
                func.count(House.id).label('count')
            ).filter(House.city.isnot(None)).group_by(House.city).all()
            
            if city_stats:
                start_row = len(status_stats) + 6
                ws_houses.cell(row=start_row, column=1, value="房源城市分布").font = Font(bold=True, size=14)
                
                ws_houses.cell(row=start_row+2, column=1, value="城市").font = header_font
                ws_houses.cell(row=start_row+2, column=2, value="数量").font = header_font
                ws_houses.cell(row=start_row+2, column=1).fill = header_fill
                ws_houses.cell(row=start_row+2, column=2).fill = header_fill
                
                for idx, stat in enumerate(city_stats, start=start_row+3):
                    ws_houses.cell(row=idx, column=1, value=stat[0]).border = thin_border
                    ws_houses.cell(row=idx, column=2, value=stat[1]).border = thin_border
        
        # 创建收入统计工作表
        if report_type in ['income', 'all']:
            ws_income = wb.create_sheet(title="收入统计")
            
            ws_income['A1'] = f"收入统计 ({start_date} 至 {end_date})"
            ws_income['A1'].font = Font(bold=True, size=14)
            
            # 按类型统计
            type_stats = db.session.query(
                Payment.payment_type,
                func.sum(Payment.paid_amount).label('total'),
                func.count(Payment.id).label('count')
            ).filter(
                Payment.status == 'paid',
                Payment.payment_date >= start_date,
                Payment.payment_date <= end_date
            ).group_by(Payment.payment_type).all()
            
            ws_income['A3'] = "支付类型"
            ws_income['B3'] = "总金额"
            ws_income['C3'] = "笔数"
            
            for col, header in enumerate(['A3', 'B3', 'C3'], start=1):
                cell = ws_income[header]
                cell.font = header_font
                cell.fill = header_fill
                cell.alignment = header_alignment
            
            for idx, stat in enumerate(type_stats, start=4):
                type_name = Payment.PAYMENT_TYPES.get(stat[0], stat[0])
                ws_income.cell(row=idx, column=1, value=type_name).border = thin_border
                ws_income.cell(row=idx, column=2, value=f"¥{stat[1]:,.2f}").border = thin_border
                ws_income.cell(row=idx, column=3, value=stat[2]).border = thin_border
        
        # 保存为字节流
        output = io.BytesIO()
        wb.save(output)
        output.seek(0)
        
        # 生成文件名
        filename = f"statistics_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        current_app.logger.error(f"导出 Excel 失败：{str(e)}")
        return APIResponse.server_error(f"导出 Excel 失败：{str(e)}")


# ============================================================================
# PDF 导出接口
# ============================================================================

@statistics_bp.route('/export/pdf', methods=['GET'])
@login_required
def export_statistics_pdf():
    """
    导出 PDF 报表
    
    Query Parameters:
        report_type: 报表类型 (overview/houses/income/tenants/contracts/all)
        start_date: 开始日期 (YYYY-MM-DD)
        end_date: 结束日期 (YYYY-MM-DD)
        
    Response:
        下载 PDF 文件
    """
    try:
        # 检查是否安装了 reportlab
        try:
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import A4
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import cm
            from reportlab.lib.enums import TA_CENTER, TA_LEFT
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont
        except ImportError:
            return APIResponse.server_error("未安装 reportlab 库，请运行：pip install reportlab")
        
        report_type = request.args.get('report_type', 'all')
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        
        # 解析日期
        if start_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        else:
            start_date = date.today() - timedelta(days=30)
        
        if end_date_str:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        else:
            end_date = date.today()
        
        # 创建字节流
        buffer = io.BytesIO()
        
        # 创建 PDF 文档
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )
        
        # 存储所有元素
        elements = []
        
        # 样式
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            name='Title',
            parent=styles['Heading1'],
            fontSize=18,
            alignment=TA_CENTER,
            spaceAfter=20
        )
        
        heading_style = ParagraphStyle(
            name='Heading',
            parent=styles['Heading2'],
            fontSize=14,
            spaceAfter=10,
            spaceBefore=10
        )
        
        # 标题
        title = Paragraph(f"房屋租赁统计报表", title_style)
        elements.append(title)
        
        period_text = Paragraph(f"统计期间：{start_date} 至 {end_date}", 
                               ParagraphStyle(name='Period', parent=styles['Normal'], alignment=TA_CENTER))
        elements.append(period_text)
        elements.append(Spacer(1, 0.5*cm))
        
        # 概览数据
        if report_type in ['overview', 'all']:
            elements.append(Paragraph("一、概览统计", heading_style))
            
            total_houses = House.query.count()
            rented_houses = House.query.filter(House.status == 'rented').count()
            occupancy_rate = (rented_houses / total_houses * 100) if total_houses > 0 else 0
            
            total_income = db.session.query(func.sum(Payment.paid_amount)).filter(
                Payment.status == 'paid',
                Payment.payment_date >= start_date,
                Payment.payment_date <= end_date
            ).scalar() or 0
            
            active_contracts = Contract.query.filter(Contract.status == 'active').count()
            active_tenants = Tenant.query.filter(Tenant.status == 'active').count()
            
            overview_data = [
                ['指标', '数值'],
                ['房源总数', str(total_houses)],
                ['出租房源数', f'{rented_houses} ({occupancy_rate:.1f}%)'],
                ['期间总收入', f'¥{total_income:,.2f}'],
                ['活跃合同数', str(active_contracts)],
                ['活跃租客数', str(active_tenants)],
            ]
            
            overview_table = Table(overview_data, colWidths=[5*cm, 5*cm])
            overview_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4472C4')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#D6DCE4')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F2F2F2')]),
            ]))
            
            elements.append(overview_table)
            elements.append(Spacer(1, 0.5*cm))
            
            if report_type == 'overview':
                elements.append(PageBreak())
        
        # 房源统计
        if report_type in ['houses', 'all']:
            elements.append(Paragraph("二、房源统计", heading_style))
            
            status_stats = db.session.query(
                House.status,
                func.count(House.id).label('count')
            ).group_by(House.status).all()
            
            status_data = [['状态', '数量']]
            status_map = {
                'available': '空闲',
                'rented': '已租',
                'maintenance': '维护中',
                'partially_rented': '部分出租'
            }
            
            for stat in status_stats:
                status_name = status_map.get(stat[0], stat[0])
                status_data.append([status_name, str(stat[1])])
            
            status_table = Table(status_data, colWidths=[5*cm, 5*cm])
            status_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4472C4')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F2F2F2')]),
            ]))
            
            elements.append(status_table)
            elements.append(Spacer(1, 0.5*cm))
            
            if report_type == 'houses':
                elements.append(PageBreak())
        
        # 收入统计
        if report_type in ['income', 'all']:
            elements.append(Paragraph("三、收入统计", heading_style))
            
            type_stats = db.session.query(
                Payment.payment_type,
                func.sum(Payment.paid_amount).label('total'),
                func.count(Payment.id).label('count')
            ).filter(
                Payment.status == 'paid',
                Payment.payment_date >= start_date,
                Payment.payment_date <= end_date
            ).group_by(Payment.payment_type).all()
            
            type_data = [['支付类型', '总金额', '笔数']]
            
            for stat in type_stats:
                type_name = Payment.PAYMENT_TYPES.get(stat[0], stat[0])
                type_data.append([
                    type_name,
                    f'¥{stat[1]:,.2f}',
                    str(stat[2])
                ])
            
            type_table = Table(type_data, colWidths=[4*cm, 4*cm, 2*cm])
            type_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4472C4')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F2F2F2')]),
            ]))
            
            elements.append(type_table)
            elements.append(Spacer(1, 0.5*cm))
        
        # 构建 PDF
        doc.build(elements)
        
        # 获取 PDF 数据
        pdf_data = buffer.getvalue()
        buffer.close()
        
        # 生成文件名
        filename = f"statistics_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        return send_file(
            io.BytesIO(pdf_data),
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        current_app.logger.error(f"导出 PDF 失败：{str(e)}")
        return APIResponse.server_error(f"导出 PDF 失败：{str(e)}")


# ============================================================================
# 仪表盘统计数据接口 (GET /api/statistics/dashboard)
# ============================================================================

@statistics_bp.route('/dashboard', methods=['GET'])
@login_required
def get_dashboard_statistics():
    """
    获取仪表盘统计数据
    
    Query Parameters:
        period: 统计周期 (today/week/month/year)，默认 month
        
    Response:
        {
            "success": true,
            "data": {
                "houses": {
                    "total": 100,
                    "available": 60,
                    "rented": 35,
                    "maintenance": 5,
                    "occupancy_rate": 0.35
                },
                "income": {
                    "current_period": 150000.00,
                    "previous_period": 130000.00,
                    "growth_rate": 0.1538
                },
                "contracts": {
                    "total": 150,
                    "active": 80,
                    "expiring_soon": 12
                },
                "tenants": {
                    "total": 200,
                    "active": 120
                }
            }
        }
    """
    try:
        # 获取周期参数
        period = request.args.get('period', 'month')
        
        # 计算日期范围
        end_date = date.today()
        if period == 'today':
            start_date = end_date
        elif period == 'week':
            start_date = end_date - timedelta(days=7)
        elif period == 'month':
            start_date = end_date - timedelta(days=30)
        elif period == 'year':
            start_date = end_date - timedelta(days=365)
        else:
            start_date = end_date - timedelta(days=30)
        
        # 上一个周期
        period_days = (end_date - start_date).days
        prev_start_date = start_date - timedelta(days=period_days) if period_days > 0 else start_date - timedelta(days=30)
        prev_end_date = start_date - timedelta(days=1)
        
        # 房源统计
        total_houses = House.query.count()
        available_houses = House.query.filter(House.status == 'available').count()
        rented_houses = House.query.filter(House.status == 'rented').count()
        maintenance_houses = House.query.filter(House.status == 'maintenance').count()
        
        # 出租率
        occupancy_rate = rented_houses / total_houses if total_houses > 0 else 0
        
        # 收入统计（当前周期）
        current_income = db.session.query(
            func.sum(Payment.paid_amount)
        ).filter(
            Payment.status == 'paid',
            Payment.payment_date >= start_date,
            Payment.payment_date <= end_date
        ).scalar() or 0.0
        
        # 收入统计（上一周期）
        prev_income = db.session.query(
            func.sum(Payment.paid_amount)
        ).filter(
            Payment.status == 'paid',
            Payment.payment_date >= prev_start_date,
            Payment.payment_date <= prev_end_date
        ).scalar() or 0.0
        
        # 收入增长率
        income_growth = (current_income - prev_income) / prev_income if prev_income > 0 else 0
        
        # 合同统计
        total_contracts = Contract.query.count()
        active_contracts = Contract.query.filter(Contract.status == 'active').count()
        
        # 即将到期合同（30 天内）
        expiring_soon = Contract.query.filter(
            Contract.status == 'active',
            Contract.end_date >= end_date,
            Contract.end_date <= end_date + timedelta(days=30)
        ).count()
        
        # 租客统计
        total_tenants = Tenant.query.count()
        active_tenants = Tenant.query.filter(Tenant.status == 'active').count()
        
        return APIResponse.success({
            'houses': {
                'total': total_houses,
                'available': available_houses,
                'rented': rented_houses,
                'maintenance': maintenance_houses,
                'occupancy_rate': round(occupancy_rate, 4)
            },
            'income': {
                'current_period': round(current_income, 2),
                'previous_period': round(prev_income, 2),
                'growth_rate': round(income_growth, 4),
                'period': period
            },
            'contracts': {
                'total': total_contracts,
                'active': active_contracts,
                'expiring_soon': expiring_soon
            },
            'tenants': {
                'total': total_tenants,
                'active': active_tenants
            },
            'period': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            }
        }, "获取仪表盘统计成功")
        
    except Exception as e:
        current_app.logger.error(f"获取仪表盘统计失败：{str(e)}")
        return APIResponse.server_error("获取仪表盘统计失败")


# ============================================================================
# 收入统计接口 (GET /api/statistics/revenue)
# ============================================================================

@statistics_bp.route('/revenue', methods=['GET'])
@login_required
def get_revenue_statistics():
    """
    获取收入统计
    
    Query Parameters:
        period: 时间周期 (monthly/quarterly/yearly)，默认 monthly
        months: 统计月数，默认 12
        payment_type: 支付类型筛选 (rent/deposit/utility/other)
        
    Response:
        {
            "success": true,
            "data": {
                "monthly_trend": [...],
                "yearly_comparison": [...],
                "by_type": {...},
                "summary": {...}
            }
        }
    """
    try:
        period = request.args.get('period', 'monthly')
        months = request.args.get('months', 12, type=int)
        payment_type = request.args.get('payment_type')
        
        result = {}
        
        # 月度收入趋势
        if period == 'monthly' or period == 'all':
            monthly_trend = []
            end_date = date.today()
            
            for i in range(months - 1, -1, -1):
                month_date = end_date - timedelta(days=30 * i)
                month_start = month_date.replace(day=1)
                # 计算月末
                if month_date.month == 12:
                    month_end = month_date.replace(day=31)
                else:
                    next_month = month_date.replace(month=month_date.month + 1, day=1)
                    month_end = next_month - timedelta(days=1)
                
                # 查询该月的收入
                query = db.session.query(
                    func.sum(Payment.paid_amount).label('total')
                ).filter(
                    Payment.status == 'paid',
                    Payment.payment_date >= month_start,
                    Payment.payment_date <= month_end
                )
                
                if payment_type:
                    query = query.filter(Payment.payment_type == payment_type)
                
                income = query.scalar() or 0.0
                
                # 查询该月的支付笔数
                count_query = db.session.query(func.count(Payment.id)).filter(
                    Payment.status == 'paid',
                    Payment.payment_date >= month_start,
                    Payment.payment_date <= month_end
                )
                if payment_type:
                    count_query = count_query.filter(Payment.payment_type == payment_type)
                
                paid_count = count_query.scalar() or 0
                
                monthly_trend.append({
                    'month': month_date.strftime('%Y-%m'),
                    'income': round(income, 2),
                    'paid_count': paid_count
                })
            
            result['monthly_trend'] = monthly_trend
        
        # 年度收入对比
        if period == 'yearly' or period == 'all':
            yearly_comparison = []
            current_year = datetime.now().year
            
            for i in range(2, -1, -1):
                year = current_year - i
                
                query = db.session.query(
                    func.sum(Payment.paid_amount).label('total')
                ).filter(
                    Payment.status == 'paid',
                    extract('year', Payment.payment_date) == year
                )
                
                if payment_type:
                    query = query.filter(Payment.payment_type == payment_type)
                
                income = query.scalar() or 0.0
                
                yearly_comparison.append({
                    'year': year,
                    'income': round(income, 2),
                    'growth_rate': None
                })
            
            # 计算增长率
            for i in range(1, len(yearly_comparison)):
                prev_income = yearly_comparison[i-1]['income']
                curr_income = yearly_comparison[i]['income']
                if prev_income > 0:
                    yearly_comparison[i]['growth_rate'] = round((curr_income - prev_income) / prev_income, 4)
            
            result['yearly_comparison'] = yearly_comparison
        
        # 收入构成
        by_type_query = db.session.query(
            Payment.payment_type,
            func.sum(Payment.paid_amount).label('total')
        ).filter(
            Payment.status == 'paid'
        ).group_by(Payment.payment_type).all()
        
        result['by_type'] = {
            stat.payment_type: round(stat.total, 2) for stat in by_type_query
        }
        
        # 汇总统计
        total_income_query = db.session.query(
            func.sum(Payment.paid_amount)
        ).filter(Payment.status == 'paid')
        
        if payment_type:
            total_income_query = total_income_query.filter(Payment.payment_type == payment_type)
        
        total_income = total_income_query.scalar() or 0.0
        
        total_paid = db.session.query(func.count(Payment.id)).filter(
            Payment.status == 'paid'
        ).scalar() or 0
        
        total_pending = db.session.query(func.count(Payment.id)).filter(
            Payment.status == 'pending'
        ).scalar() or 0
        
        total_overdue = db.session.query(func.count(Payment.id)).filter(
            Payment.status == 'overdue'
        ).scalar() or 0
        
        result['summary'] = {
            'total_income': round(total_income, 2),
            'total_paid': total_paid,
            'total_pending': total_pending,
            'total_overdue': total_overdue,
            'collection_rate': round(total_paid / (total_paid + total_pending + total_overdue), 4) if (total_paid + total_pending + total_overdue) > 0 else 0
        }
        
        return APIResponse.success(result, "获取收入统计成功")
        
    except Exception as e:
        current_app.logger.error(f"获取收入统计失败：{str(e)}")
        return APIResponse.server_error("获取收入统计失败")


# ============================================================================
# 房源出租率统计接口 (GET /api/statistics/occupancy)
# ============================================================================

@statistics_bp.route('/occupancy', methods=['GET'])
@login_required
def get_occupancy_statistics():
    """
    获取房源出租率统计
    
    Query Parameters:
        group_by: 分组维度 (city/district/all)
        include_trend: 是否包含趋势数据，默认 false
        
    Response:
        {
            "success": true,
            "data": {
                "occupancy_rate": 0.70,
                "by_city": {...},
                "by_district": {...},
                "trend": [...]
            }
        }
    """
    try:
        group_by = request.args.get('group_by', '')
        include_trend = request.args.get('include_trend', 'false').lower() == 'true'
        
        result = {}
        
        # 总体统计
        total_houses = House.query.count()
        rented_houses = House.query.filter(House.status == 'rented').count()
        available_houses = House.query.filter(House.status == 'available').count()
        maintenance_houses = House.query.filter(House.status == 'maintenance').count()
        
        occupancy_rate = rented_houses / total_houses if total_houses > 0 else 0
        
        result['occupancy_rate'] = round(occupancy_rate, 4)
        result['total'] = total_houses
        result['rented'] = rented_houses
        result['available'] = available_houses
        result['maintenance'] = maintenance_houses
        
        # 按城市分布
        if group_by == 'city' or group_by == 'all':
            city_stats = db.session.query(
                House.city,
                func.count(House.id).label('total'),
                func.sum(case((House.status == 'rented', 1), else_=0)).label('rented')
            ).filter(
                House.city.isnot(None)
            ).group_by(House.city).all()
            
            result['by_city'] = {}
            for stat in city_stats:
                rate = stat.rented / stat.total if stat.total > 0 else 0
                result['by_city'][stat.city] = {
                    'total': stat.total,
                    'rented': stat.rented,
                    'occupancy_rate': round(rate, 4)
                }
        
        # 按区县分布
        if group_by == 'district' or group_by == 'all':
            district_stats = db.session.query(
                House.district,
                func.count(House.id).label('total'),
                func.sum(case((House.status == 'rented', 1), else_=0)).label('rented')
            ).filter(
                House.district.isnot(None)
            ).group_by(House.district).all()
            
            result['by_district'] = {}
            for stat in district_stats:
                rate = stat.rented / stat.total if stat.total > 0 else 0
                result['by_district'][stat.district] = {
                    'total': stat.total,
                    'rented': stat.rented,
                    'occupancy_rate': round(rate, 4)
                }
        
        # 出租率趋势
        if include_trend:
            trend = []
            end_date = date.today()
            
            for i in range(11, -1, -1):
                month_date = end_date - timedelta(days=30 * i)
                month_str = month_date.strftime('%Y-%m')
                
                # 简化计算：使用当前状态
                trend.append({
                    'month': month_str,
                    'rate': round(occupancy_rate, 4)
                })
            
            result['trend'] = trend
        
        return APIResponse.success(result, "获取出租率统计成功")
        
    except Exception as e:
        current_app.logger.error(f"获取出租率统计失败：{str(e)}")
        return APIResponse.server_error("获取出租率统计失败")


# ============================================================================
# 合同到期提醒接口 (GET /api/statistics/expiring-contracts)
# ============================================================================

@statistics_bp.route('/expiring-contracts', methods=['GET'])
@login_required
def get_expiring_contracts():
    """
    获取合同到期提醒
    
    Query Parameters:
        days: 查询未来多少天内到期的合同，默认 30
        
    Response:
        {
            "success": true,
            "data": {
                "count": 12,
                "contracts": [...]
            }
        }
    """
    try:
        days = request.args.get('days', 30, type=int)
        
        # 使用SQLAlchemy的func.current_date()进行日期比较
        from sqlalchemy import func
        
        end_date = date.today() + timedelta(days=days)
        
        # 查询即将到期的合同
        expiring_contracts = Contract.query.filter(
            Contract.status == 'active',
            Contract.end_date >= func.current_date(),
            Contract.end_date <= end_date
        ).order_by(Contract.end_date).all()
        
        contracts_list = []
        for contract in expiring_contracts:
            contract_data = {
                'id': contract.id,
                'contract_no': contract.contract_no,
                'title': contract.title,
                'end_date': contract.end_date.isoformat(),
                'days_until_expiry': (contract.end_date - date.today()).days,
                'status': contract.status,
                'rent_amount': contract.rent_amount
            }
            
            # 添加租客信息
            if contract.tenant_rel:
                contract_data['tenant_name'] = contract.tenant_rel.name
                contract_data['tenant_phone'] = contract.tenant_rel.phone
            
            # 添加房源信息
            if contract.house:
                contract_data['house_title'] = contract.house.title
                contract_data['house_address'] = contract.house.address
            
            contracts_list.append(contract_data)
        
        return APIResponse.success({
            'count': len(contracts_list),
            'total': len(contracts_list),
            'contracts': contracts_list
        }, "获取到期合同提醒成功")
        
    except Exception as e:
        current_app.logger.error(f"获取到期合同提醒失败：{str(e)}")
        return APIResponse.server_error("获取到期合同提醒失败")
