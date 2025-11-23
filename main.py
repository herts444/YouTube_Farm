import os
import asyncio
import platform
import shutil

# Настройка ffmpeg для pydub и moviepy ДО всех импортов
# Это предотвращает предупреждение "Couldn't find ffmpeg"

# Ищем ffmpeg в системе
_ffmpeg_path = shutil.which("ffmpeg")
if not _ffmpeg_path:
    # Если не найден в PATH, используем стандартное имя
    _ffmpeg_path = "ffmpeg.exe" if platform.system().lower().startswith("win") else "ffmpeg"

_ffprobe_path = shutil.which("ffprobe")
if not _ffprobe_path:
    _ffprobe_path = "ffprobe.exe" if platform.system().lower().startswith("win") else "ffprobe"

# Устанавливаем переменные окружения для pydub и moviepy
os.environ["FFMPEG_BINARY"] = _ffmpeg_path
os.environ["FFPROBE_BINARY"] = _ffprobe_path
os.environ["IMAGEMAGICK_BINARY"] = "magick"  # для moviepy (опционально)

# Создаем конфигурационный файл для moviepy чтобы избежать ошибки при импорте
try:
    _moviepy_config_dir = os.path.join(os.path.expanduser("~"), ".config")
    os.makedirs(_moviepy_config_dir, exist_ok=True)
    _moviepy_config_file = os.path.join(_moviepy_config_dir, "moviepy.cfg")

    if not os.path.exists(_moviepy_config_file):
        with open(_moviepy_config_file, "w") as f:
            f.write(f"[MOVIEPY]\n")
            f.write(f"FFMPEG_BINARY = {_ffmpeg_path}\n")
except Exception:
    pass  # Не критично если не удалось создать конфиг

from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from utils.config import BOT_TOKEN

# Дополнительная настройка pydub если он используется
# ВАЖНО: Не импортируем pydub здесь - он импортируется в других модулях
# Переменные окружения установлены выше и pydub их подхватит

# Роутеры подключаем напрямую
from handlers.start import router as start_router
from handlers.create import router as create_router  # Новый inline-обработчик создания видео

# Импортируем long_video только если ffmpeg доступен
long_video_router = None
try:
    from handlers.long_video import router as long_video_router
except (OSError, ImportError) as e:
    print(f"[!] Long video module disabled (ffmpeg required): {e}")
    long_video_router = None

# from handlers.cuts import router as cuts_router  # УДАЛЯЕМ ЭТУ СТРОКУ - cuts.py в utils, не в handlers
from handlers.statistics import router as statistics_router
# Voice cloning removed - using GenAIPro API for pre-made voices only

# Инициализация БД
from db.database import init_db

async def main():
    # 0) Проверяем наличие ffmpeg
    if not shutil.which("ffmpeg"):
        print("\n[!] WARNING: ffmpeg not found in system!")
        print("[i] Install ffmpeg:")
        print("   - Download: https://ffmpeg.org/download.html")
        print("   - Or specify path in .env: FFMPEG_BIN=C:\\path\\to\\ffmpeg.exe")
        print("   - After installation add ffmpeg to PATH\n")
        print("[!] Some functions (video, audio) may not work!\n")

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
    dp.include_router(start_router)  # Главное меню + настройки + статистика (все в одном!)
    dp.include_router(create_router)  # Inline-меню создания видео
    if long_video_router:
        dp.include_router(long_video_router)  # Длинные видео (только если ffmpeg доступен)
    dp.include_router(statistics_router)

    # 4) Запускаем фоновый worker для обработки задач
    from utils.task_queue import get_task_queue
    from utils.task_worker import process_video_task

    task_queue = get_task_queue()
    asyncio.create_task(task_queue.start_worker(bot, process_video_task))
    print("Task queue worker started")

    print("Bot is running...")
    try:
        await dp.start_polling(bot, polling_timeout=50)
    finally:
        # 5) Останавливаем worker
        print("Stopping task queue worker...")
        task_queue.stop_worker()

        # 6) Аккуратно закрываем сессию бота и БД
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