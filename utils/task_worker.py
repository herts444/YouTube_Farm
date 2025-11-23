"""
Worker для обработки задач из очереди
"""
import os
import shutil
import tempfile
from typing import Dict, Any


async def process_video_task(task) -> Dict[str, Any]:
    """
    Обрабатывает задачу на генерацию видео

    Args:
        task: VideoTask объект с конфигурацией

    Returns:
        Dict с результатом генерации
    """
    task_type = task.task_type
    config = task.config

    print(f"[TaskWorker] Processing task {task.task_id}, type: {task_type}")
    print(f"[TaskWorker] Config: {config}")

    workdir = tempfile.mkdtemp(prefix=f"{task_type}_{task.task_id}_")
    print(f"[TaskWorker] Created workdir: {workdir}")

    try:
        if task_type == "cuts":
            print(f"[TaskWorker] Starting cuts task...")
            return await _process_cuts_task(config, workdir)
        elif task_type in ("reddit", "educational", "horror", "facts", "history", "news"):
            print(f"[TaskWorker] Starting story task...")
            return await _process_story_task(task_type, config, workdir)
        else:
            raise ValueError(f"Unknown task type: {task_type}")
    except Exception as e:
        print(f"[TaskWorker] ERROR: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        # Очистка временной директории
        try:
            shutil.rmtree(workdir, ignore_errors=True)
            print(f"[TaskWorker] Cleaned up workdir: {workdir}")
        except Exception as e:
            print(f"[TaskWorker] Failed to cleanup workdir: {e}")


async def _process_cuts_task(config: Dict[str, Any], workdir: str) -> Dict[str, Any]:
    """Обработка задачи нарезки"""
    from utils.cuts import make_cut_from_collection
    from utils.ffmpeg import ensure_telegram_size

    kind = config.get("kind")
    collection = config.get("collection")
    min_sec = config.get("min_sec", 30)
    max_sec = config.get("max_sec", 60)
    banner_config = config.get("banner_config")

    # Генерируем нарезку
    final, picked, seg_dur = await make_cut_from_collection(
        kind=kind,
        collection=collection,
        out_dir=workdir,
        min_sec=min_sec,
        max_sec=max_sec,
        banner_config=banner_config
    )

    # Оптимизируем для Telegram
    target_path = os.path.join(workdir, "final_tg.mp4")
    safe_path = await ensure_telegram_size(final, target_path, target_mb=48)

    # Копируем в постоянное место
    final_dir = os.path.join("output", "cuts")
    os.makedirs(final_dir, exist_ok=True)
    final_output = os.path.join(final_dir, os.path.basename(safe_path))
    shutil.copy2(safe_path, final_output)

    caption = (
        f"✂️ <b>Нарезка готова!</b>\n\n"
        f"Коллекция: {collection}\n"
        f"Длительность: {int(seg_dur)}с"
    )

    return {
        "video_path": final_output,
        "caption": caption,
        "duration": seg_dur
    }


async def _process_story_task(task_type: str, config: Dict[str, Any], workdir: str) -> Dict[str, Any]:
    """Обработка задачи истории (reddit/educational)"""
    from utils.generation import _generate_reddit
    from utils.ffmpeg import ensure_telegram_size
    from utils.french_metadata import generate_french_metadata

    # Генерируем историю
    result = await _generate_reddit(config, workdir)
    final_path = result["video_path"]

    # Оптимизируем для Telegram
    target_path = os.path.join(workdir, "final_tg.mp4")
    safe_path = await ensure_telegram_size(final_path, target_path, target_mb=48)

    # Копируем в постоянное место
    final_dir = os.path.join("output", task_type)
    os.makedirs(final_dir, exist_ok=True)
    final_output = os.path.join(final_dir, os.path.basename(safe_path))
    shutil.copy2(safe_path, final_output)

    # Французские метаданные
    story_text = result.get("text", "")
    french_meta = await generate_french_metadata(story_text, story_type=task_type)

    # Формируем подпись
    type_map = {
        "reddit": ("📱", "Жизненная история"),
        "educational": ("🧠", "Познавательная история"),
        "horror": ("😱", "Страшная история"),
        "facts": ("💡", "Познавательные факты"),
        "history": ("📜", "Исторические факты"),
        "news": ("📰", "Последние новости")
    }
    type_emoji, type_text = type_map.get(task_type, ("🎬", "История"))

    lang = config.get("tts_lang", "en").upper()
    voice_name = config.get("voice_name", "Unknown")

    caption = (
        f"{type_emoji} <b>{type_text}</b>\n"
        f"🌐 {lang} | 🎤 {voice_name}\n\n"
        f"🇫🇷 {french_meta['description']}\n"
        f"{' '.join(french_meta['hashtags'])}"
    )

    return {
        "video_path": final_output,
        "caption": caption,
        "text": story_text
    }
