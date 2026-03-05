"""
异步审计日志队列
提供高性能的审计日志记录功能，避免阻塞主流程
"""
import threading
import queue
import atexit
from datetime import datetime
from typing import Optional, Dict, Any, List
from flask import has_app_context, g, current_app


class AsyncAuditQueue:
    """
    异步审计日志队列
    
    使用后台线程批量写入审计日志，避免阻塞主请求
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        self._queue = queue.Queue()
        self._worker_thread = None
        self._running = False
        self._batch_size = 10
        self._flush_interval = 1.0
        self._app = None
        
        self._start_worker()
        atexit.register(self._shutdown)
    
    def set_app(self, app):
        """设置 Flask 应用实例"""
        self._app = app
    
    def _start_worker(self):
        """启动后台工作线程"""
        if self._worker_thread is None or not self._worker_thread.is_alive():
            self._running = True
            self._worker_thread = threading.Thread(target=self._worker, daemon=True)
            self._worker_thread.start()
    
    def _worker(self):
        """后台工作线程，批量处理日志"""
        import time
        
        batch = []
        last_flush = time.time()
        
        while self._running:
            try:
                try:
                    item = self._queue.get(timeout=0.1)
                    batch.append(item)
                except queue.Empty:
                    pass
                
                current_time = time.time()
                
                if len(batch) >= self._batch_size or (batch and current_time - last_flush >= self._flush_interval):
                    self._flush_batch(batch)
                    batch = []
                    last_flush = current_time
                    
            except Exception as e:
                import logging
                logging.error(f"审计日志工作线程错误: {str(e)}")
        
        if batch:
            self._flush_batch(batch)
    
    def _flush_batch(self, batch: List[Dict]):
        """批量写入日志"""
        if not batch:
            return
        
        try:
            from app.models.base import db
            from app.models.sensitive_data_audit import SensitiveDataAuditLog
            from app.models.encryption_audit import EncryptionAuditLog
            
            app = self._app
            if app is None:
                from flask import current_app
                try:
                    app = current_app._get_current_object()
                except Exception:
                    from app import create_app
                    app = create_app()
            
            with app.app_context():
                for item in batch:
                    try:
                        if item['log_type'] == 'sensitive':
                            audit_log = SensitiveDataAuditLog(**item['data'])
                        elif item['log_type'] == 'encryption':
                            audit_log = EncryptionAuditLog(**item['data'])
                        else:
                            continue
                        
                        db.session.add(audit_log)
                    except Exception as e:
                        import logging
                        logging.error(f"创建审计日志记录失败: {str(e)}")
                
                db.session.commit()
                
        except Exception as e:
            import logging
            logging.error(f"批量写入审计日志失败: {str(e)}")
    
    def add_sensitive_log(self, data: Dict):
        """添加敏感数据审计日志到队列"""
        self._queue.put({
            'log_type': 'sensitive',
            'data': data
        })
    
    def add_encryption_log(self, data: Dict):
        """添加加密审计日志到队列"""
        self._queue.put({
            'log_type': 'encryption',
            'data': data
        })
    
    def _shutdown(self):
        """关闭工作线程"""
        self._running = False
        if self._worker_thread and self._worker_thread.is_alive():
            self._worker_thread.join(timeout=5)


_async_queue = AsyncAuditQueue()


def init_async_audit(app):
    """
    初始化异步审计队列
    
    Args:
        app: Flask 应用实例
    """
    _async_queue.set_app(app)


def get_async_queue() -> AsyncAuditQueue:
    """获取异步审计队列实例"""
    return _async_queue


def queue_sensitive_audit(
    operation_type: str,
    model_name: str,
    record_id: int,
    field_name: str,
    field_display_name: str = None,
    old_value: str = None,
    new_value: str = None,
    success: bool = True,
    error_message: str = None,
    user_id: int = None,
    username: str = None,
    user_role: str = None,
    ip_address: str = None,
    remark: str = None
):
    """
    异步记录敏感数据审计日志
    
    Args:
        operation_type: 操作类型（view/modify/delete/export）
        model_name: 模型名称
        record_id: 记录 ID
        field_name: 字段名称
        field_display_name: 字段显示名称
        old_value: 变更前的值（脱敏）
        new_value: 变更后的值（脱敏）
        success: 操作是否成功
        error_message: 错误信息
        user_id: 用户 ID
        username: 用户名
        user_role: 用户角色
        ip_address: IP 地址
        remark: 备注信息
    """
    try:
        from flask import request
        
        if user_id is None or username is None:
            if hasattr(g, 'current_user') and g.current_user:
                user_id = user_id or g.current_user.id
                username = username or g.current_user.username
                user_role = user_role or getattr(g.current_user, 'role', None)
            elif hasattr(g, 'user_id'):
                user_id = user_id or g.user_id
                username = username or getattr(g, 'username', 'unknown')
                user_role = user_role or getattr(g, 'user_role', None)
        
        if ip_address is None:
            try:
                if request:
                    forwarded_for = request.headers.get('X-Forwarded-For')
                    if forwarded_for:
                        ip_address = forwarded_for.split(',')[0].strip()
                    else:
                        ip_address = request.remote_addr
            except Exception:
                pass
        
        def mask_value(value: str, show_last: int = 4) -> str:
            if not value:
                return None
            if len(value) <= show_last:
                return '*' * len(value)
            return '*' * (len(value) - show_last) + value[-show_last:]
        
        masked_old_value = mask_value(old_value) if old_value else None
        masked_new_value = mask_value(new_value) if new_value else None
        
        user_agent = None
        request_path = None
        request_method = None
        
        try:
            if request:
                user_agent = request.headers.get('User-Agent', '')[:500]
                request_path = request.path
                request_method = request.method
        except Exception:
            pass
        
        data = {
            'operation_type': operation_type,
            'model_name': model_name,
            'record_id': record_id,
            'field_name': field_name,
            'field_display_name': field_display_name or field_name,
            'user_id': user_id,
            'username': username or 'unknown',
            'user_role': user_role,
            'ip_address': ip_address,
            'user_agent': user_agent,
            'request_path': request_path,
            'request_method': request_method,
            'success': success,
            'error_message': error_message,
            'old_value': masked_old_value,
            'new_value': masked_new_value,
            'operation_time': datetime.now(),
            'remark': remark
        }
        
        _async_queue.add_sensitive_log(data)
        
    except Exception as e:
        import logging
        logging.error(f"队列敏感数据审计日志失败: {str(e)}")


def queue_encryption_audit(
    operation: str,
    field_name: str,
    model_name: str,
    record_id: int,
    key_id: str,
    user_id: Optional[int] = None,
    ip_address: Optional[str] = None,
    success: bool = True,
    error_message: Optional[str] = None
):
    """
    异步记录加密操作审计日志
    
    Args:
        operation: 操作类型（encrypt/decrypt）
        field_name: 字段名称
        model_name: 模型名称
        record_id: 记录 ID
        key_id: 使用的密钥 ID
        user_id: 操作用户 ID
        ip_address: 操作 IP 地址
        success: 操作是否成功
        error_message: 错误信息（如果失败）
    """
    try:
        from flask import request
        
        if user_id is None:
            if hasattr(g, 'current_user') and g.current_user:
                user_id = g.current_user.id
            elif hasattr(g, 'user_id'):
                user_id = g.user_id
        
        if ip_address is None:
            try:
                if request:
                    forwarded_for = request.headers.get('X-Forwarded-For')
                    if forwarded_for:
                        ip_address = forwarded_for.split(',')[0].strip()
                    else:
                        ip_address = request.remote_addr
            except Exception:
                pass
        
        data = {
            'operation': operation,
            'field_name': field_name,
            'model_name': model_name,
            'record_id': record_id,
            'key_id': key_id,
            'user_id': user_id,
            'ip_address': ip_address,
            'success': success,
            'error_message': error_message,
            'timestamp': datetime.now()
        }
        
        _async_queue.add_encryption_log(data)
        
    except Exception as e:
        import logging
        logging.error(f"队列加密审计日志失败: {str(e)}")
