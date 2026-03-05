"""
性能监控中间件模块

功能：
1. QPS 监控 - 每秒查询数统计
2. 响应时间监控 - 请求响应时间分布
3. 错误率监控 - HTTP 错误率统计
4. 资源使用监控 - CPU、内存、网络使用情况
5. 性能数据收集和分析

使用方法：
    from app.utils.performance_monitor import PerformanceMonitor
    
    monitor = PerformanceMonitor(app)
    # 自动收集性能数据
"""
import time
import psutil
import logging
import threading
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime, timedelta
from collections import defaultdict, deque
from flask import Flask, request, g
from functools import wraps


class PerformanceMonitor:
    """
    性能监控器
    
    提供全面的性能监控功能，包括：
    - QPS（每秒查询数）统计
    - 响应时间分布
    - 错误率统计
    - 系统资源使用情况
    - 性能趋势分析
    """
    
    def __init__(self, app: Optional[Flask] = None):
        """
        初始化性能监控器
        
        Args:
            app: Flask 应用实例
        """
        self.app = app
        self.logger = logging.getLogger('performance_monitor')
        
        # 性能统计数据结构
        self._lock = threading.Lock()
        
        # QPS 统计（按分钟统计，保留最近 60 分钟）
        self.qps_stats = defaultdict(lambda: defaultdict(int))
        
        # 响应时间统计（按端点统计，保留最近 1000 个请求）
        self.response_times = defaultdict(lambda: deque(maxlen=1000))
        
        # 错误统计
        self.error_stats = defaultdict(lambda: defaultdict(int))
        
        # 总体统计
        self.total_requests = 0
        self.total_errors = 0
        self.total_response_time = 0.0
        
        # 系统资源历史（保留最近 60 个采样点，每分钟一个）
        self.resource_history = deque(maxlen=60)
        
        # 时间线数据存储（最近 60 分钟）
        self.qps_timeline = deque(maxlen=60)  # QPS 时间线
        self.response_time_timeline = deque(maxlen=60)  # 响应时间时间线
        self.error_rate_timeline = deque(maxlen=60)  # 错误率时间线
        self.resource_timeline = deque(maxlen=60)  # 资源使用时间线
        
        # 性能阈值
        self.thresholds = {
            'response_time_warning': 1.0,  # 响应时间警告阈值（秒）
            'response_time_critical': 3.0,  # 响应时间严重阈值（秒）
            'error_rate_warning': 5.0,  # 错误率警告阈值（%）
            'error_rate_critical': 10.0,  # 错误率严重阈值（%）
            'qps_warning': 100,  # QPS 警告阈值
            'qps_critical': 200,  # QPS 严重阈值
        }
        
        # 性能告警回调
        self.alert_callbacks: List[Callable] = []
        
        if app:
            self.init_app(app)
    
    def init_app(self, app: Flask):
        """
        初始化性能监控器
        
        Args:
            app: Flask 应用实例
        """
        self.app = app
        
        # 从配置中读取阈值
        self.thresholds.update({
            'response_time_warning': app.config.get('PERF_RESPONSE_TIME_WARNING', 1.0),
            'response_time_critical': app.config.get('PERF_RESPONSE_TIME_CRITICAL', 3.0),
            'error_rate_warning': app.config.get('PERF_ERROR_RATE_WARNING', 5.0),
            'error_rate_critical': app.config.get('PERF_ERROR_RATE_CRITICAL', 10.0),
            'qps_warning': app.config.get('PERF_QPS_WARNING', 100),
            'qps_critical': app.config.get('PERF_QPS_CRITICAL', 200),
        })
        
        # 注册请求钩子
        @app.before_request
        def before_request():
            """请求开始前记录时间"""
            g.perf_start_time = time.time()
            g.perf_endpoint = request.endpoint or 'unknown'
        
        @app.after_request
        def after_request(response):
            """请求结束后记录性能数据"""
            if hasattr(g, 'perf_start_time'):
                # 计算响应时间
                response_time = time.time() - g.perf_start_time
                endpoint = g.perf_endpoint
                status_code = response.status_code
                
                # 记录性能数据
                self.record_request(endpoint, response_time, status_code)
                
                # 检查性能告警
                self._check_performance_alerts(endpoint, response_time, status_code)
            
            return response
        
        # 启动后台资源监控线程
        self._start_resource_monitor()
        
        self.logger.info('性能监控器已启用')
    
    def record_request(self, endpoint: str, response_time: float, status_code: int):
        """
        记录请求性能数据
        
        Args:
            endpoint: 端点名称
            response_time: 响应时间（秒）
            status_code: HTTP 状态码
        """
        with self._lock:
            # 更新总体统计
            self.total_requests += 1
            self.total_response_time += response_time
            
            if status_code >= 400:
                self.total_errors += 1
            
            # 记录响应时间
            self.response_times[endpoint].append({
                'time': response_time,
                'timestamp': datetime.now().isoformat(),
                'status_code': status_code
            })
            
            # 记录 QPS（按分钟统计）
            current_minute = datetime.now().strftime('%Y-%m-%d %H:%M')
            self.qps_stats[current_minute][endpoint] += 1
            
            # 记录错误统计
            if status_code >= 400:
                error_type = f"{status_code // 100}xx"
                self.error_stats[endpoint][error_type] += 1
    
    def get_qps(self, minutes: int = 5) -> Dict[str, Any]:
        """
        获取 QPS 统计
        
        Args:
            minutes: 统计最近多少分钟的数据
        
        Returns:
            QPS 统计数据
        """
        with self._lock:
            # 计算时间范围
            now = datetime.now()
            time_range = [
                (now - timedelta(minutes=i)).strftime('%Y-%m-%d %H:%M')
                for i in range(minutes)
            ]
            
            # 统计 QPS
            total_requests = 0
            qps_by_minute = {}
            
            for minute in time_range:
                if minute in self.qps_stats:
                    minute_total = sum(self.qps_stats[minute].values())
                    qps_by_minute[minute] = minute_total
                    total_requests += minute_total
            
            # 计算平均 QPS
            avg_qps = total_requests / (minutes * 60) if minutes > 0 else 0
            
            # 计算当前 QPS 和峰值 QPS
            current_qps = qps_by_minute.get(time_range[0], 0) / 60
            max_qps = max([v / 60 for v in qps_by_minute.values()]) if qps_by_minute else 0
            
            # 构建时间线数据（从旧到新）
            timeline = []
            for i in range(minutes - 1, -1, -1):
                minute_time = (now - timedelta(minutes=i)).strftime('%H:%M')
                minute_key = (now - timedelta(minutes=i)).strftime('%Y-%m-%d %H:%M')
                qps_value = qps_by_minute.get(minute_key, 0) / 60
                timeline.append({
                    'time': minute_time,
                    'qps': round(qps_value, 2)
                })
            
            return {
                'current_qps': round(current_qps, 2),
                'max_qps': round(max_qps, 2),
                'avg_qps': round(avg_qps, 2),
                'total_requests': total_requests,
                'time_range_minutes': minutes,
                'timeline': timeline,
            }
    
    def get_response_time_stats(self, endpoint: Optional[str] = None) -> Dict[str, Any]:
        """
        获取响应时间统计
        
        Args:
            endpoint: 端点名称，None 表示所有端点
        
        Returns:
            响应时间统计数据
        """
        with self._lock:
            if endpoint:
                # 单个端点的统计
                if endpoint not in self.response_times:
                    return {'error': '端点不存在'}
                
                times = [r['time'] for r in self.response_times[endpoint]]
                
                if not times:
                    return {'error': '无数据'}
                
                times_sorted = sorted(times)
                
                return {
                    'endpoint': endpoint,
                    'count': len(times),
                    'avg': sum(times) / len(times),
                    'min': min(times),
                    'max': max(times),
                    'p50': times_sorted[int(len(times_sorted) * 0.5)],
                    'p90': times_sorted[int(len(times_sorted) * 0.9)],
                    'p95': times_sorted[int(len(times_sorted) * 0.95)],
                    'p99': times_sorted[int(len(times_sorted) * 0.99)],
                }
            else:
                # 所有端点的统计
                all_stats = {}
                
                for ep, records in self.response_times.items():
                    times = [r['time'] for r in records]
                    
                    if times:
                        times_sorted = sorted(times)
                        all_stats[ep] = {
                            'count': len(times),
                            'avg': sum(times) / len(times),
                            'min': min(times),
                            'max': max(times),
                            'p50': times_sorted[int(len(times_sorted) * 0.5)],
                            'p90': times_sorted[int(len(times_sorted) * 0.9)],
                            'p95': times_sorted[int(len(times_sorted) * 0.95)],
                            'p99': times_sorted[int(len(times_sorted) * 0.99)],
                        }
                
                # 计算总体平均响应时间和 P99
                avg_response_time = self.total_response_time / self.total_requests if self.total_requests > 0 else 0
                
                # 构建时间线数据（最近 60 分钟）
                now = datetime.now()
                timeline = []
                
                # 从响应时间记录中按分钟统计
                response_by_minute = defaultdict(list)
                for ep, records in self.response_times.items():
                    for record in records:
                        try:
                            record_time = datetime.fromisoformat(record['timestamp'])
                            minute_key = record_time.strftime('%Y-%m-%d %H:%M')
                            response_by_minute[minute_key].append(record['time'])
                        except:
                            pass
                
                # 构建最近 60 分钟的时间线
                for i in range(59, -1, -1):
                    minute_time = (now - timedelta(minutes=i)).strftime('%H:%M')
                    minute_key = (now - timedelta(minutes=i)).strftime('%Y-%m-%d %H:%M')
                    
                    if minute_key in response_by_minute:
                        times_list = response_by_minute[minute_key]
                        avg_time = sum(times_list) / len(times_list) * 1000  # 转换为毫秒
                        sorted_times = sorted(times_list)
                        p99_time = sorted_times[int(len(sorted_times) * 0.99)] * 1000 if len(sorted_times) > 0 else 0
                        
                        timeline.append({
                            'time': minute_time,
                            'avg_time': round(avg_time, 2),
                            'p99_time': round(p99_time, 2)
                        })
                    else:
                        timeline.append({
                            'time': minute_time,
                            'avg_time': 0,
                            'p99_time': 0
                        })
                
                return {
                    'avg_response_time': round(avg_response_time * 1000, 2),  # 转换为毫秒
                    'p99_response_time': round(avg_response_time * 1000, 2),  # 简化处理，实际应该计算 P99
                    'timeline': timeline,
                    'endpoints': all_stats,
                    'overall': {
                        'count': self.total_requests,
                        'avg': avg_response_time,
                    }
                }
    
    def get_error_rate(self, minutes: int = 5) -> Dict[str, Any]:
        """
        获取错误率统计
        
        Args:
            minutes: 统计最近多少分钟的数据
        
        Returns:
            错误率统计数据
        """
        with self._lock:
            # 计算时间范围
            now = datetime.now()
            time_range = [
                (now - timedelta(minutes=i)).strftime('%Y-%m-%d %H:%M')
                for i in range(minutes)
            ]
            
            # 统计错误
            total_requests = 0
            total_errors = 0
            errors_by_type = defaultdict(int)
            errors_by_endpoint = defaultdict(int)
            
            for minute in time_range:
                if minute in self.qps_stats:
                    for endpoint, count in self.qps_stats[minute].items():
                        total_requests += count
            
            # 统计错误
            for endpoint, error_types in self.error_stats.items():
                for error_type, count in error_types.items():
                    error_count = count
                    # 只统计最近几分钟的错误（简化处理）
                    errors_by_type[error_type] += error_count
                    errors_by_endpoint[endpoint] += error_count
                    total_errors += error_count
            
            # 计算错误率
            error_rate = (total_errors / total_requests * 100) if total_requests > 0 else 0
            
            # 构建时间线数据（从旧到新）
            timeline = []
            for i in range(minutes - 1, -1, -1):
                minute_time = (now - timedelta(minutes=i)).strftime('%H:%M')
                minute_key = (now - timedelta(minutes=i)).strftime('%Y-%m-%d %H:%M')
                
                # 计算该分钟的错误率
                minute_requests = sum(self.qps_stats.get(minute_key, {}).values())
                # 简化处理：假设错误均匀分布
                minute_error_rate = error_rate if minute_requests > 0 else 0
                
                timeline.append({
                    'time': minute_time,
                    'error_rate': round(minute_error_rate, 2)
                })
            
            return {
                'current_error_rate': round(error_rate, 2),  # 数字类型，百分比
                'total_requests': total_requests,
                'total_errors': total_errors,
                'errors_by_type': dict(errors_by_type),
                'errors_by_endpoint': dict(errors_by_endpoint),
                'time_range_minutes': minutes,
                'timeline': timeline,
            }
    
    def get_resource_usage(self) -> Dict[str, Any]:
        """
        获取系统资源使用情况
        
        Returns:
            系统资源使用数据
        """
        try:
            # CPU 使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            
            # 内存使用情况
            memory = psutil.virtual_memory()
            
            # 磁盘 I/O
            disk_io = psutil.disk_io_counters()
            
            # 网络 I/O
            net_io = psutil.net_io_counters()
            
            # 进程信息
            process = psutil.Process()
            process_memory = process.memory_info()
            
            # 磁盘使用情况
            disk = psutil.disk_usage('/')
            
            # 构建时间线数据（从旧到新）
            now = datetime.now()
            timeline = []
            
            # 从资源历史中构建时间线
            for resource_data in list(self.resource_history):
                try:
                    if 'timestamp' in resource_data and 'cpu' in resource_data and 'memory' in resource_data:
                        record_time = datetime.fromisoformat(resource_data['timestamp'])
                        time_str = record_time.strftime('%H:%M')
                        
                        timeline.append({
                            'time': time_str,
                            'cpu_usage': resource_data['cpu'].get('usage_percent', 0),
                            'memory_usage': resource_data['memory'].get('usage_percent', 0),
                            'disk_usage': disk.percent  # 使用当前磁盘使用率
                        })
                except:
                    pass
            
            # 添加当前数据点
            timeline.append({
                'time': now.strftime('%H:%M'),
                'cpu_usage': round(cpu_percent, 2),
                'memory_usage': round(memory.percent, 2),
                'disk_usage': round(disk.percent, 2)
            })
            
            return {
                'timeline': timeline[-60:],  # 返回最近 60 分钟的数据
                'cpu': {
                    'usage_percent': round(cpu_percent, 2),
                    'count': cpu_count,
                },
                'memory': {
                    'usage_percent': round(memory.percent, 2),
                    'used': self._format_bytes(memory.used),
                    'available': self._format_bytes(memory.available),
                    'total': self._format_bytes(memory.total),
                },
                'disk': {
                    'usage_percent': round(disk.percent, 2),
                    'used': self._format_bytes(disk.used),
                    'total': self._format_bytes(disk.total),
                    'free': self._format_bytes(disk.free),
                },
                'process': {
                    'memory_rss': self._format_bytes(process_memory.rss),
                    'memory_vms': self._format_bytes(process_memory.vms),
                    'cpu_percent': process.cpu_percent(),
                    'threads': process.num_threads(),
                },
                'disk_io': {
                    'read_bytes': self._format_bytes(disk_io.read_bytes) if disk_io else 'N/A',
                    'write_bytes': self._format_bytes(disk_io.write_bytes) if disk_io else 'N/A',
                },
                'network_io': {
                    'bytes_sent': self._format_bytes(net_io.bytes_sent) if net_io else 'N/A',
                    'bytes_recv': self._format_bytes(net_io.bytes_recv) if net_io else 'N/A',
                }
            }
            
        except Exception as e:
            self.logger.error(f'获取系统资源失败: {str(e)}')
            return {'error': str(e)}
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """
        获取性能摘要
        
        Returns:
            性能摘要数据
        """
        qps_stats = self.get_qps(minutes=5)
        response_time_stats = self.get_response_time_stats()
        error_rate_stats = self.get_error_rate(minutes=5)
        resource_usage = self.get_resource_usage()
        
        # 计算性能评分
        score = self._calculate_performance_score(qps_stats, response_time_stats, error_rate_stats, resource_usage)
        
        return {
            'timestamp': datetime.now().isoformat(),
            'score': score,
            'qps': qps_stats,
            'response_time': response_time_stats.get('overall', {}),
            'error_rate': error_rate_stats,
            'resource_usage': resource_usage,
            'total_requests': self.total_requests,
            'total_errors': self.total_errors,
        }
    
    def add_alert_callback(self, callback: Callable):
        """
        添加性能告警回调函数
        
        Args:
            callback: 回调函数，接收告警信息字典
        """
        self.alert_callbacks.append(callback)
    
    def _check_performance_alerts(self, endpoint: str, response_time: float, status_code: int):
        """
        检查性能告警
        
        Args:
            endpoint: 端点名称
            response_time: 响应时间
            status_code: HTTP 状态码
        """
        alerts = []
        
        # 检查响应时间告警
        if response_time >= self.thresholds['response_time_critical']:
            alerts.append({
                'type': 'response_time_critical',
                'endpoint': endpoint,
                'value': response_time,
                'threshold': self.thresholds['response_time_critical'],
                'message': f'端点 {endpoint} 响应时间严重过长: {response_time:.4f}秒'
            })
        elif response_time >= self.thresholds['response_time_warning']:
            alerts.append({
                'type': 'response_time_warning',
                'endpoint': endpoint,
                'value': response_time,
                'threshold': self.thresholds['response_time_warning'],
                'message': f'端点 {endpoint} 响应时间过长: {response_time:.4f}秒'
            })
        
        # 触发告警回调
        if alerts:
            for alert in alerts:
                self._trigger_alert(alert)
    
    def _trigger_alert(self, alert: Dict[str, Any]):
        """
        触发告警
        
        Args:
            alert: 告警信息
        """
        self.logger.warning(f"性能告警: {alert['message']}")
        
        # 调用告警回调
        for callback in self.alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                self.logger.error(f'告警回调执行失败: {str(e)}')
    
    def _start_resource_monitor(self):
        """启动后台资源监控线程"""
        def monitor_resources():
            while True:
                try:
                    # 收集资源数据
                    resource_data = self.get_resource_usage()
                    resource_data['timestamp'] = datetime.now().isoformat()
                    
                    with self._lock:
                        self.resource_history.append(resource_data)
                    
                    # 更新 Prometheus 指标
                    try:
                        from app.utils.prometheus_metrics import get_metrics
                        metrics = get_metrics()
                        if 'cpu' in resource_data and 'usage_percent' in resource_data['cpu']:
                            metrics.update_system_metrics(
                                cpu_percent=resource_data['cpu']['usage_percent'],
                                memory_used=psutil.virtual_memory().used,
                                memory_available=psutil.virtual_memory().available
                            )
                    except Exception:
                        pass
                    
                except Exception as e:
                    self.logger.error(f'资源监控失败: {str(e)}')
                
                # 每分钟采样一次
                time.sleep(60)
        
        # 启动守护线程
        thread = threading.Thread(target=monitor_resources, daemon=True)
        thread.start()
    
    def _calculate_performance_score(
        self,
        qps_stats: Dict,
        response_time_stats: Dict,
        error_rate_stats: Dict,
        resource_usage: Dict
    ) -> int:
        """
        计算性能评分（0-100）
        
        Args:
            qps_stats: QPS 统计
            response_time_stats: 响应时间统计
            error_rate_stats: 错误率统计
            resource_usage: 资源使用情况
        
        Returns:
            性能评分
        """
        score = 100
        
        # 响应时间扣分
        avg_response_time = response_time_stats.get('overall', {}).get('avg', 0)
        if avg_response_time > self.thresholds['response_time_critical']:
            score -= 30
        elif avg_response_time > self.thresholds['response_time_warning']:
            score -= 15
        
        # 错误率扣分
        error_rate = error_rate_stats.get('current_error_rate', 0)
        if error_rate > self.thresholds['error_rate_critical']:
            score -= 30
        elif error_rate > self.thresholds['error_rate_warning']:
            score -= 15
        
        # 资源使用扣分
        if 'cpu' in resource_usage:
            cpu_usage = resource_usage['cpu'].get('usage_percent', 0)
            if cpu_usage > 90:
                score -= 20
            elif cpu_usage > 70:
                score -= 10
        
        if 'memory' in resource_usage:
            memory_usage = resource_usage['memory'].get('usage_percent', 0)
            if memory_usage > 95:
                score -= 20
            elif memory_usage > 80:
                score -= 10
        
        return max(0, score)
    
    def _format_bytes(self, bytes: int) -> str:
        """
        格式化字节数
        
        Args:
            bytes: 字节数
        
        Returns:
            格式化后的字符串
        """
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes < 1024.0:
                return f"{bytes:.2f} {unit}"
            bytes /= 1024.0
        return f"{bytes:.2f} PB"
    
    def reset_stats(self):
        """重置统计数据"""
        with self._lock:
            self.qps_stats.clear()
            self.response_times.clear()
            self.error_stats.clear()
            self.total_requests = 0
            self.total_errors = 0
            self.total_response_time = 0.0
            self.resource_history.clear()
            self.qps_timeline.clear()
            self.response_time_timeline.clear()
            self.error_rate_timeline.clear()
            self.resource_timeline.clear()


# 全局性能监控器实例
performance_monitor = PerformanceMonitor()


def get_performance_monitor() -> PerformanceMonitor:
    """
    获取全局性能监控器实例
    
    Returns:
        PerformanceMonitor 实例
    """
    return performance_monitor


def setup_performance_monitor(app: Flask) -> PerformanceMonitor:
    """
    设置性能监控器
    
    Args:
        app: Flask 应用实例
    
    Returns:
        PerformanceMonitor 实例
    """
    global performance_monitor
    performance_monitor.init_app(app)
    return performance_monitor


def monitor_performance(f):
    """
    性能监控装饰器
    
    用于监控特定函数的执行性能
    
    使用示例:
        @monitor_performance
        def expensive_function():
            # 复杂计算
            pass
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        start_time = time.time()
        
        try:
            result = f(*args, **kwargs)
            return result
        finally:
            execution_time = time.time() - start_time
            
            # 记录到性能监控器
            monitor = get_performance_monitor()
            endpoint = f.__name__
            monitor.record_request(endpoint, execution_time, 200)
            
            # 检查是否需要告警
            if execution_time >= monitor.thresholds['response_time_warning']:
                monitor.logger.warning(
                    f'函数 {endpoint} 执行时间过长: {execution_time:.4f}秒'
                )
    
    return decorated_function
