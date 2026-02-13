import time
from typing import Dict, Optional
from aiogram import BaseMiddleware, types
from aiogram.types import Message, CallbackQuery, InlineQuery

class CooldownMiddleware(BaseMiddleware):
    """Middleware to handle cooldowns for commands and inline queries"""
    
    def __init__(self):
        self.pm_cooldown: Dict[int, float] = {}  # Private message cooldowns
        self.inline_cooldown: Dict[int, float] = {}  # Inline query cooldowns
        self.pm_cooldown_time = 5.0  # 5 seconds for PM
        self.inline_cooldown_time = 0.7  # 0.7 seconds for inline
        
    async def __call__(self, handler, event, data):
        current_time = time.time()
        user_id = None
        
        if isinstance(event, Message):
            user_id = event.from_user.id
            
            # Only apply cooldown to private messages with commands
            if event.chat.type == "private" and event.text and event.text.startswith('/'):
                last_command_time = self.pm_cooldown.get(user_id, 0)
                
                if current_time - last_command_time < self.pm_cooldown_time:
                    remaining = round(self.pm_cooldown_time - (current_time - last_command_time), 1)
                    try:
                        await event.answer(f"⏰ Please wait {remaining} seconds before using another command.")
                    except:
                        pass  # If we can't send a message, just ignore
                    return  # Stop processing this event
                
                # Update last command time
                self.pm_cooldown[user_id] = current_time
                
        elif isinstance(event, InlineQuery):
            user_id = event.from_user.id
            
            # Check inline cooldown
            last_inline_time = self.inline_cooldown.get(user_id, 0)
            
            if current_time - last_inline_time < self.inline_cooldown_time:
                return  # Silently ignore rapid inline queries
            
            # Update last inline time
            self.inline_cooldown[user_id] = current_time
            
        elif isinstance(event, CallbackQuery):
            user_id = event.from_user.id
            # Callback queries are typically fast, no cooldown needed
            
        # Continue with the handler if cooldown check passed
        return await handler(event, data)