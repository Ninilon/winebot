import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aiogram import Router, types, F, Bot
from aiogram.filters import Command
from utils.user_logger import user_logger
from utils.language_manager import language_manager

router = Router()
ADMIN_ID = 8509052775  # Admin ID

@router.message(F.chat.type == "private", ~F.text.startswith('/'))
async def feedback_handler(message: types.Message, bot: Bot):
    """Handle feedback messages - ignores commands, only processes regular messages"""
    
    # Ignore admins (they don't need feedback forwarding)
    if message.from_user.id == ADMIN_ID:
        return
    
    # Check if user is banned
    if user_logger.is_user_banned(message.from_user.id):
        return
    
    # Prepare message content
    message_content = message.text or message.caption or "[Media/Sticker/Voice]"
    
    # Prepare user info
    user_info = f"@{message.from_user.username}" if message.from_user.username else f"ID: {message.from_user.id}"
    
    try:
        # Forward to admin
        await bot.send_message(
            ADMIN_ID,
            f"📩 {language_manager.get_text('message', message.from_user.id, bold=lambda x: f'<b>{x}</b>')}!\n"
            f"From: {user_info} (ID: <code>{message.from_user.id}</code>)\n\n"
            f"{message_content}",
            parse_mode="HTML"
        )
        
        # Send confirmation to user
        confirmation_text = language_manager.get_text('message_delivered', message.from_user.id)
        await message.answer(confirmation_text)
        
    except Exception as e:
        print(f"Error sending feedback: {e}")
        # Optionally notify user about the error
        error_text = language_manager.get_text('error', message.from_user.id)
        await message.answer(error_text)
