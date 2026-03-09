"""
租客模型
"""
import hashlib
from datetime import datetime
from .base import db, BaseModel
from app.utils.aes_encryption import (
    encrypt_sensitive_data, 
    decrypt_sensitive_data,
    HybridEncryptor
)
from app.utils.sensitive_data_audit import SensitiveDataAuditLogger


def calculate_id_card_hash(id_card: str) -> str:
    """
    计算身份证号的哈希值（用于快速查重）
    
    使用 SHA-256 哈希算法，确保相同身份证号生成相同的哈希值
    这样可以在不解密的情况下快速检测重复
    
    Args:
        id_card: 身份证号明文
        
    Returns:
        str: 64 位十六进制哈希值
    """
    if not id_card:
        return None
    # 统一转为大写，确保 X 和 x 生成相同的哈希值
    normalized = id_card.strip().upper()
    return hashlib.sha256(normalized.encode('utf-8')).hexdigest()


class Tenant(BaseModel):
    """
    租客模型
    
    用于管理租客信息，支持同一房源多个租客（合租场景）
    租客可以与多个合同关联
    
    安全特性：
    - 身份证号使用 AES-256-GCM 加密存储
    - 支持向后兼容旧的 Fernet 加密数据
    - 所有加密操作记录审计日志
    - 所有敏感数据访问记录审计日志
    """
    
    __tablename__ = 'tenants'
    
    # 基本信息
    name = db.Column(db.String(50), nullable=False, comment='姓名')
    
    # 身份证号（加密存储）
    id_card_encrypted = db.Column(db.Text, comment='身份证号（AES-256-GCM 加密存储）')
    
    # 身份证号哈希值（用于快速查重，无需解密）
    id_card_hash = db.Column(db.String(64), index=True, unique=True, comment='身份证号哈希值（SHA-256，用于快速查重）')
    
    # 联系方式
    phone = db.Column(db.String(20), nullable=False, comment='联系电话')
    email = db.Column(db.String(120), comment='电子邮箱')
    
    # 紧急联系人
    emergency_contact = db.Column(db.String(50), comment='紧急联系人姓名')
    emergency_phone = db.Column(db.String(20), comment='紧急联系人电话')
    emergency_relation = db.Column(db.String(20), comment='与紧急联系人关系')
    
    # 工作信息
    company = db.Column(db.String(100), comment='工作单位')
    occupation = db.Column(db.String(50), comment='职业')
    
    # 租客状态：pending-待租/潜在租客，active-在租，expired-已退租，blacklisted-黑名单
    status = db.Column(db.String(20), default='pending', comment='租客状态')
    
    # 备注
    remark = db.Column(db.Text, comment='备注')
    
    # 个人照片
    photo = db.Column(db.String(255), comment='个人照片 URL')
    
    # 信用评分
    credit_score = db.Column(db.Integer, default=100, comment='信用评分（0-100）')
    credit_records = db.Column(db.JSON, default=list, comment='信用记录列表')
    
    # 索引
    __table_args__ = (
        db.Index('idx_tenants_phone', 'phone'),
        db.Index('idx_tenants_status', 'status'),
        db.Index('idx_tenants_credit_score', 'credit_score'),
    )
    
    # 关系 - 通过合同关联房源
    contracts = db.relationship('Contract', back_populates='tenant_rel', lazy='dynamic')
    
    def set_id_card(self, id_card_number, user_id=None):
        """
        设置身份证号并使用 AES-256-GCM 加密存储
        
        同时计算并存储哈希值，用于快速查重
        
        Args:
            id_card_number: 身份证号明文
            user_id: 操作用户 ID（用于审计日志）
        """
        # 获取旧值用于审计
        old_value = None
        if self.id_card_encrypted:
            try:
                old_value = decrypt_sensitive_data(
                    encrypted_data=self.id_card_encrypted,
                    field_name='id_card',
                    model_name='Tenant',
                    record_id=self.id if self.id else 0,
                    user_id=user_id
                )
            except:
                pass
        
        # 加密存储身份证号
        self.id_card_encrypted = encrypt_sensitive_data(
            data=id_card_number,
            field_name='id_card',
            model_name='Tenant',
            record_id=self.id if self.id else 0,
            user_id=user_id
        )
        
        # 计算并存储哈希值（用于快速查重）
        self.id_card_hash = calculate_id_card_hash(id_card_number)
        
        # 记录敏感数据修改审计日志
        SensitiveDataAuditLogger.log_modify(
            model_name='Tenant',
            record_id=self.id if self.id else 0,
            field_name='id_card',
            field_display_name='身份证号',
            old_value=old_value,
            new_value=id_card_number,
            user_id=user_id,
            remark='设置身份证号'
        )
    
    def get_id_card(self, user_id=None):
        """
        获取解密后的身份证号
        
        Args:
            user_id: 操作用户 ID（用于审计日志）
            
        Returns:
            str: 解密后的身份证号
        """
        decrypted = decrypt_sensitive_data(
            encrypted_data=self.id_card_encrypted,
            field_name='id_card',
            model_name='Tenant',
            record_id=self.id if self.id else 0,
            user_id=user_id
        )
        
        # 记录敏感数据查看审计日志
        if decrypted:
            SensitiveDataAuditLogger.log_view(
                model_name='Tenant',
                record_id=self.id if self.id else 0,
                field_name='id_card',
                field_display_name='身份证号',
                user_id=user_id,
                remark='查看身份证号'
            )
        
        return decrypted
    
    def verify_id_card(self, id_card_number, user_id=None):
        """
        验证身份证号是否匹配
        
        Args:
            id_card_number: 待验证的身份证号
            user_id: 操作用户 ID（用于审计日志）
            
        Returns:
            bool: 是否匹配
        """
        decrypted = self.get_id_card(user_id=user_id)
        return decrypted == id_card_number
    
    def needs_re_encryption(self):
        """
        检查是否需要重新加密（从 Fernet 迁移到 AES-256-GCM）
        
        Returns:
            bool: 是否需要重新加密
        """
        if self.id_card_encrypted and not HybridEncryptor.is_encrypted_with_aes(self.id_card_encrypted):
            return True
        return False
    
    def re_encrypt_data(self, user_id=None):
        """
        重新加密数据（从 Fernet 迁移到 AES-256-GCM）
        
        Args:
            user_id: 操作用户 ID（用于审计日志）
        """
        if self.id_card_encrypted and not HybridEncryptor.is_encrypted_with_aes(self.id_card_encrypted):
            decrypted = decrypt_sensitive_data(
                encrypted_data=self.id_card_encrypted,
                field_name='id_card',
                model_name='Tenant',
                record_id=self.id if self.id else 0,
                user_id=user_id
            )
            if decrypted:
                self.set_id_card(decrypted, user_id=user_id)
    
    def get_active_contracts(self):
        """获取当前有效的合同"""
        from .contract import Contract
        return self.contracts.filter(
            Contract.status.in_(['active', 'draft']),
            Contract.end_date >= datetime.now().date()
        ).all()
    
    def get_current_houses(self):
        """获取当前租住的房源"""
        active_contracts = self.get_active_contracts()
        return [contract.house for contract in active_contracts if contract.house]
    
    def update_status(self):
        """
        根据合同状态自动更新租客状态
        
        状态更新规则：
        - 如果有活跃合同（active/draft 且未过期），状态为 active
        - 如果没有活跃合同但有过期/终止的合同，状态为 expired
        - 如果从未有过合同，状态为 pending
        - blacklisted 状态不自动更新（需要手动设置）
        
        Returns:
            str: 更新后的状态
        """
        from datetime import date
        
        if self.status == 'blacklisted':
            return self.status
        
        active_contracts = self.get_active_contracts()
        
        if active_contracts:
            new_status = 'active'
        else:
            all_contracts = self.contracts.all()
            has_historical_contracts = any(
                c.status in ['expired', 'terminated', 'renewed'] or 
                (c.status == 'active' and c.end_date < date.today())
                for c in all_contracts
            )
            
            if has_historical_contracts:
                new_status = 'expired'
            else:
                new_status = 'pending'
        
        if self.status != new_status:
            self.status = new_status
        
        return self.status
    
    def add_credit_record(self, event_type, score_change, description, related_id=None, user_id=None):
        """
        添加信用记录并更新信用评分
        
        Args:
            event_type: 事件类型（late_payment/on_time_payment/contract_complete/early_termination）
            score_change: 分数变化（正数加分，负数减分）
            description: 事件描述
            related_id: 关联ID（合同ID或支付ID）
            user_id: 操作用户ID
            
        Returns:
            dict: 新增的信用记录
        """
        from datetime import datetime
        
        record = {
            'event_type': event_type,
            'score_change': score_change,
            'description': description,
            'related_id': related_id,
            'created_at': datetime.now().isoformat()
        }
        
        if not self.credit_records:
            self.credit_records = []
        
        self.credit_records.append(record)
        
        new_score = self.credit_score + score_change
        self.credit_score = max(0, min(100, new_score))
        
        return record
    
    def get_credit_records(self, limit=None):
        """
        获取信用记录
        
        Args:
            limit: 限制返回数量
            
        Returns:
            list: 信用记录列表（按时间倒序）
        """
        records = self.credit_records or []
        sorted_records = sorted(records, key=lambda x: x.get('created_at', ''), reverse=True)
        
        if limit:
            return sorted_records[:limit]
        return sorted_records
    
    def calculate_credit_score_from_history(self):
        """
        根据历史信用记录重新计算信用评分
        
        Returns:
            int: 重新计算的信用评分
        """
        base_score = 100
        total_change = 0
        
        for record in (self.credit_records or []):
            total_change += record.get('score_change', 0)
        
        return max(0, min(100, base_score + total_change))
    
    def to_dict(self):
        """转换为字典"""
        data = super().to_dict()
        # 移除敏感字段
        data.pop('id_card_encrypted', None)
        data.pop('id_card_hash', None)  # 哈希值不对外暴露
        return data
    
    def get_cascade_relations(self):
        """
        获取需要级联处理的关系定义
        
        租客删除规则：
        - 如果有活跃合同（active/draft），不允许删除
        - 历史合同可以级联软删除
        """
        from .contract import Contract
        
        return {
            'contracts': {
                'model': Contract,
                'cascade_delete': True,
                'validate_not_empty': False,
                'error_message': '关联的合同'
            }
        }
    
    def validate_delete(self):
        """
        验证是否可以删除租客
        
        特殊规则：
        - 如果有活跃合同（active/draft），不允许删除
        
        Returns:
            Tuple[bool, List[str]]: (是否可以删除, 错误消息列表)
        """
        # 先调用父类的基础验证
        can_delete, errors = super().validate_delete()
        
        # 检查是否有活跃合同
        from .contract import Contract
        active_contracts = self.contracts.filter(
            Contract.status.in_(['active', 'draft'])
        ).count()
        
        if active_contracts > 0:
            errors.append(f'存在 {active_contracts} 个活跃合同，无法删除')
            can_delete = False
        
        return can_delete, errors
    
    def __repr__(self):
        return f'<Tenant {self.name}>'
