"""
安全模块：API密钥加密存储
使用机器绑定的密钥进行轻量级加密
"""
import os
import platform
import hashlib
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class SecurityManager:
    def __init__(self):
        self._cipher = None
        self._init_cipher()
    
    def _get_machine_key(self) -> bytes:
        """生成基于机器信息的密钥"""
        # 收集机器特征信息
        machine_info = []
        
        try:
            # 用户名
            machine_info.append(os.getenv('USERNAME', os.getenv('USER', 'unknown')))
            
            # 计算机名
            machine_info.append(platform.node())
            
            # 系统信息
            machine_info.append(platform.system())
            machine_info.append(platform.machine())
            
            # 组合信息
            combined = '|'.join(machine_info).encode('utf-8')
            
            # 生成固定的salt（基于机器信息）
            salt = hashlib.sha256(combined).digest()[:16]
            
            # 使用PBKDF2生成密钥
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(combined))
            
            logger.info("机器密钥生成成功")
            return key
            
        except Exception as e:
            logger.warning(f"生成机器密钥失败，使用默认密钥: {e}")
            # fallback到固定密钥
            return base64.urlsafe_b64encode(b'dify_chatflow_batch_default_key_32')
    
    def _init_cipher(self):
        """初始化加密器"""
        try:
            key = self._get_machine_key()
            self._cipher = Fernet(key)
            logger.info("加密器初始化成功")
        except Exception as e:
            logger.error(f"加密器初始化失败: {e}")
            raise
    
    def encrypt_api_key(self, api_key: Optional[str]) -> str:
        """加密API密钥"""
        if not api_key:
            return ""
        
        try:
            if not self._cipher:
                raise ValueError("加密器未初始化")
            encrypted = self._cipher.encrypt(api_key.encode('utf-8'))
            return base64.urlsafe_b64encode(encrypted).decode('utf-8')
        except Exception as e:
            logger.error(f"API密钥加密失败: {e}")
            raise ValueError("API密钥加密失败")
    
    def decrypt_api_key(self, encrypted_key: Optional[str]) -> str:
        """解密API密钥"""
        if not encrypted_key:
            return ""
        
        try:
            if not self._cipher:
                raise ValueError("加密器未初始化")
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_key.encode('utf-8'))
            decrypted = self._cipher.decrypt(encrypted_bytes)
            return decrypted.decode('utf-8')
        except Exception as e:
            logger.error(f"API密钥解密失败: {e}")
            raise ValueError("API密钥解密失败，可能是密钥损坏或机器环境变化")
    
    def mask_api_key(self, api_key: Optional[str], show_chars: int = 4) -> str:
        """遮蔽API密钥用于显示"""
        if not api_key:
            return ""
        
        if len(api_key) <= show_chars * 2:
            return "*" * len(api_key)
        
        return api_key[:show_chars] + "*" * (len(api_key) - show_chars * 2) + api_key[-show_chars:]

# 全局安全管理器实例
security = SecurityManager()