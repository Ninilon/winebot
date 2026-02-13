import uuid
import time
import aiohttp
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aiogram import Router, types, F
from aiogram.filters import Command, CommandObject
from aiogram import html
from utils.language_manager import language_manager

router = Router()

@router.message(Command("status"))
async def cmd_status(message: types.Message, command: CommandObject):
    if not command.args:
        error_text = language_manager.get_text('error', message.from_user.id)
        return await message.answer(f"⚠️ {error_text}: Please provide domain, e.g.: `/status google.com`", parse_mode="Markdown")

    url = command.args.strip()
    if not url.startswith(('http://', 'https://')):
        url = f'http://{url}'

    checking_text = language_manager.get_text('status_checking', message.from_user.id)
    sent_message = await message.answer(f"{checking_text} {html.bold(url)}...")
    
    start_time = time.monotonic()
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as response:
                # Calculate response time in ms
                ping_ms = round((time.monotonic() - start_time) * 1000)
                
                status_code = response.status
                server = response.headers.get('Server', 'Unknown')
                
                # Choose emoji based on response code
                icon = "✅" if response.ok else "⚠️"
                
                result_text = language_manager.get_text('success', message.from_user.id)
                text = (
                    f"{icon} {html.bold('Check Result:')}\n"
                    f"{'─' * 20}\n"
                    f"🌐 {html.bold('URL:')} {url}\n"
                    f"📊 {html.bold('Status:')} {status_code}\n"
                    f"⚡ {html.bold('Ping:')} {ping_ms} ms\n"
                    f"🖥 {html.bold('Server:')} {server}"
                )
                
    except Exception as e:
        error_title = language_manager.get_text('error', message.from_user.id)
        text = (
            f"❌ {html.bold(error_title)}\n"
            f"{'─' * 20}\n"
            f"🌐 {html.bold('URL:')} {url}\n"
            f"🛠 {html.bold('Reason:')} {type(e).__name__}"
        )

    await sent_message.edit_text(text, parse_mode="HTML")

@router.inline_query(F.query.startswith("st "))
async def inline_status(inline_query: types.InlineQuery):
    url = inline_query.query[3:].strip()
    if not url:
        return

    if not url.startswith(('http://', 'https://')):
        url = f'http://{url}'

    start_time = time.monotonic()
    try:
        # Fast timeout to prevent inline from hanging (3 seconds)
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=3) as response:
                ping_ms = round((time.monotonic() - start_time) * 1000)
                status_code = response.status
                icon = "✅" if response.ok else "⚠️"
                
                res_text = (
                    f"{icon} {html.bold('Website Status:')}\n"
                    f"🌐 {url}\n"
                    f"📊 Code: {status_code} | ⚡ {ping_ms} ms"
                )
    except Exception as e:
        error_text = language_manager.get_text('error', inline_query.from_user.id)
        res_text = f"❌ {html.bold(error_text)}: {url}\n🛠 {type(e).__name__}"

    # Format result
    results = [
        types.InlineQueryResultArticle(
            id=str(uuid.uuid4()),
            title=f"Check: {url}",
            description="Click to send check result",
            input_message_content=types.InputTextMessageContent(
                message_text=res_text,
                parse_mode="HTML"
            )
        )
    ]
    
    await inline_query.answer(results, is_personal=True, cache_time=10)
