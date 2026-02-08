from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
import base64
import os
from typing import Optional


class TokenEncryption:
    """Token 加密工具类"""
    
    def __init__(self, key: Optional[str] = None):
        """
        初始化加密器
        
        Args:
            key: Base64 编码的 32 字节密钥，如果为 None 则生成新密钥
        """
        if key:
            # 使用提供的密钥
            self._key = key.encode() if isinstance(key, str) else key
        else:
            # 生成新密钥
            self._key = Fernet.generate_key()
        
        self._fernet = Fernet(self._key)
    
    @classmethod
    def generate_key(cls) -> str:
        """生成新的加密密钥"""
        return Fernet.generate_key().decode()
    
    @classmethod
    def from_password(cls, password: str, salt: Optional[bytes] = None) -> tuple:
        """
        从密码生成密钥
        
        Returns:
            (TokenEncryption 实例, salt)
        """
        if salt is None:
            salt = os.urandom(16)
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=480000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return cls(key.decode()), salt
    
    def encrypt(self, data: str) -> str:
        """加密字符串数据"""
        if not data:
            return ""
        return self._fernet.encrypt(data.encode()).decode()
    
    def decrypt(self, encrypted_data: str) -> str:
        """解密字符串数据"""
        if not encrypted_data:
            return ""
        try:
            return self._fernet.decrypt(encrypted_data.encode()).decode()
        except Exception:
            return ""
    
    def encrypt_dict(self, data: dict) -> str:
        """加密字典数据"""
        import json
        return self.encrypt(json.dumps(data))
    
    def decrypt_dict(self, encrypted_data: str) -> dict:
        """解密字典数据"""
        import json
        try:
            decrypted = self.decrypt(encrypted_data)
            return json.loads(decrypted) if decrypted else {}
        except Exception:
            return {}


# 全局加密实例
def get_encryption() -> TokenEncryption:
    """获取全局加密实例"""
    from app.core.config import get_settings
    settings = get_settings()
    
    key = settings.ENCRYPTION_KEY
    if not key:
        # 如果没有设置加密密钥，使用 SECRET_KEY 生成一个
        key = TokenEncryption.generate_key()
        print("WARNING: ENCRYPTION_KEY not set, using auto-generated key. "
              "Tokens will not persist across restarts.")
    
    return TokenEncryption(key)
