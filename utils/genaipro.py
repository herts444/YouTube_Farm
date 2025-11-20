"""
Модуль для работы с genaipro.vn TTS API (ElevenLabs voices).
Поддерживает синтез речи через task-based API с polling.
"""
import os
import asyncio
import aiohttp
import logging
from typing import List, Tuple, Optional, Dict, Any

logger = logging.getLogger(__name__)

# ============================================================
#                      КОНФИГУРАЦИЯ
# ============================================================

BASE_URL = "https://genaipro.vn/api/v1"


def _get_api_token() -> str:
    """Получает JWT токен для genaipro.vn из env"""
    token = os.getenv("GENAIPRO_API_TOKEN", "")
    if not token:
        raise ValueError("GENAIPRO_API_TOKEN not set in .env")
    return token


def _get_headers() -> Dict[str, str]:
    """Возвращает заголовки для API запросов"""
    return {
        "Authorization": f"Bearer {_get_api_token()}",
        "Content-Type": "application/json"
    }


# ============================================================
#                      ПОЛУЧЕНИЕ ГОЛОСОВ
# ============================================================

async def list_voices(
    page: int = 0,
    page_size: int = 30,
    search: Optional[str] = None,
    language: Optional[str] = None,
    gender: Optional[str] = None,
    accent: Optional[str] = None,
    age: Optional[str] = None,
    sort: str = "trending"
) -> List[Dict[str, Any]]:
    """
    Получает список доступных голосов ElevenLabs через genaipro API.

    Args:
        page: Номер страницы (начиная с 0)
        page_size: Количество голосов на странице
        search: Поиск по имени голоса
        language: Фильтр по языку (en, ru, etc.)
        gender: Фильтр по полу (male, female, neutral)
        accent: Фильтр по акценту (american, british, etc.)
        age: Фильтр по возрасту (young, middle_aged, old)
        sort: Сортировка (trending, created_date, etc.)

    Returns:
        Список голосов с их параметрами
    """
    params = {
        "page": page,
        "page_size": page_size,
        "sort": sort,
        "include_live_moderated": "true"
    }

    if search:
        params["search"] = search
    if language:
        params["language"] = language
    if gender:
        params["gender"] = gender
    if accent:
        params["accent"] = accent
    if age:
        params["age"] = age

    url = f"{BASE_URL}/labs/voices"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=_get_headers(), params=params, timeout=30) as resp:
                if resp.status != 200:
                    error_text = await resp.text()
                    raise RuntimeError(f"GenAIPro API error ({resp.status}): {error_text}")

                data = await resp.json()

                # Проверяем, что data - это dict
                if not isinstance(data, dict):
                    logger.error(f"Unexpected API response type: {type(data)}, data: {data}")
                    raise RuntimeError(f"Unexpected API response format: expected dict, got {type(data)}")

                voices = data.get("voices", [])

                # Проверяем, что voices - это list
                if not isinstance(voices, list):
                    logger.error(f"Unexpected voices type: {type(voices)}, voices: {voices}")
                    raise RuntimeError(f"Unexpected voices format: expected list, got {type(voices)}")

                return voices
    except Exception as e:
        logger.exception("Failed to fetch voices from GenAIPro: %s", e)
        raise


async def list_voices_simple(
    lang: Optional[str] = None,
    gender: Optional[str] = None
) -> List[Tuple[str, str]]:
    """
    Упрощенный интерфейс для получения списка голосов.

    Args:
        lang: Язык (en, ru, etc.)
        gender: Пол (male, female)

    Returns:
        Список кортежей [(display_name, voice_id), ...]
    """
    # Преобразуем язык в формат API
    language = None
    if lang:
        lang_map = {
            "en": "en",
            "ru": "ru",
            "es": "es",
            "fr": "fr",
            "de": "de",
            "it": "it",
            "pt": "pt",
            "pl": "pl",
            "ja": "ja",
            "ko": "ko",
            "zh": "zh",
        }
        language = lang_map.get(lang.lower(), lang)

    # Преобразуем пол
    gender_param = None
    if gender:
        gender_map = {
            "Male": "male",
            "Female": "female",
            "male": "male",
            "female": "female"
        }
        gender_param = gender_map.get(gender, gender.lower())

    voices = await list_voices(
        page=0,
        page_size=50,
        language=language,
        gender=gender_param
    )

    result = []
    for i, v in enumerate(voices):
        # Проверяем, что v - это dict
        if not isinstance(v, dict):
            logger.warning(f"Voice at index {i} is not a dict: {type(v)}, skipping")
            continue

        voice_id = v.get("voice_id")
        name = v.get("name", "Unknown")
        if voice_id:
            # Добавляем информацию о характеристиках
            labels = v.get("labels", {})
            if isinstance(labels, dict):
                accent = labels.get("accent", "")
                age = labels.get("age", "")
                desc = labels.get("description", "")
            else:
                accent = age = desc = ""

            display_parts = [name]
            if accent:
                display_parts.append(f"({accent})")
            if desc:
                display_parts.append(f"- {desc}")

            display_name = " ".join(display_parts)
            result.append((display_name, voice_id))

    return result


async def get_user_balance() -> Dict[str, Any]:
    """
    Получает информацию о балансе пользователя.

    Returns:
        Словарь с информацией о балансе и кредитах
    """
    url = f"{BASE_URL}/me"

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=_get_headers(), timeout=30) as resp:
            if resp.status != 200:
                error_text = await resp.text()
                raise RuntimeError(f"GenAIPro API error ({resp.status}): {error_text}")

            return await resp.json()


# ============================================================
#                      СОЗДАНИЕ TTS ЗАДАЧИ
# ============================================================

async def create_tts_task(
    text: str,
    voice_id: str,
    model_id: str = "eleven_multilingual_v2",
    style: float = 0.0,
    speed: float = 1.0,
    stability: float = 0.5,
    similarity: float = 0.75,
    use_speaker_boost: bool = True
) -> str:
    """
    Создает задачу на синтез речи.

    Args:
        text: Текст для озвучки
        voice_id: ID голоса
        model_id: Модель TTS
        style: Стиль (0.0 - 1.0)
        speed: Скорость (0.7 - 1.2)
        stability: Стабильность (0.0 - 1.0)
        similarity: Схожесть (0.0 - 1.0)
        use_speaker_boost: Усиление голоса

    Returns:
        task_id для отслеживания задачи
    """
    url = f"{BASE_URL}/labs/task"

    payload = {
        "input": text,
        "voice_id": voice_id,
        "model_id": model_id,
        "style": style,
        "speed": speed,
        "stability": stability,
        "similarity": similarity,
        "use_speaker_boost": use_speaker_boost
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=_get_headers(), json=payload, timeout=60) as resp:
            if resp.status != 200:
                error_text = await resp.text()
                raise RuntimeError(f"GenAIPro create task error ({resp.status}): {error_text}")

            data = await resp.json()
            task_id = data.get("task_id")
            if not task_id:
                raise RuntimeError(f"No task_id in response: {data}")

            return task_id


async def get_task_status(task_id: str) -> Dict[str, Any]:
    """
    Получает статус задачи по task_id.

    Args:
        task_id: ID задачи

    Returns:
        Информация о задаче включая статус и результат
    """
    url = f"{BASE_URL}/labs/task/{task_id}"

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=_get_headers(), timeout=30) as resp:
            if resp.status != 200:
                error_text = await resp.text()
                raise RuntimeError(f"GenAIPro get task error ({resp.status}): {error_text}")

            return await resp.json()


async def wait_for_task_completion(
    task_id: str,
    max_wait_seconds: int = 300,
    poll_interval: float = 2.0
) -> Dict[str, Any]:
    """
    Ожидает завершения задачи с polling.

    Args:
        task_id: ID задачи
        max_wait_seconds: Максимальное время ожидания в секундах
        poll_interval: Интервал между проверками в секундах

    Returns:
        Информация о завершенной задаче

    Raises:
        TimeoutError: Если задача не завершилась вовремя
        RuntimeError: Если задача завершилась с ошибкой
    """
    elapsed = 0.0

    while elapsed < max_wait_seconds:
        task_info = await get_task_status(task_id)
        status = task_info.get("status", "").lower()

        if status == "completed":
            return task_info

        if status == "failed" or status == "error":
            error_msg = task_info.get("error", "Unknown error")
            raise RuntimeError(f"TTS task failed: {error_msg}")

        # Ждем перед следующей проверкой
        await asyncio.sleep(poll_interval)
        elapsed += poll_interval

        # Увеличиваем интервал после нескольких попыток (exponential backoff)
        if elapsed > 30:
            poll_interval = min(poll_interval * 1.5, 10.0)

    raise TimeoutError(f"Task {task_id} did not complete within {max_wait_seconds} seconds")


async def download_audio(audio_url: str, output_path: str) -> str:
    """
    Скачивает аудиофайл по URL.

    Args:
        audio_url: URL аудиофайла
        output_path: Путь для сохранения

    Returns:
        Путь к сохраненному файлу
    """
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    async with aiohttp.ClientSession() as session:
        async with session.get(audio_url, timeout=120) as resp:
            if resp.status != 200:
                raise RuntimeError(f"Failed to download audio ({resp.status})")

            audio_data = await resp.read()
            with open(output_path, "wb") as f:
                f.write(audio_data)

    return output_path


# ============================================================
#                      ОСНОВНАЯ ФУНКЦИЯ СИНТЕЗА
# ============================================================

async def synthesize_speech(
    text: str,
    voice_id: str,
    output_path: str,
    model_id: str = "eleven_multilingual_v2",
    style: float = 0.0,
    speed: float = 1.0,
    stability: float = 0.5,
    similarity: float = 0.75,
    use_speaker_boost: bool = True,
    max_wait_seconds: int = 300
) -> str:
    """
    Полный цикл синтеза речи: создание задачи, ожидание, скачивание.

    Args:
        text: Текст для озвучки
        voice_id: ID голоса
        output_path: Путь для сохранения аудио
        model_id: Модель TTS
        style: Стиль
        speed: Скорость
        stability: Стабильность
        similarity: Схожесть
        use_speaker_boost: Усиление голоса
        max_wait_seconds: Максимальное время ожидания

    Returns:
        Путь к аудиофайлу
    """
    # 1. Создаем задачу
    logger.info(f"Creating TTS task for {len(text)} chars with voice {voice_id}")
    task_id = await create_tts_task(
        text=text,
        voice_id=voice_id,
        model_id=model_id,
        style=style,
        speed=speed,
        stability=stability,
        similarity=similarity,
        use_speaker_boost=use_speaker_boost
    )
    logger.info(f"Task created: {task_id}")

    # 2. Ожидаем завершения
    logger.info("Waiting for task completion...")
    task_info = await wait_for_task_completion(task_id, max_wait_seconds)

    # 3. Скачиваем результат
    result_url = task_info.get("result")
    if not result_url:
        raise RuntimeError(f"No result URL in completed task: {task_info}")

    logger.info(f"Downloading audio from {result_url}")
    await download_audio(result_url, output_path)

    logger.info(f"Audio saved to {output_path}")
    return output_path


async def get_voice_preview_url(voice_id: str) -> Optional[str]:
    """
    Получает URL готового превью голоса (без генерации).

    Args:
        voice_id: ID голоса

    Returns:
        URL превью или None если не найден
    """
    url = f"{BASE_URL}/labs/voices/{voice_id}"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=_get_headers(), timeout=30) as resp:
                if resp.status != 200:
                    logger.warning(f"Failed to get voice info for {voice_id}: {resp.status}")
                    return None

                data = await resp.json()

                # Проверяем наличие preview_url или samples
                if isinstance(data, dict):
                    # Пробуем получить preview_url
                    preview_url = data.get("preview_url")
                    if preview_url:
                        return preview_url

                    # Если нет preview_url, пробуем получить первый sample
                    samples = data.get("samples", [])
                    if samples and len(samples) > 0:
                        if isinstance(samples[0], dict):
                            return samples[0].get("audio_url") or samples[0].get("url")
                        elif isinstance(samples[0], str):
                            return samples[0]

                return None
    except Exception as e:
        logger.exception("Failed to get voice preview URL: %s", e)
        return None


async def synthesize_preview(
    voice_id: str,
    text: Optional[str],
    output_path: str
) -> str:
    """
    Создает превью голоса с тестовым текстом.

    Args:
        voice_id: ID голоса
        text: Текст для озвучки (если None - используется дефолтный)
        output_path: Путь для сохранения

    Returns:
        Путь к аудиофайлу
    """
    if not text:
        text = "Hello! This is a voice preview from GenAIPro. The voice quality is excellent for your projects."

    return await synthesize_speech(
        text=text,
        voice_id=voice_id,
        output_path=output_path,
        model_id="eleven_multilingual_v2",
        stability=0.5,
        similarity=0.75,
        max_wait_seconds=120  # Для превью достаточно 2 минут
    )


# ============================================================
#                      ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================================

async def get_supported_languages() -> List[str]:
    """
    Возвращает список поддерживаемых языков.
    """
    return [
        "en",  # English
        "ru",  # Russian
        "es",  # Spanish
        "fr",  # French
        "de",  # German
        "it",  # Italian
        "pt",  # Portuguese
        "pl",  # Polish
        "tr",  # Turkish
        "nl",  # Dutch
        "cs",  # Czech
        "ar",  # Arabic
        "zh",  # Chinese
        "ja",  # Japanese
        "ko",  # Korean
        "hi",  # Hindi
        "id",  # Indonesian
    ]


async def get_available_models() -> List[Dict[str, str]]:
    """
    Возвращает список доступных моделей TTS.
    """
    return [
        {
            "id": "eleven_multilingual_v2",
            "name": "Multilingual v2",
            "description": "Best quality, supports 28 languages including Russian"
        },
        {
            "id": "eleven_turbo_v2_5",
            "name": "Turbo v2.5",
            "description": "Fast generation with good quality"
        },
        {
            "id": "eleven_flash_v2_5",
            "name": "Flash v2.5",
            "description": "Fastest generation, lower quality"
        },
        {
            "id": "eleven_v3",
            "name": "ElevenLabs v3",
            "description": "Latest model with improved quality"
        }
    ]
