# utils/engines/RedditStory.py
"""
Единый модуль для генерации Reddit историй.
Объединяет функционал story.py, template.py и compose.py
"""
from __future__ import annotations

import os
import math
from typing import Dict, Any, List, Tuple, Optional
from PIL import Image, ImageDraw, ImageFont

from utils.config import FONT_PATH, FFMPEG_BIN
from utils.ffmpeg import _run as _ffrun
from utils.backgrounds import choose_random_bg_segment
from utils.story_gen import generate_story as _llm_generate

# ======================== STORY GENERATION ========================

async def _get_prompt_from_db(lang: str, preset: str) -> Optional[str]:
    """Читает промпт из БД"""
    try:
        from db.database import db
        doc = await db().prompts.find_one({"scope": "reddit", "preset": preset, "lang": lang})
        if doc and doc.get("text"):
            return doc["text"]
    except Exception:
        pass
    return None


def _fallback_prompt(lang: str) -> str:
    """Дефолтный промпт если в БД пусто"""
    if lang.startswith("ru"):
        return (
            "Расскажи РЕАЛЬНУЮ историю из жизни. Выбери ОДНУ тему:\n"
            "• Сегодня в очереди случилось кое-что интересное\n"
            "• Почему я больше не хожу в тот магазин\n"
            "• Разговор который изменил моё отношение к работе\n"
            "• Как незнакомец в метро преподал мне урок\n"
            "• Что я узнал о соседях за год жизни в этом доме\n"
            "• Почему я перестал давать в долг друзьям\n\n"
            "КАК ПИСАТЬ:\n"
            "1. Начни с сути — что случилось, где, когда\n"
            "2. Опиши ситуацию конкретно — кто что сказал, как выглядел\n"
            "3. Твои мысли и реакция в тот момент\n"
            "4. Чем закончилось\n"
            "5. Что ты из этого вынес (без морализаторства)\n\n"
            "ГЛАВНОЕ: пиши как рассказываешь другу за пивом. Простые слова, живые диалоги, "
            "обычные человеческие эмоции. История должна быть такой, что каждый скажет "
            "'блин, у меня похожее было'. Без выдумок и преувеличений."
        )
    return (
        "Tell a REAL life story. Pick ONE topic:\n"
        "• Something interesting happened in line today\n"
        "• Why I don't go to that store anymore\n"
        "• A conversation that changed how I see my job\n"
        "• What a stranger on the subway taught me\n"
        "• What I learned about my neighbors after a year\n"
        "• Why I stopped lending money to friends\n\n"
        "HOW TO WRITE:\n"
        "1. Start with what happened — where, when, the situation\n"
        "2. Describe it specifically — who said what, how they looked\n"
        "3. Your thoughts and reaction in that moment\n"
        "4. How it ended\n"
        "5. What you took away from it (no preaching)\n\n"
        "KEY: write like you're telling a friend over beers. Simple words, real dialogue, "
        "normal human emotions. Story should make everyone say 'damn, same thing happened to me'. "
        "No made-up stuff, no exaggeration."
    )


async def make_story_text(lang: str, target_sec: int, preset: str = "default") -> str:
    """Генерирует текст истории"""
    prompt = await _get_prompt_from_db(lang=lang, preset=preset) or _fallback_prompt(lang)
    # Используем preset как theme_name чтобы generate_story могла определить тип истории
    theme_name = f"{preset} [{lang}]"
    text = await _llm_generate(prompt, theme_name, lang, target_sec=target_sec)
    return text


# ======================== TEMPLATE RENDERING ========================

LINE_H_TITLE = 72
LINE_H_BODY = 56
CARD_ALPHA = (255, 255, 255, 235)
CURSOR_W = 8
CURSOR_H_RATIO = 0.78
CURSOR_COLOR = (35, 35, 35, 255)
CURSOR_MARGIN_X = 4
CURSOR_MARGIN_Y = 6


def _load_font(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONT_PATH, size)


def _sanitize_singleline(text: str) -> str:
    return " ".join((text or "").replace("\r", " ").replace("\n", " ").split())


def _wrap_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, max_width: int) -> List[str]:
    text = _sanitize_singleline(text)
    if not text:
        return []
    words = text.split(" ")
    lines, cur = [], ""
    for w in words:
        test = (cur + " " + w).strip()
        if draw.textlength(test, font=font) <= max_width:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def _draw_reddit_card(base: Image.Image, W: int, H: int,
                      title: str, visible_text: str, show_cursor: bool, theme_cfg: dict):
    """Рисует карточку Reddit на изображении"""
    draw = ImageDraw.Draw(base, "RGBA")
    
    pad = int(theme_cfg.get("pad", 24))
    # Ширина карточки - 60% от canvas (отступы по 20% слева и справа)
    card_w = int(W * 0.6)
    card_h = int(H * 0.86)
    # Позиция карточки - 20% от левого края
    card_x = int(W * 0.2)
    card_y = max(0, int((H - card_h) // 2))
    
    draw.rounded_rectangle((card_x, card_y, card_x + card_w, card_y + card_h), 
                          radius=32, fill=CARD_ALPHA)
    
    f_small = _load_font(28 if H <= 960 else 36)
    f_title = _load_font(56 if H <= 960 else 64)
    f_body = _load_font(40 if H <= 960 else 44)
    
    sb = theme_cfg.get("subreddit", "r/AskReddit")
    meta = theme_cfg.get("meta", "↑ 12.3k • 6 hours ago")
    
    # Заголовок
    draw.text((card_x + 32, card_y + 24), sb, fill=(237, 90, 49), font=f_small)
    draw.text((card_x + 32, card_y + 24 + 44), meta, fill=(110, 110, 110), font=f_small)
    
    title_x = card_x + 32
    title_y = card_y + 24 + 44 + 44
    title_w = card_w - 64
    
    title_lines = _wrap_text(draw, title, f_title, title_w)
    cur_y = title_y
    for line in title_lines:
        draw.text((title_x, cur_y), line, fill=(33, 33, 33), font=f_title)
        cur_y += LINE_H_TITLE
    
    draw.line((title_x, cur_y + 16, title_x + title_w, cur_y + 16), fill=(230, 230, 230), width=3)
    cur_y += 36
    
    # Тело истории
    body_lines = _wrap_text(draw, visible_text, f_body, title_w)
    
    for line in body_lines:
        if cur_y + LINE_H_BODY > card_y + card_h - 32:
            break
        draw.text((title_x, cur_y), line, fill=(35, 35, 35), font=f_body)
        cur_y += LINE_H_BODY
    
    # Курсор
    if show_cursor and body_lines:
        last_line = body_lines[-1] if cur_y > title_y else ""
        if last_line:
            x = title_x + draw.textlength(last_line, font=f_body)
            h = int(LINE_H_BODY * CURSOR_H_RATIO)
            y_top = cur_y - LINE_H_BODY + CURSOR_MARGIN_Y
            draw.rectangle(
                (x + CURSOR_MARGIN_X, y_top, x + CURSOR_MARGIN_X + CURSOR_W, y_top + h),
                fill=CURSOR_COLOR
            )


def render_reddit_frames(out_dir: str, raw_title: str, raw_body: str,
                         fps: int, duration: float, theme_cfg: dict,
                         canvas: Tuple[int, int] = (1080, 960)) -> Tuple[str, int]:
    """Рендерит PNG кадры карточки Reddit с пагинацией

    Canvas по умолчанию 1080x960 - нижняя половина экрана
    """
    os.makedirs(out_dir, exist_ok=True)
    total_frames = int(math.ceil(max(0.1, duration) * max(1, fps)))
    W, H = canvas

    title = _sanitize_singleline(raw_title or "")
    body_src = _sanitize_singleline(raw_body or "")
    if not body_src:
        body_src = " "

    typing_frames = max(1, total_frames - int(0.5 * fps))
    total_chars = max(1, len(body_src))

    # Предварительно разбиваем текст на страницы
    pages = _split_text_into_pages(body_src, W, H, title, theme_cfg)

    # Оптимизация: кешируем предыдущий кадр
    last_visible_text = None
    last_show_cursor = None
    last_page_idx = None
    last_img = None

    # Оптимизация: сохраняем PNG с минимальным сжатием для скорости
    png_params = {"compress_level": 1}

    for i in range(total_frames):
        if i < typing_frames:
            show_chars = int((i / typing_frames) * total_chars)
        else:
            show_chars = total_chars

        visible_text = body_src[:show_chars]
        show_cursor = (show_chars < total_chars) and ((i // 6) % 2 == 0)

        # Определяем текущую страницу
        current_page_idx = _get_page_for_chars(pages, show_chars)

        # Получаем текст для текущей страницы
        if current_page_idx < len(pages):
            page_start, page_end, _ = pages[current_page_idx]
            page_visible_text = visible_text[page_start:min(show_chars, page_end)]
        else:
            page_visible_text = ""

        # Оптимизация: пропускаем рендеринг если контент не изменился
        if (page_visible_text == last_visible_text and
            show_cursor == last_show_cursor and
            current_page_idx == last_page_idx and
            last_img is not None):
            # Копируем предыдущий кадр
            last_img.save(os.path.join(out_dir, f"frame_{i:05d}.png"), **png_params)
        else:
            img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            _draw_reddit_card(img, W, H, title, page_visible_text, show_cursor, theme_cfg)
            img.save(os.path.join(out_dir, f"frame_{i:05d}.png"), **png_params)
            last_img = img
            last_visible_text = page_visible_text
            last_show_cursor = show_cursor
            last_page_idx = current_page_idx

    return out_dir, total_frames


def _split_text_into_pages(text: str, W: int, H: int, title: str, theme_cfg: dict) -> List[Tuple[int, int, str]]:
    """Разбивает текст на страницы, возвращает [(start_char, end_char, page_text), ...]"""
    from PIL import Image, ImageDraw

    # Создаем временное изображение для измерения
    temp_img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(temp_img, "RGBA")

    # Ширина карточки - 60% от canvas (отступы по 20% слева и справа)
    card_w = int(W * 0.6)
    card_h = int(H * 0.86)

    f_title = _load_font(56 if H <= 960 else 64)
    f_body = _load_font(40 if H <= 960 else 44)

    title_w = card_w - 64

    # Рассчитываем доступное пространство для текста
    title_lines = _wrap_text(draw, title, f_title, title_w)
    title_height = len(title_lines) * LINE_H_TITLE

    # Высота для body (с учетом заголовка, meta, разделителя)
    header_height = 24 + 44 + 44 + title_height + 36  # meta + title + separator
    available_height = card_h - header_height - 64  # 64 = отступы
    max_body_lines = max(1, int(available_height / LINE_H_BODY))

    # Разбиваем текст на слова
    words = text.split()
    pages = []
    current_start = 0
    current_text = ""

    for word in words:
        test_text = (current_text + " " + word).strip()
        test_lines = _wrap_text(draw, test_text, f_body, title_w)

        if len(test_lines) > max_body_lines:
            # Страница заполнена, сохраняем
            if current_text:
                pages.append((current_start, current_start + len(current_text), current_text))
                current_start += len(current_text) + 1  # +1 для пробела
                current_text = word
            else:
                # Даже одно слово не влезает - принудительно добавляем
                pages.append((current_start, current_start + len(word), word))
                current_start += len(word) + 1
                current_text = ""
        else:
            current_text = test_text

    # Добавляем последнюю страницу
    if current_text:
        pages.append((current_start, current_start + len(current_text), current_text))

    return pages if pages else [(0, len(text), text)]


def _get_page_for_chars(pages: List[Tuple[int, int, str]], char_count: int) -> int:
    """Определяет номер страницы для заданного количества символов"""
    for idx, (start, end, _) in enumerate(pages):
        if char_count <= end:
            return idx
    return len(pages) - 1


# ======================== COMPOSITION ========================

async def compose_pngseq_blur_base(bg_video_path: str, frames_dir: str,
                                   duration: float, fps: int, out_path: str) -> None:
    """Композиция: фон + карточка (оптимизированная версия)"""
    d = f"{duration:.3f}"
    pattern = f"{frames_dir}/frame_%05d.png"

    # Оптимизации:
    # 1. boxblur вместо gblur (в 3-5 раз быстрее)
    # 2. preset ultrafast для максимальной скорости
    # 3. threads 0 для использования всех ядер
    # 4. tune stillimage для статичных кадров
    await _ffrun(
        FFMPEG_BIN, "-y",
        "-threads", "0",
        "-stream_loop", "-1", "-i", bg_video_path,
        "-framerate", str(fps), "-i", pattern,
        "-t", d,
        "-filter_complex",
        (
            f"[0:v]scale=1080:1920:flags=fast_bilinear,setsar=1,trim=0:{d},setpts=PTS-STARTPTS,boxblur=20:2[base];"
            f"[0:v]scale=1080:960:flags=fast_bilinear,setsar=1,trim=0:{d},setpts=PTS-STARTPTS[bot];"
            "[1:v]scale=1080:960:flags=fast_bilinear,setsar=1[card];"
            "[base][bot]overlay=x=0:y=960:format=auto[tmp];"
            "[tmp][card]overlay=x=0:y=0:format=auto[v]"
        ),
        "-map", "[v]",
        "-r", str(fps),
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-tune", "stillimage",
        "-crf", "23",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        out_path
    )


async def compose_pngseq_animation(bg_video_path: str, frames_dir: str,
                                   duration: float, fps: int, out_path: str,
                                   card_position: str = "center") -> None:
    """Композиция: анимационный фон + карточка (без blur)"""
    d = f"{duration:.3f}"
    pattern = f"{frames_dir}/frame_%05d.png"

    # Композиция с правильным размещением:
    # 1. Анимация масштабируется и обрезается под верхнюю половину (1080x960)
    # 2. Карточка размещается внизу БЕЗ растягивания, сохраняя качество
    # 3. Карточка центрируется по горизонтали, прижата к низу экрана
    await _ffrun(
        FFMPEG_BIN, "-y",
        "-threads", "0",
        "-stream_loop", "-1", "-i", bg_video_path,
        "-framerate", str(fps), "-i", pattern,
        "-t", d,
        "-filter_complex",
        (
            # Анимация: масштабируем и обрезаем под верхнюю половину (1080x960)
            f"[0:v]scale=1080:960:force_original_aspect_ratio=increase,crop=1080:960,setsar=1,trim=0:{d},setpts=PTS-STARTPTS[anim];"
            # Карточка: НЕ растягиваем, сохраняем пропорции (width=1080, height автоматически)
            "[1:v]scale=1080:-1:flags=lanczos,setsar=1[card];"
            # Создаём чёрный фон 1080x1920
            f"color=black:s=1080x1920:d={d},format=yuv420p[bg];"
            # Накладываем анимацию сверху
            "[bg][anim]overlay=x=0:y=0:format=auto[tmp1];"
            # Накладываем карточку внизу по центру
            "[tmp1][card]overlay=x=(W-w)/2:y=H-h:format=auto[v]"
        ),
        "-map", "[v]",
        "-r", str(fps),
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-tune", "stillimage",
        "-crf", "23",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        out_path
    )


# ======================== MAIN FUNCTIONS ========================

async def generate(channel: Dict[str, Any], out_dir: str) -> Dict[str, Any]:
    """Генерация Reddit истории"""
    os.makedirs(out_dir, exist_ok=True)
    
    lang = str(channel.get("tts_lang") or "en").lower()
    target_sec = int(channel.get("reddit_target_sec") or 75)
    preset = str(channel.get("prompt_preset") or "default")
    
    # 1) Генерим текст
    text = await make_story_text(lang=lang, target_sec=target_sec, preset=preset)
    parts = (text or "Untitled\n\n").split("\n", 1)
    title = parts[0].strip() or "Untitled"
    body = (parts[1] if len(parts) > 1 else "").strip()
    
    # 2) Рендерим PNG кадры
    frames_dir = os.path.join(out_dir, "frames")
    fps = int(channel.get("fps") or 30)
    theme_cfg = {
        "subreddit": channel.get("reddit_subreddit") or "r/AskReddit",
        "meta": channel.get("reddit_meta") or "↑ 12.3k • 6 hours ago",
        "pad": 24,
    }
    
    render_reddit_frames(
        out_dir=frames_dir,
        raw_title=title,
        raw_body=body,
        fps=fps,
        duration=float(target_sec),
        theme_cfg=theme_cfg,
        canvas=(1080, 960),
    )
    
    return {
        "title": title,
        "body": body,
        "tts_text": f"{title}. {body}",
        "frames_dir": frames_dir,
        "duration_sec": float(target_sec),
    }


async def compose(frames_dir: str, bg_video_path: str,
                 duration: float, fps: int, out_dir: str,
                 background_type: str = "video",
                 card_position: str = "center") -> str:
    """Склеивает финальное видео"""
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "reddit_visual.mp4")

    # Выбираем тип композиции в зависимости от background_type
    if background_type == "animation":
        await compose_pngseq_animation(
            bg_video_path=bg_video_path,
            frames_dir=frames_dir,
            duration=float(duration),
            fps=int(fps),
            out_path=out_path,
            card_position=card_position,
        )
    else:  # video или любой другой тип - используем blur
        await compose_pngseq_blur_base(
            bg_video_path=bg_video_path,
            frames_dir=frames_dir,
            duration=float(duration),
            fps=int(fps),
            out_path=out_path,
        )

    return out_path