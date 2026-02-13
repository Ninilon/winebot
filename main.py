from middlewares.antiflood import AntiFloodMiddleware
from middlewares.user_logging import UserLoggingMiddleware
from middlewares.cooldown import CooldownMiddleware
import asyncio
import logging
from aiogram import Bot, Dispatcher
from config_reader import config

# Import all modules including new ones
from handlers import (
    common, tools, sys_info, net_tools, 
    qr_generator, feedback, web_reader, 
    rp_inline, inline_translator, settings, admin,
    url_shortener, file_converter
)

async def main():
    # Enable logging to see errors in terminal
    logging.basicConfig(level=logging.INFO)
    logging.getLogger("aiogram.event").setLevel(logging.CRITICAL)
    logging.getLogger("aiogram.dispatcher").setLevel(logging.CRITICAL)
    
    bot = Bot(token=config.bot_token.get_secret_value())
    dp = Dispatcher()
    
    # Add middleware (order matters)
    # 1. User logging first
    dp.message.middleware(UserLoggingMiddleware())
    dp.callback_query.middleware(UserLoggingMiddleware())
    dp.inline_query.middleware(UserLoggingMiddleware())
    
    # 2. Cooldown middleware (before antiflood)
    dp.message.middleware(CooldownMiddleware())
    dp.callback_query.middleware(CooldownMiddleware())
    dp.inline_query.middleware(CooldownMiddleware())
    
    # 3. Anti-flood middleware
    antiflood = AntiFloodMiddleware(msg_limit=3.0, inline_limit=0.7)
    dp.message.middleware(antiflood)
    dp.inline_query.middleware(antiflood)
    
    # Register routers (order matters for inline handlers)
    dp.include_router(admin.router)  # Admin commands first
    dp.include_router(settings.router)  # Settings handler
    dp.include_router(sys_info.router)  # System info (admin-only)
    dp.include_router(inline_translator.router)
    dp.include_router(url_shortener.router)  # URL shortener
    # Register other routers
    dp.include_router(file_converter.router)  # File converter
    dp.include_router(rp_inline.router)
    dp.include_router(web_reader.router)
    dp.include_router(qr_generator.router)
    dp.include_router(tools.router)
    dp.include_router(net_tools.router)
    dp.include_router(feedback.router)  # Feedback (now with command filtering)
    dp.include_router(common.router)  # Common commands last

    # Clear update queue and start
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот остановлен")
