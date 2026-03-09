"""
数据库备份管理器模块

功能：
1. 支持完整备份和增量备份
2. 备份文件压缩（ZIP）
3. 备份文件加密（AES-256-GCM）
4. 自动清理过期备份
5. 备份完整性验证
6. 备份恢复功能
7. 数据归档功能（合同和支付记录）

安全特性：
- 使用 AES-256-GCM 加密算法
- 支持密钥轮换
- 加密元数据存储
- 备份文件完整性校验
"""
import os
import json
import shutil
import zipfile
import hashlib
import sqlite3
import time
from datetime import datetime, timedelta, date
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.backends import default_backend
import secrets
import base64
import logging

logger = logging.getLogger(__name__)


class BackupEncryptionError(Exception):
    """备份加密异常"""
    pass


class BackupDecryptionError(Exception):
    """备份解密异常"""
    pass


class BackupIntegrityError(Exception):
    """备份完整性异常"""
    pass


class BackupManager:
    """
    数据库备份管理器
    
    支持功能：
    - 完整备份：备份整个数据库文件
    - 增量备份：基于 WAL 模式的增量备份
    - 压缩：使用 ZIP 压缩备份文件
    - 加密：使用 AES-256-GCM 加密备份文件
    - 清理：自动清理过期备份
    - 验证：备份完整性验证
    """
    
    def __init__(self, app=None):
        """
        初始化备份管理器
        
        Args:
            app: Flask 应用实例
        """
        self.app = app
        self.backup_folder = None
        self.database_path = None
        self.upload_folder = None
        self.encryption_key = None
        self.backup_retention_days = 30
        self.enable_encryption = True
        self.enable_compression = True
        
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
        self.database_path = self._get_database_path()
        self.upload_folder = app.config.get('UPLOAD_FOLDER', 'uploads')
        self.backup_retention_days = app.config.get('BACKUP_RETENTION_DAYS', 30)
        self.enable_encryption = app.config.get('BACKUP_ENCRYPTION_ENABLED', True)
        self.enable_compression = app.config.get('BACKUP_COMPRESSION_ENABLED', True)
        
        # 获取或生成加密密钥
        self.encryption_key = self._get_or_create_encryption_key()
        
        # 确保备份目录存在
        os.makedirs(self.backup_folder, exist_ok=True)
        
        logger.info(f"备份管理器初始化完成 - 备份目录: {self.backup_folder}")
    
    def _get_database_path(self) -> Optional[str]:
        """
        获取数据库文件路径
        
        Returns:
            str: 数据库文件绝对路径
        """
        if not self.app:
            return None
        
        database_uri = self.app.config.get('SQLALCHEMY_DATABASE_URI', '')
        if database_uri.startswith('sqlite:///'):
            db_path = database_uri.replace('sqlite:///', '')
            if not os.path.isabs(db_path):
                db_path = os.path.join(self.app.instance_path or self.app.root_path, db_path)
            return os.path.abspath(db_path)
        return None
    
    def _get_or_create_encryption_key(self) -> bytes:
        """
        获取或创建备份加密密钥
        
        Returns:
            bytes: 256 位加密密钥
        """
        if not self.app:
            # 生成临时密钥
            return secrets.token_bytes(32)
        
        key_file = os.path.join(self.backup_folder, '.backup_key')
        
        # 如果密钥文件存在，读取密钥
        if os.path.exists(key_file):
            try:
                with open(key_file, 'rb') as f:
                    key_data = f.read()
                    # 验证密钥格式
                    if len(key_data) == 32:
                        logger.info("加载现有备份加密密钥")
                        return key_data
            except Exception as e:
                logger.warning(f"读取备份密钥失败: {str(e)}")
        
        # 生成新密钥
        key = secrets.token_bytes(32)
        
        try:
            # 保存密钥文件（设置权限为 600）
            with open(key_file, 'wb') as f:
                f.write(key)
            os.chmod(key_file, 0o600)
            logger.info("生成新的备份加密密钥")
        except Exception as e:
            logger.warning(f"保存备份密钥失败: {str(e)}")
        
        return key
    
    def create_full_backup(
        self,
        remark: str = None,
        include_uploads: bool = True,
        encrypt: bool = None,
        compress: bool = None
    ) -> Dict[str, Any]:
        """
        创建完整备份
        
        Args:
            remark: 备份备注
            include_uploads: 是否包含上传文件
            encrypt: 是否加密（None 使用默认配置）
            compress: 是否压缩（None 使用默认配置）
        
        Returns:
            Dict: 备份信息
        
        Raises:
            Exception: 备份失败时抛出异常
        """
        logger.info("开始创建完整备份...")
        
        if encrypt is None:
            encrypt = self.enable_encryption
        if compress is None:
            compress = self.enable_compression
        
        # 生成备份文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f'backup_full_{timestamp}'
        if encrypt:
            backup_filename += '.enc'
        if compress:
            backup_filename += '.zip'
        else:
            backup_filename += '.db'
        
        backup_path = os.path.join(self.backup_folder, backup_filename)
        
        # 创建临时目录
        temp_dir = os.path.join(self.backup_folder, f'temp_{timestamp}')
        os.makedirs(temp_dir, exist_ok=True)
        
        try:
            # 1. 备份数据库文件
            if not self.database_path or not os.path.exists(self.database_path):
                raise FileNotFoundError("数据库文件不存在")
            
            db_backup_path = os.path.join(temp_dir, 'database.db')
            
            # 使用 SQLite 在线备份 API（确保数据一致性）
            self._backup_database_online(db_backup_path)
            
            # 2. 备份上传文件
            uploads_backup_path = None
            if include_uploads and os.path.exists(self.upload_folder):
                uploads_backup_path = os.path.join(temp_dir, 'uploads')
                shutil.copytree(self.upload_folder, uploads_backup_path)
            
            # 3. 创建元数据
            metadata = {
                'backup_type': 'full',
                'backup_time': datetime.now().isoformat(),
                'backup_by': 'system',
                'remark': remark or '完整备份',
                'includes_uploads': include_uploads,
                'encrypted': encrypt,
                'compressed': compress,
                'database_path': self.database_path,
                'upload_folder': self.upload_folder if include_uploads else None,
                'app_version': self.app.config.get('VERSION', '1.0.0') if self.app else '1.0.0'
            }
            
            # 计算数据库文件哈希
            metadata['database_hash'] = self._calculate_file_hash(db_backup_path)
            
            meta_file_path = os.path.join(temp_dir, 'metadata.json')
            with open(meta_file_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            # 4. 创建备份文件
            if compress:
                # 压缩备份
                self._create_compressed_backup(temp_dir, backup_path, encrypt)
            elif encrypt:
                # 仅加密
                self._encrypt_file(db_backup_path, backup_path)
            else:
                # 直接复制
                shutil.copy2(db_backup_path, backup_path)
            
            # 5. 清理临时目录
            shutil.rmtree(temp_dir)
            
            # 6. 获取备份文件信息
            file_size = os.path.getsize(backup_path)
            file_hash = self._calculate_file_hash(backup_path)
            
            backup_info = {
                'filename': backup_filename,
                'backup_path': backup_path,
                'backup_type': 'full',
                'backup_time': datetime.now().isoformat(),
                'file_size': file_size,
                'file_size_mb': round(file_size / (1024 * 1024), 2),
                'file_hash': file_hash,
                'encrypted': encrypt,
                'compressed': compress,
                'includes_uploads': include_uploads,
                'remark': remark
            }
            
            logger.info(f"完整备份创建成功: {backup_filename}")
            
            return backup_info
            
        except Exception as e:
            # 清理临时文件
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            if os.path.exists(backup_path):
                os.remove(backup_path)
            
            logger.error(f"创建完整备份失败: {str(e)}")
            raise
    
    def create_incremental_backup(
        self,
        last_backup_time: datetime,
        remark: str = None,
        encrypt: bool = None,
        compress: bool = None
    ) -> Dict[str, Any]:
        """
        创建增量备份
        
        Args:
            last_backup_time: 上次备份时间
            remark: 备份备注
            encrypt: 是否加密
            compress: 是否压缩
        
        Returns:
            Dict: 备份信息
        
        注意：
            SQLite 的增量备份需要启用 WAL 模式
        """
        logger.info("开始创建增量备份...")
        
        if encrypt is None:
            encrypt = self.enable_encryption
        if compress is None:
            compress = self.enable_compression
        
        # 生成备份文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f'backup_inc_{timestamp}'
        if encrypt:
            backup_filename += '.enc'
        if compress:
            backup_filename += '.zip'
        else:
            backup_filename += '.db'
        
        backup_path = os.path.join(self.backup_folder, backup_filename)
        
        # 创建临时目录
        temp_dir = os.path.join(self.backup_folder, f'temp_inc_{timestamp}')
        os.makedirs(temp_dir, exist_ok=True)
        
        try:
            # 1. 检查 WAL 模式
            if not self._check_wal_mode():
                logger.warning("数据库未启用 WAL 模式，将创建完整备份")
                return self.create_full_backup(remark, False, encrypt, compress)
            
            # 2. 备份 WAL 文件
            db_backup_path = os.path.join(temp_dir, 'database.db')
            wal_path = self.database_path + '-wal'
            shm_path = self.database_path + '-shm'
            
            # 备份主数据库文件
            shutil.copy2(self.database_path, db_backup_path)
            
            # 备份 WAL 和 SHM 文件
            if os.path.exists(wal_path):
                shutil.copy2(wal_path, db_backup_path + '-wal')
            if os.path.exists(shm_path):
                shutil.copy2(shm_path, db_backup_path + '-shm')
            
            # 3. 创建元数据
            metadata = {
                'backup_type': 'incremental',
                'backup_time': datetime.now().isoformat(),
                'last_backup_time': last_backup_time.isoformat() if last_backup_time else None,
                'backup_by': 'system',
                'remark': remark or '增量备份',
                'encrypted': encrypt,
                'compressed': compress,
                'database_path': self.database_path
            }
            
            meta_file_path = os.path.join(temp_dir, 'metadata.json')
            with open(meta_file_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            # 4. 创建备份文件
            if compress:
                self._create_compressed_backup(temp_dir, backup_path, encrypt)
            elif encrypt:
                self._encrypt_file(db_backup_path, backup_path)
            else:
                shutil.copy2(db_backup_path, backup_path)
            
            # 5. 清理临时目录
            shutil.rmtree(temp_dir)
            
            # 6. 获取备份文件信息
            file_size = os.path.getsize(backup_path)
            
            backup_info = {
                'filename': backup_filename,
                'backup_path': backup_path,
                'backup_type': 'incremental',
                'backup_time': datetime.now().isoformat(),
                'file_size': file_size,
                'file_size_mb': round(file_size / (1024 * 1024), 2),
                'encrypted': encrypt,
                'compressed': compress,
                'remark': remark
            }
            
            logger.info(f"增量备份创建成功: {backup_filename}")
            
            return backup_info
            
        except Exception as e:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            if os.path.exists(backup_path):
                os.remove(backup_path)
            
            logger.error(f"创建增量备份失败: {str(e)}")
            raise
    
    def restore_backup(
        self,
        backup_path: str,
        create_pre_backup: bool = True
    ) -> Dict[str, Any]:
        """
        恢复备份
        
        Args:
            backup_path: 备份文件路径
            create_pre_backup: 是否在恢复前创建当前数据备份
        
        Returns:
            Dict: 恢复信息
        
        Raises:
            Exception: 恢复失败时抛出异常
        """
        logger.info(f"开始恢复备份: {backup_path}")
        
        if not os.path.exists(backup_path):
            raise FileNotFoundError("备份文件不存在")
        
        pre_backup_path = None
        
        try:
            # 1. 创建当前数据备份
            if create_pre_backup:
                logger.info("创建恢复前备份...")
                pre_backup_info = self.create_full_backup(
                    remark="恢复前自动备份",
                    include_uploads=True
                )
                pre_backup_path = pre_backup_info['backup_path']
            
            # 2. 解压/解密备份文件
            extract_dir = os.path.join(
                self.backup_folder,
                f'extract_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
            )
            os.makedirs(extract_dir, exist_ok=True)
            
            # 判断备份类型
            if backup_path.endswith('.zip'):
                # 解压 ZIP 文件
                if backup_path.endswith('.enc.zip'):
                    # 加密压缩文件
                    temp_zip = backup_path.replace('.enc.zip', '.zip')
                    self._decrypt_file(backup_path, temp_zip)
                    
                    with zipfile.ZipFile(temp_zip, 'r') as zipf:
                        zipf.extractall(extract_dir)
                    
                    os.remove(temp_zip)
                else:
                    # 未加密压缩文件
                    with zipfile.ZipFile(backup_path, 'r') as zipf:
                        zipf.extractall(extract_dir)
            elif backup_path.endswith('.enc'):
                # 仅加密文件
                decrypted_path = backup_path.replace('.enc', '.db')
                self._decrypt_file(backup_path, decrypted_path)
                shutil.move(decrypted_path, os.path.join(extract_dir, 'database.db'))
            else:
                # 未加密未压缩文件
                shutil.copy2(backup_path, os.path.join(extract_dir, 'database.db'))
            
            # 3. 读取元数据
            metadata = {}
            meta_file = os.path.join(extract_dir, 'metadata.json')
            if os.path.exists(meta_file):
                with open(meta_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
            
            # 4. 验证备份完整性
            extracted_db = os.path.join(extract_dir, 'database.db')
            if os.path.exists(extracted_db):
                if 'database_hash' in metadata:
                    current_hash = self._calculate_file_hash(extracted_db)
                    if current_hash != metadata['database_hash']:
                        raise BackupIntegrityError("备份文件完整性验证失败")
            
            # 5. 恢复数据库
            if os.path.exists(extracted_db):
                # 关闭数据库连接
                if self.app:
                    from app import db
                    db.session.close()
                    db.engine.dispose()
                
                # 备份当前数据库
                if os.path.exists(self.database_path):
                    current_db_backup = self.database_path + '.bak'
                    shutil.copy2(self.database_path, current_db_backup)
                
                # 恢复数据库
                shutil.copy2(extracted_db, self.database_path)
                
                logger.info("数据库恢复成功")
            
            # 6. 恢复上传文件
            extracted_uploads = os.path.join(extract_dir, 'uploads')
            if os.path.exists(extracted_uploads):
                # 备份当前上传文件
                if os.path.exists(self.upload_folder):
                    current_uploads_backup = self.upload_folder + '.bak'
                    if os.path.exists(current_uploads_backup):
                        shutil.rmtree(current_uploads_backup)
                    shutil.move(self.upload_folder, current_uploads_backup)
                
                # 恢复上传文件
                shutil.move(extracted_uploads, self.upload_folder)
                
                logger.info("上传文件恢复成功")
            
            # 7. 清理临时目录
            shutil.rmtree(extract_dir)
            
            restore_info = {
                'backup_file': os.path.basename(backup_path),
                'restore_time': datetime.now().isoformat(),
                'pre_backup_file': os.path.basename(pre_backup_path) if pre_backup_path else None,
                'metadata': metadata
            }
            
            logger.info(f"备份恢复成功: {backup_path}")
            
            return restore_info
            
        except Exception as e:
            logger.error(f"恢复备份失败: {str(e)}")
            raise
    
    def cleanup_old_backups(self, retention_days: int = None) -> int:
        """
        清理过期备份
        
        Args:
            retention_days: 保留天数（None 使用默认配置）
        
        Returns:
            int: 删除的备份数量
        """
        if retention_days is None:
            retention_days = self.backup_retention_days
        
        logger.info(f"开始清理过期备份（保留 {retention_days} 天）...")
        
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        deleted_count = 0
        
        try:
            # 遍历备份文件
            for filename in os.listdir(self.backup_folder):
                if not (filename.startswith('backup_') and 
                        (filename.endswith('.db') or filename.endswith('.zip') or filename.endswith('.enc'))):
                    continue
                
                filepath = os.path.join(self.backup_folder, filename)
                
                # 获取文件修改时间
                file_mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
                
                # 删除过期文件
                if file_mtime < cutoff_date:
                    try:
                        os.remove(filepath)
                        deleted_count += 1
                        logger.info(f"删除过期备份: {filename}")
                    except Exception as e:
                        logger.error(f"删除备份失败 {filename}: {str(e)}")
            
            logger.info(f"清理完成，共删除 {deleted_count} 个过期备份")
            
        except Exception as e:
            logger.error(f"清理过期备份失败: {str(e)}")
        
        return deleted_count
    
    def verify_backup(self, backup_path: str) -> Dict[str, Any]:
        """
        验证备份完整性
        
        Args:
            backup_path: 备份文件路径
        
        Returns:
            Dict: 验证结果
        """
        logger.info(f"验证备份完整性: {backup_path}")
        
        result = {
            'valid': False,
            'backup_path': backup_path,
            'errors': []
        }
        
        try:
            if not os.path.exists(backup_path):
                result['errors'].append("备份文件不存在")
                return result
            
            # 解压/解密备份文件
            extract_dir = os.path.join(
                self.backup_folder,
                f'verify_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
            )
            os.makedirs(extract_dir, exist_ok=True)
            
            # 解压文件
            if backup_path.endswith('.zip'):
                if backup_path.endswith('.enc.zip'):
                    temp_zip = backup_path.replace('.enc.zip', '.zip')
                    self._decrypt_file(backup_path, temp_zip)
                    with zipfile.ZipFile(temp_zip, 'r') as zipf:
                        zipf.extractall(extract_dir)
                    os.remove(temp_zip)
                else:
                    with zipfile.ZipFile(backup_path, 'r') as zipf:
                        zipf.extractall(extract_dir)
            elif backup_path.endswith('.enc'):
                decrypted_path = backup_path.replace('.enc', '.db')
                self._decrypt_file(backup_path, decrypted_path)
                shutil.move(decrypted_path, os.path.join(extract_dir, 'database.db'))
            else:
                shutil.copy2(backup_path, os.path.join(extract_dir, 'database.db'))
            
            # 读取元数据
            metadata = {}
            meta_file = os.path.join(extract_dir, 'metadata.json')
            if os.path.exists(meta_file):
                with open(meta_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
            
            # 验证数据库文件
            extracted_db = os.path.join(extract_dir, 'database.db')
            if not os.path.exists(extracted_db):
                result['errors'].append("备份中缺少数据库文件")
            else:
                # 验证数据库完整性
                try:
                    conn = sqlite3.connect(extracted_db)
                    cursor = conn.cursor()
                    cursor.execute("PRAGMA integrity_check")
                    integrity_result = cursor.fetchone()
                    conn.close()
                    
                    if integrity_result[0] != 'ok':
                        result['errors'].append(f"数据库完整性检查失败: {integrity_result[0]}")
                except Exception as e:
                    result['errors'].append(f"数据库验证失败: {str(e)}")
                
                # 验证文件哈希
                if 'database_hash' in metadata:
                    current_hash = self._calculate_file_hash(extracted_db)
                    if current_hash != metadata['database_hash']:
                        result['errors'].append("数据库文件哈希不匹配")
            
            # 清理临时目录
            shutil.rmtree(extract_dir)
            
            # 判断验证结果
            result['valid'] = len(result['errors']) == 0
            result['metadata'] = metadata
            
        except Exception as e:
            result['errors'].append(f"验证过程异常: {str(e)}")
        
        return result
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """
        列出所有备份
        
        Returns:
            List[Dict]: 备份列表
        """
        backups = []
        
        try:
            for filename in os.listdir(self.backup_folder):
                if not (filename.startswith('backup_') and 
                        (filename.endswith('.db') or filename.endswith('.zip') or filename.endswith('.enc'))):
                    continue
                
                filepath = os.path.join(self.backup_folder, filename)
                file_stat = os.stat(filepath)
                
                # 尝试读取元数据
                metadata = self._read_backup_metadata(filepath)
                
                backup_info = {
                    'filename': filename,
                    'filepath': filepath,
                    'backup_time': metadata.get('backup_time', 
                        datetime.fromtimestamp(file_stat.st_mtime).isoformat()),
                    'backup_type': metadata.get('backup_type', 'unknown'),
                    'file_size': file_stat.st_size,
                    'file_size_mb': round(file_stat.st_size / (1024 * 1024), 2),
                    'encrypted': metadata.get('encrypted', False),
                    'compressed': metadata.get('compressed', False),
                    'remark': metadata.get('remark', ''),
                    'includes_uploads': metadata.get('includes_uploads', False)
                }
                
                backups.append(backup_info)
            
            # 按备份时间排序（最新的在前）
            backups.sort(key=lambda x: x['backup_time'], reverse=True)
            
        except Exception as e:
            logger.error(f"列出备份失败: {str(e)}")
        
        return backups
    
    # ==================== 私有方法 ====================
    
    def _backup_database_online(self, backup_path: str):
        """
        在线备份数据库（使用 SQLite 在线备份 API）
        
        Args:
            backup_path: 备份文件路径
        """
        # 连接到源数据库
        source_conn = sqlite3.connect(self.database_path)
        
        # 创建备份数据库
        backup_conn = sqlite3.connect(backup_path)
        
        # 执行在线备份
        source_conn.backup(backup_conn)
        
        # 关闭连接
        backup_conn.close()
        source_conn.close()
    
    def _check_wal_mode(self) -> bool:
        """
        检查数据库是否启用 WAL 模式
        
        Returns:
            bool: True 表示已启用 WAL 模式
        """
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            cursor.execute("PRAGMA journal_mode")
            result = cursor.fetchone()
            conn.close()
            
            return result[0].lower() == 'wal'
        except Exception as e:
            logger.error(f"检查 WAL 模式失败: {str(e)}")
            return False
    
    def _create_compressed_backup(
        self,
        source_dir: str,
        backup_path: str,
        encrypt: bool
    ):
        """
        创建压缩备份
        
        Args:
            source_dir: 源目录
            backup_path: 备份文件路径
            encrypt: 是否加密
        """
        if encrypt:
            # 先创建临时 ZIP 文件
            temp_zip = backup_path.replace('.enc.zip', '.zip')
            
            with zipfile.ZipFile(temp_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(source_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, source_dir)
                        zipf.write(file_path, arcname)
            
            # 加密 ZIP 文件
            self._encrypt_file(temp_zip, backup_path)
            
            # 删除临时文件
            os.remove(temp_zip)
        else:
            # 直接创建 ZIP 文件
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(source_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, source_dir)
                        zipf.write(file_path, arcname)
    
    def _encrypt_file(self, source_path: str, dest_path: str):
        """
        加密文件（使用 AES-256-GCM）
        
        Args:
            source_path: 源文件路径
            dest_path: 目标文件路径
        """
        try:
            # 读取源文件
            with open(source_path, 'rb') as f:
                plaintext = f.read()
            
            # 生成随机 nonce（12 字节）
            nonce = secrets.token_bytes(12)
            
            # 使用 AES-256-GCM 加密
            aesgcm = AESGCM(self.encryption_key)
            ciphertext = aesgcm.encrypt(nonce, plaintext, None)
            
            # 写入加密文件（nonce + ciphertext）
            with open(dest_path, 'wb') as f:
                f.write(nonce)
                f.write(ciphertext)
            
        except Exception as e:
            raise BackupEncryptionError(f"文件加密失败: {str(e)}")
    
    def _decrypt_file(self, source_path: str, dest_path: str):
        """
        解密文件
        
        Args:
            source_path: 源文件路径
            dest_path: 目标文件路径
        """
        try:
            # 读取加密文件
            with open(source_path, 'rb') as f:
                data = f.read()
            
            # 提取 nonce 和密文
            nonce = data[:12]
            ciphertext = data[12:]
            
            # 使用 AES-256-GCM 解密
            aesgcm = AESGCM(self.encryption_key)
            plaintext = aesgcm.decrypt(nonce, ciphertext, None)
            
            # 写入解密文件
            with open(dest_path, 'wb') as f:
                f.write(plaintext)
            
        except Exception as e:
            raise BackupDecryptionError(f"文件解密失败: {str(e)}")
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """
        计算文件 SHA-256 哈希值
        
        Args:
            file_path: 文件路径
        
        Returns:
            str: 哈希值（十六进制字符串）
        """
        sha256_hash = hashlib.sha256()
        
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                sha256_hash.update(chunk)
        
        return sha256_hash.hexdigest()
    
    def _read_backup_metadata(self, backup_path: str) -> Dict:
        """
        读取备份元数据
        
        Args:
            backup_path: 备份文件路径
        
        Returns:
            Dict: 元数据
        """
        metadata = {}
        
        try:
            # 解压/解密备份文件
            extract_dir = os.path.join(
                self.backup_folder,
                f'meta_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
            )
            os.makedirs(extract_dir, exist_ok=True)
            
            # 解压文件
            if backup_path.endswith('.zip'):
                if backup_path.endswith('.enc.zip'):
                    temp_zip = backup_path.replace('.enc.zip', '.zip')
                    self._decrypt_file(backup_path, temp_zip)
                    with zipfile.ZipFile(temp_zip, 'r') as zipf:
                        if 'metadata.json' in zipf.namelist():
                            with zipf.open('metadata.json') as f:
                                metadata = json.load(f)
                    os.remove(temp_zip)
                else:
                    with zipfile.ZipFile(backup_path, 'r') as zipf:
                        if 'metadata.json' in zipf.namelist():
                            with zipf.open('metadata.json') as f:
                                metadata = json.load(f)
            
            # 清理临时目录
            if os.path.exists(extract_dir):
                shutil.rmtree(extract_dir)
            
        except Exception as e:
            logger.warning(f"读取备份元数据失败: {str(e)}")
        
        return metadata
    
    # ==================== 数据归档功能 ====================
    
    def archive_contracts(
        self,
        months_retention: int = 12,
        batch_size: int = 100,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        归档过期合同
        
        将超过保留期限的已过期或已终止合同归档
        
        Args:
            months_retention: 保留月数（默认12个月）
            batch_size: 批量处理大小
            dry_run: 是否为预览模式（不实际执行）
        
        Returns:
            Dict: 归档结果
        """
        from app import db
        from app.models.contract import Contract
        from app.models.archive import ContractArchive, ArchiveRecord
        
        logger.info(f"开始归档合同（保留 {months_retention} 个月）...")
        
        # 计算归档截止日期
        cutoff_date = date.today() - timedelta(days=months_retention * 30)
        
        # 创建归档记录
        archive_record = ArchiveRecord(
            archive_type='contract',
            archive_date=date.today(),
            archive_reason='auto_archive',
            date_range_start=None,
            date_range_end=cutoff_date,
            started_at=datetime.now()
        )
        
        if not dry_run:
            db.session.add(archive_record)
            db.session.commit()
        
        total = 0
        archived = 0
        failed = 0
        errors = []
        
        try:
            # 查询符合条件的合同
            # 状态为 expired 或 terminated，且结束日期早于截止日期
            query = Contract.query.filter(
                Contract.status.in_(['expired', 'terminated']),
                Contract.end_date < cutoff_date,
                Contract.deleted_at.is_(None)
            )
            
            total = query.count()
            logger.info(f"找到 {total} 个待归档合同")
            
            if dry_run:
                # 预览模式，只返回统计信息
                return {
                    'dry_run': True,
                    'total': total,
                    'cutoff_date': cutoff_date.strftime('%Y-%m-%d'),
                    'contracts': [
                        {
                            'id': c.id,
                            'contract_no': c.contract_no,
                            'end_date': c.end_date.strftime('%Y-%m-%d'),
                            'status': c.status
                        }
                        for c in query.limit(10).all()
                    ]
                }
            
            # 分批处理
            offset = 0
            while offset < total:
                contracts = query.offset(offset).limit(batch_size).all()
                
                for contract in contracts:
                    try:
                        # 创建归档记录
                        archive = ContractArchive.archive_from_contract(
                            contract,
                            archive_reason='auto_archive'
                        )
                        db.session.add(archive)
                        
                        # 硬删除原合同（归档后不再需要）
                        db.session.delete(contract)
                        
                        archived += 1
                        
                    except Exception as e:
                        failed += 1
                        error_msg = f"归档合同 {contract.id} 失败: {str(e)}"
                        errors.append(error_msg)
                        logger.error(error_msg)
                
                # 提交批次
                db.session.commit()
                
                # 更新进度
                archive_record.archived_records = archived
                archive_record.failed_records = failed
                db.session.commit()
                
                offset += batch_size
                
                # 短暂延迟，避免数据库压力
                time.sleep(0.1)
            
            # 更新归档记录
            archive_record.total_records = total
            archive_record.archived_records = archived
            archive_record.failed_records = failed
            archive_record.completed_at = datetime.now()
            archive_record.execution_time = (
                archive_record.completed_at - archive_record.started_at
            ).total_seconds()
            
            if errors:
                archive_record.error_message = '\n'.join(errors[:10])  # 只保存前10条错误
            
            db.session.commit()
            
            logger.info(
                f"合同归档完成 - "
                f"总数: {total}, "
                f"已归档: {archived}, "
                f"失败: {failed}"
            )
            
        except Exception as e:
            logger.error(f"合同归档异常: {str(e)}")
            archive_record.error_message = str(e)
            archive_record.completed_at = datetime.now()
            db.session.commit()
            raise
        
        return {
            'total': total,
            'archived': archived,
            'failed': failed,
            'cutoff_date': cutoff_date.strftime('%Y-%m-%d'),
            'execution_time': archive_record.execution_time
        }
    
    def archive_payments(
        self,
        months_retention: int = 12,
        batch_size: int = 100,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        归档支付记录
        
        将超过保留期限的已完成或已取消支付记录归档
        
        Args:
            months_retention: 保留月数（默认12个月）
            batch_size: 批量处理大小
            dry_run: 是否为预览模式（不实际执行）
        
        Returns:
            Dict: 归档结果
        """
        from app import db
        from app.models.payment import Payment
        from app.models.archive import PaymentArchive, ArchiveRecord
        
        logger.info(f"开始归档支付记录（保留 {months_retention} 个月）...")
        
        # 计算归档截止日期
        cutoff_date = date.today() - timedelta(days=months_retention * 30)
        
        # 创建归档记录
        archive_record = ArchiveRecord(
            archive_type='payment',
            archive_date=date.today(),
            archive_reason='auto_archive',
            date_range_start=None,
            date_range_end=cutoff_date,
            started_at=datetime.now()
        )
        
        if not dry_run:
            db.session.add(archive_record)
            db.session.commit()
        
        total = 0
        archived = 0
        failed = 0
        errors = []
        
        try:
            # 查询符合条件的支付记录
            # 状态为 paid, cancelled 或 refunded，且支付日期早于截止日期
            query = Payment.query.filter(
                Payment.status.in_(['paid', 'cancelled', 'refunded']),
                Payment.payment_date < cutoff_date,
                Payment.deleted_at.is_(None)
            )
            
            total = query.count()
            logger.info(f"找到 {total} 个待归档支付记录")
            
            if dry_run:
                # 预览模式，只返回统计信息
                return {
                    'dry_run': True,
                    'total': total,
                    'cutoff_date': cutoff_date.strftime('%Y-%m-%d'),
                    'payments': [
                        {
                            'id': p.id,
                            'payment_no': p.payment_no,
                            'payment_date': p.payment_date.strftime('%Y-%m-%d') if p.payment_date else None,
                            'status': p.status,
                            'amount': float(p.amount)
                        }
                        for p in query.limit(10).all()
                    ]
                }
            
            # 分批处理
            offset = 0
            while offset < total:
                payments = query.offset(offset).limit(batch_size).all()
                
                for payment in payments:
                    try:
                        # 创建归档记录
                        archive = PaymentArchive.archive_from_payment(
                            payment,
                            archive_reason='auto_archive'
                        )
                        db.session.add(archive)
                        
                        # 硬删除原支付记录（归档后不再需要）
                        db.session.delete(payment)
                        
                        archived += 1
                        
                    except Exception as e:
                        failed += 1
                        error_msg = f"归档支付记录 {payment.id} 失败: {str(e)}"
                        errors.append(error_msg)
                        logger.error(error_msg)
                
                # 提交批次
                db.session.commit()
                
                # 更新进度
                archive_record.archived_records = archived
                archive_record.failed_records = failed
                db.session.commit()
                
                offset += batch_size
                
                # 短暂延迟，避免数据库压力
                time.sleep(0.1)
            
            # 更新归档记录
            archive_record.total_records = total
            archive_record.archived_records = archived
            archive_record.failed_records = failed
            archive_record.completed_at = datetime.now()
            archive_record.execution_time = (
                archive_record.completed_at - archive_record.started_at
            ).total_seconds()
            
            if errors:
                archive_record.error_message = '\n'.join(errors[:10])  # 只保存前10条错误
            
            db.session.commit()
            
            logger.info(
                f"支付记录归档完成 - "
                f"总数: {total}, "
                f"已归档: {archived}, "
                f"失败: {failed}"
            )
            
        except Exception as e:
            logger.error(f"支付记录归档异常: {str(e)}")
            archive_record.error_message = str(e)
            archive_record.completed_at = datetime.now()
            db.session.commit()
            raise
        
        return {
            'total': total,
            'archived': archived,
            'failed': failed,
            'cutoff_date': cutoff_date.strftime('%Y-%m-%d'),
            'execution_time': archive_record.execution_time
        }
    
    def archive_all(
        self,
        months_retention: int = 12,
        batch_size: int = 100,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        执行完整归档（合同和支付记录）
        
        Args:
            months_retention: 保留月数（默认12个月）
            batch_size: 批量处理大小
            dry_run: 是否为预览模式（不实际执行）
        
        Returns:
            Dict: 归档结果
        """
        logger.info("开始执行完整归档...")
        
        start_time = time.time()
        
        results = {
            'contracts': None,
            'payments': None,
            'total_archived': 0,
            'total_failed': 0,
            'execution_time': 0
        }
        
        try:
            # 归档合同
            results['contracts'] = self.archive_contracts(
                months_retention=months_retention,
                batch_size=batch_size,
                dry_run=dry_run
            )
            
            # 归档支付记录
            results['payments'] = self.archive_payments(
                months_retention=months_retention,
                batch_size=batch_size,
                dry_run=dry_run
            )
            
            # 汇总结果
            if not dry_run:
                results['total_archived'] = (
                    results['contracts']['archived'] + 
                    results['payments']['archived']
                )
                results['total_failed'] = (
                    results['contracts']['failed'] + 
                    results['payments']['failed']
                )
            
            results['execution_time'] = time.time() - start_time
            
            logger.info(
                f"完整归档完成 - "
                f"总归档: {results['total_archived']}, "
                f"总失败: {results['total_failed']}, "
                f"耗时: {results['execution_time']:.2f}秒"
            )
            
        except Exception as e:
            logger.error(f"完整归档异常: {str(e)}")
            raise
        
        return results
    
    def get_archive_statistics(self) -> Dict[str, Any]:
        """
        获取归档统计信息
        
        Returns:
            Dict: 统计信息
        """
        from app.models.archive import ContractArchive, PaymentArchive, ArchiveRecord
        
        try:
            # 合同归档统计
            contract_count = ContractArchive.query.count()
            oldest_contract = ContractArchive.query.order_by(
                ContractArchive.archived_at.asc()
            ).first()
            newest_contract = ContractArchive.query.order_by(
                ContractArchive.archived_at.desc()
            ).first()
            
            # 支付记录归档统计
            payment_count = PaymentArchive.query.count()
            oldest_payment = PaymentArchive.query.order_by(
                PaymentArchive.archived_at.asc()
            ).first()
            newest_payment = PaymentArchive.query.order_by(
                PaymentArchive.archived_at.desc()
            ).first()
            
            # 最近归档操作
            recent_archives = ArchiveRecord.query.order_by(
                ArchiveRecord.created_at.desc()
            ).limit(10).all()
            
            return {
                'contracts': {
                    'total': contract_count,
                    'oldest_archived': oldest_contract.archived_at.strftime('%Y-%m-%d %H:%M:%S') if oldest_contract else None,
                    'newest_archived': newest_contract.archived_at.strftime('%Y-%m-%d %H:%M:%S') if newest_contract else None
                },
                'payments': {
                    'total': payment_count,
                    'oldest_archived': oldest_payment.archived_at.strftime('%Y-%m-%d %H:%M:%S') if oldest_payment else None,
                    'newest_archived': newest_payment.archived_at.strftime('%Y-%m-%d %H:%M:%S') if newest_payment else None
                },
                'recent_operations': [r.to_dict() for r in recent_archives]
            }
            
        except Exception as e:
            logger.error(f"获取归档统计失败: {str(e)}")
            return {
                'contracts': {'total': 0},
                'payments': {'total': 0},
                'recent_operations': []
            }


# 全局备份管理器实例
backup_manager = BackupManager()


def get_backup_manager() -> BackupManager:
    """
    获取备份管理器实例
    
    Returns:
        BackupManager: 备份管理器实例
    """
    return backup_manager
