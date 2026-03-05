"""
Prometheus 监控指标模块

功能：
1. 请求计数器 - 统计 HTTP 请求总数
2. 请求延迟直方图 - 记录请求响应时间分布
3. 错误率统计 - 跟踪错误请求比例
4. 数据库连接池监控 - 监控数据库连接状态
5. 自定义业务指标 - 房源、租客、合同等业务指标

使用方法：
    from app.utils.prometheus_metrics import metrics
    
    # 在路由中记录业务指标
    metrics.house_created_total.inc()
    metrics.contract_signed_total.labels(contract_type='rental').inc()
"""
import time
import logging
import threading
from typing import Optional, Dict, Any
from flask import Flask, request, Response
from prometheus_client import Counter, Histogram, Gauge, Info, CollectorRegistry, generate_latest, CONTENT_TYPE_LATEST
from prometheus_client.core import CollectorRegistry
from prometheus_flask_exporter import PrometheusMetrics


class CustomPrometheusMetrics:
    """
    自定义 Prometheus 监控指标管理器
    
    提供应用级别的监控指标，包括：
    - HTTP 请求指标（自动收集）
    - 数据库连接池指标
    - 业务指标（房源、租客、合同等）
    - 系统资源指标
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls, app: Optional[Flask] = None):
        """单例模式"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, app: Optional[Flask] = None):
        """
        初始化 Prometheus 监控指标
        
        Args:
            app: Flask 应用实例
        """
        # 防止重复初始化
        if hasattr(self, '_initialized') and self._initialized:
            if app:
                self.init_app(app)
            return
        
        self.app = app
        self.flask_metrics = None
        self.registry = CollectorRegistry(auto_describe=True)
        
        # 初始化指标
        self._init_http_metrics()
        self._init_database_metrics()
        self._init_business_metrics()
        self._init_system_metrics()
        
        self._initialized = True
        
        if app:
            self.init_app(app)
    
    def init_app(self, app: Flask):
        """
        初始化 Flask 应用的 Prometheus 监控
        
        Args:
            app: Flask 应用实例
        """
        self.app = app
        
        # 初始化 Flask Prometheus Metrics（自动收集 HTTP 请求指标）
        self.flask_metrics = PrometheusMetrics(
            app,
            registry=self.registry,
            path=None,  # 不自动注册 /metrics 路由，我们手动控制
            static_labels={'application': 'housing_rental_system'},
            group_by_endpoint=True,
            buckets=[0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0],
            exclude_paths=['/metrics', '/health', '/api/health'],
            skip_registry=True
        )
        
        # 注册自定义指标收集器
        self._register_custom_collectors()
        
        # 添加指标端点
        @app.route('/metrics')
        def metrics_endpoint():
            """Prometheus 指标抓取端点"""
            return Response(
                generate_latest(self.registry),
                mimetype=CONTENT_TYPE_LATEST
            )
        
        app.logger.info('Prometheus 监控指标已启用 - 端点: /metrics')
    
    def _init_http_metrics(self):
        """初始化 HTTP 请求相关指标"""
        # 请求计数器（按方法、路径、状态码分组）
        self.http_requests_total = Counter(
            'http_requests_total',
            'HTTP 请求总数',
            ['method', 'endpoint', 'status'],
            registry=self.registry
        )
        
        # 请求延迟直方图
        self.http_request_duration_seconds = Histogram(
            'http_request_duration_seconds',
            'HTTP 请求延迟（秒）',
            ['method', 'endpoint'],
            buckets=[0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0],
            registry=self.registry
        )
        
        # 活跃请求数
        self.http_requests_active = Gauge(
            'http_requests_active',
            '当前活跃的 HTTP 请求数',
            registry=self.registry
        )
        
        # 请求大小
        self.http_request_size_bytes = Histogram(
            'http_request_size_bytes',
            'HTTP 请求大小（字节）',
            ['method', 'endpoint'],
            buckets=[100, 1000, 10000, 100000, 1000000],
            registry=self.registry
        )
        
        # 响应大小
        self.http_response_size_bytes = Histogram(
            'http_response_size_bytes',
            'HTTP 响应大小（字节）',
            ['method', 'endpoint'],
            buckets=[100, 1000, 10000, 100000, 1000000],
            registry=self.registry
        )
    
    def _init_database_metrics(self):
        """初始化数据库相关指标"""
        # 数据库连接池大小
        self.db_pool_size = Gauge(
            'db_pool_size',
            '数据库连接池大小',
            registry=self.registry
        )
        
        # 活跃连接数
        self.db_pool_active = Gauge(
            'db_pool_active_connections',
            '数据库活跃连接数',
            registry=self.registry
        )
        
        # 空闲连接数
        self.db_pool_idle = Gauge(
            'db_pool_idle_connections',
            '数据库空闲连接数',
            registry=self.registry
        )
        
        # 溢出连接数
        self.db_pool_overflow = Gauge(
            'db_pool_overflow_connections',
            '数据库溢出连接数',
            registry=self.registry
        )
        
        # 连接创建总数
        self.db_connections_created_total = Counter(
            'db_connections_created_total',
            '数据库连接创建总数',
            registry=self.registry
        )
        
        # 连接检出总数
        self.db_connections_checked_out_total = Counter(
            'db_connections_checked_out_total',
            '数据库连接检出总数',
            registry=self.registry
        )
        
        # 连接归还总数
        self.db_connections_checked_in_total = Counter(
            'db_connections_checked_in_total',
            '数据库连接归还总数',
            registry=self.registry
        )
        
        # 连接关闭总数
        self.db_connections_closed_total = Counter(
            'db_connections_closed_total',
            '数据库连接关闭总数',
            registry=self.registry
        )
        
        # 慢查询计数器
        self.db_slow_queries_total = Counter(
            'db_slow_queries_total',
            '慢查询总数',
            ['table', 'query_type'],
            registry=self.registry
        )
        
        # 查询延迟直方图
        self.db_query_duration_seconds = Histogram(
            'db_query_duration_seconds',
            '数据库查询延迟（秒）',
            ['query_type'],
            buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
            registry=self.registry
        )
    
    def _init_business_metrics(self):
        """初始化业务相关指标"""
        # 房源指标
        self.houses_total = Gauge(
            'houses_total',
            '房源总数',
            ['status'],
            registry=self.registry
        )
        
        self.house_created_total = Counter(
            'house_created_total',
            '创建房源总数',
            registry=self.registry
        )
        
        self.house_updated_total = Counter(
            'house_updated_total',
            '更新房源总数',
            registry=self.registry
        )
        
        self.house_deleted_total = Counter(
            'house_deleted_total',
            '删除房源总数',
            registry=self.registry
        )
        
        # 租客指标
        self.tenants_total = Gauge(
            'tenants_total',
            '租客总数',
            ['status'],
            registry=self.registry
        )
        
        self.tenant_created_total = Counter(
            'tenant_created_total',
            '创建租客总数',
            registry=self.registry
        )
        
        # 合同指标
        self.contracts_total = Gauge(
            'contracts_total',
            '合同总数',
            ['status', 'type'],
            registry=self.registry
        )
        
        self.contract_signed_total = Counter(
            'contract_signed_total',
            '签署合同总数',
            ['contract_type'],
            registry=self.registry
        )
        
        self.contract_expired_total = Counter(
            'contract_expired_total',
            '过期合同总数',
            registry=self.registry
        )
        
        # 支付指标
        self.payments_total = Gauge(
            'payments_total',
            '支付记录总数',
            ['status'],
            registry=self.registry
        )
        
        self.payment_amount_total = Counter(
            'payment_amount_total',
            '支付总金额',
            ['payment_method'],
            registry=self.registry
        )
        
        # 房东指标
        self.landlords_total = Gauge(
            'landlords_total',
            '房东总数',
            ['status'],
            registry=self.registry
        )
        
        # 员工指标
        self.employees_total = Gauge(
            'employees_total',
            '员工总数',
            ['department', 'status'],
            registry=self.registry
        )
        
        # 用户指标
        self.users_total = Gauge(
            'users_total',
            '用户总数',
            ['role', 'status'],
            registry=self.registry
        )
        
        self.user_login_total = Counter(
            'user_login_total',
            '用户登录总数',
            ['status'],
            registry=self.registry
        )
    
    def _init_system_metrics(self):
        """初始化系统资源指标"""
        # CPU 使用率
        self.system_cpu_usage = Gauge(
            'system_cpu_usage_percent',
            'CPU 使用率（百分比）',
            registry=self.registry
        )
        
        # 内存使用
        self.system_memory_usage = Gauge(
            'system_memory_usage_bytes',
            '内存使用量（字节）',
            registry=self.registry
        )
        
        self.system_memory_available = Gauge(
            'system_memory_available_bytes',
            '可用内存量（字节）',
            registry=self.registry
        )
        
        # 磁盘使用
        self.system_disk_usage = Gauge(
            'system_disk_usage_bytes',
            '磁盘使用量（字节）',
            ['path'],
            registry=self.registry
        )
        
        # 应用信息
        self.app_info = Info(
            'app',
            '应用信息',
            registry=self.registry
        )
        self.app_info.info({
            'version': '1.0.0',
            'name': 'housing_rental_system'
        })
    
    def _register_custom_collectors(self):
        """注册自定义指标收集器"""
        # 这里可以注册自定义的指标收集器
        # 例如：定期收集系统资源指标
        pass
    
    def track_request(self, method: str, endpoint: str, status: int, duration: float):
        """
        跟踪 HTTP 请求
        
        Args:
            method: HTTP 方法
            endpoint: 端点路径
            status: HTTP 状态码
            duration: 请求持续时间（秒）
        """
        self.http_requests_total.labels(method=method, endpoint=endpoint, status=status).inc()
        self.http_request_duration_seconds.labels(method=method, endpoint=endpoint).observe(duration)
    
    def track_db_connection_created(self):
        """跟踪数据库连接创建"""
        self.db_connections_created_total.inc()
    
    def track_db_connection_checkout(self):
        """跟踪数据库连接检出"""
        self.db_connections_checked_out_total.inc()
    
    def track_db_connection_checkin(self):
        """跟踪数据库连接归还"""
        self.db_connections_checked_in_total.inc()
    
    def track_db_connection_closed(self):
        """跟踪数据库连接关闭"""
        self.db_connections_closed_total.inc()
    
    def track_slow_query(self, table: str, query_type: str):
        """
        跟踪慢查询
        
        Args:
            table: 表名
            query_type: 查询类型
        """
        self.db_slow_queries_total.labels(table=table, query_type=query_type).inc()
    
    def update_db_pool_metrics(self, pool_size: int, active: int, idle: int, overflow: int):
        """
        更新数据库连接池指标
        
        Args:
            pool_size: 连接池大小
            active: 活跃连接数
            idle: 空闲连接数
            overflow: 溢出连接数
        """
        self.db_pool_size.set(pool_size)
        self.db_pool_active.set(active)
        self.db_pool_idle.set(idle)
        self.db_pool_overflow.set(overflow)
    
    def update_business_metrics(self, metric_name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """
        更新业务指标
        
        Args:
            metric_name: 指标名称
            value: 指标值
            labels: 标签字典
        """
        metric = getattr(self, metric_name, None)
        if metric is None:
            logging.warning(f"未找到指标: {metric_name}")
            return
        
        if labels:
            metric.labels(**labels).set(value)
        else:
            metric.set(value)
    
    def increment_business_counter(self, metric_name: str, labels: Optional[Dict[str, str]] = None):
        """
        递增业务计数器
        
        Args:
            metric_name: 指标名称
            labels: 标签字典
        """
        metric = getattr(self, metric_name, None)
        if metric is None:
            logging.warning(f"未找到指标: {metric_name}")
            return
        
        if labels:
            metric.labels(**labels).inc()
        else:
            metric.inc()
    
    def update_system_metrics(self, cpu_percent: float, memory_used: int, memory_available: int):
        """
        更新系统资源指标
        
        Args:
            cpu_percent: CPU 使用率
            memory_used: 已使用内存（字节）
            memory_available: 可用内存（字节）
        """
        self.system_cpu_usage.set(cpu_percent)
        self.system_memory_usage.set(memory_used)
        self.system_memory_available.set(memory_available)
    
    def get_metrics(self) -> str:
        """
        获取 Prometheus 格式的指标数据
        
        Returns:
            Prometheus 格式的指标文本
        """
        return generate_latest(self.registry)


# 全局指标实例
metrics = CustomPrometheusMetrics()


def get_metrics() -> CustomPrometheusMetrics:
    """
    获取全局 Prometheus 指标实例
    
    Returns:
        CustomPrometheusMetrics 实例
    """
    return metrics


def setup_prometheus_metrics(app: Flask) -> CustomPrometheusMetrics:
    """
    设置 Prometheus 监控指标
    
    Args:
        app: Flask 应用实例
    
    Returns:
        CustomPrometheusMetrics 实例
    """
    global metrics
    metrics.init_app(app)
    return metrics
