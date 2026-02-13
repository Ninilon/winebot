import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import aiohttp
import uuid
from aiogram import Router, types, html, F
from aiogram.filters import Command, CommandObject
from utils.language_manager import language_manager

router = Router()

@router.message(Command("short"))
async def cmd_short(message: types.Message, command: CommandObject):
    if not command.args:
        error_text = language_manager.get_text('error', message.from_user.id)
        return await message.answer(
            f"🔗 {error_text}: Usage: `/short https://example.com/very/long/url`",
            parse_mode="HTML"
        )
    
    url = command.args.strip()
    
    if not url.startswith(('http://', 'https://')):
        error_text = language_manager.get_text('error', message.from_user.id)
        return await message.answer(
            f"🔗 {error_text}: Please provide a valid URL starting with http:// or https://",
            parse_mode="HTML"
        )
    
    checking_text = language_manager.get_text('url_short', message.from_user.id)
    sent_message = await message.answer(f"🔗 {checking_text}...")
    
    try:
        tinyurl_api = f"https://tinyurl.com/api-create.php?url={url}"
        async with aiohttp.ClientSession() as session:
            async with session.get(tinyurl_api, timeout=10) as response:
                if response.status == 200:
                    short_url = (await response.text()).strip()
                    if short_url and short_url.startswith('http'):
                        short_text = language_manager.get_text('url_short', message.from_user.id)
                        text = (
                            f"🔗 {html.bold('Shortened URL:')}\n"
                            f"{'─' * 20}\n"
                            f"{html.bold('Short:')}\n{short_url}\n\n"
                            f"{html.bold('Original:')}\n{url[:100]}" + ('...' if len(url) > 100 else '')
                        )
                        await sent_message.edit_text(text, parse_mode="HTML")
                    else:
                        error_text = language_manager.get_text('error', message.from_user.id)
                        await sent_message.edit_text(f"❌ {error_text}: Invalid response from TinyURL")
                else:
                    error_text = language_manager.get_text('error', message.from_user.id)
                    await sent_message.edit_text(f"❌ {error_text}: TinyURL API error")
    except aiohttp.ClientError:
        error_text = language_manager.get_text('error', message.from_user.id)
        await sent_message.edit_text(f"❌ {error_text}: Network error")
    except Exception as e:
        error_text = language_manager.get_text('error', message.from_user.id)
        await sent_message.edit_text(f"❌ {error_text}: {type(e).__name__}")

@router.inline_query(F.query.startswith("short "))
async def inline_short(inline_query: types.InlineQuery):
    url = inline_query.query[6:].strip()
    if not url:
        return
    
    if not url.startswith(('http://', 'https://')):
        return
    
    try:
        tinyurl_api = f"https://tinyurl.com/api-create.php?url={url}"
        async with aiohttp.ClientSession() as session:
            async with session.get(tinyurl_api, timeout=3) as response:
                if response.status == 200:
                    short_url = (await response.text()).strip()
                    if short_url and short_url.startswith('http'):
                        result_text = (
                            f"🔗 {html.bold('Shortened:')}\n"
                            f"Short: {short_url}\n"
                            f"Original: {url[:80]}" + ('...' if len(url) > 80 else '')
                        )
                        
                        results = [
                            types.InlineQueryResultArticle(
                                id=str(uuid.uuid4()),
                                title=f"Short: {url[:50]}",
                                description=f"→ {short_url}",
                                input_message_content=types.InputTextMessageContent(
                                    message_text=result_text,
                                    parse_mode="HTML"
                                )
                            )
                        ]
                        
                        await inline_query.answer(results, is_personal=True, cache_time=300)
    except Exception:
        pass
