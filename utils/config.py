# utils/config.py
import os
import platform
from dotenv import load_dotenv

load_dotenv()

# -------- БОТ / БД / API-ключи --------
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB = os.getenv("MONGO_DB", "shorts_bot")

# Оставим даже если veo3.py удалён — не мешает
VEO3_API_KEY = os.getenv("VEO3_API_KEY", "")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")

# FAL.ai API для генерации изображений (длинные видео)
FAL_API_KEY = os.getenv("FAL_API_KEY", "")

# Кто может пользоваться ботом
_allowed_raw = os.getenv("ALLOWED_USER_IDS", "")
ALLOWED_USER_IDS = set()
for part in _allowed_raw.replace(";", ",").split(","):
    part = part.strip()
    if part:
        try:
            ALLOWED_USER_IDS.add(int(part))
        except ValueError:
            pass

# -------- FFmpeg / FFprobe --------
def _guess_ffmpeg() -> str:
    # приоритет .env
    p = os.getenv("FFMPEG_BIN")
    if p:
        return p
    # иначе — имя в PATH
    return "ffmpeg.exe" if platform.system().lower().startswith("win") else "ffmpeg"

def _guess_ffprobe() -> str:
    p = os.getenv("FFPROBE_BIN")
    if p:
        return p
    return "ffprobe.exe" if platform.system().lower().startswith("win") else "ffprobe"

FFMPEG_BIN = _guess_ffmpeg()
FFPROBE_BIN = _guess_ffprobe()

# -------- Шрифт (Pillow) --------
# если явно указан в .env — используем его
FONT_PATH = os.getenv("FONT_PATH")
if not FONT_PATH:
    if platform.system().lower().startswith("win"):
        # стандартные шрифты Windows
        for c in (
            r"C:\Windows\Fonts\arial.ttf",
            r"C:\Windows\Fonts\segoeui.ttf",
        ):
            if os.path.exists(c):
                FONT_PATH = c
                break
    else:
        for c in (
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/Library/Fonts/Arial.ttf",
            "/System/Library/Fonts/SFNS.ttf",
        ):
            if os.path.exists(c):
                FONT_PATH = c
                break

# запасной вариант — Pillow тогда сам упадёт с понятной ошибкой, если такого файла нет
FONT_PATH = FONT_PATH or ("C:\\Windows\\Fonts\\arial.ttf" if os.name == "nt" else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")

# -------- Валидация критичного --------
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is not set in .env")
