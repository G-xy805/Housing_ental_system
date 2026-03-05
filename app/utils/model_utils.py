"""
模型工具函数

提供模型相关的通用工具函数，减少代码重复
"""
from datetime import datetime, date
from typing import Any, Dict, List, Optional, Type
from decimal import Decimal


def format_datetime(value: Optional[datetime]) -> Optional[str]:
    """
    格式化 datetime 对象为字符串
    
    Args:
        value: datetime 对象
        
    Returns:
        str: 格式化后的时间字符串（YYYY-MM-DD HH:MM:SS）
    """
    if value is None:
        return None
    return value.strftime('%Y-%m-%d %H:%M:%S')


def format_date(value: Optional[date]) -> Optional[str]:
    """
    格式化 date 对象为字符串
    
    Args:
        value: date 对象
        
    Returns:
        str: 格式化后的日期字符串（YYYY-MM-DD）
    """
    if value is None:
        return None
    return value.isoformat()


def serialize_model_to_dict(
    model_instance,
    exclude_fields: Optional[List[str]] = None,
    include_fields: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    将 SQLAlchemy 模型实例序列化为字典
    
    Args:
        model_instance: SQLAlchemy 模型实例
        exclude_fields: 需要排除的字段列表
        include_fields: 需要包含的字段列表（如果指定，则只包含这些字段）
        
    Returns:
        Dict: 序列化后的字典
    """
    if model_instance is None:
        return None
    
    result = {}
    
    # 获取所有列
    for column in model_instance.__table__.columns:
        field_name = column.name
        
        # 如果指定了包含字段列表，只包含这些字段
        if include_fields and field_name not in include_fields:
            continue
        
        # 排除指定字段
        if exclude_fields and field_name in exclude_fields:
            continue
        
        value = getattr(model_instance, field_name)
        
        # 格式化日期时间
        if isinstance(value, datetime):
            value = format_datetime(value)
        elif isinstance(value, date):
            value = format_date(value)
        
        result[field_name] = value
    
    return result


def generate_unique_number(prefix: str, length: int = 8) -> str:
    """
    生成唯一编号
    
    Args:
        prefix: 编号前缀
        length: 随机部分长度
        
    Returns:
        str: 唯一编号（格式：前缀 + 年月日 + 随机数）
    """
    import uuid
    timestamp = datetime.now().strftime('%Y%m%d')
    unique_id = uuid.uuid4().hex[:length].upper()
    return f'{prefix}{timestamp}{unique_id}'


def calculate_late_fee(
    amount: float,
    due_date: date,
    current_date: Optional[date] = None,
    daily_rate: Decimal = Decimal('0.0005'),
    max_rate: Decimal = Decimal('0.2')
) -> tuple:
    """
    计算滞纳金
    
    Args:
        amount: 应缴金额
        due_date: 应缴日期
        current_date: 当前日期（默认今天）
        daily_rate: 日利率（默认 0.05%）
        max_rate: 滞纳金上限比例（默认 20%）
        
    Returns:
        tuple: (滞纳金金额, 逾期天数)
    """
    if current_date is None:
        current_date = date.today()
    
    # 如果未到期，不计算滞纳金
    if current_date <= due_date:
        return 0.0, 0
    
    # 计算逾期天数
    overdue_days = (current_date - due_date).days
    
    # 计算滞纳金
    base_amount = Decimal(str(amount))
    calculated_late_fee = base_amount * daily_rate * overdue_days
    
    # 应用滞纳金上限
    max_late_fee = base_amount * max_rate
    final_late_fee = min(calculated_late_fee, max_late_fee)
    
    return float(final_late_fee), overdue_days


def calculate_total_rent(
    start_date: date,
    end_date: date,
    monthly_rent: float
) -> float:
    """
    计算合同期内的总租金
    
    Args:
        start_date: 开始日期
        end_date: 结束日期
        monthly_rent: 月租金
        
    Returns:
        float: 总租金
    """
    # 计算租赁月数
    months = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month)
    
    # 如果有剩余天数，按天计算
    remaining_days = (end_date.day - start_date.day)
    if remaining_days > 0:
        daily_rent = monthly_rent / 30
        return months * monthly_rent + remaining_days * daily_rent
    
    return months * monthly_rent


def calculate_service_fee(
    contract_amount: float,
    service_fee_rate: float,
    minimum_fee: Optional[float] = None
) -> float:
    """
    计算服务费
    
    Args:
        contract_amount: 合同金额
        service_fee_rate: 服务费率（百分比）
        minimum_fee: 最低服务费
        
    Returns:
        float: 服务费金额
    """
    if not contract_amount or contract_amount <= 0:
        return 0.0
    
    # 计算服务费
    service_fee = contract_amount * (service_fee_rate / 100)
    
    # 如果有最低服务费，取较大值
    if minimum_fee and minimum_fee > 0:
        service_fee = max(service_fee, minimum_fee)
    
    return round(service_fee, 2)


def calculate_contract_term(start_date: date, end_date: date) -> float:
    """
    计算合同期限（月数）
    
    Args:
        start_date: 开始日期
        end_date: 结束日期
        
    Returns:
        float: 合同期限（月数）
    """
    days = (end_date - start_date).days
    return round(days / 30, 1)


def get_days_until_expiry(end_date: date) -> int:
    """
    获取距离到期天数
    
    Args:
        end_date: 结束日期
        
    Returns:
        int: 距离到期天数（负数表示已过期）
    """
    delta = end_date - date.today()
    return delta.days


def is_expired(end_date: date) -> bool:
    """
    检查是否已过期
    
    Args:
        end_date: 结束日期
        
    Returns:
        bool: 是否已过期
    """
    return date.today() > end_date


def is_expiring_soon(end_date: date, days: int = 30) -> bool:
    """
    检查是否即将到期
    
    Args:
        end_date: 结束日期
        days: 提前天数
        
    Returns:
        bool: 是否即将到期
    """
    from datetime import timedelta
    expiring_date = end_date - timedelta(days=days)
    return date.today() >= expiring_date and not is_expired(end_date)


def format_file_size(size_bytes: int) -> str:
    """
    格式化文件大小
    
    Args:
        size_bytes: 文件大小（字节）
        
    Returns:
        str: 格式化后的文件大小（如：1.5 MB）
    """
    if not size_bytes:
        return '0 B'
    
    size_units = ['B', 'KB', 'MB', 'GB']
    size = size_bytes
    unit_index = 0
    
    while size >= 1024 and unit_index < len(size_units) - 1:
        size /= 1024
        unit_index += 1
    
    return f'{size:.2f} {size_units[unit_index]}'


def mask_sensitive_data(data: str, show_length: int = 4) -> str:
    """
    脱敏敏感数据
    
    Args:
        data: 原始数据
        show_length: 显示的字符数
        
    Returns:
        str: 脱敏后的数据
    """
    if not data:
        return None
    
    if len(data) <= show_length:
        return '*' * len(data)
    
    # 显示前几位和后几位
    masked = '*' * (len(data) - show_length) + data[-show_length:]
    
    # 格式化银行卡号（每4位一组）
    if len(data) >= 16:
        return ' '.join([masked[i:i+4] for i in range(0, len(masked), 4)])
    
    return masked


class ModelSerializer:
    """
    模型序列化器基类
    
    提供统一的序列化接口，支持：
    - 字段过滤
    - 嵌套对象序列化
    - 计算字段
    """
    
    # 默认排除的字段
    DEFAULT_EXCLUDE_FIELDS = {'password_hash', 'id_card_encrypted', 'bank_card_encrypted'}
    
    # 计算字段映射
    COMPUTED_FIELDS = {}
    
    @classmethod
    def serialize(
        cls,
        instance,
        exclude_fields: Optional[List[str]] = None,
        include_fields: Optional[List[str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        序列化模型实例
        
        Args:
            instance: 模型实例
            exclude_fields: 排除字段
            include_fields: 包含字段
            **kwargs: 额外参数
            
        Returns:
            Dict: 序列化后的字典
        """
        # 合并默认排除字段
        all_exclude = cls.DEFAULT_EXCLUDE_FIELDS.copy()
        if exclude_fields:
            all_exclude.update(exclude_fields)
        
        # 序列化基础字段
        result = serialize_model_to_dict(
            instance,
            exclude_fields=list(all_exclude),
            include_fields=include_fields
        )
        
        # 添加计算字段
        for field_name, method_name in cls.COMPUTED_FIELDS.items():
            if hasattr(instance, method_name):
                method = getattr(instance, method_name)
                result[field_name] = method()
        
        return result
    
    @classmethod
    def serialize_list(
        cls,
        instances: List,
        exclude_fields: Optional[List[str]] = None,
        include_fields: Optional[List[str]] = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        序列化模型实例列表
        
        Args:
            instances: 模型实例列表
            exclude_fields: 排除字段
            include_fields: 包含字段
            **kwargs: 额外参数
            
        Returns:
            List[Dict]: 序列化后的字典列表
        """
        return [
            cls.serialize(
                instance,
                exclude_fields=exclude_fields,
                include_fields=include_fields,
                **kwargs
            )
            for instance in instances
        ]
