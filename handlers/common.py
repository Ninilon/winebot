import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aiogram import Router, types, html, F
from aiogram.filters import Command
from utils.language_manager import language_manager

router = Router()

@router.message(Command("start"), F.chat.type == "private")
async def cmd_start(message: types.Message):
    # Works ONLY in private chat with bot
    text = language_manager.get_text(
        'start', 
        message.from_user.id,
        name=html.bold(message.from_user.first_name or "User")
    )
    await message.answer(text, parse_mode="HTML")

@router.message(Command("help"))
async def cmd_help(message: types.Message):
    bot_info = await message.bot.get_me()
    help_text = language_manager.get_text(
        'help',
        message.from_user.id,
        bold=html.bold,
        italic=html.italic,
        username=bot_info.username
    )
    
    await message.answer(help_text, parse_mode="HTML")
