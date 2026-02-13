import uuid
import psutil
import platform
from datetime import datetime
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aiogram import Router, types, html, F
from aiogram.filters import Command
from utils.language_manager import language_manager

router = Router()
ADMIN_ID = YOUR_TELEGRAM_ID  # Admin ID - change this as needed

def get_server_info():
    """Get server system information"""
    # CPU
    cpu_usage = psutil.cpu_percent(interval=1)
    
    # RAM
    ram = psutil.virtual_memory()
    ram_total = round(ram.total / (1024**3), 1)
    ram_used = round(ram.used / (1024**3), 1)
    
    # Disk
    disk = psutil.disk_usage('/')
    disk_total = round(disk.total / (1024**3), 1)
    disk_free = round(disk.free / (1024**3), 1)
    
    # Uptime
    boot_time = datetime.fromtimestamp(psutil.boot_time())
    uptime = datetime.now() - boot_time
    uptime_str = str(uptime).split('.')[0]  # Remove microseconds
    
    return {
        'cpu_usage': cpu_usage,
        'ram_used': ram_used,
        'ram_total': ram_total,
        'disk_free': disk_free,
        'disk_total': disk_total,
        'uptime': uptime_str,
        'os': f"{platform.system()} {platform.release()}"
    }

@router.message(Command("server"), F.from_user.id == ADMIN_ID)
async def cmd_server(message: types.Message):
    """Admin-only server information command"""
    info = get_server_info()
    
    text = (
        f"🖥 {html.bold(language_manager.get_text('server_info', message.from_user.id))}\n"
        f"{'─' * 20}\n"
        f"⚙️ {html.bold('OS:')} {info['os']}\n"
        f"⌛ {html.bold('Uptime:')} {info['uptime']}\n\n"
        f"💿 {html.bold('CPU:')} {info['cpu_usage']}%\n"
        f"🧠 {html.bold('RAM:')} {info['ram_used']}GB / {info['ram_total']}GB\n"
        f"💾 {html.bold('Disk:')} {info['disk_free']}GB free of {info['disk_total']}GB"
    )
    
    await message.answer(text, parse_mode="HTML")

@router.inline_query(F.query.startswith("sys"), F.from_user.id == ADMIN_ID)
async def inline_server_info(inline_query: types.InlineQuery):
    """Admin-only inline server information"""
    info = get_server_info()

    text = (
        f"🖥 {html.bold(language_manager.get_text('server_info', inline_query.from_user.id))}\n"
        f"{'─' * 20}\n"
        f"⚙️ {html.bold('OS:')} {info['os']}\n"
        f"⌛ {html.bold('Uptime:')} {info['uptime']}\n\n"
        f"💿 {html.bold('CPU:')} {info['cpu_usage']}%\n"
        f"🧠 {html.bold('RAM:')} {info['ram_used']}GB / {info['ram_total']}GB\n"
        f"💾 {html.bold('Disk:')} {info['disk_free']}GB free of {info['disk_total']}GB"
    )

    await inline_query.answer([
        types.InlineQueryResultArticle(
            id=str(uuid.uuid4()),
            title="Show server status",
            description=f"CPU: {info['cpu_usage']}% | RAM: {info['ram_used']}G",
            input_message_content=types.InputTextMessageContent(
                message_text=text,
                parse_mode="HTML"
            )
        )
    ], is_personal=True, cache_time=10)
