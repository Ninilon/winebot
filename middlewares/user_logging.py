import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aiogram import BaseMiddleware, types
from aiogram.types import Message, CallbackQuery, InlineQuery
from utils.user_logger import user_logger

class UserLoggingMiddleware(BaseMiddleware):
    """Middleware to log all user interactions and check bans"""
    
    async def __call__(self, handler, event, data):
        # Extract user info from different event types
        if isinstance(event, Message):
            user = event.from_user
            command = None
            message_text = event.text or event.caption
            
            # Extract command if present
            if message_text and message_text.startswith('/'):
                command = message_text.split()[0]
            
            # Log the interaction
            user_logger.log_user_interaction(
                user_id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name,
                command=command,
                message_text=message_text,
                chat_type=event.chat.type
            )
            
            # Check if user is banned
            if user_logger.is_user_banned(user.id):
                # Silently ignore banned users
                return
                
        elif isinstance(event, CallbackQuery):
            user = event.from_user
            user_logger.log_user_interaction(
                user_id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name,
                command="callback",
                message_text=event.data,
                chat_type="callback"
            )
            
            # Check if user is banned
            if user_logger.is_user_banned(user.id):
                # Answer the callback but don't process further
                await event.answer("You are banned", show_alert=True)
                return
                
        elif isinstance(event, InlineQuery):
            user = event.from_user
            user_logger.log_user_interaction(
                user_id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name,
                command="inline",
                message_text=event.query,
                chat_type="inline"
            )
            
            # Check if user is banned
            if user_logger.is_user_banned(user.id):
                return
        
        # Continue with the handler if not banned
        return await handler(event, data)