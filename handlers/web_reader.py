import aiohttp
from bs4 import BeautifulSoup
from aiogram import Router, types, html
from aiogram.filters import Command, CommandObject
from yarl import URL

router = Router()

async def fetch_site_text(user_url: str):
    # 1. Принудительно чиним протокол
    if not user_url.startswith(('http://', 'https://')):
        user_url = 'https://' + user_url

    try:
        # 2. yarl.URL(user_url) — МАГИЯ ТУТ. Она берет всё: домен, путь, параметры (?q=...)
        target_url = URL(user_url, encoded=False) 
        
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
        }

        async with aiohttp.ClientSession(headers=headers) as session:
            # allow_redirects=True — чтобы он шел по всем пересылкам страницы
            async with session.get(target_url, timeout=15, allow_redirects=True) as response:
                if response.status != 200:
                    return f"Ошибка сервера: {response.status}"
                
                # Читаем содержимое
                html_content = await response.text()

        soup = BeautifulSoup(html_content, 'html.parser')

        # Вычищаем мусор (скрипты, стили, формы)
        for s in soup(["script", "style", "nav", "footer", "header", "aside", "form", "button"]):
            s.decompose()

        # Вытаскиваем текст с сохранением переносов
        text = soup.get_text(separator='\n')
        clean_text = "\n".join([line.strip() for line in text.splitlines() if line.strip()])

        if not clean_text:
            return "Сайт открылся, но текста на странице не найдено."

        return clean_text[:3800] # Лимит сообщения ТГ

    except Exception as e:
        return f"Не удалось прочитать {user_url}\nОшибка: {type(e).__name__}"

@router.message(Command("getweb"))
async def cmd_getweb(message: types.Message, command: CommandObject):
    # command.args в aiogram 3 забирает ВООБЩЕ ВСЁ после пробела
    url_str = command.args

    if not url_str:
        return await message.answer("Введи полную ссылку: <code>/getweb ://site.com</code>", parse_mode="HTML")

    wait_msg = await message.answer(f"🔎 Запрашиваю: <code>{html.quote(url_str)}</code>...", parse_mode="HTML")
    
    result = await fetch_site_text(url_str.strip())

    # Выводим результат (экран обязательно, чтобы ТГ не ругался на спецсимволы в тексте сайта)
    await wait_msg.edit_text(f"📄 <b>Текст страницы:</b>\n\n{html.quote(result)}", parse_mode="HTML")
