"""
查询优化工具模块
提供 SQLAlchemy eager loading 优化工具函数，解决 N+1 查询问题

N+1 问题说明：
当查询一个对象列表时，如果访问每个对象的关联属性，会产生 N+1 次数据库查询：
- 1 次查询获取主对象列表
- N 次查询获取每个对象的关联数据

解决方案：
使用 SQLAlchemy 的 eager loading 策略一次性加载关联数据：
1. joinedload() - 使用 JOIN 在同一查询中加载关联数据（适合一对一、多对一关系）
2. selectinload() - 使用 IN 查询加载关联数据（适合一对多关系）
3. subqueryload() - 使用子查询加载关联数据（适合一对多关系，避免重复数据）

性能对比：
- 未优化：1 + N 次查询
- joinedload：1 次查询（使用 JOIN）
- selectinload：2 次查询（主查询 + IN 查询）
- subqueryload：2 次查询（主查询 + 子查询）
"""
from sqlalchemy.orm import joinedload, selectinload, subqueryload, contains_eager
from typing import List, Optional, Any
from flask import current_app


class QueryOptimizer:
    """
    查询优化器
    
    提供常用的 eager loading 配置，避免 N+1 查询问题
    """
    
    # ==================== 房源相关优化 ====================
    
    @staticmethod
    def get_house_list_options():
        """
        获取房源列表查询的 eager loading 选项
        
        房源列表需要加载的关联：
        - owner: 负责员工（多对一，使用 joinedload）
        - landlord_rel: 房东信息（多对一，使用 joinedload）
        
        Returns:
            list: eager loading 选项列表
        """
        from app.models.house import House
        from app.models.user import User
        from app.models.landlord import Landlord
        
        return [
            joinedload(House.owner),           # 加载负责员工信息
            joinedload(House.landlord_rel),    # 加载房东信息
        ]
    
    @staticmethod
    def get_house_detail_options():
        """
        获取房源详情查询的 eager loading 选项
        
        房源详情需要加载的关联：
        - owner: 负责员工
        - landlord_rel: 房东信息
        
        注意：media 关系使用 lazy='dynamic'，不支持 eager loading，
        在 format_house_response 函数中手动查询
        
        Returns:
            list: eager loading 选项列表
        """
        from app.models.house import House
        
        return [
            joinedload(House.owner),
            joinedload(House.landlord_rel),
            # media 使用 lazy='dynamic'，不支持 eager loading
        ]
    
    # ==================== 合同相关优化 ====================
    
    @staticmethod
    def get_contract_list_options():
        """
        获取合同列表查询的 eager loading 选项
        
        合同列表需要加载的关联：
        - house: 房源信息（多对一，使用 joinedload）
        - house.owner: 房源的负责员工（嵌套加载）
        - tenant_rel: 租客信息（多对一，使用 joinedload）
        
        注意：不加载 payments 关系，因为：
        1. 默认不需要显示支付记录
        2. Contract.payments 使用 lazy='dynamic'，与 eager loading 冲突
        
        Returns:
            list: eager loading 选项列表
        """
        from app.models.contract import Contract
        from app.models.house import House
        
        return [
            joinedload(Contract.house),           # 加载房源信息
            joinedload(Contract.house).joinedload(House.owner),     # 加载房源的负责员工
            joinedload(Contract.tenant_rel),      # 加载租客信息
        ]
    
    @staticmethod
    def get_contract_detail_options():
        """
        获取合同详情查询的 eager loading 选项
        
        合同详情需要加载的关联：
        - house: 房源信息
        - house.owner: 房源的负责员工
        - tenant_rel: 租客信息
        - payments: 支付记录列表（一对多，使用 selectinload）
        
        注意：详情页面可能需要显示支付记录，所以需要加载
        
        Returns:
            list: eager loading 选项列表
        """
        from app.models.contract import Contract
        from app.models.house import House
        
        return [
            joinedload(Contract.house),
            joinedload(Contract.house).joinedload(House.owner),
            joinedload(Contract.tenant_rel),
            selectinload(Contract.payments),      # 加载支付记录
        ]
    
    # ==================== 支付相关优化 ====================
    
    @staticmethod
    def get_payment_list_options():
        """
        获取支付列表查询的 eager loading 选项
        
        支付列表需要加载的关联：
        - contract_rel: 合同信息（多对一，使用 joinedload）
        - contract_rel.house: 合同的房源（嵌套加载）
        - contract_rel.tenant_rel: 合同的租客（嵌套加载）
        - operator: 操作人（多对一，使用 joinedload）
        
        Returns:
            list: eager loading 选项列表
        """
        from app.models.payment import Payment
        from app.models.contract import Contract
        
        return [
            joinedload(Payment.contract_rel),            # 加载合同信息
            joinedload(Payment.contract_rel).joinedload(Contract.house),      # 加载合同的房源
            joinedload(Payment.contract_rel).joinedload(Contract.tenant_rel), # 加载合同的租客
            joinedload(Payment.operator),                # 加载操作人
        ]
    
    @staticmethod
    def get_payment_detail_options():
        """
        获取支付详情查询的 eager loading 选项
        
        与列表查询相同，支付详情不需要额外的关联数据
        
        Returns:
            list: eager loading 选项列表
        """
        return QueryOptimizer.get_payment_list_options()
    
    # ==================== 通用优化工具 ====================
    
    @staticmethod
    def apply_options(query, options: List[Any]):
        """
        应用 eager loading 选项到查询
        
        Args:
            query: SQLAlchemy 查询对象
            options: eager loading 选项列表
            
        Returns:
            应用了选项的查询对象
            
        Example:
            query = House.query
            options = QueryOptimizer.get_house_list_options()
            query = QueryOptimizer.apply_options(query, options)
        """
        for option in options:
            query = query.options(option)
        return query
    
    @staticmethod
    def optimize_query(query, *load_strategies):
        """
        优化查询（链式调用方式）
        
        Args:
            query: SQLAlchemy 查询对象
            *load_strategies: 加载策略（joinedload/selectinload/subqueryload）
            
        Returns:
            应用了优化策略的查询对象
            
        Example:
            houses = QueryOptimizer.optimize_query(
                House.query,
                joinedload('owner'),
                joinedload('landlord_rel')
            ).all()
        """
        if load_strategies:
            query = query.options(*load_strategies)
        return query


class QueryPerformanceMonitor:
    """
    查询性能监控器
    
    用于监控和记录查询性能，帮助识别 N+1 问题
    """
    
    @staticmethod
    def log_query_count(label: str = "Query"):
        """
        记录当前查询数量（需要在 Flask 应用上下文中使用）
        
        Args:
            label: 查询标签
            
        Example:
            from flask import g
            from sqlalchemy import event
            from sqlalchemy.engine import Engine
            
            @event.listens_for(Engine, "before_cursor_execute")
            def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
                if not hasattr(g, 'query_count'):
                    g.query_count = 0
                g.query_count += 1
            
            # 使用
            QueryPerformanceMonitor.log_query_count("Before query")
            houses = House.query.all()
            QueryPerformanceMonitor.log_query_count("After query")
        """
        try:
            from flask import g
            if hasattr(g, 'query_count'):
                current_app.logger.info(f"[{label}] Query count: {g.query_count}")
            else:
                current_app.logger.info(f"[{label}] Query count: Not tracked")
        except Exception as e:
            current_app.logger.warning(f"Failed to log query count: {e}")
    
    @staticmethod
    def measure_time(func):
        """
        装饰器：测量函数执行时间
        
        Args:
            func: 要测量的函数
            
        Returns:
            装饰后的函数
            
        Example:
            @QueryPerformanceMonitor.measure_time
            def get_houses():
                return House.query.all()
        """
        import time
        from functools import wraps
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            end_time = time.time()
            execution_time = end_time - start_time
            current_app.logger.info(
                f"[Performance] {func.__name__} executed in {execution_time:.4f}s"
            )
            return result
        
        return wrapper


# ==================== 便捷函数 ====================

def optimize_house_query(query):
    """
    优化房源查询（列表）
    
    Args:
        query: House 查询对象
        
    Returns:
        优化后的查询对象
    """
    return QueryOptimizer.apply_options(
        query,
        QueryOptimizer.get_house_list_options()
    )


def optimize_house_detail_query(query):
    """
    优化房源查询（详情）
    
    Args:
        query: House 查询对象
        
    Returns:
        优化后的查询对象
    """
    return QueryOptimizer.apply_options(
        query,
        QueryOptimizer.get_house_detail_options()
    )


def optimize_contract_query(query):
    """
    优化合同查询（列表）
    
    Args:
        query: Contract 查询对象
        
    Returns:
        优化后的查询对象
    """
    return QueryOptimizer.apply_options(
        query,
        QueryOptimizer.get_contract_list_options()
    )


def optimize_contract_detail_query(query):
    """
    优化合同查询（详情）
    
    Args:
        query: Contract 查询对象
        
    Returns:
        优化后的查询对象
    """
    return QueryOptimizer.apply_options(
        query,
        QueryOptimizer.get_contract_detail_options()
    )


def optimize_payment_query(query):
    """
    优化支付查询（列表）
    
    Args:
        query: Payment 查询对象
        
    Returns:
        优化后的查询对象
    """
    return QueryOptimizer.apply_options(
        query,
        QueryOptimizer.get_payment_list_options()
    )


def optimize_payment_detail_query(query):
    """
    优化支付查询（详情）
    
    Args:
        query: Payment 查询对象
        
    Returns:
        优化后的查询对象
    """
    return QueryOptimizer.apply_options(
        query,
        QueryOptimizer.get_payment_detail_options()
    )


# ==================== 使用示例 ====================

"""
使用示例：

# 示例 1：房源列表查询优化
from app.utils.query_optimizer import optimize_house_query

# 优化前（N+1 问题）
houses = House.query.all()  # 1 次查询
for house in houses:
    print(house.owner.username)  # N 次查询
    print(house.landlord_rel.name)  # N 次查询

# 优化后（1 次查询）
houses = optimize_house_query(House.query).all()  # 1 次查询（使用 JOIN）
for house in houses:
    print(house.owner.username)  # 0 次查询（已加载）
    print(house.landlord_rel.name)  # 0 次查询（已加载）


# 示例 2：合同列表查询优化
from app.utils.query_optimizer import optimize_contract_query

# 优化前（N+1 问题）
contracts = Contract.query.all()  # 1 次查询
for contract in contracts:
    print(contract.house.title)  # N 次查询
    print(contract.tenant_rel.name)  # N 次查询

# 优化后（1 次查询）
contracts = optimize_contract_query(Contract.query).all()  # 1 次查询
for contract in contracts:
    print(contract.house.title)  # 0 次查询（已加载）
    print(contract.tenant_rel.name)  # 0 次查询（已加载）


# 示例 3：支付列表查询优化
from app.utils.query_optimizer import optimize_payment_query

# 优化前（N+1 问题）
payments = Payment.query.all()  # 1 次查询
for payment in payments:
    print(payment.contract_rel.contract_no)  # N 次查询
    print(payment.contract_rel.tenant_rel.name)  # N 次查询

# 优化后（1 次查询）
payments = optimize_payment_query(Payment.query).all()  # 1 次查询
for payment in payments:
    print(payment.contract_rel.contract_no)  # 0 次查询（已加载）
    print(payment.contract_rel.tenant_rel.name)  # 0 次查询（已加载）


# 示例 4：使用 QueryOptimizer 类
from app.utils.query_optimizer import QueryOptimizer
from sqlalchemy.orm import joinedload, selectinload

# 自定义加载策略
houses = QueryOptimizer.optimize_query(
    House.query,
    joinedload('owner'),
    selectinload('media')
).all()


# 示例 5：性能监控
from app.utils.query_optimizer import QueryPerformanceMonitor

@QueryPerformanceMonitor.measure_time
def get_houses_with_monitoring():
    return optimize_house_query(House.query).all()

houses = get_houses_with_monitoring()
# 日志输出：[Performance] get_houses_with_monitoring executed in 0.0234s
"""
