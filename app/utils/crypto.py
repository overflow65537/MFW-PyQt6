import os
import platform
from pathlib import Path
from typing import Optional, Union

from cryptography.fernet import Fernet
from cryptography.fernet import InvalidToken

from app.utils.logger import logger

APP_NAME = "MFW-ChainFlow Assistant"


def get_app_support_dir(app_name: str = APP_NAME) -> Path:
    """返回操作系统推荐的应用支持目录，确保目录存在。"""
    sys_name = platform.system()
    if sys_name == "Windows":
        base = Path(os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA") or Path.home() / "AppData" / "Local")
    elif sys_name == "Darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")

    target = base / app_name
    target.mkdir(parents=True, exist_ok=True)
    return target


class CryptoManager:
    """提供密钥加载与数据的加解密能力。"""

    KEY_FILE = get_app_support_dir() / "k.ey"

    def __init__(self) -> None:
        self._fernet: Optional[Fernet] = None

    def ensure_key_exists(self, path: str | Path | None = None) -> bytes:
        """确保密钥文件存在并返回密钥内容。"""
        key_path = Path(path) if path is not None else self.KEY_FILE
        key_path.parent.mkdir(parents=True, exist_ok=True)
        if not key_path.exists():
            logger.debug("生成密钥文件: %s", key_path)
            key = Fernet.generate_key()
            with key_path.open("wb") as key_file:
                key_file.write(key)
            return key
        logger.debug("加载密钥文件成功: %s", key_path)
        return key_path.read_bytes()

    def get_fernet(self, path: str | Path | None = None) -> Fernet:
        """返回用于加密/解密的 Fernet 实例。"""
        if self._fernet is None:
            self._fernet = Fernet(self.ensure_key_exists(path))
        return self._fernet

    def encrypt_payload(self, value: Union[bytes, str]) -> bytes:
        """将字符串或字节数据加密后返回字节串。"""
        if isinstance(value, bytes):
            data = value
        elif isinstance(value, str):
            data = value.encode("utf-8")
        else:
            raise TypeError("Value must be bytes or str")
        return self.get_fernet().encrypt(data)

    def encrypt_text(self, value: Union[bytes, str]) -> str:
        """将字符串加密为可直接写入配置的 utf-8 文本。"""
        encrypted = self.encrypt_payload(value)
        return encrypted.decode("utf-8")

    def decrypt_payload(self, value: Union[bytes, str]) -> bytes:
        """将密文还原为原始字节串。"""
        if isinstance(value, bytes):
            token = value
        elif isinstance(value, str):
            token = value.encode("utf-8")
        else:
            raise TypeError("Value must be bytes or str")
        return self.get_fernet().decrypt(token)

    def decrypt_text(
        self, value: Union[bytes, str], *, fallback_to_plaintext: bool = False
    ) -> str:
        """将密文解密为字符串，必要时兼容旧版明文配置。"""
        try:
            return self.decrypt_payload(value).decode("utf-8")
        except InvalidToken:
            if not fallback_to_plaintext:
                raise
            if isinstance(value, bytes):
                return value.decode("utf-8", errors="ignore")
            return str(value)

    def is_encrypted_text(self, value: Union[bytes, str]) -> bool:
        """判断给定文本是否为当前密钥可解密的 Fernet 密文。"""
        if not value:
            return False
        try:
            self.decrypt_payload(value)
            return True
        except Exception:
            return False


crypto_manager = CryptoManager()
