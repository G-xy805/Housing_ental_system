"""
监控路由模块

提供统一的监控端点：
1. /api/monitoring/health - 综合健康检查
2. /api/monitoring/health/db - 数据库健康检查
3. /api/monitoring/health/redis - Redis 健康检查
4. /api/monitoring/health/system - 系统资源检查
5. /api/monitoring/metrics - Prometheus 指标
6. /api/monitoring/performance - 性能摘要
7. /api/monitoring/alerts - 告警信息
8. /api/monitoring/alerts/history - 告警历史

使用方法：
    from app.routes.monitoring import monitoring_bp
    app.register_blueprint(monitoring_bp, url_prefix='/api/monitoring')
"""
from flask import Blueprint, jsonify, request
from app import db


monitoring_bp = Blueprint('monitoring', __name__)


@monitoring_bp.route('/health', methods=['GET'])
def health_check():
    """
    综合健康检查端点
    
    返回系统整体健康状态，包括：
    - 数据库状态
    - Redis 状态
    - 系统资源状态
    
    Returns:
        JSON 响应，包含健康检查结果
    """
    from app.utils.health_check import get_health_checker
    
    checker = get_health_checker()
    result = checker.check_all()
    
    status_code = 200 if result['status'] == 'healthy' else 503
    
    return jsonify({
        'success': True,
        'data': result
    }), status_code


@monitoring_bp.route('/health/db', methods=['GET'])
def health_db():
    """
    数据库健康检查端点
    
    检查数据库连接状态和连接池状态
    
    Returns:
        JSON 响应，包含数据库健康检查结果
    """
    from app.utils.health_check import get_health_checker
    
    checker = get_health_checker()
    
    db_check = checker.check_database()
    
    if db_check.status == 'unhealthy':
        overall_status = 'unhealthy'
        status_code = 503
    elif db_check.status == 'degraded':
        overall_status = 'degraded'
        status_code = 200
    else:
        overall_status = 'healthy'
        status_code = 200
    
    result = {
        'status': overall_status,
        'response_time': db_check.details.get('response_time', 0),
        'connections': db_check.details.get('connections', 0),
        'max_connections': db_check.details.get('max_connections', 0)
    }
    
    return jsonify({
        'success': True,
        'data': result
    }), status_code


@monitoring_bp.route('/health/redis', methods=['GET'])
def health_redis():
    """
    Redis 健康检查端点
    
    检查 Redis 连接状态和性能
    
    Returns:
        JSON 响应，包含 Redis 健康检查结果
    """
    from app.utils.health_check import get_health_checker
    
    checker = get_health_checker()
    redis_check = checker.check_redis()
    
    status_code = 200 if redis_check.status in ['healthy', 'degraded'] else 503
    
    result = {
        'status': redis_check.details.get('status', redis_check.status),
        'response_time': redis_check.details.get('response_time', 0),
        'memory_usage': redis_check.details.get('memory_usage', 'N/A')
    }
    
    return jsonify({
        'success': True,
        'data': result
    }), status_code


@monitoring_bp.route('/health/system', methods=['GET'])
def health_system():
    """
    系统资源健康检查端点
    
    检查 CPU、内存、磁盘使用情况
    
    Returns:
        JSON 响应，包含系统资源健康检查结果
    """
    from app.utils.health_check import get_health_checker
    
    checker = get_health_checker()
    system_check = checker.check_system_resources()
    
    status_code = 200 if system_check.status in ['healthy', 'degraded'] else 503
    
    details = system_check.details
    result = {
        'status': system_check.status,
        'cpu': {
            'usage': details.get('cpu', {}).get('usage', 0),
            'cores': details.get('cpu', {}).get('cores', 0),
            'load': details.get('cpu', {}).get('load', 'N/A')
        },
        'memory': {
            'usage_percent': details.get('memory', {}).get('usage_percent', 0),
            'used': details.get('memory', {}).get('used', '0 B'),
            'total': details.get('memory', {}).get('total', '0 B')
        },
        'disk': {
            'usage_percent': details.get('disk', {}).get('usage_percent', 0),
            'used': details.get('disk', {}).get('used', '0 B'),
            'total': details.get('disk', {}).get('total', '0 B')
        },
        'start_time': details.get('start_time', ''),
        'uptime': details.get('uptime', '0分钟')
    }
    
    return jsonify({
        'success': True,
        'data': result
    }), status_code


@monitoring_bp.route('/metrics', methods=['GET'])
def prometheus_metrics():
    """
    Prometheus 指标端点
    
    返回 Prometheus 格式的监控指标
    
    Returns:
        Prometheus 格式的指标文本
    """
    from flask import Response
    from app.utils.prometheus_metrics import get_metrics
    
    metrics = get_metrics()
    return Response(
        metrics.get_metrics(),
        mimetype='text/plain; version=0.0.4; charset=utf-8'
    )


@monitoring_bp.route('/performance', methods=['GET'])
def performance_summary():
    """
    性能摘要端点
    
    返回系统性能摘要，包括：
    - QPS 统计
    - 响应时间统计
    - 错误率统计
    - 资源使用情况
    - 性能评分
    
    Returns:
        JSON 响应，包含性能摘要数据
    """
    from app.utils.performance_monitor import get_performance_monitor
    
    monitor = get_performance_monitor()
    summary = monitor.get_performance_summary()
    
    return jsonify({
        'success': True,
        'data': summary
    })


@monitoring_bp.route('/performance/qps', methods=['GET'])
def performance_qps():
    """
    QPS 统计端点
    
    返回每秒查询数统计
    
    Query Parameters:
        minutes: 统计时间范围（分钟），默认 5
    
    Returns:
        JSON 响应，包含 QPS 统计数据
    """
    from app.utils.performance_monitor import get_performance_monitor
    
    minutes = request.args.get('minutes', default=5, type=int)
    minutes = min(max(minutes, 1), 60)
    
    monitor = get_performance_monitor()
    qps_stats = monitor.get_qps(minutes=minutes)
    
    return jsonify({
        'success': True,
        'data': qps_stats
    })


@monitoring_bp.route('/performance/response-time', methods=['GET'])
def performance_response_time():
    """
    响应时间统计端点
    
    返回响应时间分布统计
    
    Query Parameters:
        endpoint: 端点名称，不指定则返回所有端点统计
    
    Returns:
        JSON 响应，包含响应时间统计数据
    """
    from app.utils.performance_monitor import get_performance_monitor
    
    endpoint = request.args.get('endpoint', default=None, type=str)
    
    monitor = get_performance_monitor()
    stats = monitor.get_response_time_stats(endpoint=endpoint)
    
    return jsonify({
        'success': True,
        'data': stats
    })


@monitoring_bp.route('/performance/error-rate', methods=['GET'])
def performance_error_rate():
    """
    错误率统计端点
    
    返回 HTTP 错误率统计
    
    Query Parameters:
        minutes: 统计时间范围（分钟），默认 5
    
    Returns:
        JSON 响应，包含错误率统计数据
    """
    from app.utils.performance_monitor import get_performance_monitor
    
    minutes = request.args.get('minutes', default=5, type=int)
    minutes = min(max(minutes, 1), 60)
    
    monitor = get_performance_monitor()
    error_stats = monitor.get_error_rate(minutes=minutes)
    
    return jsonify({
        'success': True,
        'data': error_stats
    })


@monitoring_bp.route('/performance/resources', methods=['GET'])
def performance_resources():
    """
    系统资源使用端点
    
    返回当前系统资源使用情况
    
    Returns:
        JSON 响应，包含系统资源使用数据
    """
    from app.utils.performance_monitor import get_performance_monitor
    
    monitor = get_performance_monitor()
    resources = monitor.get_resource_usage()
    
    return jsonify({
        'success': True,
        'data': resources
    })


@monitoring_bp.route('/alerts', methods=['GET'])
def get_alerts():
    """
    获取活跃告警
    
    返回当前未解决的告警列表
    
    Query Parameters:
        page: 页码，默认 1
        page_size: 每页数量，默认 20
    
    Returns:
        JSON 响应，包含活跃告警列表
    """
    from app.utils.alerting import get_alert_manager
    
    page = request.args.get('page', default=1, type=int)
    page_size = request.args.get('page_size', default=20, type=int)
    page_size = min(max(page_size, 1), 100)
    
    alert_mgr = get_alert_manager()
    all_alerts = alert_mgr.get_active_alerts()
    
    total = len(all_alerts)
    start = (page - 1) * page_size
    end = start + page_size
    paginated_alerts = all_alerts[start:end]
    
    items = []
    for idx, alert in enumerate(paginated_alerts):
        items.append({
            'id': start + idx + 1,
            'title': alert.get('type', 'Unknown Alert'),
            'message': alert.get('message', ''),
            'source': alert.get('endpoint', 'System'),
            'severity': 'high' if 'critical' in alert.get('type', '').lower() else 'medium',
            'status': 'active',
            'triggeredAt': alert.get('timestamp', ''),
            'resolvedAt': None,
            'resolvedBy': None,
            'resolution': None
        })
    
    return jsonify({
        'success': True,
        'data': {
            'items': items,
            'total': total
        }
    })


@monitoring_bp.route('/alerts/history', methods=['GET'])
def get_alert_history():
    """
    获取告警历史
    
    返回历史告警记录
    
    Query Parameters:
        limit: 返回数量限制，默认 100
    
    Returns:
        JSON 响应，包含告警历史记录
    """
    from app.utils.alerting import get_alert_manager
    
    limit = request.args.get('limit', default=100, type=int)
    limit = min(max(limit, 1), 1000)
    
    alert_mgr = get_alert_manager()
    history = alert_mgr.get_alert_history(limit=limit)
    
    return jsonify({
        'success': True,
        'data': {
            'total': len(history),
            'alerts': history
        }
    })


@monitoring_bp.route('/alerts/<int:alert_index>/resolve', methods=['POST'])
def resolve_alert(alert_index):
    """
    解决告警
    
    标记指定告警为已解决
    
    Args:
        alert_index: 告警索引
    
    Returns:
        JSON 响应，表示操作结果
    """
    from app.utils.alerting import get_alert_manager
    
    alert_mgr = get_alert_manager()
    alert_mgr.resolve_alert(alert_index)
    
    return jsonify({
        'success': True,
        'message': f'告警 {alert_index} 已标记为已解决'
    })


@monitoring_bp.route('/alerts/clear-resolved', methods=['POST'])
def clear_resolved_alerts():
    """
    清除已解决的告警
    
    从活跃告警列表中移除已解决的告警
    
    Returns:
        JSON 响应，表示操作结果
    """
    from app.utils.alerting import get_alert_manager
    
    alert_mgr = get_alert_manager()
    alert_mgr.clear_resolved_alerts()
    
    return jsonify({
        'success': True,
        'message': '已清除所有已解决的告警'
    })


@monitoring_bp.route('/dashboard', methods=['GET'])
def monitoring_dashboard():
    """
    监控仪表板数据端点
    
    返回监控仪表板所需的所有数据
    
    Returns:
        JSON 响应，包含仪表板数据
    """
    from app.utils.health_check import get_health_checker
    from app.utils.performance_monitor import get_performance_monitor
    from app.utils.alerting import get_alert_manager
    
    health_checker = get_health_checker()
    health_status = health_checker.check_all()
    
    perf_monitor = get_performance_monitor()
    perf_summary = perf_monitor.get_performance_summary()
    
    alert_mgr = get_alert_manager()
    active_alerts = alert_mgr.get_active_alerts()
    
    dashboard_data = {
        'timestamp': health_status['timestamp'],
        'health': {
            'status': health_status['status'],
            'summary': health_status['summary'],
        },
        'performance': {
            'score': perf_summary['score'],
            'qps': perf_summary['qps'],
            'response_time': perf_summary['response_time'],
            'error_rate': perf_summary['error_rate'],
        },
        'resources': perf_summary['resource_usage'],
        'alerts': {
            'total': len(active_alerts),
            'alerts': active_alerts[:10],
        },
        'statistics': {
            'total_requests': perf_summary['total_requests'],
            'total_errors': perf_summary['total_errors'],
        }
    }
    
    return jsonify({
        'success': True,
        'data': dashboard_data
    })


@monitoring_bp.route('/reset', methods=['POST'])
def reset_monitoring_stats():
    """
    重置监控统计数据
    
    清空所有统计数据（性能监控、告警历史等）
    
    Returns:
        JSON 响应，表示操作结果
    """
    from app.utils.performance_monitor import get_performance_monitor
    from app.utils.alerting import get_alert_manager
    
    perf_monitor = get_performance_monitor()
    perf_monitor.reset_stats()
    
    alert_mgr = get_alert_manager()
    alert_mgr.clear_resolved_alerts()
    
    return jsonify({
        'success': True,
        'message': '监控统计数据已重置'
    })
