"""
敏感数据访问审计日志模型
记录所有敏感数据的访问、修改、删除操作，用于安全审计和合规性检查
"""
from datetime import datetime
from .base import db, BaseModel


class SensitiveDataAuditLog(BaseModel):
    """
    敏感数据访问审计日志模型
    
    记录所有敏感数据操作的详细信息，包括：
    - 操作类型（查看、修改、删除）
    - 操作对象（模型、记录ID、字段）
    - 操作人信息（用户ID、用户名）
    - 操作时间和 IP 地址
    - 操作结果（成功/失败）
    
    安全特性：
    - 完整记录敏感数据访问轨迹
    - 支持按用户、时间、模型等多维度查询
    - 提供统计分析功能
    - 支持数据导出
    """
    
    __tablename__ = 'sensitive_data_audit_logs'
    
    # ==================== 操作类型 ====================
    # 操作类型：view-查看，modify-修改，delete-删除，export-导出
    operation_type = db.Column(db.String(20), nullable=False, comment='操作类型')
    
    # ==================== 操作对象信息 ====================
    # 模型名称（如：Landlord, Tenant）
    model_name = db.Column(db.String(100), nullable=False, comment='模型名称')
    
    # 记录 ID
    record_id = db.Column(db.Integer, nullable=False, comment='记录 ID')
    
    # 字段名称（如：id_card, bank_card）
    field_name = db.Column(db.String(100), nullable=False, comment='字段名称')
    
    # 字段显示名称（如：身份证号、银行卡号）
    field_display_name = db.Column(db.String(100), comment='字段显示名称')
    
    # ==================== 操作人信息 ====================
    # 操作用户 ID
    user_id = db.Column(db.Integer, comment='操作用户 ID')
    
    # 操作用户名
    username = db.Column(db.String(50), comment='操作用户名')
    
    # 用户角色
    user_role = db.Column(db.String(20), comment='用户角色')
    
    # ==================== 操作环境信息 ====================
    # 操作 IP 地址
    ip_address = db.Column(db.String(50), comment='操作 IP 地址')
    
    # 用户代理（浏览器信息）
    user_agent = db.Column(db.String(500), comment='用户代理')
    
    # 请求路径
    request_path = db.Column(db.String(255), comment='请求路径')
    
    # 请求方法
    request_method = db.Column(db.String(10), comment='请求方法')
    
    # ==================== 操作结果信息 ====================
    # 操作是否成功
    success = db.Column(db.Boolean, default=True, comment='操作是否成功')
    
    # 错误信息（如果失败）
    error_message = db.Column(db.Text, comment='错误信息')
    
    # ==================== 数据变更信息 ====================
    # 变更前的值（脱敏后）
    old_value = db.Column(db.Text, comment='变更前的值（脱敏）')
    
    # 变更后的值（脱敏后）
    new_value = db.Column(db.Text, comment='变更后的值（脱敏）')
    
    # ==================== 时间戳 ====================
    # 操作时间
    operation_time = db.Column(db.DateTime, nullable=False, default=datetime.now, index=True, comment='操作时间')
    
    # ==================== 额外信息 ====================
    # 备注信息
    remark = db.Column(db.Text, comment='备注信息')
    
    # ==================== 索引配置 ====================
    __table_args__ = (
        db.Index('idx_sensitive_audit_operation_time', 'operation_time'),
        db.Index('idx_sensitive_audit_operation_type', 'operation_type'),
        db.Index('idx_sensitive_audit_model_record', 'model_name', 'record_id'),
        db.Index('idx_sensitive_audit_user', 'user_id'),
        db.Index('idx_sensitive_audit_field', 'model_name', 'field_name'),
        db.Index('idx_sensitive_audit_success', 'success'),
        {'comment': '敏感数据访问审计日志表'}
    )
    
    # ==================== 操作类型常量 ====================
    OPERATION_VIEW = 'view'       # 查看敏感数据
    OPERATION_MODIFY = 'modify'   # 修改敏感数据
    OPERATION_DELETE = 'delete'   # 删除敏感数据
    OPERATION_EXPORT = 'export'   # 导出敏感数据
    
    # 操作类型映射
    OPERATION_TYPES = {
        OPERATION_VIEW: '查看',
        OPERATION_MODIFY: '修改',
        OPERATION_DELETE: '删除',
        OPERATION_EXPORT: '导出'
    }
    
    # ==================== 敏感字段定义 ====================
    # 各模型的敏感字段配置
    SENSITIVE_FIELDS = {
        'Landlord': {
            'id_card': '身份证号',
            'bank_card': '银行卡号',
            'property_cert_no': '房产证编号'
        },
        'Tenant': {
            'id_card': '身份证号',
            'emergency_phone': '紧急联系人电话',
            'phone': '联系电话'
        },
        'User': {
            'password': '密码',
            'phone': '联系电话',
            'email': '电子邮箱'
        }
    }
    
    def to_dict(self):
        """
        转换为字典
        
        Returns:
            dict: 审计日志信息字典
        """
        data = super().to_dict()
        
        # 添加操作类型中文名称
        data['operation_type_name'] = self.OPERATION_TYPES.get(
            self.operation_type, 
            self.operation_type
        )
        
        # 格式化操作时间
        if self.operation_time:
            data['operation_time'] = self.operation_time.strftime('%Y-%m-%d %H:%M:%S')
        
        # 移除敏感信息
        data.pop('old_value', None)
        data.pop('new_value', None)
        
        return data
    
    def to_detail_dict(self):
        """
        转换为详细字典（包含变更信息）
        
        Returns:
            dict: 审计日志详细信息字典
        """
        data = self.to_dict()
        data['old_value'] = self.old_value
        data['new_value'] = self.new_value
        return data
    
    # ==================== 查询方法 ====================
    
    @classmethod
    def get_logs_by_record(cls, model_name: str, record_id: int, limit: int = 100):
        """
        获取指定记录的审计日志
        
        Args:
            model_name: 模型名称
            record_id: 记录 ID
            limit: 返回记录数量限制
            
        Returns:
            list: 审计日志列表
        """
        return db.session.query(cls).filter(
            cls.deleted_at.is_(None),
            cls.model_name == model_name,
            cls.record_id == record_id
        ).order_by(cls.operation_time.desc()).limit(limit).all()
    
    @classmethod
    def get_logs_by_user(cls, user_id: int, limit: int = 100):
        """
        获取指定用户的审计日志
        
        Args:
            user_id: 用户 ID
            limit: 返回记录数量限制
            
        Returns:
            list: 审计日志列表
        """
        return db.session.query(cls).filter(
            cls.deleted_at.is_(None),
            cls.user_id == user_id
        ).order_by(cls.operation_time.desc()).limit(limit).all()
    
    @classmethod
    def get_logs_by_field(cls, model_name: str, field_name: str, limit: int = 100):
        """
        获取指定字段的审计日志
        
        Args:
            model_name: 模型名称
            field_name: 字段名称
            limit: 返回记录数量限制
            
        Returns:
            list: 审计日志列表
        """
        return db.session.query(cls).filter(
            cls.deleted_at.is_(None),
            cls.model_name == model_name,
            cls.field_name == field_name
        ).order_by(cls.operation_time.desc()).limit(limit).all()
    
    @classmethod
    def get_logs_by_operation(cls, operation_type: str, limit: int = 100):
        """
        获取指定操作类型的审计日志
        
        Args:
            operation_type: 操作类型
            limit: 返回记录数量限制
            
        Returns:
            list: 审计日志列表
        """
        return db.session.query(cls).filter(
            cls.deleted_at.is_(None),
            cls.operation_type == operation_type
        ).order_by(cls.operation_time.desc()).limit(limit).all()
    
    @classmethod
    def get_failed_operations(cls, limit: int = 100):
        """
        获取失败的操作日志
        
        Args:
            limit: 返回记录数量限制
            
        Returns:
            list: 失败的审计日志列表
        """
        return db.session.query(cls).filter(
            cls.deleted_at.is_(None),
            cls.success == False
        ).order_by(cls.operation_time.desc()).limit(limit).all()
    
    @classmethod
    def get_logs_by_time_range(cls, start_time: datetime, end_time: datetime, limit: int = 1000):
        """
        获取指定时间范围的审计日志
        
        Args:
            start_time: 开始时间
            end_time: 结束时间
            limit: 返回记录数量限制
            
        Returns:
            list: 审计日志列表
        """
        return db.session.query(cls).filter(
            cls.deleted_at.is_(None),
            cls.operation_time >= start_time,
            cls.operation_time <= end_time
        ).order_by(cls.operation_time.desc()).limit(limit).all()
    
    # ==================== 统计方法 ====================
    
    @classmethod
    def get_statistics(cls, start_date: datetime = None, end_date: datetime = None):
        """
        获取审计日志统计信息
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            dict: 统计信息
        """
        # 基础查询条件
        base_filter = [cls.deleted_at.is_(None)]
        
        if start_date:
            base_filter.append(cls.operation_time >= start_date)
        if end_date:
            base_filter.append(cls.operation_time <= end_date)
        
        # 总操作数
        total_operations = db.session.query(cls).filter(*base_filter).count()
        
        # 按操作类型统计
        operation_stats = db.session.query(
            cls.operation_type,
            db.func.count(cls.id).label('count')
        ).filter(*base_filter).group_by(cls.operation_type).all()
        
        # 按模型统计
        model_stats = db.session.query(
            cls.model_name,
            db.func.count(cls.id).label('count')
        ).filter(*base_filter).group_by(cls.model_name).all()
        
        # 按字段统计
        field_stats = db.session.query(
            cls.model_name,
            cls.field_name,
            db.func.count(cls.id).label('count')
        ).filter(*base_filter).group_by(cls.model_name, cls.field_name).all()
        
        # 按用户统计（Top 10）
        user_stats = db.session.query(
            cls.user_id,
            cls.username,
            db.func.count(cls.id).label('count')
        ).filter(*base_filter).group_by(cls.user_id, cls.username).order_by(
            db.desc('count')
        ).limit(10).all()
        
        # 成功/失败统计
        success_filter = base_filter + [cls.success == True]
        failed_filter = base_filter + [cls.success == False]
        
        success_count = db.session.query(cls).filter(*success_filter).count()
        failed_count = db.session.query(cls).filter(*failed_filter).count()
        
        # 按小时统计（今日）
        from sqlalchemy import func
        hourly_stats = db.session.query(
            func.strftime('%H', cls.operation_time).label('hour'),
            db.func.count(cls.id).label('count')
        ).filter(
            cls.deleted_at.is_(None),
            func.date(cls.operation_time) == func.date('now')
        ).group_by(func.strftime('%H', cls.operation_time)).all()
        
        return {
            'total_operations': total_operations,
            'success_count': success_count,
            'failed_count': failed_count,
            'success_rate': (success_count / total_operations * 100) if total_operations > 0 else 0,
            'operation_statistics': [
                {
                    'operation_type': stat[0],
                    'operation_type_name': cls.OPERATION_TYPES.get(stat[0], stat[0]),
                    'count': stat[1]
                } 
                for stat in operation_stats
            ],
            'model_statistics': [
                {'model_name': stat[0], 'count': stat[1]} 
                for stat in model_stats
            ],
            'field_statistics': [
                {
                    'model_name': stat[0], 
                    'field_name': stat[1], 
                    'count': stat[2]
                } 
                for stat in field_stats
            ],
            'user_statistics': [
                {
                    'user_id': stat[0], 
                    'username': stat[1], 
                    'count': stat[2]
                } 
                for stat in user_stats
            ],
            'hourly_statistics': [
                {'hour': stat[0], 'count': stat[1]} 
                for stat in hourly_stats
            ]
        }
    
    @classmethod
    def get_user_activity_summary(cls, user_id: int, days: int = 30):
        """
        获取用户活动摘要
        
        Args:
            user_id: 用户 ID
            days: 统计天数
            
        Returns:
            dict: 用户活动摘要
        """
        from datetime import timedelta
        
        start_date = datetime.now() - timedelta(days=days)
        
        # 用户操作统计
        operations = db.session.query(
            cls.operation_type,
            db.func.count(cls.id).label('count')
        ).filter(
            cls.deleted_at.is_(None),
            cls.user_id == user_id,
            cls.operation_time >= start_date
        ).group_by(cls.operation_type).all()
        
        # 用户访问的模型统计
        models = db.session.query(
            cls.model_name,
            db.func.count(cls.id).label('count')
        ).filter(
            cls.deleted_at.is_(None),
            cls.user_id == user_id,
            cls.operation_time >= start_date
        ).group_by(cls.model_name).all()
        
        # 最近操作
        recent_logs = db.session.query(cls).filter(
            cls.deleted_at.is_(None),
            cls.user_id == user_id,
            cls.operation_time >= start_date
        ).order_by(cls.operation_time.desc()).limit(10).all()
        
        return {
            'user_id': user_id,
            'period_days': days,
            'operations': [
                {
                    'operation_type': op[0],
                    'operation_type_name': cls.OPERATION_TYPES.get(op[0], op[0]),
                    'count': op[1]
                } 
                for op in operations
            ],
            'models': [
                {'model_name': m[0], 'count': m[1]} 
                for m in models
            ],
            'recent_activities': [log.to_dict() for log in recent_logs]
        }
    
    @classmethod
    def get_sensitive_access_alert(cls, threshold: int = 10, hours: int = 1):
        """
        获取敏感数据访问预警
        
        检测短时间内频繁访问敏感数据的行为
        
        Args:
            threshold: 阈值（访问次数）
            hours: 时间窗口（小时）
            
        Returns:
            list: 预警列表
        """
        from datetime import timedelta
        
        start_time = datetime.now() - timedelta(hours=hours)
        
        # 查询频繁访问的用户
        frequent_users = db.session.query(
            cls.user_id,
            cls.username,
            db.func.count(cls.id).label('access_count')
        ).filter(
            cls.deleted_at.is_(None),
            cls.operation_time >= start_time,
            cls.operation_type == cls.OPERATION_VIEW
        ).group_by(
            cls.user_id, 
            cls.username
        ).having(
            db.func.count(cls.id) >= threshold
        ).all()
        
        alerts = []
        for user in frequent_users:
            # 获取该用户的详细访问记录
            recent_access = db.session.query(cls).filter(
                cls.deleted_at.is_(None),
                cls.user_id == user.user_id,
                cls.operation_time >= start_time,
                cls.operation_type == cls.OPERATION_VIEW
            ).order_by(cls.operation_time.desc()).limit(20).all()
            
            alerts.append({
                'user_id': user.user_id,
                'username': user.username,
                'access_count': user.access_count,
                'threshold': threshold,
                'time_window_hours': hours,
                'alert_level': 'high' if user.access_count >= threshold * 2 else 'medium',
                'recent_access': [log.to_dict() for log in recent_access]
            })
        
        return alerts
    
    def __repr__(self):
        return f'<SensitiveDataAuditLog {self.operation_type} {self.model_name}.{self.field_name} by user:{self.user_id}>'
