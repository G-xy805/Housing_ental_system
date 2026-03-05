"""
慢查询监控模块

功能：
1. 监控 SQL 查询执行时间
2. 记录执行时间超过阈值的慢查询
3. 提供慢查询统计和分析功能
4. 支持慢查询日志轮转

使用方法：
    在 Flask 应用初始化时调用 setup_slow_query_monitor(app, db) 即可启用慢查询监控
"""
import os
import time
import logging
import traceback
import threading
from datetime import datetime
from logging.handlers import RotatingFileHandler
from collections import defaultdict
from typing import Dict, List, Any, Optional
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event


class SlowQueryMonitor:
    """
    慢查询监控器
    
    负责监控数据库查询性能，记录慢查询，并提供统计分析功能
    """
    
    def __init__(self, app: Optional[Flask] = None, db: Optional[SQLAlchemy] = None):
        """
        初始化慢查询监控器
        
        Args:
            app: Flask 应用实例
            db: SQLAlchemy 数据库实例
        """
        self.app = app
        self.db = db
        self.logger = None
        self.threshold = 1.0  # 默认阈值 1 秒
        self.enabled = True
        
        # 使用线程本地存储来跟踪查询开始时间
        self._query_context = threading.local()
        
        # 慢查询统计信息
        self.stats = {
            'total_queries': 0,
            'slow_queries': 0,
            'total_slow_query_time': 0.0,
            'slow_queries_by_table': defaultdict(int),
            'slow_queries_by_type': defaultdict(int),
            'recent_slow_queries': [],  # 最近 100 条慢查询
        }
        
        # 锁用于线程安全的统计更新
        self._lock = threading.Lock()
        
        if app and db:
            self.init_app(app, db)
    
    def init_app(self, app: Flask, db: SQLAlchemy):
        """
        初始化慢查询监控器
        
        Args:
            app: Flask 应用实例
            db: SQLAlchemy 数据库实例
        """
        self.app = app
        self.db = db
        
        # 从应用配置中读取参数
        self.threshold = app.config.get('SLOW_QUERY_THRESHOLD', 1.0)
        self.enabled = app.config.get('SLOW_QUERY_MONITOR_ENABLED', True)
        
        # 设置日志记录器
        self._setup_logger()
        
        # 注册 SQLAlchemy 事件监听器
        if self.enabled:
            # 标记监听器未注册
            self._listeners_registered = False
            
            # 尝试立即注册（如果应用上下文可用）
            try:
                with app.app_context():
                    self._register_event_listeners()
                    self._listeners_registered = True
                    app.logger.info(f'慢查询监控已启用，阈值: {self.threshold} 秒')
            except Exception:
                # 如果应用上下文不可用，在第一次请求时注册
                @app.before_request
                def register_listeners_if_needed():
                    """在第一次请求时注册事件监听器"""
                    if not self._listeners_registered:
                        self._register_event_listeners()
                        self._listeners_registered = True
                
                app.logger.info(f'慢查询监控已启用，阈值: {self.threshold} 秒（将在首次请求时激活）')
        else:
            app.logger.info('慢查询监控已禁用')
    
    def _setup_logger(self):
        """配置慢查询日志记录器"""
        # 创建日志目录
        log_file = self.app.config.get('SLOW_QUERY_LOG_FILE', 'logs/slow_queries.log')
        log_dir = os.path.dirname(log_file)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
        
        # 创建专用的慢查询日志记录器
        self.logger = logging.getLogger('slow_query_monitor')
        self.logger.setLevel(logging.WARNING)
        
        # 清除已有的处理器，避免重复
        self.logger.handlers.clear()
        
        # 创建轮转文件处理器
        max_size = self.app.config.get('SLOW_QUERY_LOG_MAX_SIZE', 10 * 1024 * 1024)
        backup_count = self.app.config.get('SLOW_QUERY_LOG_BACKUP_COUNT', 10)
        
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_size,
            backupCount=backup_count,
            encoding='utf-8'
        )
        
        # 设置日志格式
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        
        # 如果应用在调试模式，也输出到控制台
        if self.app.debug:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.WARNING)
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
    
    def _register_event_listeners(self):
        """注册 SQLAlchemy 事件监听器"""
        # 监听 before_cursor_execute 事件，记录查询开始时间
        @event.listens_for(self.db.engine, 'before_cursor_execute')
        def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            """查询执行前触发，记录开始时间"""
            if not self.enabled:
                return
            
            # 记录查询开始时间
            self._query_context.start_time = time.time()
            self._query_context.statement = statement
            self._query_context.parameters = parameters
        
        # 监听 after_cursor_execute 事件，计算查询执行时间
        @event.listens_for(self.db.engine, 'after_cursor_execute')
        def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            """查询执行后触发，计算执行时间并记录慢查询"""
            if not self.enabled:
                return
            
            # 计算查询执行时间
            end_time = time.time()
            start_time = getattr(self._query_context, 'start_time', None)
            
            if start_time is None:
                return
            
            execution_time = end_time - start_time
            
            # 更新总查询计数
            with self._lock:
                self.stats['total_queries'] += 1
            
            # 检查是否为慢查询
            if execution_time >= self.threshold:
                self._record_slow_query(
                    statement=statement,
                    parameters=parameters,
                    execution_time=execution_time,
                    context=context
                )
    
    def _record_slow_query(self, statement: str, parameters: Any, 
                          execution_time: float, context: Any):
        """
        记录慢查询
        
        Args:
            statement: SQL 语句
            parameters: 查询参数
            execution_time: 执行时间（秒）
            context: SQLAlchemy 执行上下文
        """
        # 获取调用堆栈
        stack_trace = self._get_relevant_stack_trace()
        
        # 提取表名和查询类型
        table_name = self._extract_table_name(statement)
        query_type = self._extract_query_type(statement)
        
        # 构建慢查询记录
        slow_query_record = {
            'timestamp': datetime.now().isoformat(),
            'execution_time': round(execution_time, 4),
            'statement': statement,
            'parameters': self._format_parameters(parameters),
            'stack_trace': stack_trace,
            'table': table_name,
            'query_type': query_type,
        }
        
        # 记录到日志文件
        self._log_slow_query(slow_query_record)
        
        # 更新统计信息
        with self._lock:
            self.stats['slow_queries'] += 1
            self.stats['total_slow_query_time'] += execution_time
            
            if table_name:
                self.stats['slow_queries_by_table'][table_name] += 1
            
            if query_type:
                self.stats['slow_queries_by_type'][query_type] += 1
            
            # 保留最近 100 条慢查询
            self.stats['recent_slow_queries'].append(slow_query_record)
            if len(self.stats['recent_slow_queries']) > 100:
                self.stats['recent_slow_queries'].pop(0)
    
    def _log_slow_query(self, record: Dict[str, Any]):
        """
        将慢查询记录写入日志文件
        
        Args:
            record: 慢查询记录字典
        """
        log_message = (
            f"执行时间: {record['execution_time']:.4f}秒 | "
            f"查询类型: {record['query_type']} | "
            f"表: {record['table']} | "
            f"SQL: {record['statement'][:200]}{'...' if len(record['statement']) > 200 else ''}"
        )
        
        self.logger.warning(log_message)
        
        # 记录详细信息到调试日志
        self.logger.debug(
            f"\n{'='*80}\n"
            f"慢查询详情:\n"
            f"时间: {record['timestamp']}\n"
            f"执行时间: {record['execution_time']:.4f}秒\n"
            f"查询类型: {record['query_type']}\n"
            f"表: {record['table']}\n"
            f"SQL语句:\n{record['statement']}\n"
            f"参数:\n{record['parameters']}\n"
            f"调用堆栈:\n{record['stack_trace']}\n"
            f"{'='*80}\n"
        )
    
    def _get_relevant_stack_trace(self) -> str:
        """
        获取相关的调用堆栈信息
        
        Returns:
            格式化的堆栈跟踪字符串
        """
        stack = traceback.extract_stack()
        
        # 过滤掉框架内部的调用，只保留应用代码
        relevant_frames = []
        for frame in stack:
            # 排除框架和库的调用
            if 'site-packages' in frame.filename or 'lib/python' in frame.filename:
                continue
            # 排除慢查询监控模块自身的调用
            if 'slow_query_monitor' in frame.filename:
                continue
            relevant_frames.append(frame)
        
        # 只保留最近的 5 帧
        relevant_frames = relevant_frames[-5:]
        
        # 格式化堆栈跟踪
        formatted_frames = []
        for frame in relevant_frames:
            formatted_frames.append(
                f"  File \"{frame.filename}\", line {frame.lineno}, in {frame.name}\n"
                f"    {frame.line}"
            )
        
        return '\n'.join(formatted_frames) if formatted_frames else '无调用堆栈信息'
    
    def _extract_table_name(self, statement: str) -> str:
        """
        从 SQL 语句中提取表名
        
        Args:
            statement: SQL 语句
        
        Returns:
            表名或 'unknown'
        """
        try:
            # 简单的表名提取逻辑
            statement_upper = statement.upper()
            
            # 常见的 SQL 关键字后的表名
            keywords = ['FROM', 'INTO', 'UPDATE', 'JOIN']
            
            for keyword in keywords:
                if keyword in statement_upper:
                    # 找到关键字位置
                    pos = statement_upper.find(keyword)
                    # 提取关键字后的内容
                    after_keyword = statement[pos + len(keyword):].strip()
                    # 取第一个单词作为表名
                    table_name = after_keyword.split()[0] if after_keyword.split() else 'unknown'
                    # 移除可能的引号和括号
                    table_name = table_name.strip('`"[]()')
                    return table_name
            
            return 'unknown'
        except Exception:
            return 'unknown'
    
    def _extract_query_type(self, statement: str) -> str:
        """
        从 SQL 语句中提取查询类型
        
        Args:
            statement: SQL 语句
        
        Returns:
            查询类型（SELECT, INSERT, UPDATE, DELETE 等）
        """
        try:
            # 去除前导空格并转大写
            statement_stripped = statement.strip().upper()
            
            # 提取第一个关键字
            first_word = statement_stripped.split()[0] if statement_stripped.split() else 'UNKNOWN'
            
            # 标准化查询类型
            query_types = ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'ALTER', 'DROP']
            
            for query_type in query_types:
                if first_word.startswith(query_type):
                    return query_type
            
            return first_word if first_word else 'UNKNOWN'
        except Exception:
            return 'UNKNOWN'
    
    def _format_parameters(self, parameters: Any) -> str:
        """
        格式化查询参数
        
        Args:
            parameters: 查询参数
        
        Returns:
            格式化后的参数字符串
        """
        try:
            if parameters is None:
                return '无参数'
            
            # 如果是字典或列表，转换为字符串
            if isinstance(parameters, (dict, list, tuple)):
                # 限制长度，避免日志过大
                param_str = str(parameters)
                if len(param_str) > 500:
                    param_str = param_str[:500] + '...'
                return param_str
            
            return str(parameters)
        except Exception:
            return '参数格式化失败'
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取慢查询统计信息
        
        Returns:
            统计信息字典
        """
        with self._lock:
            stats_copy = {
                'total_queries': self.stats['total_queries'],
                'slow_queries': self.stats['slow_queries'],
                'total_slow_query_time': round(self.stats['total_slow_query_time'], 4),
                'average_slow_query_time': (
                    round(self.stats['total_slow_query_time'] / self.stats['slow_queries'], 4)
                    if self.stats['slow_queries'] > 0 else 0
                ),
                'slow_query_rate': (
                    round(self.stats['slow_queries'] / self.stats['total_queries'] * 100, 2)
                    if self.stats['total_queries'] > 0 else 0
                ),
                'slow_queries_by_table': dict(self.stats['slow_queries_by_table']),
                'slow_queries_by_type': dict(self.stats['slow_queries_by_type']),
                'recent_slow_queries': self.stats['recent_slow_queries'][-10:],  # 最近 10 条
                'threshold': self.threshold,
                'enabled': self.enabled,
            }
        
        return stats_copy
    
    def get_recent_slow_queries(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        获取最近的慢查询记录
        
        Args:
            limit: 返回的记录数量
        
        Returns:
            慢查询记录列表
        """
        with self._lock:
            return self.stats['recent_slow_queries'][-limit:]
    
    def get_slow_queries_by_table(self) -> Dict[str, int]:
        """
        获取按表分组的慢查询统计
        
        Returns:
            表名到慢查询数量的映射
        """
        with self._lock:
            return dict(self.stats['slow_queries_by_table'])
    
    def get_slow_queries_by_type(self) -> Dict[str, int]:
        """
        获取按查询类型分组的慢查询统计
        
        Returns:
            查询类型到慢查询数量的映射
        """
        with self._lock:
            return dict(self.stats['slow_queries_by_type'])
    
    def reset_stats(self):
        """重置统计信息"""
        with self._lock:
            self.stats = {
                'total_queries': 0,
                'slow_queries': 0,
                'total_slow_query_time': 0.0,
                'slow_queries_by_table': defaultdict(int),
                'slow_queries_by_type': defaultdict(int),
                'recent_slow_queries': [],
            }
    
    def set_threshold(self, threshold: float):
        """
        设置慢查询阈值
        
        Args:
            threshold: 新的阈值（秒）
        """
        self.threshold = threshold
        if self.app:
            self.app.config['SLOW_QUERY_THRESHOLD'] = threshold
            self.app.logger.info(f'慢查询阈值已更新为: {threshold} 秒')
    
    def enable(self):
        """启用慢查询监控"""
        self.enabled = True
        if self.app:
            self.app.config['SLOW_QUERY_MONITOR_ENABLED'] = True
            self.app.logger.info('慢查询监控已启用')
    
    def disable(self):
        """禁用慢查询监控"""
        self.enabled = False
        if self.app:
            self.app.config['SLOW_QUERY_MONITOR_ENABLED'] = False
            self.app.logger.info('慢查询监控已禁用')


# 全局慢查询监控器实例
slow_query_monitor = SlowQueryMonitor()


def setup_slow_query_monitor(app: Flask, db: SQLAlchemy) -> SlowQueryMonitor:
    """
    设置慢查询监控器
    
    Args:
        app: Flask 应用实例
        db: SQLAlchemy 数据库实例
    
    Returns:
        慢查询监控器实例
    """
    global slow_query_monitor
    slow_query_monitor.init_app(app, db)
    return slow_query_monitor


def get_slow_query_monitor() -> SlowQueryMonitor:
    """
    获取全局慢查询监控器实例
    
    Returns:
        慢查询监控器实例
    """
    return slow_query_monitor
