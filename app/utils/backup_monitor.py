"""
备份监控和告警模块

功能：
1. 备份状态记录（成功/失败）
2. 备份统计信息
3. 备份告警（失败告警、空间不足告警）
4. 备份健康检查
5. 告警通知（邮件、日志）

监控指标：
- 备份成功率
- 备份耗时
- 备份文件大小
- 磁盘空间使用率
- 最后备份时间
"""
import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class BackupMonitor:
    """
    备份监控器
    
    监控备份任务的状态、性能和健康度
    """
    
    def __init__(self, app=None):
        """
        初始化备份监控器
        
        Args:
            app: Flask 应用实例
        """
        self.app = app
        self.backup_folder = None
        self.monitor_file = None
        self.stats = {
            'total_backups': 0,
            'successful_backups': 0,
            'failed_backups': 0,
            'total_size': 0,
            'last_backup_time': None,
            'last_backup_status': None,
            'average_backup_time': 0,
            'average_backup_size': 0
        }
        self.alerts = []
        self.max_alerts = 100
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """
        初始化 Flask 应用
        
        Args:
            app: Flask 应用实例
        """
        self.app = app
        self.backup_folder = app.config.get('BACKUP_FOLDER', 'backups')
        self.monitor_file = os.path.join(self.backup_folder, '.backup_monitor.json')
        
        # 确保备份目录存在
        os.makedirs(self.backup_folder, exist_ok=True)
        
        # 加载历史统计数据
        self._load_stats()
        
        logger.info("备份监控器初始化完成")
    
    def record_backup_start(self, backup_type: str = 'full') -> str:
        """
        记录备份开始
        
        Args:
            backup_type: 备份类型（full/incremental）
        
        Returns:
            str: 备份 ID
        """
        backup_id = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        record = {
            'backup_id': backup_id,
            'backup_type': backup_type,
            'start_time': datetime.now().isoformat(),
            'status': 'running',
            'error': None
        }
        
        # 保存记录
        self._save_backup_record(record)
        
        logger.info(f"备份开始 - ID: {backup_id}, 类型: {backup_type}")
        
        return backup_id
    
    def record_backup_success(
        self,
        backup_id: str,
        backup_info: Dict[str, Any]
    ):
        """
        记录备份成功
        
        Args:
            backup_id: 备份 ID
            backup_info: 备份信息
        """
        # 加载备份记录
        record = self._load_backup_record(backup_id)
        
        if not record:
            logger.warning(f"未找到备份记录: {backup_id}")
            return
        
        # 更新记录
        record['end_time'] = datetime.now().isoformat()
        record['status'] = 'success'
        record['backup_info'] = backup_info
        
        # 计算耗时
        start_time = datetime.fromisoformat(record['start_time'])
        end_time = datetime.fromisoformat(record['end_time'])
        duration = (end_time - start_time).total_seconds()
        record['duration'] = duration
        
        # 保存记录
        self._save_backup_record(record)
        
        # 更新统计信息
        self._update_stats_success(backup_info, duration)
        
        logger.info(f"备份成功 - ID: {backup_id}, 耗时: {duration:.2f}秒")
    
    def record_backup_failure(
        self,
        backup_id: str,
        error: str
    ):
        """
        记录备份失败
        
        Args:
            backup_id: 备份 ID
            error: 错误信息
        """
        # 加载备份记录
        record = self._load_backup_record(backup_id)
        
        if not record:
            logger.warning(f"未找到备份记录: {backup_id}")
            return
        
        # 更新记录
        record['end_time'] = datetime.now().isoformat()
        record['status'] = 'failed'
        record['error'] = error
        
        # 计算耗时
        start_time = datetime.fromisoformat(record['start_time'])
        end_time = datetime.fromisoformat(record['end_time'])
        duration = (end_time - start_time).total_seconds()
        record['duration'] = duration
        
        # 保存记录
        self._save_backup_record(record)
        
        # 更新统计信息
        self._update_stats_failure()
        
        # 添加告警
        self.add_alert(
            level='error',
            message=f"备份失败: {error}",
            backup_id=backup_id
        )
        
        logger.error(f"备份失败 - ID: {backup_id}, 错误: {error}")
    
    def add_alert(
        self,
        level: str,
        message: str,
        backup_id: str = None,
        details: Dict = None
    ):
        """
        添加告警
        
        Args:
            level: 告警级别（info/warning/error/critical）
            message: 告警消息
            backup_id: 相关备份 ID
            details: 详细信息
        """
        alert = {
            'id': datetime.now().strftime('%Y%m%d_%H%M%S_%f'),
            'level': level,
            'message': message,
            'backup_id': backup_id,
            'details': details or {},
            'timestamp': datetime.now().isoformat(),
            'acknowledged': False
        }
        
        self.alerts.append(alert)
        
        # 限制告警数量
        if len(self.alerts) > self.max_alerts:
            self.alerts = self.alerts[-self.max_alerts:]
        
        # 保存告警
        self._save_alerts()
        
        # 记录日志
        log_method = getattr(logger, level, logger.info)
        log_method(f"备份告警 [{level.upper()}]: {message}")
        
        # 发送通知（如果配置了）
        self._send_alert_notification(alert)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取备份统计信息
        
        Returns:
            Dict: 统计信息
        """
        # 更新实时统计
        self._update_realtime_stats()
        
        # 计算成功率
        success_rate = 0
        if self.stats['total_backups'] > 0:
            success_rate = (self.stats['successful_backups'] / self.stats['total_backups']) * 100
        
        return {
            **self.stats,
            'success_rate': round(success_rate, 2),
            'backup_folder_size': self._get_folder_size(),
            'backup_folder_size_mb': round(self._get_folder_size() / (1024 * 1024), 2),
            'disk_usage': self._get_disk_usage(),
            'oldest_backup': self._get_oldest_backup_time(),
            'newest_backup': self._get_newest_backup_time()
        }
    
    def get_health_status(self) -> Dict[str, Any]:
        """
        获取备份健康状态
        
        Returns:
            Dict: 健康状态
        """
        health = {
            'status': 'healthy',
            'issues': [],
            'recommendations': []
        }
        
        # 检查最后备份时间
        if self.stats['last_backup_time']:
            last_backup = datetime.fromisoformat(self.stats['last_backup_time'])
            hours_since_backup = (datetime.now() - last_backup).total_seconds() / 3600
            
            if hours_since_backup > 48:
                health['status'] = 'warning'
                health['issues'].append(f"距离上次备份已超过 {int(hours_since_backup)} 小时")
                health['recommendations'].append("建议立即执行手动备份")
        else:
            health['status'] = 'critical'
            health['issues'].append("从未执行过备份")
            health['recommendations'].append("必须立即执行首次备份")
        
        # 检查备份成功率
        if self.stats['total_backups'] > 0:
            success_rate = (self.stats['successful_backups'] / self.stats['total_backups']) * 100
            
            if success_rate < 80:
                health['status'] = 'critical'
                health['issues'].append(f"备份成功率过低: {success_rate:.2f}%")
                health['recommendations'].append("检查备份失败原因并修复")
            elif success_rate < 95:
                if health['status'] == 'healthy':
                    health['status'] = 'warning'
                health['issues'].append(f"备份成功率偏低: {success_rate:.2f}%")
        
        # 检查磁盘空间
        disk_usage = self._get_disk_usage()
        if disk_usage and disk_usage > 90:
            health['status'] = 'critical'
            health['issues'].append(f"磁盘空间不足: {disk_usage}%")
            health['recommendations'].append("清理过期备份或扩展存储空间")
        elif disk_usage and disk_usage > 80:
            if health['status'] == 'healthy':
                health['status'] = 'warning'
            health['issues'].append(f"磁盘空间紧张: {disk_usage}%")
        
        # 检查备份文件数量
        backup_count = self._get_backup_count()
        if backup_count == 0:
            if health['status'] != 'critical':
                health['status'] = 'warning'
            health['issues'].append("没有可用的备份文件")
        
        return health
    
    def get_alerts(
        self,
        level: str = None,
        acknowledged: bool = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        获取告警列表
        
        Args:
            level: 告警级别过滤
            acknowledged: 是否已确认
            limit: 返回数量限制
        
        Returns:
            List[Dict]: 告警列表
        """
        alerts = self.alerts.copy()
        
        # 过滤
        if level:
            alerts = [a for a in alerts if a['level'] == level]
        
        if acknowledged is not None:
            alerts = [a for a in alerts if a['acknowledged'] == acknowledged]
        
        # 排序（最新的在前）
        alerts.sort(key=lambda x: x['timestamp'], reverse=True)
        
        # 限制数量
        return alerts[:limit]
    
    def acknowledge_alert(self, alert_id: str) -> bool:
        """
        确认告警
        
        Args:
            alert_id: 告警 ID
        
        Returns:
            bool: 是否成功
        """
        for alert in self.alerts:
            if alert['id'] == alert_id:
                alert['acknowledged'] = True
                alert['acknowledged_at'] = datetime.now().isoformat()
                self._save_alerts()
                return True
        
        return False
    
    def get_backup_history(
        self,
        limit: int = 50,
        status: str = None
    ) -> List[Dict[str, Any]]:
        """
        获取备份历史记录
        
        Args:
            limit: 返回数量限制
            status: 状态过滤（success/failed/running）
        
        Returns:
            List[Dict]: 备份历史记录
        """
        history_file = os.path.join(self.backup_folder, '.backup_history.json')
        
        if not os.path.exists(history_file):
            return []
        
        try:
            with open(history_file, 'r', encoding='utf-8') as f:
                history = json.load(f)
            
            # 过滤
            if status:
                history = [h for h in history if h.get('status') == status]
            
            # 排序（最新的在前）
            history.sort(key=lambda x: x['start_time'], reverse=True)
            
            return history[:limit]
            
        except Exception as e:
            logger.error(f"读取备份历史失败: {str(e)}")
            return []
    
    # ==================== 私有方法 ====================
    
    def _load_stats(self):
        """加载统计数据"""
        if not self.monitor_file or not os.path.exists(self.monitor_file):
            return
        
        try:
            with open(self.monitor_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.stats = data.get('stats', self.stats)
                self.alerts = data.get('alerts', [])
        except Exception as e:
            logger.warning(f"加载备份监控数据失败: {str(e)}")
    
    def _save_stats(self):
        """保存统计数据"""
        if not self.monitor_file:
            return
        
        try:
            data = {
                'stats': self.stats,
                'alerts': self.alerts,
                'updated_at': datetime.now().isoformat()
            }
            
            with open(self.monitor_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"保存备份监控数据失败: {str(e)}")
    
    def _save_backup_record(self, record: Dict):
        """保存备份记录"""
        history_file = os.path.join(self.backup_folder, '.backup_history.json')
        
        try:
            # 加载现有历史
            history = []
            if os.path.exists(history_file):
                with open(history_file, 'r', encoding='utf-8') as f:
                    history = json.load(f)
            
            # 更新或添加记录
            updated = False
            for i, h in enumerate(history):
                if h['backup_id'] == record['backup_id']:
                    history[i] = record
                    updated = True
                    break
            
            if not updated:
                history.append(record)
            
            # 限制历史记录数量
            if len(history) > 1000:
                history = history[-1000:]
            
            # 保存
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(history, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"保存备份记录失败: {str(e)}")
    
    def _load_backup_record(self, backup_id: str) -> Optional[Dict]:
        """加载备份记录"""
        history_file = os.path.join(self.backup_folder, '.backup_history.json')
        
        if not os.path.exists(history_file):
            return None
        
        try:
            with open(history_file, 'r', encoding='utf-8') as f:
                history = json.load(f)
            
            for record in history:
                if record['backup_id'] == backup_id:
                    return record
            
            return None
            
        except Exception as e:
            logger.error(f"加载备份记录失败: {str(e)}")
            return None
    
    def _save_alerts(self):
        """保存告警"""
        self._save_stats()
    
    def _update_stats_success(self, backup_info: Dict, duration: float):
        """更新成功统计"""
        self.stats['total_backups'] += 1
        self.stats['successful_backups'] += 1
        self.stats['last_backup_time'] = datetime.now().isoformat()
        self.stats['last_backup_status'] = 'success'
        
        # 更新平均备份时间
        if self.stats['average_backup_time'] == 0:
            self.stats['average_backup_time'] = duration
        else:
            self.stats['average_backup_time'] = (
                (self.stats['average_backup_time'] * (self.stats['successful_backups'] - 1) + duration)
                / self.stats['successful_backups']
            )
        
        # 更新总大小和平均大小
        if 'file_size' in backup_info:
            self.stats['total_size'] += backup_info['file_size']
            
            if self.stats['average_backup_size'] == 0:
                self.stats['average_backup_size'] = backup_info['file_size']
            else:
                self.stats['average_backup_size'] = (
                    (self.stats['average_backup_size'] * (self.stats['successful_backups'] - 1) + backup_info['file_size'])
                    / self.stats['successful_backups']
                )
        
        self._save_stats()
    
    def _update_stats_failure(self):
        """更新失败统计"""
        self.stats['total_backups'] += 1
        self.stats['failed_backups'] += 1
        self.stats['last_backup_time'] = datetime.now().isoformat()
        self.stats['last_backup_status'] = 'failed'
        
        self._save_stats()
    
    def _update_realtime_stats(self):
        """更新实时统计"""
        # 计算备份文件夹大小
        self.stats['backup_folder_size'] = self._get_folder_size()
    
    def _get_folder_size(self) -> int:
        """获取备份文件夹大小"""
        if not self.backup_folder or not os.path.exists(self.backup_folder):
            return 0
        
        total_size = 0
        try:
            for dirpath, dirnames, filenames in os.walk(self.backup_folder):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    if not os.path.islink(filepath):
                        total_size += os.path.getsize(filepath)
        except Exception as e:
            logger.error(f"计算文件夹大小失败: {str(e)}")
        
        return total_size
    
    def _get_disk_usage(self) -> Optional[float]:
        """获取磁盘使用率"""
        if not self.backup_folder or not os.path.exists(self.backup_folder):
            return None
        
        try:
            import shutil
            total, used, free = shutil.disk_usage(self.backup_folder)
            return (used / total) * 100
        except Exception as e:
            logger.error(f"获取磁盘使用率失败: {str(e)}")
            return None
    
    def _get_backup_count(self) -> int:
        """获取备份文件数量"""
        if not self.backup_folder or not os.path.exists(self.backup_folder):
            return 0
        
        count = 0
        try:
            for filename in os.listdir(self.backup_folder):
                if filename.startswith('backup_') and (
                    filename.endswith('.db') or 
                    filename.endswith('.zip') or 
                    filename.endswith('.enc')
                ):
                    count += 1
        except Exception as e:
            logger.error(f"统计备份文件数量失败: {str(e)}")
        
        return count
    
    def _get_oldest_backup_time(self) -> Optional[str]:
        """获取最早备份时间"""
        if not self.backup_folder or not os.path.exists(self.backup_folder):
            return None
        
        oldest_time = None
        try:
            for filename in os.listdir(self.backup_folder):
                if filename.startswith('backup_') and (
                    filename.endswith('.db') or 
                    filename.endswith('.zip') or 
                    filename.endswith('.enc')
                ):
                    filepath = os.path.join(self.backup_folder, filename)
                    mtime = os.path.getmtime(filepath)
                    
                    if oldest_time is None or mtime < oldest_time:
                        oldest_time = mtime
            
            if oldest_time:
                return datetime.fromtimestamp(oldest_time).isoformat()
        except Exception as e:
            logger.error(f"获取最早备份时间失败: {str(e)}")
        
        return None
    
    def _get_newest_backup_time(self) -> Optional[str]:
        """获取最新备份时间"""
        if not self.backup_folder or not os.path.exists(self.backup_folder):
            return None
        
        newest_time = None
        try:
            for filename in os.listdir(self.backup_folder):
                if filename.startswith('backup_') and (
                    filename.endswith('.db') or 
                    filename.endswith('.zip') or 
                    filename.endswith('.enc')
                ):
                    filepath = os.path.join(self.backup_folder, filename)
                    mtime = os.path.getmtime(filepath)
                    
                    if newest_time is None or mtime > newest_time:
                        newest_time = mtime
            
            if newest_time:
                return datetime.fromtimestamp(newest_time).isoformat()
        except Exception as e:
            logger.error(f"获取最新备份时间失败: {str(e)}")
        
        return None
    
    def _send_alert_notification(self, alert: Dict):
        """发送告警通知"""
        # 这里可以扩展为邮件、短信、Webhook 等通知方式
        # 目前仅记录日志
        
        if alert['level'] in ['error', 'critical']:
            # 可以在这里添加邮件通知逻辑
            # send_email_alert(alert)
            pass


# 全局备份监控器实例
backup_monitor = BackupMonitor()


def get_backup_monitor() -> BackupMonitor:
    """
    获取备份监控器实例
    
    Returns:
        BackupMonitor: 备份监控器实例
    """
    return backup_monitor
