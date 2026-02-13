from typing import Dict, Optional
from .user_logger import user_logger

class LanguageManager:
    def __init__(self):
        self.translations = {
            'en': {
                 'start': "👋 Hello, {name}!\nBot is ready to work. Use /help to see the list of commands.",
                'help': (
                    "🛠 <b>Available commands:</b>\n"
                    "────────────────────\n"
                    "🎵 <b>/yamusic token</b> — Set Yandex Music token\n"
                    "🖼 <b>/qr text</b> — Create QR code\n"
                    "🔗 <b>/short url</b> — Shorten URL\n"
                    "📁 <b>/convert format</b> — Convert files\n"
                    "🌐 <b>/status domain</b> — Check website status\n"
                    "🔍 <b>/whois target</b> — WHOIS information\n"
                    "🔧 <b>/settings</b> — Bot settings\n"
                    "❓ <b>/help</b> — This menu\n\n"
                    "💡 <i>Inline modes (type in any chat):</i>\n"
                    "<code>@{username} ym</code> — Now playing\n"
                    "<code>@{username} qr text</code>\n"
                    "<code>@{username} short url</code>\n"
                    "<code>@{username} st url</code>\n"
                    "<code>@{username} sys</code>\n\n"
                    "Developed by @wineaki\n"
                    "Licensing: GNU GPL v3.0\n"
                ),
                'settings': "⚙️ Settings",
                'language': "🌐 Language",
                'select_language': "Select your preferred language:",
                'language_updated': "✅ Language updated successfully!",
                'banned_message': "You are banned from using this bot.",
                'message_delivered': "Message delivered to administrator.",
                'qr_created': "✅ QR code created successfully!",
                'status_checking': "🔍 Checking website status...",
                'whois_info': "🔍 WHOIS information:",
                'server_info': "🖥 System Monitor",
                 'not_found': "❌ Not found",
                'error': "❌ Error occurred",
                'success': "✅ Success",
                'url_short': "🔗 Shortened URL",
                'convert': "📁 File Conversion",
                'convert_success': "✅ Converted to {format}",
                'convert_too_large': "❌ File exceeds 100MB",
                'convert_unsupported': "❌ Format not supported"
            },
            'ru': {
                'start': "👋 Привет, {name}!\nБот готов к работе. Используй /help, чтобы увидеть список команд.",
                'help': (
                    "🛠 <b>Доступные команды:</b>\n"
                    "────────────────────\n"
                    "🎵 <b>/yamusic токен</b> — Настроить Яндекс.Музыку\n"
                    "🖼 <b>/qr текст</b> — Создать QR-код\n"
                    "🔗 <b>/short url</b> — Сократить URL\n"
                    "📁 <b>/convert формат</b> — Конвертировать файл\n"
                    "🌐 <b>/status домен</b> — Проверить сайт\n"
                    "🔍 <b>/whois цель</b> — WHOIS инфо\n"
                    "🔧 <b>/settings</b> — Настройки бота\n"
                    "❓ <b>/help</b> — Это меню\n\n"
                    "💡 <i>Inline режимы (вводи в любом чате):</i>\n"
                    "<code>@{username} ym</code> — Сейчас играет\n"
                    "<code>@{username} qr текст</code>\n"
                    "<code>@{username} short url</code>\n"
                    "<code>@{username} st url</code>\n"
                    "<code>@{username} sys</code>\n\n"
                    "Разработано @wineaki"
                ),
                'settings': "⚙️ Настройки",
                'language': "🌐 Язык",
                'select_language': "Выберите предпочитаемый язык:",
                'language_updated': "✅ Язык успешно обновлен!",
                'banned_message': "Вы заблокированы в этом боте.",
                'message_delivered': "Сообщение доставлено администратору.",
                'qr_created': "✅ QR-код успешно создан!",
                'status_checking': "🔍 Проверка статуса сайта...",
                'whois_info': "🔍 WHOIS информация:",
                'server_info': "🖥 Системный монитор",
                 'not_found': "❌ Не найдено",
                'error': "❌ Произошла ошибка",
                'success': "✅ Успешно",
                'url_short': "🔗 Сокращенная ссылка",
                'convert': "📁 Конвертация файла",
                'convert_success': "✅ Конвертировано в {format}",
                'convert_too_large': "❌ Файл превышает 100МБ",
                'convert_unsupported': "❌ Формат не поддерживается"
            }
        }
    
    def get_text(self, key: str, user_id: Optional[int] = None, **kwargs) -> str:
        """Get translated text for user"""
        language = 'en'  # Default to English
        
        if user_id is not None:
            try:
                language = user_logger.get_user_language(user_id)
            except:
                language = 'en'
        
        if language not in self.translations:
            language = 'en'
        
        text = self.translations[language].get(key, key)
        
        # Format the text with provided kwargs (for simple substitutions like {username})
        try:
            formatted_text = text.format(**kwargs)
            return formatted_text
        except KeyError:
            # If some placeholders aren't provided, return text with basic formatting
            return text
    
    def get_language_keyboard(self, user_id: Optional[int] = None):
        """Get language selection keyboard"""
        current_lang = user_logger.get_user_language(user_id) if user_id is not None else 'en'
        
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🇺🇸 English" + (" ✅" if current_lang == 'en' else ""),
                    callback_data="lang_en"
                ),
                InlineKeyboardButton(
                    text="🇷🇺 Русский" + (" ✅" if current_lang == 'ru' else ""),
                    callback_data="lang_ru"
                )
            ]
        ])
        
        return keyboard
    
    def get_settings_keyboard(self, user_id: Optional[int] = None):
        """Get main settings keyboard"""
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=self.get_text('language', user_id),
                    callback_data="settings_language"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 Back",
                    callback_data="settings_back"
                )
            ]
        ])
        
        return keyboard

# Global instance
language_manager = LanguageManager()