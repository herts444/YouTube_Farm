import asyncio
from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from utils.config import BOT_TOKEN
from handlers import settings

# Роутеры подключаем напрямую
from handlers.start import router as start_router
from handlers.menu import router as menu_router
from handlers.themes import router as themes_router
from handlers.channels import router as channels_router
# from handlers.generate import router as generate_router  # Старый обработчик - заменен на simplified_generate
from handlers.simplified_generate import router as simplified_generate_router  # Новый упрощенный обработчик
from handlers.long_video import router as long_video_router
# from handlers.cuts import router as cuts_router  # УДАЛЯЕМ ЭТУ СТРОКУ - cuts.py в utils, не в handlers
from handlers.statistics import router as statistics_router
# Voice cloning removed - using GenAIPro API for pre-made voices only

# Инициализация БД
from db.database import init_db

async def main():
    # 1) Инициализируем базу ДО старта поллинга
    await init_db()
    print("DB is initialized.")

    # 2) Бот/Диспетчер
    session = AiohttpSession(timeout=65)  # число секунд, совместимо с aiogram 3.7
    bot = Bot(
        BOT_TOKEN,
        session=session,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()

    # 3) Регистрируем роутеры (порядок важен!)
    dp.include_router(start_router)
    dp.include_router(channels_router)
    dp.include_router(simplified_generate_router)  # Новый упрощенный обработчик создания видео
    dp.include_router(long_video_router)  # Длинные видео
    # dp.include_router(cuts_router)  # УДАЛЯЕМ ЭТУ СТРОКУ
    dp.include_router(statistics_router)
    # Voice cloning removed
    dp.include_router(settings.router)
    dp.include_router(themes_router)
    dp.include_router(menu_router)  # menu последний из-за общего BTN_BACK

    print("Bot is running...")
    try:
        await dp.start_polling(bot, polling_timeout=50)
    finally:
        # 4) Аккуратно закрываем сессию бота и БД (если в БД есть закрытие)
        try:
            await bot.session.close()
        except Exception:
            pass
        try:
            from db.database import close_db  # если у тебя есть такая функция — вызовем
            await close_db()
        except Exception:
            pass

if __name__ == "__main__":
    asyncio.run(main())