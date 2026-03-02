"""
加密工具模块
提供敏感数据加密和解密功能
"""
from cryptography.fernet import Fernet, InvalidToken
from functools import lru_cache


def get_encryption_key():
    """
    获取加密密钥
    
    Returns:
        bytes: 加密密钥
    """
    from app.config import config
    
    # 从配置中获取加密密钥
    key = config['default'].ENCRYPTION_KEY
    if not key:
        raise ValueError("ENCRYPTION_KEY 未配置，请在环境变量中设置")
    return key.encode() if isinstance(key, str) else key


def get_fernet():
    """
    获取 Fernet 实例
    
    Returns:
        Fernet: Fernet 加密实例
    """
    key = get_encryption_key()
    return Fernet(key)


def encrypt_sensitive_data(data):
    """
    加密敏感数据
    
    Args:
        data: 待加密的数据（字符串）
        
    Returns:
        str: 加密后的数据（Base64编码的字符串）
    """
    if not data:
        return None
    
    try:
        fernet = get_fernet()
        encrypted = fernet.encrypt(data.encode())
        return encrypted.decode()
    except Exception:
        return None


def decrypt_sensitive_data(encrypted_data):
    """
    解密敏感数据
    
    Args:
        encrypted_data: 加密的数据
        
    Returns:
        str: 解密后的数据
    """
    if not encrypted_data:
        return None
    
    try:
        fernet = get_fernet()
        decrypted = fernet.decrypt(encrypted_data.encode())
        return decrypted.decode()
    except InvalidToken:
        return None
    except Exception:
        return None


def mask_sensitive_data(data, show_last=4):
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


def generate_encryption_key():
    """
    生成新的加密密钥
    
    Returns:
        str: Base64编码的密钥
    """
    return Fernet.generate_key().decode()
