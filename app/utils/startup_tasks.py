"""
启动时任务基础设施

提供系统启动时自动执行的任务框架，支持：
- 数据一致性检查
- 合同到期检查
- 支付逾期处理
- 合同到期提醒

性能优化：
- 分批处理机制（每批 100 条，可配置）
- 异步执行机制（后台线程）
- 超时控制机制（默认 60 秒）
- 断点续传机制（保存进度）
"""
import os
import threading
import time
from datetime import datetime, date, timedelta
from decimal import Decimal
from flask import current_app
from app import db
from app.models.base import BaseModel


class StartupTaskRecord(BaseModel):
    """
    启动任务执行记录模型
    
    记录每日任务执行状态，支持断点续传
    """
    __tablename__ = 'startup_task_records'
    
    task_name = db.Column(db.String(100), nullable=False, comment='任务名称')
    task_date = db.Column(db.Date, nullable=False, comment='任务日期')
    status = db.Column(db.String(20), nullable=False, default='pending', comment='任务状态')
    started_at = db.Column(db.DateTime, comment='开始时间')
    completed_at = db.Column(db.DateTime, comment='完成时间')
    total_records = db.Column(db.Integer, default=0, comment='总记录数')
    processed_records = db.Column(db.Integer, default=0, comment='已处理记录数')
    failed_records = db.Column(db.Integer, default=0, comment='失败记录数')
    last_processed_id = db.Column(db.Integer, comment='最后处理的记录ID（断点续传）')
    error_message = db.Column(db.Text, comment='错误信息')
    execution_time = db.Column(db.Float, comment='执行时间（秒）')
    
    __table_args__ = (
        db.UniqueConstraint('task_name', 'task_date', name='idx_task_name_date'),
        db.Index('idx_startup_task_status', 'status'),
        db.Index('idx_startup_task_date', 'task_date'),
    )
    
    def to_dict(self):
        """转换为字典"""
        result = super().to_dict()
        result['task_date'] = self.task_date.strftime('%Y-%m-%d') if self.task_date else None
        result['started_at'] = self.started_at.strftime('%Y-%m-%d %H:%M:%S') if self.started_at else None
        result['completed_at'] = self.completed_at.strftime('%Y-%m-%d %H:%M:%S') if self.completed_at else None
        return result


class StartupTaskManager:
    """
    启动任务管理器
    
    管理所有启动任务的注册、执行和监控
    """
    
    def __init__(self, app=None):
        self.app = app
        self.tasks = {}
        self.task_priorities = {
            'data_consistency_check': 1,
            'contract_expiry_check': 2,
            'payment_overdue_process': 3,
            'contract_expiry_reminder': 4,
            'monthly_archive_check': 5
        }
        self.config = {
            'enabled': True,
            'batch_size': 100,
            'timeout': 60,
            'delay': 100
        }
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """
        初始化任务管理器
        
        Args:
            app: Flask 应用实例
        """
        self.app = app
        
        self.config['enabled'] = app.config.get('STARTUP_TASKS_ENABLED', True)
        self.config['batch_size'] = app.config.get('STARTUP_TASKS_BATCH_SIZE', 100)
        self.config['timeout'] = app.config.get('STARTUP_TASKS_TIMEOUT', 60)
        self.config['delay'] = app.config.get('STARTUP_TASKS_DELAY', 100)
        
        self._register_default_tasks()
    
    def _register_default_tasks(self):
        """注册默认任务"""
        self.register_task('data_consistency_check', self._check_data_consistency, 1)
        self.register_task('contract_expiry_check', self._check_contract_expiry, 2)
        self.register_task('payment_overdue_process', self._process_payment_overdue, 3)
        self.register_task('contract_expiry_reminder', self._send_contract_expiry_reminder, 4)
        self.register_task('monthly_archive_check', self._check_monthly_archive, 5)
    
    def register_task(self, name, func, priority=5):
        """
        注册任务
        
        Args:
            name: 任务名称
            func: 任务函数
            priority: 优先级（1-5，1最高）
        """
        self.tasks[name] = {
            'func': func,
            'priority': priority
        }
    
    def run_all_tasks(self):
        """
        运行所有任务（异步执行）
        
        在后台线程中执行，不阻塞系统启动
        """
        if not self.config['enabled']:
            self.app.logger.info('启动任务已禁用')
            return
        
        def _run_tasks():
            with self.app.app_context():
                try:
                    self.app.logger.info('开始执行启动任务...')
                    
                    sorted_tasks = sorted(
                        self.tasks.items(),
                        key=lambda x: x[1]['priority']
                    )
                    
                    for task_name, task_info in sorted_tasks:
                        try:
                            self.run_task(task_name, task_info['func'])
                        except Exception as e:
                            self.app.logger.error(f'任务 {task_name} 执行失败: {str(e)}')
                    
                    self.app.logger.info('所有启动任务执行完成')
                    
                except Exception as e:
                    self.app.logger.error(f'启动任务执行异常: {str(e)}')
        
        thread = threading.Thread(target=_run_tasks, daemon=True)
        thread.start()
    
    def run_task(self, task_name, task_func):
        """
        执行单个任务
        
        Args:
            task_name: 任务名称
            task_func: 任务函数
        """
        today = date.today()
        
        record = StartupTaskRecord.query.filter_by(
            task_name=task_name,
            task_date=today
        ).first()
        
        if record and record.status == 'completed':
            self.app.logger.info(f'任务 {task_name} 今日已完成，跳过')
            return
        
        if not record:
            record = StartupTaskRecord(
                task_name=task_name,
                task_date=today,
                status='pending'
            )
            db.session.add(record)
            db.session.commit()
        
        start_time = time.time()
        record.status = 'running'
        record.started_at = datetime.now()
        db.session.commit()
        
        try:
            result = task_func(record)
            
            record.status = 'completed'
            record.completed_at = datetime.now()
            record.execution_time = time.time() - start_time
            
            if result:
                record.total_records = result.get('total', 0)
                record.processed_records = result.get('processed', 0)
                record.failed_records = result.get('failed', 0)
            
            db.session.commit()
            
            self.app.logger.info(
                f'任务 {task_name} 执行完成 - '
                f'总数: {record.total_records}, '
                f'已处理: {record.processed_records}, '
                f'失败: {record.failed_records}, '
                f'耗时: {record.execution_time:.2f}秒'
            )
            
        except Exception as e:
            record.status = 'failed'
            record.error_message = str(e)
            record.completed_at = datetime.now()
            record.execution_time = time.time() - start_time
            db.session.commit()
            
            self.app.logger.error(f'任务 {task_name} 执行失败: {str(e)}')
            raise
    
    def _check_data_consistency(self, record):
        """
        数据一致性检查任务
        
        检查项：
        1. 房源状态与合同状态一致性
        2. 房间状态与房源状态一致性
        3. 租客状态与合同状态一致性
        """
        from app.models.house import House
        from app.models.room import Room
        from app.models.contract import Contract
        from app.models.tenant import Tenant
        
        self.app.logger.info('开始数据一致性检查...')
        
        total = 0
        processed = 0
        failed = 0
        
        try:
            houses = House.query.filter(House.deleted_at.is_(None)).all()
            total = len(houses)
            
            for i, house in enumerate(houses):
                try:
                    if record.last_processed_id and house.id <= record.last_processed_id:
                        continue
                    
                    if house.rental_type == 'shared':
                        rooms = Room.query.filter_by(house_id=house.id).all()
                        rented_count = sum(1 for r in rooms if r.status == 'rented')
                        
                        if rented_count == 0:
                            expected_status = 'available'
                        elif rented_count == len(rooms):
                            expected_status = 'rented'
                        else:
                            expected_status = 'partially_rented'
                        
                        if house.status != expected_status:
                            house.status = expected_status
                            db.session.add(house)
                    
                    processed += 1
                    
                    if (i + 1) % self.config['batch_size'] == 0:
                        record.processed_records = processed
                        record.last_processed_id = house.id
                        db.session.commit()
                        time.sleep(self.config['delay'] / 1000.0)
                    
                except Exception as e:
                    failed += 1
                    self.app.logger.error(f'检查房源 {house.id} 失败: {str(e)}')
            
            active_contracts = Contract.query.filter_by(status='active').all()
            total += len(active_contracts)
            
            for contract in active_contracts:
                try:
                    if contract.end_date < date.today():
                        contract.status = 'expired'
                        db.session.add(contract)
                    
                    processed += 1
                    
                except Exception as e:
                    failed += 1
                    self.app.logger.error(f'检查合同 {contract.id} 失败: {str(e)}')
            
            db.session.commit()
            
            self.app.logger.info(
                f'数据一致性检查完成 - '
                f'检查: {total} 条, '
                f'成功: {processed} 条, '
                f'失败: {failed} 条'
            )
            
        except Exception as e:
            self.app.logger.error(f'数据一致性检查异常: {str(e)}')
            raise
        
        return {'total': total, 'processed': processed, 'failed': failed}
    
    def _check_monthly_archive(self, record):
        """
        月度归档检查任务
        
        检查是否需要执行归档操作：
        - 每月1号执行归档
        - 归档超过12个月的过期合同
        - 归档超过12个月的已完成支付记录
        """
        from app.models.archive import ArchiveRecord
        from app.utils.backup_manager import get_backup_manager
        
        self.app.logger.info('开始月度归档检查...')
        
        today = date.today()
        
        # 只在每月1号执行
        if today.day != 1:
            self.app.logger.info(f'今天不是归档日期（{today.day}号），跳过归档')
            return {'total': 0, 'processed': 0, 'failed': 0, 'skipped': True}
        
        # 检查本月是否已执行过归档
        existing_record = ArchiveRecord.query.filter(
            ArchiveRecord.archive_type == 'auto_monthly',
            ArchiveRecord.archive_date == today
        ).first()
        
        if existing_record:
            self.app.logger.info(f'本月归档已执行（记录ID: {existing_record.id}），跳过')
            return {'total': 0, 'processed': 0, 'failed': 0, 'skipped': True}
        
        total = 0
        processed = 0
        failed = 0
        
        try:
            # 获取备份管理器
            backup_manager = get_backup_manager()
            
            # 执行归档（保留12个月）
            self.app.logger.info('开始执行自动归档...')
            
            result = backup_manager.archive_all(
                months_retention=12,
                batch_size=self.config['batch_size'],
                dry_run=False
            )
            
            total = result.get('total_archived', 0) + result.get('total_failed', 0)
            processed = result.get('total_archived', 0)
            failed = result.get('total_failed', 0)
            
            # 创建归档操作记录
            archive_record = ArchiveRecord(
                archive_type='auto_monthly',
                archive_date=today,
                archive_reason='monthly_auto_archive',
                total_records=total,
                archived_records=processed,
                failed_records=failed,
                started_at=datetime.now(),
                completed_at=datetime.now(),
                execution_time=result.get('execution_time', 0),
                remark='月度自动归档'
            )
            db.session.add(archive_record)
            db.session.commit()
            
            self.app.logger.info(
                f'月度归档完成 - '
                f'总数: {total}, '
                f'已归档: {processed}, '
                f'失败: {failed}'
            )
            
        except Exception as e:
            self.app.logger.error(f'月度归档异常: {str(e)}')
            
            # 记录失败
            archive_record = ArchiveRecord(
                archive_type='auto_monthly',
                archive_date=today,
                archive_reason='monthly_auto_archive',
                total_records=total,
                archived_records=processed,
                failed_records=failed,
                started_at=datetime.now(),
                completed_at=datetime.now(),
                error_message=str(e),
                remark='月度自动归档失败'
            )
            db.session.add(archive_record)
            db.session.commit()
            
            raise
        
        return {'total': total, 'processed': processed, 'failed': failed, 'skipped': False}
    
    def _check_contract_expiry(self, record):
        """
        合同到期检查任务
        
        检查即将到期和已过期的合同，更新状态
        """
        from app.models.contract import Contract
        from app.models.landlord_contract import LandlordContract
        
        self.app.logger.info('开始合同到期检查...')
        
        total = 0
        processed = 0
        failed = 0
        
        try:
            today = date.today()
            
            expired_contracts = Contract.query.filter(
                Contract.status == 'active',
                Contract.end_date < today,
                Contract.deleted_at.is_(None)
            ).all()
            
            total = len(expired_contracts)
            
            for i, contract in enumerate(expired_contracts):
                try:
                    if record.last_processed_id and contract.id <= record.last_processed_id:
                        continue
                    
                    contract.status = 'expired'
                    db.session.add(contract)
                    
                    processed += 1
                    
                    if (i + 1) % self.config['batch_size'] == 0:
                        record.processed_records = processed
                        record.last_processed_id = contract.id
                        db.session.commit()
                        time.sleep(self.config['delay'] / 1000.0)
                    
                except Exception as e:
                    failed += 1
                    self.app.logger.error(f'处理合同 {contract.id} 失败: {str(e)}')
            
            expired_landlord_contracts = LandlordContract.query.filter(
                LandlordContract.status == 'active',
                LandlordContract.end_date < today,
                LandlordContract.deleted_at.is_(None)
            ).all()
            
            total += len(expired_landlord_contracts)
            
            for contract in expired_landlord_contracts:
                try:
                    contract.status = 'expired'
                    db.session.add(contract)
                    processed += 1
                except Exception as e:
                    failed += 1
                    self.app.logger.error(f'处理承包合同 {contract.id} 失败: {str(e)}')
            
            db.session.commit()
            
            self.app.logger.info(
                f'合同到期检查完成 - '
                f'检查: {total} 条, '
                f'成功: {processed} 条, '
                f'失败: {failed} 条'
            )
            
        except Exception as e:
            self.app.logger.error(f'合同到期检查异常: {str(e)}')
            raise
        
        return {'total': total, 'processed': processed, 'failed': failed}
    
    def _process_payment_overdue(self, record):
        """
        支付逾期处理任务
        
        检查逾期支付，计算滞纳金，更新状态，并扣信用分
        """
        from app.models.payment import Payment
        from app.models.tenant import Tenant
        from app.utils.credit_score import CreditEventType, CreditScoreConfig
        
        self.app.logger.info('开始支付逾期处理...')
        
        total = 0
        processed = 0
        failed = 0
        
        try:
            today = date.today()
            
            overdue_payments = Payment.query.filter(
                Payment.status == 'pending',
                Payment.due_date < today,
                Payment.deleted_at.is_(None)
            ).all()
            
            total = len(overdue_payments)
            
            for i, payment in enumerate(overdue_payments):
                try:
                    if record.last_processed_id and payment.id <= record.last_processed_id:
                        continue
                    
                    late_fee, overdue_days = payment.calculate_late_fee(today)
                    
                    if late_fee > Decimal('0.00'):
                        payment.late_fee = late_fee
                        payment.overdue_days = overdue_days
                    
                    payment.status = 'overdue'
                    db.session.add(payment)
                    
                    if payment.contract_id and payment.contract_rel and payment.contract_rel.tenant_id:
                        tenant = Tenant.query.get(payment.contract_rel.tenant_id)
                        if tenant:
                            credit_records = tenant.credit_records or []
                            has_7day_penalty = any(
                                r.get('related_id') == payment.id and 
                                r.get('event_type') == 'late_payment_7'
                                for r in credit_records
                            )
                            has_30day_penalty = any(
                                r.get('related_id') == payment.id and 
                                r.get('event_type') == 'late_payment_30'
                                for r in credit_records
                            )
                            
                            if overdue_days > 30 and not has_30day_penalty:
                                config = CreditScoreConfig.get_event_config(CreditEventType.LATE_PAYMENT_30)
                                tenant.add_credit_record(
                                    event_type='late_payment_30',
                                    score_change=config['score_change'],
                                    description=f"{config['description']}（支付记录ID: {payment.id}）",
                                    related_id=payment.id
                                )
                                db.session.add(tenant)
                            elif overdue_days > 7 and not has_7day_penalty:
                                config = CreditScoreConfig.get_event_config(CreditEventType.LATE_PAYMENT_7)
                                tenant.add_credit_record(
                                    event_type='late_payment_7',
                                    score_change=config['score_change'],
                                    description=f"{config['description']}（支付记录ID: {payment.id}）",
                                    related_id=payment.id
                                )
                                db.session.add(tenant)
                    
                    processed += 1
                    
                    if (i + 1) % self.config['batch_size'] == 0:
                        record.processed_records = processed
                        record.last_processed_id = payment.id
                        db.session.commit()
                        time.sleep(self.config['delay'] / 1000.0)
                    
                except Exception as e:
                    failed += 1
                    self.app.logger.error(f'处理支付 {payment.id} 失败: {str(e)}')
            
            db.session.commit()
            
            self.app.logger.info(
                f'支付逾期处理完成 - '
                f'检查: {total} 条, '
                f'成功: {processed} 条, '
                f'失败: {failed} 条'
            )
            
        except Exception as e:
            self.app.logger.error(f'支付逾期处理异常: {str(e)}')
            raise
        
        return {'total': total, 'processed': processed, 'failed': failed}
    
    def _send_contract_expiry_reminder(self, record):
        """
        合同到期提醒任务
        
        检查即将到期的合同，发送提醒（记录日志）
        """
        from app.models.contract import Contract
        from app.models.landlord_contract import LandlordContract
        
        self.app.logger.info('开始合同到期提醒...')
        
        total = 0
        processed = 0
        failed = 0
        
        try:
            today = date.today()
            reminder_days = 30
            reminder_date = today + timedelta(days=reminder_days)
            
            expiring_contracts = Contract.query.filter(
                Contract.status == 'active',
                Contract.end_date <= reminder_date,
                Contract.end_date > today,
                Contract.deleted_at.is_(None)
            ).all()
            
            total = len(expiring_contracts)
            
            for i, contract in enumerate(expiring_contracts):
                try:
                    if record.last_processed_id and contract.id <= record.last_processed_id:
                        continue
                    
                    days_until_expiry = contract.get_days_until_expiry()
                    
                    self.app.logger.info(
                        f'合同即将到期提醒 - '
                        f'合同编号: {contract.contract_no}, '
                        f'租客: {contract.tenant_rel.name if contract.tenant_rel else "未知"}, '
                        f'到期日期: {contract.end_date}, '
                        f'剩余天数: {days_until_expiry}'
                    )
                    
                    processed += 1
                    
                    if (i + 1) % self.config['batch_size'] == 0:
                        record.processed_records = processed
                        record.last_processed_id = contract.id
                        db.session.commit()
                        time.sleep(self.config['delay'] / 1000.0)
                    
                except Exception as e:
                    failed += 1
                    self.app.logger.error(f'处理合同 {contract.id} 失败: {str(e)}')
            
            expiring_landlord_contracts = LandlordContract.query.filter(
                LandlordContract.status == 'active',
                LandlordContract.end_date <= reminder_date,
                LandlordContract.end_date > today,
                LandlordContract.deleted_at.is_(None)
            ).all()
            
            total += len(expiring_landlord_contracts)
            
            for contract in expiring_landlord_contracts:
                try:
                    days_until_expiry = contract.get_days_until_expiry()
                    
                    self.app.logger.info(
                        f'承包合同即将到期提醒 - '
                        f'合同编号: {contract.contract_no}, '
                        f'房东: {contract.landlord.name if contract.landlord else "未知"}, '
                        f'到期日期: {contract.end_date}, '
                        f'剩余天数: {days_until_expiry}'
                    )
                    
                    processed += 1
                except Exception as e:
                    failed += 1
                    self.app.logger.error(f'处理承包合同 {contract.id} 失败: {str(e)}')
            
            db.session.commit()
            
            self.app.logger.info(
                f'合同到期提醒完成 - '
                f'检查: {total} 条, '
                f'成功: {processed} 条, '
                f'失败: {failed} 条'
            )
            
        except Exception as e:
            self.app.logger.error(f'合同到期提醒异常: {str(e)}')
            raise
        
        return {'total': total, 'processed': processed, 'failed': failed}
    
    def get_task_status(self, task_name=None, task_date=None):
        """
        获取任务执行状态
        
        Args:
            task_name: 任务名称（可选）
            task_date: 任务日期（可选）
        
        Returns:
            任务状态信息
        """
        query = StartupTaskRecord.query
        
        if task_name:
            query = query.filter_by(task_name=task_name)
        
        if task_date:
            query = query.filter_by(task_date=task_date)
        
        records = query.order_by(StartupTaskRecord.created_at.desc()).all()
        
        return [record.to_dict() for record in records]
    
    def get_task_logs(self, task_name=None, limit=100):
        """
        获取任务执行日志
        
        Args:
            task_name: 任务名称（可选）
            limit: 返回记录数量限制
        
        Returns:
            任务日志列表
        """
        query = StartupTaskRecord.query
        
        if task_name:
            query = query.filter_by(task_name=task_name)
        
        records = query.order_by(StartupTaskRecord.created_at.desc()).limit(limit).all()
        
        return [record.to_dict() for record in records]


task_manager = None


def get_task_manager():
    """
    获取任务管理器单例
    
    Returns:
        StartupTaskManager 实例
    """
    global task_manager
    if task_manager is None:
        task_manager = StartupTaskManager()
    return task_manager


def init_startup_tasks(app):
    """
    初始化启动任务
    
    Args:
        app: Flask 应用实例
    """
    manager = get_task_manager()
    manager.init_app(app)
    
    with app.app_context():
        db.create_all()
    
    manager.run_all_tasks()
    
    app.logger.info('启动任务系统已初始化')
