import os
from cryptography.fernet import Fernet
from typing import Optional
import logging
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config_reader import config

logger = logging.getLogger(__name__)

class CryptoManager:
    def __init__(self):
        encryption_key = config.db_encryption_key
        if not encryption_key:
            logger.warning("DB_ENCRYPTION_KEY not set. Using insecure mode!")
            self.cipher = None
        else:
            try:
                self.cipher = Fernet(encryption_key)
            except Exception as e:
                logger.error(f"Failed to initialize encryption: {e}")
                self.cipher = None
    
    def encrypt(self, plaintext: str) -> str:
        if not plaintext:
            return ""
        if not self.cipher:
            return plaintext
        try:
            return self.cipher.encrypt(plaintext.encode()).decode()
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            return plaintext
    
    def decrypt(self, ciphertext: str) -> Optional[str]:
        if not ciphertext:
            return None
        if not self.cipher:
            return ciphertext
        try:
            return self.cipher.decrypt(ciphertext.encode()).decode()
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            return None

crypto_manager = CryptoManager()
