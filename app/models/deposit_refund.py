"""
押金退款模型
"""
from datetime import datetime, date
from .base import db, BaseModel


class DepositRefund(BaseModel):
    """
    押金退款模型

    用于管理合同结束后的押金退款流程
    支持扣款项管理和退款状态跟踪
    """

    __tablename__ = 'deposit_refunds'

    # 外键关联
    contract_id = db.Column(db.Integer, db.ForeignKey('contracts.id'), nullable=False, comment='合同 ID')
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False, comment='租客 ID')
    house_id = db.Column(db.Integer, db.ForeignKey('houses.id'), nullable=False, comment='房源 ID')

    # 押金信息
    original_deposit = db.Column(db.Numeric(10, 2), nullable=False, comment='原始押金金额')
    deductions = db.Column(db.JSON, default=list, comment='扣款项列表（JSON格式）')
    total_deduction = db.Column(db.Numeric(10, 2), default=0, comment='总扣款金额')
    refund_amount = db.Column(db.Numeric(10, 2), nullable=False, comment='实际退款金额')

    # 退款状态：pending-待处理，processed-已处理，completed-已完成，cancelled-已取消
    status = db.Column(db.String(20), default='pending', comment='退款状态')

    # 处理信息
    processed_by = db.Column(db.Integer, db.ForeignKey('users.id'), comment='处理人 ID')
    processed_at = db.Column(db.DateTime, comment='处理时间')
    completed_at = db.Column(db.DateTime, comment='完成时间')

    # 备注
    remark = db.Column(db.Text, comment='备注')

    # 索引
    __table_args__ = (
        db.Index('idx_deposit_refunds_contract_id', 'contract_id'),
        db.Index('idx_deposit_refunds_tenant_id', 'tenant_id'),
        db.Index('idx_deposit_refunds_house_id', 'house_id'),
        db.Index('idx_deposit_refunds_status', 'status'),
        db.Index('idx_deposit_refunds_processed_by', 'processed_by'),
    )

    # 关系
    contract = db.relationship('Contract', foreign_keys=[contract_id], lazy='select')
    tenant = db.relationship('Tenant', foreign_keys=[tenant_id], lazy='select')
    house = db.relationship('House', foreign_keys=[house_id], lazy='select')
    processor = db.relationship('User', foreign_keys=[processed_by], lazy='select')

    # 扣款项类型常量
    DEDUCTION_TYPES = {
        'unpaid_rent': '未付租金',
        'unpaid_utilities': '未付水电费',
        'late_fees': '滞纳金',
        'damage_compensation': '损坏赔偿',
        'other': '其他扣款'
    }

    # 状态映射
    STATUS_NAMES = {
        'pending': '待处理',
        'processed': '已处理',
        'completed': '已完成',
        'cancelled': '已取消'
    }

    def calculate_total_deduction(self):
        """计算总扣款金额"""
        if not self.deductions:
            self.total_deduction = 0
        else:
            self.total_deduction = sum(
                deduction.get('amount', 0) for deduction in self.deductions
            )
        self.refund_amount = self.original_deposit - self.total_deduction
        return self.total_deduction

    def add_deduction(self, deduction_type, amount, description=''):
        """
        添加扣款项

        Args:
            deduction_type: 扣款类型
            amount: 扣款金额
            description: 扣款说明
        """
        if not self.deductions:
            self.deductions = []

        self.deductions.append({
            'type': deduction_type,
            'type_name': self.DEDUCTION_TYPES.get(deduction_type, deduction_type),
            'amount': float(amount),
            'description': description
        })

        self.calculate_total_deduction()

    def remove_deduction(self, index):
        """
        移除扣款项

        Args:
            index: 扣款项索引
        """
        if self.deductions and 0 <= index < len(self.deductions):
            self.deductions.pop(index)
            self.calculate_total_deduction()

    def process(self, processed_by):
        """
        处理退款

        Args:
            processed_by: 处理人 ID
        """
        self.status = 'processed'
        self.processed_by = processed_by
        self.processed_at = datetime.now()

    def complete(self):
        """完成退款"""
        self.status = 'completed'
        self.completed_at = datetime.now()
    
    def can_complete(self):
        """
        检查是否可以完成退款
        
        Returns:
            tuple: (是否可以完成, 错误消息)
        """
        if self.status != 'processed':
            return False, "只有已处理状态的退款才能完成"
        
        # 检查合同押金状态
        from app.models.contract import Contract
        contract = Contract.query.get(self.contract_id)
        if contract and contract.deposit_status not in ['paid', 'transferred']:
            return False, f"合同押金状态为 '{contract.DEPOSIT_STATUS.get(contract.deposit_status)}'，无法退款"
        
        return True, None

    def cancel(self, reason=''):
        """
        取消退款

        Args:
            reason: 取消原因
        """
        self.status = 'cancelled'
        if reason:
            if self.remark:
                self.remark += f'\n取消原因：{reason}'
            else:
                self.remark = f'取消原因：{reason}'

    def get_deduction_summary(self):
        """获取扣款项汇总"""
        summary = {}
        for deduction in (self.deductions or []):
            deduction_type = deduction.get('type', 'other')
            if deduction_type not in summary:
                summary[deduction_type] = {
                    'type': deduction_type,
                    'type_name': self.DEDUCTION_TYPES.get(deduction_type, deduction_type),
                    'total_amount': 0,
                    'count': 0,
                    'items': []
                }
            summary[deduction_type]['total_amount'] += deduction.get('amount', 0)
            summary[deduction_type]['count'] += 1
            summary[deduction_type]['items'].append(deduction)

        return list(summary.values())

    def to_dict(self):
        """转换为字典"""
        data = super().to_dict()

        try:
            if self.contract:
                data['contract_no'] = self.contract.contract_no
                data['contract_title'] = self.contract.title
                # 添加押金状态信息
                data['deposit_status'] = self.contract.deposit_status
                data['deposit_status_name'] = self.contract.DEPOSIT_STATUS.get(
                    self.contract.deposit_status, self.contract.deposit_status
                )
        except Exception:
            pass

        try:
            if self.tenant:
                data['tenant_name'] = self.tenant.name
                data['tenant_phone'] = self.tenant.phone
        except Exception:
            pass

        try:
            if self.house:
                data['house_title'] = self.house.title
                data['house_address'] = self.house.address
        except Exception:
            pass

        try:
            if self.processor:
                data['processor_name'] = self.processor.username
        except Exception:
            pass

        data['deduction_summary'] = self.get_deduction_summary()
        data['status_name'] = self.STATUS_NAMES.get(self.status, self.status)

        if self.processed_at:
            data['processed_at'] = self.processed_at.strftime('%Y-%m-%d %H:%M:%S')
        if self.completed_at:
            data['completed_at'] = self.completed_at.strftime('%Y-%m-%d %H:%M:%S')

        return data

    def __repr__(self):
        return f'<DepositRefund {self.id} - Contract {self.contract_id}>'
