import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aiogram import Router, types, F, html
from aiogram.filters import Command
from aiogram.types import CallbackQuery
from utils.language_manager import language_manager
from utils.user_logger import user_logger

router = Router()

@router.message(Command("settings"))
async def cmd_settings(message: types.Message):
    """Show settings menu"""
    keyboard = language_manager.get_settings_keyboard(message.from_user.id)
    
    text = language_manager.get_text('settings', message.from_user.id)
    
    await message.answer(
        f"{text}\n\n"
        f"👤 {html.bold('User Info:')}\n"
        f"ID: <code>{message.from_user.id}</code>\n"
        f"Username: @{message.from_user.username or 'N/A'}\n"
        f"Language: {user_logger.get_user_language(message.from_user.id).upper()}",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("settings_"))
async def handle_settings_callback(callback: CallbackQuery):
    """Handle settings callbacks"""
    action = callback.data.replace("settings_", "")
    
    if action == "language":
        # Show language selection
        keyboard = language_manager.get_language_keyboard(callback.from_user.id)
        text = language_manager.get_text('select_language', callback.from_user.id)
        
        await callback.message.edit_text(
            text,
            reply_markup=keyboard
        )
        
    elif action == "back":
        # Go back to main settings
        keyboard = language_manager.get_settings_keyboard(callback.from_user.id)
        text = language_manager.get_text('settings', callback.from_user.id)
        
        await callback.message.edit_text(
            f"{text}\n\n"
            f"👤 {html.bold('User Info:')}\n"
            f"ID: <code>{callback.from_user.id}</code>\n"
            f"Username: @{callback.from_user.username or 'N/A'}\n"
            f"Language: {user_logger.get_user_language(callback.from_user.id).upper()}",
            reply_markup=keyboard,
            parse_mode="HTML"
        )

@router.callback_query(F.data.startswith("lang_"))
async def handle_language_callback(callback: CallbackQuery):
    """Handle language selection"""
    lang_code = callback.data.replace("lang_", "")
    
    if lang_code in ['en', 'ru']:
        # Update user language preference
        user_logger.set_user_language(callback.from_user.id, lang_code)
        
        # Show confirmation
        text = language_manager.get_text('language_updated', callback.from_user.id)
        
        # Get updated keyboard
        keyboard = language_manager.get_language_keyboard(callback.from_user.id)
        
        await callback.answer(text, show_alert=True)
        await callback.message.edit_reply_markup(reply_markup=keyboard)

@router.callback_query(F.data == "settings_back")
async def handle_back_to_main(callback: CallbackQuery):
    """Handle going back to main menu"""
    # This could go back to a main menu if we had one
    await callback.answer("Going back to settings...")