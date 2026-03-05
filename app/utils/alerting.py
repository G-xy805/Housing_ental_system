"""
告警配置模块

功能：
1. 慢查询告警 - 检测执行时间过长的数据库查询
2. 连接数告警 - 监控数据库连接池使用情况
3. 错误率告警 - 监控 HTTP 错误率
4. 资源使用告警 - CPU、内存、磁盘使用告警
5. 告警通知 - 支持多种通知方式（日志、邮件、Webhook）

使用方法：
    from app.utils.alerting import AlertManager
    
    alert_manager = AlertManager(app)
    alert_manager.check_and_alert()
"""
import time
import json
import logging
import smtplib
import threading
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Flask


class AlertLevel:
    """告警级别"""
    INFO = 'info'
    WARNING = 'warning'
    CRITICAL = 'critical'
    ERROR = 'error'


class AlertType:
    """告警类型"""
    SLOW_QUERY = 'slow_query'
    CONNECTION_POOL = 'connection_pool'
    ERROR_RATE = 'error_rate'
    CPU_USAGE = 'cpu_usage'
    MEMORY_USAGE = 'memory_usage'
    DISK_USAGE = 'disk_usage'
    RESPONSE_TIME = 'response_time'
    CUSTOM = 'custom'


class Alert:
    """
    告警对象
    
    Attributes:
        alert_type: 告警类型
        level: 告警级别
        message: 告警消息
        details: 详细信息
        timestamp: 时间戳
        resolved: 是否已解决
    """
    
    def __init__(
        self,
        alert_type: str,
        level: str,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ):
        self.alert_type = alert_type
        self.level = level
        self.message = message
        self.details = details or {}
        self.timestamp = datetime.now()
        self.resolved = False
        self.resolved_at = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'alert_type': self.alert_type,
            'level': self.level,
            'message': self.message,
            'details': self.details,
            'timestamp': self.timestamp.isoformat(),
            'resolved': self.resolved,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
        }
    
    def resolve(self):
        """标记为已解决"""
        self.resolved = True
        self.resolved_at = datetime.now()


class AlertRule:
    """
    告警规则
    
    定义何时触发告警的条件
    """
    
    def __init__(
        self,
        name: str,
        alert_type: str,
        condition: Callable[[Dict], bool],
        level: str = AlertLevel.WARNING,
        message_template: str = "",
        cooldown: int = 300  # 冷却时间（秒），避免频繁告警
    ):
        """
        初始化告警规则
        
        Args:
            name: 规则名称
            alert_type: 告警类型
            condition: 判断条件的函数，接收指标数据，返回布尔值
            level: 告警级别
            message_template: 消息模板
            cooldown: 冷却时间（秒）
        """
        self.name = name
        self.alert_type = alert_type
        self.condition = condition
        self.level = level
        self.message_template = message_template
        self.cooldown = cooldown
        self.last_triggered = None
    
    def should_trigger(self, metrics: Dict) -> bool:
        """
        判断是否应该触发告警
        
        Args:
            metrics: 指标数据
        
        Returns:
            是否触发
        """
        # 检查冷却时间
        if self.last_triggered:
            elapsed = (datetime.now() - self.last_triggered).total_seconds()
            if elapsed < self.cooldown:
                return False
        
        # 检查条件
        return self.condition(metrics)
    
    def trigger(self, metrics: Dict) -> Alert:
        """
        触发告警
        
        Args:
            metrics: 指标数据
        
        Returns:
            Alert 对象
        """
        self.last_triggered = datetime.now()
        
        # 生成告警消息
        message = self.message_template.format(**metrics)
        
        return Alert(
            alert_type=self.alert_type,
            level=self.level,
            message=message,
            details=metrics
        )


class AlertManager:
    """
    告警管理器
    
    管理告警规则、触发告警、发送通知
    """
    
    def __init__(self, app: Optional[Flask] = None):
        """
        初始化告警管理器
        
        Args:
            app: Flask 应用实例
        """
        self.app = app
        self.logger = logging.getLogger('alerting')
        
        # 告警规则
        self.rules: List[AlertRule] = []
        
        # 活跃告警
        self.active_alerts: List[Alert] = []
        
        # 告警历史（保留最近 1000 条）
        self.alert_history: List[Alert] = []
        self.max_history = 1000
        
        # 通知处理器
        self.notification_handlers: List[Callable] = []
        
        # 配置
        self.config = {
            'email_enabled': False,
            'email_smtp_server': '',
            'email_smtp_port': 587,
            'email_username': '',
            'email_password': '',
            'email_recipients': [],
            'webhook_enabled': False,
            'webhook_url': '',
        }
        
        # 锁
        self._lock = threading.Lock()
        
        if app:
            self.init_app(app)
    
    def init_app(self, app: Flask):
        """
        初始化告警管理器
        
        Args:
            app: Flask 应用实例
        """
        self.app = app
        
        # 从配置中读取
        self.config.update({
            'email_enabled': app.config.get('ALERT_EMAIL_ENABLED', False),
            'email_smtp_server': app.config.get('ALERT_EMAIL_SMTP_SERVER', ''),
            'email_smtp_port': app.config.get('ALERT_EMAIL_SMTP_PORT', 587),
            'email_username': app.config.get('ALERT_EMAIL_USERNAME', ''),
            'email_password': app.config.get('ALERT_EMAIL_PASSWORD', ''),
            'email_recipients': app.config.get('ALERT_EMAIL_RECIPIENTS', []),
            'webhook_enabled': app.config.get('ALERT_WEBHOOK_ENABLED', False),
            'webhook_url': app.config.get('ALERT_WEBHOOK_URL', ''),
        })
        
        # 注册默认告警规则
        self._register_default_rules()
        
        # 注册默认通知处理器
        self._register_default_handlers()
        
        self.logger.info('告警管理器已初始化')
    
    def _register_default_rules(self):
        """注册默认告警规则"""
        # 慢查询告警
        self.add_rule(AlertRule(
            name='slow_query_warning',
            alert_type=AlertType.SLOW_QUERY,
            condition=lambda m: m.get('slow_query_count', 0) > 10,
            level=AlertLevel.WARNING,
            message_template='检测到 {slow_query_count} 条慢查询',
            cooldown=600
        ))
        
        self.add_rule(AlertRule(
            name='slow_query_critical',
            alert_type=AlertType.SLOW_QUERY,
            condition=lambda m: m.get('slow_query_count', 0) > 50,
            level=AlertLevel.CRITICAL,
            message_template='检测到大量慢查询: {slow_query_count} 条',
            cooldown=300
        ))
        
        # 连接池告警
        self.add_rule(AlertRule(
            name='connection_pool_warning',
            alert_type=AlertType.CONNECTION_POOL,
            condition=lambda m: m.get('pool_usage_percent', 0) > 80,
            level=AlertLevel.WARNING,
            message_template='数据库连接池使用率过高: {pool_usage_percent:.1f}%',
            cooldown=300
        ))
        
        self.add_rule(AlertRule(
            name='connection_pool_critical',
            alert_type=AlertType.CONNECTION_POOL,
            condition=lambda m: m.get('pool_usage_percent', 0) > 95,
            level=AlertLevel.CRITICAL,
            message_template='数据库连接池即将耗尽: {pool_usage_percent:.1f}%',
            cooldown=180
        ))
        
        # 错误率告警
        self.add_rule(AlertRule(
            name='error_rate_warning',
            alert_type=AlertType.ERROR_RATE,
            condition=lambda m: m.get('error_rate', 0) > 5,
            level=AlertLevel.WARNING,
            message_template='HTTP 错误率过高: {error_rate:.2f}%',
            cooldown=300
        ))
        
        self.add_rule(AlertRule(
            name='error_rate_critical',
            alert_type=AlertType.ERROR_RATE,
            condition=lambda m: m.get('error_rate', 0) > 10,
            level=AlertLevel.CRITICAL,
            message_template='HTTP 错误率严重过高: {error_rate:.2f}%',
            cooldown=180
        ))
        
        # CPU 使用率告警
        self.add_rule(AlertRule(
            name='cpu_usage_warning',
            alert_type=AlertType.CPU_USAGE,
            condition=lambda m: m.get('cpu_usage_percent', 0) > 80,
            level=AlertLevel.WARNING,
            message_template='CPU 使用率过高: {cpu_usage_percent:.1f}%',
            cooldown=300
        ))
        
        self.add_rule(AlertRule(
            name='cpu_usage_critical',
            alert_type=AlertType.CPU_USAGE,
            condition=lambda m: m.get('cpu_usage_percent', 0) > 95,
            level=AlertLevel.CRITICAL,
            message_template='CPU 使用率严重过高: {cpu_usage_percent:.1f}%',
            cooldown=180
        ))
        
        # 内存使用率告警
        self.add_rule(AlertRule(
            name='memory_usage_warning',
            alert_type=AlertType.MEMORY_USAGE,
            condition=lambda m: m.get('memory_usage_percent', 0) > 85,
            level=AlertLevel.WARNING,
            message_template='内存使用率过高: {memory_usage_percent:.1f}%',
            cooldown=300
        ))
        
        self.add_rule(AlertRule(
            name='memory_usage_critical',
            alert_type=AlertType.MEMORY_USAGE,
            condition=lambda m: m.get('memory_usage_percent', 0) > 95,
            level=AlertLevel.CRITICAL,
            message_template='内存使用率严重过高: {memory_usage_percent:.1f}%',
            cooldown=180
        ))
        
        # 磁盘使用率告警
        self.add_rule(AlertRule(
            name='disk_usage_warning',
            alert_type=AlertType.DISK_USAGE,
            condition=lambda m: m.get('disk_usage_percent', 0) > 85,
            level=AlertLevel.WARNING,
            message_template='磁盘使用率过高: {disk_usage_percent:.1f}%',
            cooldown=3600
        ))
        
        self.add_rule(AlertRule(
            name='disk_usage_critical',
            alert_type=AlertType.DISK_USAGE,
            condition=lambda m: m.get('disk_usage_percent', 0) > 95,
            level=AlertLevel.CRITICAL,
            message_template='磁盘使用率严重过高: {disk_usage_percent:.1f}%',
            cooldown=1800
        ))
    
    def _register_default_handlers(self):
        """注册默认通知处理器"""
        # 日志处理器
        self.add_notification_handler(self._log_handler)
        
        # 邮件处理器
        if self.config['email_enabled']:
            self.add_notification_handler(self._email_handler)
        
        # Webhook 处理器
        if self.config['webhook_enabled']:
            self.add_notification_handler(self._webhook_handler)
    
    def add_rule(self, rule: AlertRule):
        """
        添加告警规则
        
        Args:
            rule: 告警规则
        """
        self.rules.append(rule)
    
    def add_notification_handler(self, handler: Callable):
        """
        添加通知处理器
        
        Args:
            handler: 处理函数，接收 Alert 对象
        """
        self.notification_handlers.append(handler)
    
    def check_and_alert(self, metrics: Dict[str, Any]):
        """
        检查指标并触发告警
        
        Args:
            metrics: 指标数据字典
        """
        with self._lock:
            for rule in self.rules:
                if rule.should_trigger(metrics):
                    alert = rule.trigger(metrics)
                    self._trigger_alert(alert)
    
    def _trigger_alert(self, alert: Alert):
        """
        触发告警
        
        Args:
            alert: Alert 对象
        """
        # 添加到活跃告警
        self.active_alerts.append(alert)
        
        # 添加到历史
        self.alert_history.append(alert)
        if len(self.alert_history) > self.max_history:
            self.alert_history.pop(0)
        
        # 发送通知
        for handler in self.notification_handlers:
            try:
                handler(alert)
            except Exception as e:
                self.logger.error(f'通知处理器执行失败: {str(e)}')
    
    def _log_handler(self, alert: Alert):
        """
        日志处理器
        
        Args:
            alert: Alert 对象
        """
        log_level = {
            AlertLevel.INFO: logging.INFO,
            AlertLevel.WARNING: logging.WARNING,
            AlertLevel.CRITICAL: logging.CRITICAL,
            AlertLevel.ERROR: logging.ERROR,
        }.get(alert.level, logging.WARNING)
        
        self.logger.log(log_level, f"[{alert.alert_type}] {alert.message}")
    
    def _email_handler(self, alert: Alert):
        """
        邮件处理器
        
        Args:
            alert: Alert 对象
        """
        try:
            # 创建邮件
            msg = MIMEMultipart()
            msg['From'] = self.config['email_username']
            msg['To'] = ', '.join(self.config['email_recipients'])
            msg['Subject'] = f"[{alert.level.upper()}] {alert.alert_type} - 房屋租赁系统告警"
            
            # 邮件正文
            body = f"""
告警类型: {alert.alert_type}
告警级别: {alert.level}
告警消息: {alert.message}
告警时间: {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}

详细信息:
{json.dumps(alert.details, indent=2, ensure_ascii=False)}

---
此邮件由房屋租赁系统自动发送
            """
            
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            # 发送邮件
            with smtplib.SMTP(
                self.config['email_smtp_server'],
                self.config['email_smtp_port']
            ) as server:
                server.starttls()
                server.login(
                    self.config['email_username'],
                    self.config['email_password']
                )
                server.send_message(msg)
            
            self.logger.info(f'告警邮件已发送: {alert.alert_type}')
            
        except Exception as e:
            self.logger.error(f'发送告警邮件失败: {str(e)}')
    
    def _webhook_handler(self, alert: Alert):
        """
        Webhook 处理器
        
        Args:
            alert: Alert 对象
        """
        try:
            import requests
            
            payload = {
                'alert_type': alert.alert_type,
                'level': alert.level,
                'message': alert.message,
                'details': alert.details,
                'timestamp': alert.timestamp.isoformat(),
            }
            
            response = requests.post(
                self.config['webhook_url'],
                json=payload,
                timeout=5
            )
            
            if response.status_code == 200:
                self.logger.info(f'告警 Webhook 已发送: {alert.alert_type}')
            else:
                self.logger.error(
                    f'告警 Webhook 发送失败: HTTP {response.status_code}'
                )
            
        except Exception as e:
            self.logger.error(f'发送告警 Webhook 失败: {str(e)}')
    
    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """
        获取活跃告警
        
        Returns:
            活跃告警列表
        """
        with self._lock:
            return [alert.to_dict() for alert in self.active_alerts if not alert.resolved]
    
    def get_alert_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        获取告警历史
        
        Args:
            limit: 返回数量限制
        
        Returns:
            告警历史列表
        """
        with self._lock:
            return [alert.to_dict() for alert in self.alert_history[-limit:]]
    
    def resolve_alert(self, alert_index: int):
        """
        解决告警
        
        Args:
            alert_index: 告警索引
        """
        with self._lock:
            if 0 <= alert_index < len(self.active_alerts):
                self.active_alerts[alert_index].resolve()
    
    def clear_resolved_alerts(self):
        """清除已解决的告警"""
        with self._lock:
            self.active_alerts = [
                alert for alert in self.active_alerts if not alert.resolved
            ]
    
    def create_custom_alert(
        self,
        alert_type: str,
        level: str,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        创建自定义告警
        
        Args:
            alert_type: 告警类型
            level: 告警级别
            message: 告警消息
            details: 详细信息
        """
        alert = Alert(
            alert_type=alert_type,
            level=level,
            message=message,
            details=details
        )
        
        with self._lock:
            self._trigger_alert(alert)


# 全局告警管理器实例
alert_manager = AlertManager()


def get_alert_manager() -> AlertManager:
    """
    获取全局告警管理器实例
    
    Returns:
        AlertManager 实例
    """
    return alert_manager


def setup_alert_manager(app: Flask) -> AlertManager:
    """
    设置告警管理器
    
    Args:
        app: Flask 应用实例
    
    Returns:
        AlertManager 实例
    """
    global alert_manager
    alert_manager.init_app(app)
    return alert_manager


def check_alerts_periodically(interval: int = 60):
    """
    定期检查告警的装饰器
    
    Args:
        interval: 检查间隔（秒）
    
    使用示例:
        @check_alerts_periodically(interval=60)
        def collect_metrics():
            # 收集指标数据
            return metrics
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # 执行原函数收集指标
            metrics = func(*args, **kwargs)
            
            # 检查告警
            alert_mgr = get_alert_manager()
            alert_mgr.check_and_alert(metrics)
            
            return metrics
        
        return wrapper
    
    return decorator
