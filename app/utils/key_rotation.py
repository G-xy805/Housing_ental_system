"""
密钥轮换定时任务
自动检查并轮换加密密钥（每 90 天）
"""
import logging
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from flask import Flask


logger = logging.getLogger(__name__)


class KeyRotationScheduler:
    """
    密钥轮换调度器
    
    功能：
    - 定期检查密钥是否需要轮换
    - 自动轮换过期密钥
    - 记录轮换日志
    - 发送轮换通知
    """
    
    def __init__(self, app: Flask = None):
        """
        初始化调度器
        
        Args:
            app: Flask 应用实例
        """
        self.app = app
        self.scheduler = None
        
        if app:
            self.init_app(app)
    
    def init_app(self, app: Flask):
        """
        初始化 Flask 应用
        
        Args:
            app: Flask 应用实例
        """
        self.app = app
        
        # 创建调度器
        self.scheduler = BackgroundScheduler()
        
        # 添加定时任务：每天凌晨 2 点检查密钥轮换
        self.scheduler.add_job(
            func=self.check_and_rotate_key,
            trigger=CronTrigger(hour=2, minute=0),
            id='key_rotation_check',
            name='检查密钥轮换',
            replace_existing=True
        )
        
        # 添加定时任务：每周一凌晨 3 点生成密钥状态报告
        self.scheduler.add_job(
            func=self.generate_key_status_report,
            trigger=CronTrigger(day_of_week='mon', hour=3, minute=0),
            id='key_status_report',
            name='生成密钥状态报告',
            replace_existing=True
        )
        
        logger.info("密钥轮换调度器已初始化")
    
    def start(self):
        """启动调度器"""
        if self.scheduler and not self.scheduler.running:
            self.scheduler.start()
            logger.info("密钥轮换调度器已启动")
    
    def shutdown(self):
        """关闭调度器"""
        if self.scheduler and self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("密钥轮换调度器已关闭")
    
    def check_and_rotate_key(self):
        """
        检查并轮换密钥
        
        此方法由定时任务调用，每天执行一次
        """
        with self.app.app_context():
            try:
                from app.utils.aes_encryption import (
                    get_key_manager, 
                    should_rotate_key, 
                    rotate_encryption_key
                )
                
                logger.info("开始检查密钥轮换状态...")
                
                # 检查是否需要轮换
                if should_rotate_key():
                    logger.info("检测到密钥需要轮换，开始轮换...")
                    
                    # 执行密钥轮换
                    new_key_id = rotate_encryption_key()
                    
                    logger.info(f"密钥轮换成功，新密钥 ID: {new_key_id}")
                    
                    # 记录审计日志
                    self._log_key_rotation(new_key_id)
                    
                    # 发送通知（可选）
                    self._send_rotation_notification(new_key_id)
                else:
                    logger.info("密钥状态正常，无需轮换")
                    
                    # 记录检查日志
                    self._log_key_check()
                    
            except Exception as e:
                logger.error(f"密钥轮换检查失败: {str(e)}", exc_info=True)
    
    def generate_key_status_report(self):
        """
        生成密钥状态报告
        
        此方法由定时任务调用，每周执行一次
        """
        with self.app.app_context():
            try:
                from app.utils.aes_encryption import get_key_manager
                
                logger.info("开始生成密钥状态报告...")
                
                key_manager = get_key_manager()
                current_key_id, _ = key_manager.get_current_key()
                
                # 获取所有密钥信息
                all_keys = key_manager.get_all_key_ids()
                
                # 生成报告
                report = {
                    'generated_at': datetime.now().isoformat(),
                    'current_key_id': current_key_id,
                    'total_keys': len(all_keys),
                    'keys': []
                }
                
                for key_id in all_keys:
                    if key_id in key_manager.keys:
                        key_data = key_manager.keys[key_id]
                        report['keys'].append({
                            'key_id': key_id,
                            'created_at': key_data['created_at'],
                            'expires_at': key_data['expires_at'],
                            'is_primary': key_data['is_primary'],
                            'days_until_expiry': self._calculate_days_until_expiry(key_data['expires_at'])
                        })
                
                # 保存报告
                self._save_key_status_report(report)
                
                logger.info(f"密钥状态报告已生成: 当前密钥 {current_key_id}, 共 {len(all_keys)} 个密钥")
                
            except Exception as e:
                logger.error(f"生成密钥状态报告失败: {str(e)}", exc_info=True)
    
    def _calculate_days_until_expiry(self, expires_at_str: str) -> int:
        """
        计算距离过期的天数
        
        Args:
            expires_at_str: 过期时间字符串
            
        Returns:
            int: 距离过期的天数
        """
        try:
            expires_at = datetime.fromisoformat(expires_at_str)
            delta = expires_at - datetime.now()
            return max(0, delta.days)
        except:
            return 0
    
    def _log_key_rotation(self, new_key_id: str):
        """
        记录密钥轮换日志
        
        Args:
            new_key_id: 新密钥 ID
        """
        try:
            import os
            from app.config import config
            
            log_dir = os.path.join(config['default'].BASE_DIR, 'logs')
            os.makedirs(log_dir, exist_ok=True)
            
            log_file = os.path.join(log_dir, 'key_rotation.log')
            
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(f"{datetime.now().isoformat()} - 密钥轮换成功 - 新密钥 ID: {new_key_id}\n")
                
        except Exception as e:
            logger.error(f"记录密钥轮换日志失败: {str(e)}")
    
    def _log_key_check(self):
        """记录密钥检查日志"""
        try:
            import os
            from app.config import config
            from app.utils.aes_encryption import get_key_manager
            
            log_dir = os.path.join(config['default'].BASE_DIR, 'logs')
            os.makedirs(log_dir, exist_ok=True)
            
            log_file = os.path.join(log_dir, 'key_rotation.log')
            key_manager = get_key_manager()
            current_key_id, _ = key_manager.get_current_key()
            
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(f"{datetime.now().isoformat()} - 密钥检查正常 - 当前密钥 ID: {current_key_id}\n")
                
        except Exception as e:
            logger.error(f"记录密钥检查日志失败: {str(e)}")
    
    def _save_key_status_report(self, report: dict):
        """
        保存密钥状态报告
        
        Args:
            report: 报告数据
        """
        try:
            import os
            import json
            from app.config import config
            
            report_dir = os.path.join(config['default'].BASE_DIR, 'logs', 'reports')
            os.makedirs(report_dir, exist_ok=True)
            
            report_file = os.path.join(
                report_dir, 
                f"key_status_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )
            
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
                
            logger.info(f"密钥状态报告已保存: {report_file}")
            
        except Exception as e:
            logger.error(f"保存密钥状态报告失败: {str(e)}")
    
    def _send_rotation_notification(self, new_key_id: str):
        """
        发送密钥轮换通知
        
        Args:
            new_key_id: 新密钥 ID
        """
        # TODO: 实现通知逻辑（邮件、短信、Webhook 等）
        logger.info(f"密钥轮换通知: 新密钥 {new_key_id} 已生成")


# 全局调度器实例
key_rotation_scheduler = KeyRotationScheduler()


def init_key_rotation_scheduler(app: Flask):
    """
    初始化密钥轮换调度器
    
    Args:
        app: Flask 应用实例
    """
    key_rotation_scheduler.init_app(app)
    key_rotation_scheduler.start()


def shutdown_key_rotation_scheduler():
    """关闭密钥轮换调度器"""
    key_rotation_scheduler.shutdown()
