"""
用户模型
"""
import jwt
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from flask import current_app
from .base import db, BaseModel


class User(BaseModel):
    """
    用户模型
    
    【重要说明】User 表仅用于公司内部员工（管理员和普通员工），房东不访问系统
    
    支持管理员和普通员工角色
    管理员拥有所有权限，普通员工仅有基础操作权限
    """
    
    __tablename__ = 'users'
    
    # 基本信息
    username = db.Column(db.String(50), unique=True, nullable=False, comment='用户名')
    email = db.Column(db.String(100), unique=True, nullable=True, comment='邮箱')
    password_hash = db.Column(db.String(255), nullable=False, comment='密码哈希')
    
    # 角色：admin-管理员，staff-普通员工
    # 规格说明要求：管理员拥有所有权限，普通员工仅有查看、录入权限（无删除权限）
    role = db.Column(db.String(20), default='staff', comment='用户角色')
    
    # 用户类型：admin-管理员，staff-员工（仅内部员工使用）
    user_type = db.Column(db.String(20), default='staff', comment='用户类型')
    
    # 员工扩展信息
    name = db.Column(db.String(50), comment='姓名')
    phone = db.Column(db.String(20), unique=True, comment='手机号')
    id_card = db.Column(db.String(18), comment='身份证号')
    id_card_hash = db.Column(db.String(64), default=None, comment='身份证号哈希（用于去重验证）')
    position = db.Column(db.String(50), comment='职位')
    
    # 员工状态：active-在职，resigned-离职，disabled-禁用
    status = db.Column(db.String(20), default='active', comment='员工状态')
    
    # 头像
    avatar = db.Column(db.String(255), comment='头像 URL')
    
    # 登录相关
    last_login = db.Column(db.DateTime, comment='最后登录时间')
    login_attempts = db.Column(db.Integer, default=0, comment='登录失败次数')
    locked_until = db.Column(db.DateTime, comment='锁定截止时间')
    
    # 创建人（用于记录哪个管理员创建的员工）
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), comment='创建人')
    
    # 索引
    __table_args__ = (
        db.Index('idx_users_username', 'username'),
        db.Index('idx_users_role', 'role'),
        db.Index('idx_users_email', 'email'),
        db.Index('idx_users_phone', 'phone'),
        db.Index('idx_users_status', 'status'),
        db.Index('idx_users_id_card_hash', 'id_card_hash'),
    )
    
    # 关系：员工负责的房源（录入人/负责人）
    # 使用 back_populates 与 House.owner 建立双向关系
    houses = db.relationship('House', back_populates='owner', lazy='dynamic', foreign_keys='House.owner_id')
    uploaded_media = db.relationship('Media', lazy='dynamic', foreign_keys='Media.uploaded_by', overlaps='uploader')
    operated_payments = db.relationship('Payment', lazy='dynamic', foreign_keys='Payment.operator_id', overlaps='operator')
    
    # 员工管理关系（记录哪个管理员创建的员工）
    created_employees = db.relationship('User', lazy='select', foreign_keys='User.created_by', remote_side='User.id', backref='creator')
    
    @property
    def is_admin(self):
        """判断是否为管理员"""
        return self.role == 'admin'
    
    @property
    def is_staff(self):
        """判断是否为普通员工"""
        return self.role == 'staff'
    
    def has_permission(self, permission):
        """
        检查用户权限
        
        Args:
            permission: 权限类型 ('view', 'create', 'edit', 'delete')
            
        Returns:
            bool: 是否有权限
        """
        if self.role == 'admin':
            return True
        elif self.role == 'staff':
            # 普通员工有查看、录入权限，无删除权限
            return permission in ['view', 'create', 'edit']
        return False
    
    def set_password(self, password, expires_days=None):
        """
        设置密码

        Args:
            password: 明文密码
            expires_days: 密码过期天数（可选，默认使用配置中的值）
        """
        from flask import current_app
        from .password_history import PasswordHistory

        # 设置密码哈希
        self.password_hash = generate_password_hash(password)

        # 检查是否启用密码历史记录，且 user.id 已存在
        keep_count = current_app.config.get('PASSWORD_HISTORY_COUNT', 5)

        # 如果 keep_count 为 0，跳过密码历史记录（用于测试环境）
        # 如果 self.id 为 None，也跳过密码历史记录（需要在数据库插入后才能添加）
        if keep_count > 0 and self.id is not None:
            # 获取密码过期天数
            if expires_days is None:
                expires_days = current_app.config.get('PASSWORD_EXPIRE_DAYS', 90)

            # 添加密码历史记录
            PasswordHistory.add_password_history(
                user_id=self.id,
                password=password,
                expires_days=expires_days
            )

            # 清理旧的密码历史记录
            PasswordHistory.cleanup_old_passwords(user_id=self.id, keep_count=keep_count)
    
    def check_password(self, password):
        """验证密码"""
        return check_password_hash(self.password_hash, password)
    
    def generate_token(self, expires_in=3600):
        """生成 JWT token"""
        payload = {
            'user_id': self.id,
            'username': self.username,
            'user_type': self.user_type,
            'exp': datetime.utcnow() + timedelta(seconds=expires_in)
        }
        return jwt.encode(payload, current_app.config['JWT_SECRET_KEY'], algorithm='HS256')
    
    @staticmethod
    def verify_token(token):
        """验证 JWT token"""
        try:
            payload = jwt.decode(token, current_app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def set_id_card(self, id_card_number):
        """设置身份证号并生成哈希"""
        import hashlib
        self.id_card = id_card_number
        self.id_card_hash = hashlib.sha256(id_card_number.encode()).hexdigest()
    
    def verify_id_card(self, id_card_number):
        """验证身份证号是否匹配"""
        import hashlib
        return self.id_card_hash == hashlib.sha256(id_card_number.encode()).hexdigest()
    
    def is_account_locked(self):
        """检查账号是否被锁定"""
        if self.locked_until and self.locked_until > datetime.now():
            return True
        return False
    
    def record_login_attempt(self, success: bool):
        """记录登录尝试"""
        if success:
            self.login_attempts = 0
            self.locked_until = None
            self.last_login = datetime.now()
        else:
            self.login_attempts += 1
            # 连续失败 5 次，锁定账号 30 分钟
            if self.login_attempts >= 5:
                from datetime import timedelta
                self.locked_until = datetime.now() + timedelta(minutes=30)
    
    def to_dict(self, include_details=False):
        """转换为字典"""
        data = super().to_dict()
        data.pop('password_hash', None)  # 移除密码字段
        data.pop('id_card_hash', None)  # 移除身份证号哈希
        
        # 身份证号脱敏处理：保留前3位和后4位
        if self.id_card and len(self.id_card) >= 8:
            data['id_card'] = self.id_card[:3] + '***********' + self.id_card[-4:]
        else:
            data['id_card'] = None
        
        if not include_details:
            # 默认响应不包含敏感信息
            data.pop('created_by', None)
            data.pop('login_attempts', None)
            data.pop('locked_until', None)
        
        return data
    
    def get_cascade_relations(self):
        """
        获取需要级联处理的关系定义
        
        用户删除规则：
        - 如果有负责的房源，不允许删除
        - 如果有操作的支付记录，不允许删除
        - 如果有创建的员工，不允许删除
        - 上传的媒体文件可以级联软删除
        """
        from .house import House
        from .media import Media
        from .payment import Payment
        
        return {
            'houses': {
                'model': House,
                'cascade_delete': False,
                'validate_not_empty': True,
                'error_message': '该员工负责的房源不为空，无法删除'
            },
            'operated_payments': {
                'model': Payment,
                'cascade_delete': False,
                'validate_not_empty': True,
                'error_message': '该员工有操作过的支付记录，无法删除'
            },
            'created_employees': {
                'model': User,
                'cascade_delete': False,
                'validate_not_empty': True,
                'error_message': '该员工创建了其他员工账号，无法删除'
            },
            'uploaded_media': {
                'model': Media,
                'cascade_delete': True,
                'validate_not_empty': False,
                'error_message': '该员工上传的媒体文件'
            }
        }
    
    def __repr__(self):
        return f'<User {self.username}>'


def create_default_admin():
    """
    创建默认管理员用户
    """
    from app import db
    admin_user = db.session.query(User).filter_by(username='admin').first()
    if not admin_user:
        admin_user = User(
            username='admin',
            email='admin@example.com',
            password_hash='',
            role='admin',
            user_type='admin'
        )
        admin_user.set_password('admin123')
        db.session.add(admin_user)
        db.session.commit()
        print('默认管理员用户创建成功！')
        print('用户名：admin')
        print('密码：admin123')
    else:
        print('管理员用户已存在，跳过创建')
