"""
文件锁工具模块

提供跨平台的文件锁实现，支持 Windows 和 Unix 系统。
用于保护关键操作，防止并发冲突。

使用方式：
    from app.utils.file_lock import file_lock, FileLockError

    # 方式1：上下文管理器
    with file_lock('contract_terminate'):
        # 执行关键操作
        pass

    # 方式2：指定锁文件路径
    with file_lock('contract_terminate', lock_dir='/tmp/locks'):
        # 执行关键操作
        pass

    # 方式3：非阻塞模式
    try:
        with file_lock('contract_terminate', timeout=0):
            # 执行关键操作
            pass
    except FileLockError:
        # 锁获取失败
        pass
"""
import os
import sys
import time
import logging
import tempfile
from typing import Optional
from contextlib import contextmanager
from pathlib import Path


class FileLockError(Exception):
    """文件锁错误异常"""
    pass


class FileLockTimeoutError(FileLockError):
    """文件锁超时异常"""
    pass


class FileLock:
    """
    跨平台文件锁实现
    
    支持 Windows 和 Unix 系统：
    - Windows: 使用 msvcrt.locking
    - Unix: 使用 fcntl.flock
    """
    
    # 锁文件目录
    DEFAULT_LOCK_DIR = None
    
    def __init__(
        self,
        lock_name: str,
        lock_dir: Optional[str] = None,
        timeout: float = 30.0,
        poll_interval: float = 0.1
    ):
        """
        初始化文件锁
        
        Args:
            lock_name: 锁名称（用于生成锁文件名）
            lock_dir: 锁文件目录，默认为系统临时目录
            timeout: 获取锁的超时时间（秒），0 表示非阻塞
            poll_interval: 轮询间隔（秒）
        """
        self.lock_name = lock_name
        self.lock_dir = lock_dir or self._get_default_lock_dir()
        self.timeout = timeout
        self.poll_interval = poll_interval
        
        # 确保锁文件名安全
        safe_name = "".join(c if c.isalnum() or c in ('_', '-') else '_' for c in lock_name)
        self.lock_file_path = os.path.join(self.lock_dir, f"{safe_name}.lock")
        
        self.lock_file = None
        self._locked = False
        self.logger = logging.getLogger('file_lock')
    
    @classmethod
    def _get_default_lock_dir(cls) -> str:
        """
        获取默认锁文件目录
        
        Returns:
            str: 锁文件目录路径
        """
        if cls.DEFAULT_LOCK_DIR:
            return cls.DEFAULT_LOCK_DIR
        
        # 使用系统临时目录
        lock_dir = os.path.join(tempfile.gettempdir(), 'housing_rental_locks')
        
        # 确保目录存在
        try:
            os.makedirs(lock_dir, exist_ok=True)
        except OSError as e:
            # 如果无法创建目录，回退到临时目录
            cls.logger.warning(f"无法创建锁目录 {lock_dir}: {e}，使用临时目录")
            lock_dir = tempfile.gettempdir()
        
        cls.DEFAULT_LOCK_DIR = lock_dir
        return lock_dir
    
    def acquire(self, blocking: bool = True) -> bool:
        """
        获取文件锁
        
        Args:
            blocking: 是否阻塞等待
            
        Returns:
            bool: 是否成功获取锁
            
        Raises:
            FileLockTimeoutError: 超时时抛出
        """
        if self._locked:
            return True
        
        start_time = time.time()
        
        while True:
            try:
                # 打开或创建锁文件
                self.lock_file = open(self.lock_file_path, 'w')
                
                # 根据平台使用不同的锁定方式
                if sys.platform == 'win32' or sys.platform == 'cygwin':
                    self._acquire_windows()
                else:
                    self._acquire_unix()
                
                self._locked = True
                self.logger.debug(f"成功获取锁: {self.lock_name}")
                return True
                
            except (IOError, OSError) as e:
                # 锁定失败
                if self.lock_file:
                    try:
                        self.lock_file.close()
                    except:
                        pass
                    self.lock_file = None
                
                # 非阻塞模式，直接返回失败
                if not blocking or self.timeout == 0:
                    self.logger.debug(f"获取锁失败（非阻塞模式）: {self.lock_name}")
                    return False
                
                # 检查是否超时
                elapsed = time.time() - start_time
                if elapsed >= self.timeout:
                    self.logger.warning(f"获取锁超时: {self.lock_name}")
                    raise FileLockTimeoutError(
                        f"获取文件锁超时: {self.lock_name}（超时时间: {self.timeout}秒）"
                    )
                
                # 等待后重试
                time.sleep(self.poll_interval)
    
    def _acquire_windows(self):
        """
        Windows 平台获取锁
        
        使用 msvcrt.locking 实现
        """
        import msvcrt
        
        # 尝试非阻塞锁定
        try:
            # LK_NBLCK: 非阻塞排他锁
            msvcrt.locking(self.lock_file.fileno(), msvcrt.LK_NBLCK, 1)
        except IOError:
            # 锁定失败，抛出异常
            raise
    
    def _acquire_unix(self):
        """
        Unix 平台获取锁
        
        使用 fcntl.flock 实现
        """
        import fcntl
        
        # LOCK_EX: 排他锁
        # LOCK_NB: 非阻塞
        fcntl.flock(self.lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    
    def release(self):
        """
        释放文件锁
        """
        if not self._locked:
            return
        
        try:
            if self.lock_file:
                if sys.platform == 'win32' or sys.platform == 'cygwin':
                    self._release_windows()
                else:
                    self._release_unix()
                
                self.lock_file.close()
                
                # 尝试删除锁文件（可选）
                try:
                    os.unlink(self.lock_file_path)
                except:
                    pass
                
                self.logger.debug(f"成功释放锁: {self.lock_name}")
        
        except Exception as e:
            self.logger.error(f"释放锁失败: {self.lock_name}, 错误: {e}")
        
        finally:
            self.lock_file = None
            self._locked = False
    
    def _release_windows(self):
        """
        Windows 平台释放锁
        """
        import msvcrt
        
        # LK_UNLCK: 解锁
        msvcrt.locking(self.lock_file.fileno(), msvcrt.LK_UNLCK, 1)
    
    def _release_unix(self):
        """
        Unix 平台释放锁
        """
        import fcntl
        
        # LOCK_UN: 解锁
        fcntl.flock(self.lock_file.fileno(), fcntl.LOCK_UN)
    
    def __enter__(self):
        """进入上下文"""
        self.acquire(blocking=self.timeout != 0)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出上下文"""
        self.release()
        return False
    
    @property
    def is_locked(self) -> bool:
        """
        检查锁是否已获取
        
        Returns:
            bool: 是否已获取锁
        """
        return self._locked


@contextmanager
def file_lock(
    lock_name: str,
    lock_dir: Optional[str] = None,
    timeout: float = 30.0,
    poll_interval: float = 0.1
):
    """
    文件锁上下文管理器
    
    提供便捷的文件锁使用方式
    
    Args:
        lock_name: 锁名称
        lock_dir: 锁文件目录
        timeout: 超时时间（秒）
        poll_interval: 轮询间隔（秒）
        
    Yields:
        FileLock: 文件锁对象
        
    Example:
        with file_lock('contract_terminate'):
            # 执行关键操作
            pass
    """
    lock = FileLock(
        lock_name=lock_name,
        lock_dir=lock_dir,
        timeout=timeout,
        poll_interval=poll_interval
    )
    
    try:
        lock.acquire()
        yield lock
    finally:
        lock.release()


def with_file_lock(
    lock_name: str,
    lock_dir: Optional[str] = None,
    timeout: float = 30.0
):
    """
    文件锁装饰器
    
    用于保护函数执行，防止并发调用
    
    Args:
        lock_name: 锁名称
        lock_dir: 锁文件目录
        timeout: 超时时间（秒）
        
    Returns:
        装饰器函数
        
    Example:
        @with_file_lock('contract_terminate')
        def terminate_contract(contract_id):
            # 执行关键操作
            pass
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            with file_lock(lock_name, lock_dir, timeout):
                return func(*args, **kwargs)
        return wrapper
    return decorator


# ============================================================================
# 合同操作专用锁
# ============================================================================

class ContractLock:
    """
    合同操作专用锁
    
    为合同相关操作提供便捷的锁管理
    """
    
    # 锁类型
    LOCK_TERMINATE = 'contract_terminate'
    LOCK_RENEW = 'contract_renew'
    LOCK_ACTIVATE = 'contract_activate'
    LOCK_PAYMENT = 'contract_payment'
    
    @classmethod
    def get_lock_name(cls, lock_type: str, contract_id: int) -> str:
        """
        获取合同锁名称
        
        Args:
            lock_type: 锁类型
            contract_id: 合同 ID
            
        Returns:
            str: 锁名称
        """
        return f"{lock_type}_{contract_id}"
    
    @classmethod
    @contextmanager
    def terminate_lock(cls, contract_id: int, timeout: float = 30.0):
        """
        合同终止操作锁
        
        Args:
            contract_id: 合同 ID
            timeout: 超时时间
            
        Yields:
            FileLock: 文件锁对象
        """
        lock_name = cls.get_lock_name(cls.LOCK_TERMINATE, contract_id)
        with file_lock(lock_name, timeout=timeout) as lock:
            yield lock
    
    @classmethod
    @contextmanager
    def renew_lock(cls, contract_id: int, timeout: float = 30.0):
        """
        合同续签操作锁
        
        Args:
            contract_id: 合同 ID
            timeout: 超时时间
            
        Yields:
            FileLock: 文件锁对象
        """
        lock_name = cls.get_lock_name(cls.LOCK_RENEW, contract_id)
        with file_lock(lock_name, timeout=timeout) as lock:
            yield lock
    
    @classmethod
    @contextmanager
    def activate_lock(cls, contract_id: int, timeout: float = 30.0):
        """
        合同激活操作锁
        
        Args:
            contract_id: 合同 ID
            timeout: 超时时间
            
        Yields:
            FileLock: 文件锁对象
        """
        lock_name = cls.get_lock_name(cls.LOCK_ACTIVATE, contract_id)
        with file_lock(lock_name, timeout=timeout) as lock:
            yield lock
    
    @classmethod
    @contextmanager
    def payment_lock(cls, contract_id: int, timeout: float = 30.0):
        """
        合同支付操作锁
        
        Args:
            contract_id: 合同 ID
            timeout: 超时时间
            
        Yields:
            FileLock: 文件锁对象
        """
        lock_name = cls.get_lock_name(cls.LOCK_PAYMENT, contract_id)
        with file_lock(lock_name, timeout=timeout) as lock:
            yield lock
