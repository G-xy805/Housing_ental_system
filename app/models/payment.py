"""
支付记录模型
"""
from datetime import datetime, date, timedelta
from decimal import Decimal
from .base import db, BaseModel


# 滞纳金配置（全局可配置）
LATE_FEE_RATE = Decimal('0.0005')  # 每日 0.05%
LATE_FEE_MAX_RATE = Decimal('0.2')  # 滞纳金上限 20%


class Payment(BaseModel):
    """
    支付记录模型
    
    支持租金、押金、水电费等支付
    支持滞纳金自动计算
    """
    
    __tablename__ = 'payments'
    
    # 支付编号
    payment_no = db.Column(db.String(50), unique=True, nullable=False, comment='支付编号')
    
    # 支付信息
    amount = db.Column(db.Float, nullable=False, comment='应缴金额')
    paid_amount = db.Column(db.Float, default=0, comment='实缴金额')
    
    # 支付类型：rent-租金，deposit-押金，utility-水电费，other-其他
    payment_type = db.Column(db.String(20), nullable=False, comment='支付类型')
    
    # 支付方式：cash-现金，bank-银行转账，wechat-微信，alipay-支付宝
    payment_method = db.Column(db.String(50), comment='支付方式')
    
    # 支付周期
    period_start = db.Column(db.Date, comment='支付周期开始')
    period_end = db.Column(db.Date, comment='周期结束')
    
    # 支付日期
    payment_date = db.Column(db.Date, comment='实际支付日期')
    due_date = db.Column(db.Date, nullable=False, comment='应缴日期')
    confirmed_date = db.Column(db.DateTime, comment='确认到账日期')
    
    # 滞纳金
    late_fee = db.Column(db.Float, default=0, comment='滞纳金金额')
    late_fee_rate = db.Column(db.Float, default=0.0005, comment='滞纳金比例（每日）')
    overdue_days = db.Column(db.Integer, default=0, comment='逾期天数')
    
    # 状态：pending-待支付，paid-已支付，overdue-逾期，partial-部分支付，refunded-已退款
    status = db.Column(db.String(20), default='pending', comment='支付状态')
    
    # 备注
    remark = db.Column(db.Text, comment='备注')
    
    # 凭证
    receipt_file = db.Column(db.String(255), comment='收据/凭证文件路径')
    
    # 外键
    contract_id = db.Column(db.Integer, db.ForeignKey('contracts.id'), comment='合同 ID')
    
    # 操作人
    operator_id = db.Column(db.Integer, db.ForeignKey('users.id'), comment='操作人 ID')
    
    # 索引
    __table_args__ = (
        db.Index('idx_payments_contract_id', 'contract_id'),
        db.Index('idx_payments_status', 'status'),
        db.Index('idx_payments_due_date', 'due_date'),
        db.Index('idx_payments_payment_type', 'payment_type'),
    )
    
    # 关系
    operator = db.relationship('User', foreign_keys=[operator_id])
    contract_rel = db.relationship('Contract', back_populates='payments', lazy='joined')
    
    # 支付类型映射
    PAYMENT_TYPES = {
        'rent': '租金',
        'deposit': '押金',
        'utility': '水电费',
        'other': '其他'
    }
    
    # 支付方式映射
    PAYMENT_METHODS = {
        'cash': '现金',
        'bank': '银行转账',
        'wechat': '微信',
        'alipay': '支付宝'
    }
    
    @classmethod
    def generate_payment_no(cls):
        """生成支付编号"""
        import uuid
        timestamp = datetime.now().strftime('%Y%m%d')
        unique_id = uuid.uuid4().hex[:8].upper()
        return f'PY{timestamp}{unique_id}'
    
    def calculate_late_fee(self, current_date=None):
        """
        计算滞纳金
        
        Args:
            current_date: 计算日期，默认为今天
            
        Returns:
            tuple: (滞纳金金额，逾期天数)
        """
        if current_date is None:
            current_date = date.today()
        
        # 如果已支付或未到期，不计算滞纳金
        if self.status == 'paid' or current_date <= self.due_date:
            return 0, 0
        
        # 计算逾期天数
        overdue_days = (current_date - self.due_date).days
        self.overdue_days = overdue_days
        
        # 计算滞纳金：应缴金额 × 日利率 × 逾期天数
        base_amount = Decimal(str(self.amount))
        rate = Decimal(str(self.late_fee_rate or LATE_FEE_RATE))
        calculated_late_fee = base_amount * rate * overdue_days
        
        # 应用滞纳金上限
        max_late_fee = base_amount * Decimal(str(LATE_FEE_MAX_RATE))
        final_late_fee = min(calculated_late_fee, max_late_fee)
        
        self.late_fee = float(final_late_fee)
        return float(final_late_fee), overdue_days
    
    def get_total_amount(self):
        """获取应缴总额（含滞纳金）"""
        self.calculate_late_fee()
        return self.amount + self.late_fee
    
    def mark_as_paid(self, paid_amount, payment_date=None, payment_method=None):
        """
        标记为已支付
        
        Args:
            paid_amount: 实付金额
            payment_date: 支付日期
            payment_method: 支付方式
        """
        if payment_date is None:
            payment_date = date.today()
        
        self.paid_amount = paid_amount
        self.payment_date = payment_date
        self.payment_method = payment_method
        self.confirmed_date = datetime.now()
        
        # 计算滞纳金
        self.calculate_late_fee(payment_date)
        
        # 判断支付状态
        total_amount = self.get_total_amount()
        if paid_amount >= total_amount:
            self.status = 'paid'
        elif paid_amount > 0:
            self.status = 'partial'
        else:
            self.status = 'overdue'
    
    def is_overdue(self, current_date=None):
        """检查是否逾期"""
        if current_date is None:
            current_date = date.today()
        return current_date > self.due_date and self.status != 'paid'
    
    def get_days_until_due(self):
        """获取距离到期天数"""
        delta = self.due_date - date.today()
        return delta.days
    
    def to_dict(self):
        """转换为字典"""
        data = super().to_dict()
        if self.contract_rel:
            data['contract_no'] = self.contract_rel.contract_no
            if self.contract_rel.tenant_rel:
                data['tenant_name'] = self.contract_rel.tenant_rel.name
                data['tenant_phone'] = self.contract_rel.tenant_rel.phone
        if self.operator:
            data['operator_name'] = self.operator.username
        data['total_amount'] = self.get_total_amount()
        data['is_overdue'] = self.is_overdue()
        data['days_until_due'] = self.get_days_until_due()
        data['payment_type_name'] = self.PAYMENT_TYPES.get(self.payment_type, self.payment_type)
        data['payment_method_name'] = self.PAYMENT_METHODS.get(self.payment_method, self.payment_method)
        return data
    
    def __repr__(self):
        return f'<Payment {self.payment_no}>'
    
    def to_dict(self):
        """转换为字典"""
        data = super().to_dict()
        if self.contract_rel:
            data['contract_no'] = self.contract_rel.contract_no
        if self.operator:
            data['operator_name'] = self.operator.username
        return data
    
    def __repr__(self):
        return f'<Payment {self.payment_no}>'
