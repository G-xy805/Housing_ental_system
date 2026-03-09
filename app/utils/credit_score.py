"""
信用评分工具类

定义信用事件权重和计算规则
"""
from enum import Enum


class CreditEventType(Enum):
    """信用事件类型"""
    LATE_PAYMENT_7 = 'late_payment_7'
    LATE_PAYMENT_30 = 'late_payment_30'
    EARLY_TERMINATION = 'early_termination'
    ON_TIME_PAYMENT = 'on_time_payment'
    CONTRACT_COMPLETE = 'contract_complete'


class CreditScoreConfig:
    """信用评分配置"""
    
    SCORE_MIN = 0
    SCORE_MAX = 100
    SCORE_DEFAULT = 100
    
    EVENT_WEIGHTS = {
        CreditEventType.LATE_PAYMENT_7: {
            'score_change': -5,
            'description': '逾期付款7天',
            'event_type': 'late_payment'
        },
        CreditEventType.LATE_PAYMENT_30: {
            'score_change': -15,
            'description': '逾期付款30天',
            'event_type': 'late_payment'
        },
        CreditEventType.EARLY_TERMINATION: {
            'score_change': -20,
            'description': '提前解约',
            'event_type': 'early_termination'
        },
        CreditEventType.ON_TIME_PAYMENT: {
            'score_change': 2,
            'description': '按时付款',
            'event_type': 'on_time_payment'
        },
        CreditEventType.CONTRACT_COMPLETE: {
            'score_change': 10,
            'description': '合同正常完成',
            'event_type': 'contract_complete'
        }
    }
    
    @classmethod
    def get_event_config(cls, event_type):
        """
        获取事件配置
        
        Args:
            event_type: CreditEventType 枚举值
            
        Returns:
            dict: 事件配置
        """
        return cls.EVENT_WEIGHTS.get(event_type, {})
    
    @classmethod
    def get_score_change(cls, event_type):
        """
        获取分数变化值
        
        Args:
            event_type: CreditEventType 枚举值
            
        Returns:
            int: 分数变化值
        """
        config = cls.get_event_config(event_type)
        return config.get('score_change', 0)
    
    @classmethod
    def get_event_description(cls, event_type):
        """
        获取事件描述
        
        Args:
            event_type: CreditEventType 枚举值
            
        Returns:
            str: 事件描述
        """
        config = cls.get_event_config(event_type)
        return config.get('description', '')
    
    @classmethod
    def normalize_score(cls, score):
        """
        标准化信用评分（限制在 0-100 范围内）
        
        Args:
            score: 原始评分
            
        Returns:
            int: 标准化后的评分
        """
        return max(cls.SCORE_MIN, min(cls.SCORE_MAX, score))
    
    @classmethod
    def get_credit_level(cls, score):
        """
        获取信用等级
        
        Args:
            score: 信用评分
            
        Returns:
            str: 信用等级
        """
        if score >= 90:
            return '优秀'
        elif score >= 80:
            return '良好'
        elif score >= 70:
            return '中等'
        elif score >= 60:
            return '一般'
        else:
            return '较差'
