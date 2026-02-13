import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aiogram import Router, types, F, html
from aiogram.filters import Command, CommandObject
from aiogram.types import CallbackQuery
from utils.user_logger import user_logger
from utils.language_manager import language_manager

router = Router()
ADMIN_ID = 8509052775  # Admin ID - you can change this

@router.message(Command("ban"), F.from_user.id == ADMIN_ID)
async def cmd_ban(message: types.Message, command: CommandObject):
    """Ban a user by ID or username"""
    if not command.args:
        await message.answer(
            f"❌ {html.bold('Usage:')} /ban <user_id or @username> [reason]\n"
            f"Example: /ban 12345 Spam\n"
            f"Example: /ban @username Inappropriate behavior"
        )
        return
    
    parts = command.args.split(maxsplit=1)
    target = parts[0]
    reason = parts[1] if len(parts) > 1 else "No reason provided"
    
    # Handle different input formats
    user_id = None
    username = None
    
    if target.startswith('@'):
        username = target[1:]
        # Try to find user ID from logs (this is a simplified approach)
        # In production, you'd want a better way to map usernames to IDs
        await message.answer(f"⚠️ Username banning requires user ID. Please use /ban <user_id> instead.")
        return
    elif target.isdigit():
        user_id = int(target)
    else:
        await message.answer("❌ Invalid format. Use user ID (numbers) or @username")
        return
    
    # Get user info for logging
    try:
        # Try to get user info if we have the user ID
        if user_id:
            try:
                user_info = await message.bot.get_chat(user_id)
                username = user_info.username
                display_name = f"@{username}" if username else f"ID: {user_id}"
            except:
                display_name = f"ID: {user_id}"
        else:
            display_name = target
        
        # Ban the user
        user_logger.ban_user(user_id, str(message.from_user.id), reason)
        
        await message.answer(
            f"🚫 {html.bold('User Banned')}\n"
            f"User: {display_name}\n"
            f"Reason: {reason}\n"
            f"Banned by: Admin"
        )
        
    except Exception as e:
        await message.answer(f"❌ Error banning user: {str(e)}")

@router.message(Command("unban"), F.from_user.id == ADMIN_ID)
async def cmd_unban(message: types.Message, command: CommandObject):
    """Unban a user by ID"""
    if not command.args or not command.args.isdigit():
        await message.answer(f"❌ {html.bold('Usage:')} /unban <user_id>\nExample: /unban 12345")
        return
    
    user_id = int(command.args)
    
    # Unban the user
    user_logger.unban_user(user_id)
    
    await message.answer(
        f"✅ {html.bold('User Unbanned')}\n"
        f"User ID: {user_id}\n"
        f"Unbanned by: Admin"
    )

@router.message(Command("banned"), F.from_user.id == ADMIN_ID)
async def cmd_banned_list(message: types.Message):
    """Show list of banned users"""
    banned_users = user_logger.get_banned_users()
    
    if not banned_users:
        await message.answer("📋 No banned users found.")
        return
    
    text = f"🚫 {html.bold('Banned Users')} ({len(banned_users)}):\n"
    text += "─" * 30 + "\n"
    
    for user_id, username, banned_by, ban_reason, timestamp in banned_users:
        display_name = f"@{username}" if username else f"ID: {user_id}"
        text += f"👤 {display_name}\n"
        text += f"📝 Reason: {ban_reason or 'No reason'}\n"
        text += f"🔨 Banned by: {banned_by}\n"
        text += f"📅 Date: {timestamp}\n"
        text += "─" * 20 + "\n"
    
    await message.answer(text, parse_mode="HTML")

@router.message(Command("userinfo"), F.from_user.id == ADMIN_ID)
async def cmd_userinfo(message: types.Message, command: CommandObject):
    """Get user information"""
    if not command.args:
        await message.answer(f"❌ {html.bold('Usage:')} /userinfo <user_id>\nExample: /userinfo 12345")
        return
    
    if not command.args.isdigit():
        await message.answer("❌ User ID must be a number")
        return
    
    user_id = int(command.args)
    
    try:
        # Get user info from Telegram
        user_info = await message.bot.get_chat(user_id)
        
        # Get additional info from our database
        is_banned = user_logger.is_user_banned(user_id)
        language = user_logger.get_user_language(user_id)
        
        text = f"👤 {html.bold('User Information')}\n"
        text += "─" * 25 + "\n"
        text += f"🆔 ID: <code>{user_id}</code>\n"
        text += f"👤 First Name: {user_info.first_name or 'N/A'}\n"
        text += f"👥 Last Name: {user_info.last_name or 'N/A'}\n"
        text += f"🏷️ Username: @{user_info.username or 'N/A'}\n"
        text += f"🌐 Language: {language.upper()}\n"
        text += f"🚫 Status: {'BANNED' if is_banned else 'Active'}\n"
        
        await message.answer(text, parse_mode="HTML")
        
    except Exception as e:
        await message.answer(f"❌ Error getting user info: {str(e)}")

# Admin panel callback handler
@router.callback_query(F.data.startswith("admin_"), F.from_user.id == ADMIN_ID)
async def handle_admin_callbacks(callback: CallbackQuery):
    """Handle admin panel callbacks"""
    action = callback.data.replace("admin_", "")
    
    if action == "banned_list":
        await cmd_banned_list(callback.message)
    elif action == "unban_user":
        # This would need a user_id parameter
        await callback.answer("Unban functionality requires user ID")
    
    await callback.answer()