# utils/cuts.py
import os
import random
import re
from typing import List, Tuple, Optional, Dict
from PIL import Image

from utils.ffmpeg import _run, probe_duration
from utils.config import FFMPEG_BIN

# --- Базовые директории библиотеки ---
LIB_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets"))
CARTOONS_DIR = os.path.join(LIB_ROOT, "cartoons")
FILMS_DIR    = os.path.join(LIB_ROOT, "films")
BANNERS_DIR  = os.path.join(LIB_ROOT, "banners", "cuts")

VIDEO_EXTS = (".mp4", ".mov", ".mkv", ".webm")

def ensure_dirs():
    os.makedirs(CARTOONS_DIR, exist_ok=True)
    os.makedirs(FILMS_DIR, exist_ok=True)
    os.makedirs(BANNERS_DIR, exist_ok=True)

def _slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", (name or "").strip().lower()).strip("_")

def base_dir_for(kind: str) -> str:
    """
    kind: 'cartoons' | 'films'
    """
    ensure_dirs()
    return CARTOONS_DIR if kind == "cartoons" else FILMS_DIR

def list_collections(kind: str) -> List[str]:
    """
    Возвращает список папок коллекций для kind.
    """
    base = base_dir_for(kind)
    if not os.path.isdir(base):
        return []
    return sorted([d for d in os.listdir(base) if os.path.isdir(os.path.join(base, d))])

def create_collection(kind: str, name: str) -> str:
    """
    Создаёт (если нет) папку коллекции и возвращает её путь.
    """
    folder = os.path.join(base_dir_for(kind), _slug(name))
    os.makedirs(folder, exist_ok=True)
    return folder

def list_videos_in(kind: str, collection: str) -> List[str]:
    """
    Возвращает список видеофайлов внутри коллекции.
    """
    folder = os.path.join(base_dir_for(kind), collection)
    if not os.path.isdir(folder):
        return []
    vids = []
    for name in os.listdir(folder):
        if name.lower().endswith(VIDEO_EXTS):
            vids.append(os.path.join(folder, name))
    return sorted(vids)

def count_videos(kind: str, collection: str) -> int:
    return len(list_videos_in(kind, collection))

def list_collections_with_counts(kind: str) -> List[Tuple[str, int]]:
    """
    [('spongebob', 12), ('tom_and_jerry', 7), ...]
    """
    cols = list_collections(kind)
    return [(c, count_videos(kind, c)) for c in cols]

def scan_library() -> Dict[str, Dict[str, int]]:
    """
    Полный обзор библиотеки:
    {
      "cartoons": {"spongebob": 12, ...},
      "films": {"matrix": 3, ...}
    }
    """
    ensure_dirs()
    out: Dict[str, Dict[str, int]] = {"cartoons": {}, "films": {}}
    for kind in ("cartoons", "films"):
        for col in list_collections(kind):
            out[kind][col] = count_videos(kind, col)
    return out

def target_duration_range(min_sec: int, max_sec: int) -> Tuple[int, int]:
    a = max(30, int(min_sec))
    b = max(a, int(max_sec))
    return a, b

async def pick_random_segment(src: str, out_path: str, min_sec: int, max_sec: int) -> Tuple[str, float, float]:
    """
    Режет случайный фрагмент [min..max] секунд из src в out_path (без перекодирования).
    Возвращает (out_path, seg_start, seg_dur).
    """
    dur = await probe_duration(src)
    mn, mx = target_duration_range(min_sec, max_sec)
    seg = min(mx, int(dur) - 2) if dur > mn + 2 else mn
    seg = max(mn, min(mx, seg))
    if dur <= seg + 1:
        ss = 0.0
    else:
        ss = random.uniform(0.0, max(0.0, dur - seg - 0.2))

    await _run(
        FFMPEG_BIN, "-y",
        "-ss", f"{ss:.3f}",
        "-i", src,
        "-t", f"{seg:.3f}",
        "-c", "copy",
        out_path
    )
    return out_path, ss, float(seg)

def prepare_banner_overlay(banner_path: str, position: str, video_width: int = 1080, video_height: int = 1920) -> str:
    """
    Подготавливает строку фильтра для наложения баннера на видео.
    position: 'top', 'center', 'bottom'
    """
    if not os.path.exists(banner_path):
        return ""
    
    # Рассчитываем размер баннера (масштабируем до 25% ширины видео)
    target_width = int(video_width * 0.25)
    
    # Определяем позицию
    if position == "top":
        y_pos = 50  # отступ от верха
    elif position == "bottom":
        y_pos = f"main_h-overlay_h-50"  # отступ от низа
    else:  # center
        y_pos = "(main_h-overlay_h)/2"
    
    x_pos = "(main_w-overlay_w)/2"  # центрируем по горизонтали
    
    # Строка фильтра для наложения PNG с альфа-каналом
    filter_str = (
        f"[1:v]scale={target_width}:-1[banner];"
        f"[0:v][banner]overlay={x_pos}:{y_pos}:format=auto"
    )
    
    return filter_str

async def compose_vertical_blur(src_path: str, out_path: str, banner_config: Optional[Dict] = None) -> str:
    """
    9:16 вертикаль с блюром на фоне и опциональным баннером:
      - задник: размазанный фуллскрин (scale to cover + crop)
      - передний план: ролик по центру (fit/decrease)
      - баннер: PNG логотип если указан
    """
    
    # Базовый фильтр без баннера
    base_filtergraph = (
        "[0:v]split=2[v][vb];"
        # background: scale to cover, then crop 1080x1920, then blur
        "[vb]scale=1080:1920:force_original_aspect_ratio=increase,"
        "crop=1080:1920,"
        "boxblur=luma_radius=40:luma_power=1:chroma_radius=40[bg];"
        # foreground: fit/decrease and center
        "[v]scale=1080:-2:force_original_aspect_ratio=decrease,setsar=1[fg];"
        "[bg][fg]overlay=(W-w)/2:(H-h)/2:format=auto"
    )
    
    # Если есть баннер, модифицируем команду
    if banner_config and banner_config.get("file"):
        banner_file = banner_config.get("file")
        banner_path = os.path.join(BANNERS_DIR, banner_file)
        position = banner_config.get("position", "center")
        
        if os.path.exists(banner_path):
            # Фильтр с баннером
            filtergraph = (
                "[0:v]split=2[v][vb];"
                # background
                "[vb]scale=1080:1920:force_original_aspect_ratio=increase,"
                "crop=1080:1920,"
                "boxblur=luma_radius=40:luma_power=1:chroma_radius=40[bg];"
                # foreground
                "[v]scale=1080:-2:force_original_aspect_ratio=decrease,setsar=1[fg];"
                "[bg][fg]overlay=(W-w)/2:(H-h)/2:format=auto[composed];"
                # banner overlay
                f"[1:v]scale=270:-1,format=rgba[banner];"
                f"[composed][banner]overlay="
            )
            
            # Позиция баннера
            if position == "top":
                filtergraph += "(W-w)/2:50"
            elif position == "bottom":
                filtergraph += "(W-w)/2:H-h-50"
            else:  # center
                filtergraph += "(W-w)/2:(H-h)/2"
            
            filtergraph += ":format=auto"
            
            # Команда с баннером
            await _run(
                FFMPEG_BIN, "-y",
                "-i", src_path,
                "-i", banner_path,  # входной PNG баннер
                "-filter_complex", filtergraph,
                "-r", "30",
                "-c:v", "libx264", "-preset", "veryfast", "-crf", "22",
                "-pix_fmt", "yuv420p", "-movflags", "+faststart",
                "-c:a", "aac", "-b:a", "128k", "-ar", "48000",
                out_path
            )
        else:
            # Баннер не найден, используем базовый фильтр
            await _run(
                FFMPEG_BIN, "-y",
                "-i", src_path,
                "-filter_complex", base_filtergraph,
                "-r", "30",
                "-c:v", "libx264", "-preset", "veryfast", "-crf", "22",
                "-pix_fmt", "yuv420p", "-movflags", "+faststart",
                "-c:a", "aac", "-b:a", "128k", "-ar", "48000",
                out_path
            )
    else:
        # Нет баннера, используем базовый фильтр
        await _run(
            FFMPEG_BIN, "-y",
            "-i", src_path,
            "-filter_complex", base_filtergraph,
            "-r", "30",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "22",
            "-pix_fmt", "yuv420p", "-movflags", "+faststart",
            "-c:a", "aac", "-b:a", "128k", "-ar", "48000",
            out_path
        )
    
    return out_path

async def make_cut_from_collection(kind: str, collection: str, out_dir: str,
                                   min_sec: int, max_sec: int,
                                   banner_config: Optional[Dict] = None) -> Tuple[str, str, float]:
    """
    Выбирает случайный файл из коллекции, режет фрагмент, делает вертикальную композицию с опциональным баннером.
    Возвращает (final_video_path, picked_filename, seg_duration).
    
    banner_config: {"file": "banner.png", "position": "top|center|bottom"}
    """
    os.makedirs(out_dir, exist_ok=True)
    videos = list_videos_in(kind, collection)
    if not videos:
        raise RuntimeError("В коллекции нет видеофайлов.")

    src = random.choice(videos)
    tmp_seg = os.path.join(out_dir, "cut_tmp_source.mp4")
    tmp_seg, _ss, seg_dur = await pick_random_segment(src, tmp_seg, min_sec, max_sec)

    final = os.path.join(out_dir, "cut_final_1080x1920.mp4")
    await compose_vertical_blur(tmp_seg, final, banner_config)

    return final, os.path.basename(src), seg_dur