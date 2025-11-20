# utils/tts.py
"""
Модуль TTS - только GenAIPro API (ElevenLabs voices через genaipro.vn)
"""
import os
import logging
from typing import Optional

# ---------- Конфиг / ключи ----------
def _get_env(name: str, default: Optional[str] = None) -> Optional[str]:
    v = os.getenv(name)
    if v:
        return v
    try:
        from utils import config as _cfg  # type: ignore
        return getattr(_cfg, name, default)
    except Exception:
        return default

# GenAIPro API Token
GENAIPRO_API_TOKEN = _get_env("GENAIPRO_API_TOKEN")

# Дефолтная скорость (1.1 = чуть быстрее нормального)
DEFAULT_SPEED = 1.1


# ============================================================
#                      ЕДИНАЯ ФУНКЦИЯ ДЛЯ GENERATION
# ============================================================

async def synthesize_tts(
    text: str,
    out_path: str,
    voice: Optional[str] = None,
    lang: str = "en",
    speed: float = DEFAULT_SPEED
) -> str:
    """
    Синтез речи через GenAIPro API (ElevenLabs voices).

    Args:
        text: Текст для озвучки
        out_path: Путь для сохранения аудио
        voice: voice_id (если None - используется дефолтный)
        lang: Язык (en/ru) - используется для выбора дефолтного голоса
        speed: Скорость речи (0.7 - 1.2, default 1.1)

    Returns:
        Путь к аудиофайлу
    """
    if not GENAIPRO_API_TOKEN:
        raise RuntimeError("GENAIPRO_API_TOKEN не задан в .env")

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)

    # Дефолтные голоса
    if not voice:
        if lang.lower().startswith("ru"):
            voice = "Xb7hH8MSUJpSbSDYk0k2"  # Antoni - подходит для RU
        else:
            voice = "uju3wxzG5OhpWcoi3SMy"  # Sarah - хороший EN голос

    # Ограничиваем скорость в допустимых пределах
    speed = max(0.7, min(1.2, speed))

    from utils.genaipro import synthesize_speech
    await synthesize_speech(
        text=text,
        voice_id=voice,
        output_path=out_path,
        model_id="eleven_multilingual_v2",
        speed=speed,
        stability=0.5,
        similarity=0.75
    )

    return out_path
