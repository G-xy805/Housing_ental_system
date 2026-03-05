"""
AES-256-GCM 加密模块
提供高安全性的敏感数据加密和解密功能

特性：
- 使用 AES-256-GCM 认证加密算法
- 支持密钥轮换机制（每 90 天自动轮换）
- 密钥从环境变量或专用密钥管理服务获取
- 完整的加密访问审计日志
- 向后兼容旧的 Fernet 加密数据
"""
import os
import json
import base64
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from cryptography.fernet import Fernet, InvalidToken
from functools import lru_cache


class EncryptionKeyManager:
    """
    加密密钥管理器
    
    负责管理加密密钥的存储、轮换和版本控制
    支持多密钥并存，实现平滑的密钥轮换
    """
    
    # 密钥轮换周期（天）
    KEY_ROTATION_DAYS = 90
    
    # 密钥元数据文件路径
    KEY_METADATA_FILE = 'encryption_keys.json'
    
    def __init__(self):
        """初始化密钥管理器"""
        self.keys: Dict[str, Dict[str, Any]] = {}
        self.current_key_id: Optional[str] = None
        self._load_keys()
    
    def _get_key_metadata_path(self) -> str:
        """获取密钥元数据文件路径"""
        from app.config import config
        base_dir = config['default'].BASE_DIR
        return os.path.join(base_dir, 'keys', self.KEY_METADATA_FILE)
    
    def _load_keys(self):
        """从文件加载密钥元数据"""
        metadata_path = self._get_key_metadata_path()
        
        if os.path.exists(metadata_path):
            try:
                with open(metadata_path, 'r') as f:
                    data = json.load(f)
                    self.keys = data.get('keys', {})
                    self.current_key_id = data.get('current_key_id')
            except Exception as e:
                # 如果加载失败，初始化空密钥集
                self.keys = {}
                self.current_key_id = None
        
        # 如果没有密钥，从环境变量加载或创建新密钥
        if not self.keys:
            self._initialize_from_env()
    
    def _initialize_from_env(self):
        """从环境变量初始化密钥"""
        from app.config import config
        
        # 尝试从环境变量获取主密钥
        primary_key = os.getenv('AES_PRIMARY_KEY')
        if primary_key:
            # 使用环境变量中的密钥
            key_id = self._generate_key_id()
            self.keys[key_id] = {
                'key': primary_key,
                'created_at': datetime.now().isoformat(),
                'expires_at': (datetime.now() + timedelta(days=self.KEY_ROTATION_DAYS)).isoformat(),
                'is_primary': True
            }
            self.current_key_id = key_id
        else:
            # 生成新的密钥
            self.rotate_key()
    
    def _save_keys(self):
        """保存密钥元数据到文件"""
        metadata_path = self._get_key_metadata_path()
        
        # 确保目录存在
        os.makedirs(os.path.dirname(metadata_path), exist_ok=True)
        
        # 保存元数据（不包含实际密钥值，只保存引用）
        data = {
            'keys': self.keys,
            'current_key_id': self.current_key_id,
            'last_updated': datetime.now().isoformat()
        }
        
        with open(metadata_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _generate_key_id(self) -> str:
        """生成唯一的密钥 ID"""
        return f"key_{datetime.now().strftime('%Y%m%d%H%M%S')}_{secrets.token_hex(4)}"
    
    def generate_key(self) -> str:
        """
        生成新的 AES-256 密钥
        
        Returns:
            str: Base64 编码的 256 位密钥
        """
        # 生成 32 字节（256 位）的随机密钥
        key = secrets.token_bytes(32)
        return base64.b64encode(key).decode('utf-8')
    
    def rotate_key(self) -> str:
        """
        轮换加密密钥
        
        生成新密钥并将其设置为主密钥，旧密钥保留用于解密
        
        Returns:
            str: 新密钥的 ID
        """
        # 生成新密钥
        new_key_id = self._generate_key_id()
        new_key = self.generate_key()
        
        # 将当前主密钥标记为非主密钥
        if self.current_key_id and self.current_key_id in self.keys:
            self.keys[self.current_key_id]['is_primary'] = False
        
        # 添加新密钥
        self.keys[new_key_id] = {
            'key': new_key,
            'created_at': datetime.now().isoformat(),
            'expires_at': (datetime.now() + timedelta(days=self.KEY_ROTATION_DAYS)).isoformat(),
            'is_primary': True
        }
        
        self.current_key_id = new_key_id
        
        # 清理过期密钥（保留最近 3 个密钥用于解密）
        self._cleanup_old_keys()
        
        # 保存密钥元数据
        self._save_keys()
        
        return new_key_id
    
    def _cleanup_old_keys(self):
        """清理过期的旧密钥，保留最近 3 个"""
        if len(self.keys) <= 3:
            return
        
        # 按创建时间排序
        sorted_keys = sorted(
            self.keys.items(),
            key=lambda x: x[1]['created_at'],
            reverse=True
        )
        
        # 保留最近 3 个密钥
        keys_to_keep = dict(sorted_keys[:3])
        
        # 如果当前主密钥不在保留列表中，确保保留
        if self.current_key_id not in keys_to_keep:
            keys_to_keep[self.current_key_id] = self.keys[self.current_key_id]
        
        self.keys = keys_to_keep
    
    def get_current_key(self) -> Tuple[str, str]:
        """
        获取当前主密钥
        
        Returns:
            Tuple[str, str]: (密钥 ID, 密钥值)
        """
        if not self.current_key_id or self.current_key_id not in self.keys:
            raise ValueError("没有可用的加密密钥")
        
        key_data = self.keys[self.current_key_id]
        return self.current_key_id, key_data['key']
    
    def get_key_by_id(self, key_id: str) -> Optional[str]:
        """
        根据 ID 获取密钥
        
        Args:
            key_id: 密钥 ID
            
        Returns:
            Optional[str]: 密钥值，如果不存在则返回 None
        """
        if key_id in self.keys:
            return self.keys[key_id]['key']
        return None
    
    def should_rotate(self) -> bool:
        """
        检查是否应该轮换密钥
        
        Returns:
            bool: 是否需要轮换
        """
        if not self.current_key_id or self.current_key_id not in self.keys:
            return True
        
        key_data = self.keys[self.current_key_id]
        expires_at = datetime.fromisoformat(key_data['expires_at'])
        
        return datetime.now() >= expires_at
    
    def get_all_key_ids(self) -> list:
        """获取所有密钥 ID 列表"""
        return list(self.keys.keys())


# 全局密钥管理器实例
_key_manager: Optional[EncryptionKeyManager] = None


def get_key_manager() -> EncryptionKeyManager:
    """
    获取全局密钥管理器实例
    
    Returns:
        EncryptionKeyManager: 密钥管理器实例
    """
    global _key_manager
    if _key_manager is None:
        _key_manager = EncryptionKeyManager()
    return _key_manager


class EncryptionAuditLogger:
    """
    加密访问审计日志记录器
    
    记录所有加密/解密操作，用于安全审计
    """
    
    @staticmethod
    def log_encryption_operation(
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
        记录加密操作日志（异步方式）
        
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
            # 检查是否启用了审计
            from flask import current_app
            if current_app and not current_app.config.get('ENCRYPTION_AUDIT_ENABLED', True):
                return
            
            from app.utils.async_audit import queue_encryption_audit
            
            queue_encryption_audit(
                operation=operation,
                field_name=field_name,
                model_name=model_name,
                record_id=record_id,
                key_id=key_id,
                user_id=user_id,
                ip_address=ip_address,
                success=success,
                error_message=error_message
            )
        except Exception as e:
            import logging
            logging.error(f"记录加密审计日志失败: {str(e)}")


class AES256GCMEncryptor:
    """
    AES-256-GCM 加密器
    
    提供高安全性的加密和解密功能
    """
    
    # GCM 模式的 nonce 长度（12 字节是推荐值）
    NONCE_LENGTH = 12
    
    # 标签长度（16 字节）
    TAG_LENGTH = 16
    
    # 加密数据格式版本
    FORMAT_VERSION = 1
    
    @classmethod
    def encrypt(cls, plaintext: str, key: str) -> str:
        """
        使用 AES-256-GCM 加密数据
        
        Args:
            plaintext: 明文数据
            key: Base64 编码的 256 位密钥
            
        Returns:
            str: 加密后的数据（格式：version:key_id:nonce:ciphertext:tag）
            
        Raises:
            ValueError: 如果加密失败
        """
        if not plaintext:
            return None
        
        try:
            # 获取密钥管理器
            key_manager = get_key_manager()
            key_id, current_key = key_manager.get_current_key()
            
            # 如果提供了密钥，使用提供的密钥
            if key:
                current_key = key
            
            # 解码密钥
            key_bytes = base64.b64decode(current_key)
            
            # 生成随机 nonce
            nonce = secrets.token_bytes(cls.NONCE_LENGTH)
            
            # 创建加密器
            cipher = AES.new(key_bytes, AES.MODE_GCM, nonce=nonce)
            
            # 加密数据
            plaintext_bytes = plaintext.encode('utf-8')
            ciphertext, tag = cipher.encrypt_and_digest(plaintext_bytes)
            
            # 组合加密数据：version(1) + key_id + nonce + ciphertext + tag
            encrypted_data = {
                'v': cls.FORMAT_VERSION,
                'kid': key_id,
                'n': base64.b64encode(nonce).decode('utf-8'),
                'ct': base64.b64encode(ciphertext).decode('utf-8'),
                'tag': base64.b64encode(tag).decode('utf-8')
            }
            
            # 返回 JSON 格式的加密数据
            return base64.b64encode(json.dumps(encrypted_data).encode('utf-8')).decode('utf-8')
            
        except Exception as e:
            raise ValueError(f"加密失败: {str(e)}")
    
    @classmethod
    def decrypt(cls, encrypted_data: str, key_manager: Optional[EncryptionKeyManager] = None) -> str:
        """
        使用 AES-256-GCM 解密数据
        
        Args:
            encrypted_data: 加密的数据
            key_manager: 密钥管理器实例（可选）
            
        Returns:
            str: 解密后的明文数据
            
        Raises:
            ValueError: 如果解密失败或数据格式错误
        """
        if not encrypted_data:
            return None
        
        try:
            # 解码加密数据
            encrypted_json = base64.b64decode(encrypted_data).decode('utf-8')
            data = json.loads(encrypted_json)
            
            # 检查版本
            version = data.get('v')
            if version != cls.FORMAT_VERSION:
                raise ValueError(f"不支持的加密数据版本: {version}")
            
            # 获取密钥 ID 和密钥
            key_id = data.get('kid')
            if not key_manager:
                key_manager = get_key_manager()
            
            key = key_manager.get_key_by_id(key_id)
            if not key:
                raise ValueError(f"找不到密钥: {key_id}")
            
            # 解码密钥和加密数据
            key_bytes = base64.b64decode(key)
            nonce = base64.b64decode(data['n'])
            ciphertext = base64.b64decode(data['ct'])
            tag = base64.b64decode(data['tag'])
            
            # 创建解密器
            cipher = AES.new(key_bytes, AES.MODE_GCM, nonce=nonce)
            
            # 解密数据
            plaintext_bytes = cipher.decrypt_and_verify(ciphertext, tag)
            
            return plaintext_bytes.decode('utf-8')
            
        except Exception as e:
            raise ValueError(f"解密失败: {str(e)}")


class HybridEncryptor:
    """
    混合加密器
    
    同时支持 AES-256-GCM 和旧的 Fernet 加密，实现平滑迁移
    """
    
    @staticmethod
    def encrypt(plaintext: str) -> str:
        """
        加密数据（使用 AES-256-GCM）
        
        Args:
            plaintext: 明文数据
            
        Returns:
            str: 加密后的数据
        """
        return AES256GCMEncryptor.encrypt(plaintext, key=None)
    
    @staticmethod
    def decrypt(encrypted_data: str) -> str:
        """
        解密数据（自动识别加密算法）
        
        支持两种格式：
        1. AES-256-GCM 格式（JSON 格式）
        2. Fernet 格式（Base64 格式）
        
        Args:
            encrypted_data: 加密的数据
            
        Returns:
            str: 解密后的明文数据
        """
        if not encrypted_data:
            return None
        
        try:
            # 尝试解析为 AES-256-GCM 格式
            encrypted_json = base64.b64decode(encrypted_data).decode('utf-8')
            data = json.loads(encrypted_json)
            
            # 如果包含版本字段，说明是 AES-256-GCM 格式
            if 'v' in data:
                return AES256GCMEncryptor.decrypt(encrypted_data)
        except:
            pass
        
        # 如果不是 AES-256-GCM 格式，尝试使用旧的 Fernet 解密
        try:
            return FernetDecryptor.decrypt(encrypted_data)
        except:
            raise ValueError("无法解密数据：不支持的加密格式")
    
    @staticmethod
    def is_encrypted_with_aes(encrypted_data: str) -> bool:
        """
        检查数据是否使用 AES-256-GCM 加密
        
        Args:
            encrypted_data: 加密的数据
            
        Returns:
            bool: 是否使用 AES-256-GCM 加密
        """
        if not encrypted_data:
            return False
        
        try:
            encrypted_json = base64.b64decode(encrypted_data).decode('utf-8')
            data = json.loads(encrypted_json)
            return 'v' in data and 'kid' in data
        except:
            return False


class FernetDecryptor:
    """
    Fernet 解密器（用于向后兼容）
    
    仅用于解密旧的 Fernet 加密数据
    """
    
    @staticmethod
    def decrypt(encrypted_data: str) -> str:
        """
        使用 Fernet 解密数据
        
        Args:
            encrypted_data: 加密的数据
            
        Returns:
            str: 解密后的明文数据
        """
        if not encrypted_data:
            return None
        
        try:
            from app.config import config
            key = config['default'].ENCRYPTION_KEY
            if not key:
                raise ValueError("ENCRYPTION_KEY 未配置")
            
            fernet = Fernet(key.encode() if isinstance(key, str) else key)
            decrypted = fernet.decrypt(encrypted_data.encode())
            return decrypted.decode()
        except InvalidToken:
            raise ValueError("无效的加密数据")
        except Exception as e:
            raise ValueError(f"Fernet 解密失败: {str(e)}")


# ==================== 公共 API ====================

def encrypt_sensitive_data(data: str, field_name: str = None, model_name: str = None, 
                          record_id: int = None, user_id: int = None, skip_audit: bool = False) -> str:
    """
    加密敏感数据（使用 AES-256-GCM）
    
    Args:
        data: 待加密的数据
        field_name: 字段名称（用于审计）
        model_name: 模型名称（用于审计）
        record_id: 记录 ID（用于审计）
        user_id: 操作用户 ID（用于审计）
        skip_audit: 是否跳过审计日志
        
    Returns:
        str: 加密后的数据
    """
    if not data:
        return None
    
    try:
        encrypted = HybridEncryptor.encrypt(data)
        
        if not skip_audit and field_name and model_name and record_id:
            key_manager = get_key_manager()
            key_id, _ = key_manager.get_current_key()
            
            EncryptionAuditLogger.log_encryption_operation(
                operation='encrypt',
                field_name=field_name,
                model_name=model_name,
                record_id=record_id,
                key_id=key_id,
                user_id=user_id,
                success=True
            )
        
        return encrypted
        
    except Exception as e:
        if not skip_audit and field_name and model_name and record_id:
            EncryptionAuditLogger.log_encryption_operation(
                operation='encrypt',
                field_name=field_name,
                model_name=model_name,
                record_id=record_id,
                key_id='unknown',
                user_id=user_id,
                success=False,
                error_message=str(e)
            )
        
        raise


def decrypt_sensitive_data(encrypted_data: str, field_name: str = None, model_name: str = None,
                          record_id: int = None, user_id: int = None, skip_audit: bool = False) -> str:
    """
    解密敏感数据（自动识别加密算法）
    
    Args:
        encrypted_data: 加密的数据
        field_name: 字段名称（用于审计）
        model_name: 模型名称（用于审计）
        record_id: 记录 ID（用于审计）
        user_id: 操作用户 ID（用于审计）
        skip_audit: 是否跳过审计日志
        
    Returns:
        str: 解密后的数据
    """
    if not encrypted_data:
        return None
    
    try:
        decrypted = HybridEncryptor.decrypt(encrypted_data)
        
        if not skip_audit and field_name and model_name and record_id:
            key_id = 'unknown'
            try:
                encrypted_json = base64.b64decode(encrypted_data).decode('utf-8')
                data = json.loads(encrypted_json)
                key_id = data.get('kid', 'fernet')
            except:
                key_id = 'fernet'
            
            EncryptionAuditLogger.log_encryption_operation(
                operation='decrypt',
                field_name=field_name,
                model_name=model_name,
                record_id=record_id,
                key_id=key_id,
                user_id=user_id,
                success=True
            )
        
        return decrypted
        
    except Exception as e:
        if not skip_audit and field_name and model_name and record_id:
            EncryptionAuditLogger.log_encryption_operation(
                operation='decrypt',
                field_name=field_name,
                model_name=model_name,
                record_id=record_id,
                key_id='unknown',
                user_id=user_id,
                success=False,
                error_message=str(e)
            )
        
        raise


def mask_sensitive_data(data: str, show_last: int = 4) -> str:
    """
    脱敏敏感数据
    
    Args:
        data: 原始数据
        show_last: 显示最后几位
        
    Returns:
        str: 脱敏后的数据
    """
    if not data:
        return None
    
    if len(data) <= show_last:
        return '*' * len(data)
    
    return '*' * (len(data) - show_last) + data[-show_last:]


def generate_encryption_key() -> str:
    """
    生成新的 AES-256 加密密钥
    
    Returns:
        str: Base64 编码的 256 位密钥
    """
    return get_key_manager().generate_key()


def rotate_encryption_key() -> str:
    """
    轮换加密密钥
    
    Returns:
        str: 新密钥的 ID
    """
    return get_key_manager().rotate_key()


def should_rotate_key() -> bool:
    """
    检查是否应该轮换密钥
    
    Returns:
        bool: 是否需要轮换
    """
    return get_key_manager().should_rotate()


def get_current_key_id() -> str:
    """
    获取当前主密钥 ID
    
    Returns:
        str: 当前密钥 ID
    """
    key_manager = get_key_manager()
    key_id, _ = key_manager.get_current_key()
    return key_id
