# utils/backgrounds.py
from __future__ import annotations

import os
import random
from typing import List, Optional

from utils.config import FFMPEG_BIN
from utils.ffmpeg import _run as _ffrun, probe_duration


def _list_videos(dirpath: str) -> List[str]:
    """Список видео из директории"""
    if not os.path.isdir(dirpath):
        return []
    vids = []
    for name in os.listdir(dirpath):
        if name.lower().endswith((".mp4", ".mov", ".mkv", ".webm")):
            vids.append(os.path.join(dirpath, name))
    return vids


async def _get_bg_videos_from_db(scope: str = "reddit") -> List[str]:
    """Получает список путей к фоновым видео из БД"""
    try:
        from db.database import backgrounds_list
        docs = await backgrounds_list(scope=scope)
        paths = []
        for doc in docs:
            path = doc.get("path")
            if path and os.path.exists(path):
                paths.append(path)
        return paths
    except Exception:
        return []


async def _cut_segment(src: str, start: float, duration: float, out_path: str) -> str:
    """
    Вырезает отрезок с перекодированием в H.264 (совместимость).
    """
    ss = max(0.0, start)
    dur = max(0.1, duration)
    await _ffrun(
        FFMPEG_BIN, "-y",
        "-ss", f"{ss:.3f}",
        "-i", src,
        "-t", f"{dur:.3f}",
        "-an",
        "-vf", "setsar=1",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        out_path
    )
    return out_path


async def choose_random_bg_segment(
    duration: float,
    out_dir: str,
    pool_dir: Optional[str] = None,
    fallback: Optional[str] = None,
    scope: str = "reddit"
) -> str:
    """
    Выбирает рандомный файл и вырезает случайный отрезок под нужную длительность.
    
    Приоритеты:
    1. Видео из БД (если есть)
    2. Видео из pool_dir
    3. fallback файл
    """
    candidates = []
    
    # Сначала пробуем из БД
    db_videos = await _get_bg_videos_from_db(scope)
    if db_videos:
        candidates = db_videos
    # Если в БД пусто, берем из директории
    elif pool_dir:
        candidates = _list_videos(pool_dir)
    
    # Выбираем источник
    src = None
    if candidates:
        src = random.choice(candidates)
    elif fallback and os.path.exists(fallback):
        src = fallback
    else:
        # Если ничего нет, создаем дефолтный путь
        default_path = os.path.join("assets", "bg", "default.mp4")
        if os.path.exists(default_path):
            src = default_path
        else:
            raise FileNotFoundError(
                "Нет доступных фоновых видео. "
                "Загрузите видео через бота: Настройки -> Библиотека фонов"
            )

    # Получаем длительность исходника
    total = await probe_duration(src)
    
    # Выбираем случайный отрезок
    if total <= duration + 0.5:
        # Видео короче нужного - берём с начала
        start = 0.0
    else:
        # Выбираем случайную позицию
        max_start = max(0.0, total - duration - 0.5)
        start = random.uniform(0.0, max_start)

    # Вырезаем сегмент
    out_path = os.path.join(out_dir, "bg_clip.mp4")
    return await _cut_segment(src, start, duration, out_path)