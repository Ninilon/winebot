import sqlite3
import logging
from datetime import datetime
from typing import Optional

class UserLogger:
    def __init__(self, db_path: str = "users.db"):
        self.db_path = db_path
        self.init_database()
        self.logger = logging.getLogger("user_logger")
        
    def init_database(self):
        """Initialize the user logging database"""
        db = sqlite3.connect(self.db_path)
        cur = db.cursor()
        
        # Create users table for logging all interactions
        cur.execute("""
            CREATE TABLE IF NOT EXISTS user_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                command TEXT,
                message_text TEXT,
                chat_type TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create banned users table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS banned_users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                banned_by TEXT,
                ban_reason TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create user settings table for language preferences
        cur.execute("""
            CREATE TABLE IF NOT EXISTS user_settings (
                user_id INTEGER PRIMARY KEY,
                language TEXT DEFAULT 'en',
                timezone TEXT DEFAULT 'UTC',
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        db.commit()
        db.close()
    
    def log_user_interaction(self, user_id: int, username: Optional[str], 
                            first_name: Optional[str], last_name: Optional[str],
                            command: Optional[str] = None, message_text: Optional[str] = None,
                            chat_type: Optional[str] = None):
        """Log user interaction to database"""
        try:
            db = sqlite3.connect(self.db_path)
            cur = db.cursor()
            
            cur.execute("""
                INSERT INTO user_logs 
                (user_id, username, first_name, last_name, command, message_text, chat_type)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (user_id, username, first_name, last_name, command, message_text, chat_type))
            
            db.commit()
            db.close()
            
            # Also log to file for easy access
            self.logger.info(f"User {username} (ID: {user_id}) - Command: {command} - Message: {message_text}")
            
        except Exception as e:
            self.logger.error(f"Failed to log user interaction: {e}")
    
    def ban_user(self, user_id: int, banned_by: str, reason: Optional[str] = None):
        """Ban a user"""
        try:
            db = sqlite3.connect(self.db_path)
            cur = db.cursor()
            
            # Get user info first
            cur.execute("SELECT username FROM user_logs WHERE user_id = ? ORDER BY timestamp DESC LIMIT 1", (user_id,))
            user_data = cur.fetchone()
            username = user_data[0] if user_data else "Unknown"
            
            cur.execute("""
                INSERT OR REPLACE INTO banned_users 
                (user_id, username, banned_by, ban_reason)
                VALUES (?, ?, ?, ?)
            """, (user_id, username, banned_by, reason))
            
            db.commit()
            db.close()
            
            self.logger.info(f"User {username} (ID: {user_id}) banned by {banned_by}. Reason: {reason}")
            
        except Exception as e:
            self.logger.error(f"Failed to ban user: {e}")
    
    def unban_user(self, user_id: int):
        """Unban a user"""
        try:
            db = sqlite3.connect(self.db_path)
            cur = db.cursor()
            
            cur.execute("DELETE FROM banned_users WHERE user_id = ?", (user_id,))
            
            db.commit()
            db.close()
            
            self.logger.info(f"User ID {user_id} unbanned")
            
        except Exception as e:
            self.logger.error(f"Failed to unban user: {e}")
    
    def is_user_banned(self, user_id: int) -> bool:
        """Check if user is banned"""
        try:
            db = sqlite3.connect(self.db_path)
            cur = db.cursor()
            
            cur.execute("SELECT 1 FROM banned_users WHERE user_id = ?", (user_id,))
            result = cur.fetchone()
            
            db.close()
            return result is not None
            
        except Exception as e:
            self.logger.error(f"Failed to check ban status: {e}")
            return False
    
    def get_banned_users(self) -> list:
        """Get list of all banned users"""
        try:
            db = sqlite3.connect(self.db_path)
            cur = db.cursor()
            
            cur.execute("""
                SELECT user_id, username, banned_by, ban_reason, timestamp 
                FROM banned_users 
                ORDER BY timestamp DESC
            """)
            results = cur.fetchall()
            
            db.close()
            return results
            
        except Exception as e:
            self.logger.error(f"Failed to get banned users: {e}")
            return []
    
    def set_user_language(self, user_id: int, language: str):
        """Set user language preference"""
        try:
            db = sqlite3.connect(self.db_path)
            cur = db.cursor()
            
            cur.execute("""
                INSERT OR REPLACE INTO user_settings (user_id, language, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            """, (user_id, language))
            
            db.commit()
            db.close()
            
        except Exception as e:
            self.logger.error(f"Failed to set user language: {e}")
    
    def get_user_language(self, user_id: int) -> str:
        """Get user language preference"""
        try:
            db = sqlite3.connect(self.db_path)
            cur = db.cursor()
            
            cur.execute("SELECT language FROM user_settings WHERE user_id = ?", (user_id,))
            result = cur.fetchone()
            
            db.close()
            return result[0] if result else "en"
            
        except Exception as e:
            self.logger.error(f"Failed to get user language: {e}")
            return "en"

# Global instance
user_logger = UserLogger()