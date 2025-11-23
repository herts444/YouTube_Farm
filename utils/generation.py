# utils/generation.py
from __future__ import annotations

import os
from typing import Any, Dict, Union

from utils.backgrounds import choose_random_bg_segment
from utils.ffmpeg import mux_av_with_optional_subs, probe_duration
from utils.subtitles import build_srt_by_text_length
from utils.tts import synthesize_tts

# Импортируем из папки RedditStory если файл не создан
try:
    from utils.engines.RedditStory import generate as reddit_generate, compose as reddit_compose
except ImportError:
    try:
        # Пробуем из старой структуры папки
        from utils.engines.RedditStory import generate as reddit_generate, compose as reddit_compose
    except:
        # Если ничего не работает, импортируем встроенные функции
        # (код RedditStory вставлен прямо сюда)
        pass

# Модуль для «Нарезок»
from utils.cuts import make_cut_from_collection

# Если импорт не сработал, определяем функции прямо здесь
if 'reddit_generate' not in globals():
    from utils.story_gen import generate_story as _llm_generate
    from utils.config import FFMPEG_BIN
    from utils.ffmpeg import _run as _ffrun
    
    async def reddit_generate(channel: Dict[str, Any], out_dir: str) -> Dict[str, Any]:
        """Упрощенная генерация Reddit истории"""
        os.makedirs(out_dir, exist_ok=True)
        
        lang = str(channel.get("tts_lang") or "en").lower()
        target_sec = int(channel.get("reddit_target_sec") or 75)
        preset = str(channel.get("prompt_preset") or "default")
        
        # Получаем промпт из БД
        prompt = None
        try:
            from db.database import db
            doc = await db().prompts.find_one({"scope": "reddit", "preset": preset, "lang": lang})
            if doc and doc.get("text"):
                prompt = doc["text"]
        except Exception:
            pass
        
        if not prompt:
            if lang.startswith("ru"):
                prompt = (
                    "Напиши захватывающую историю в стиле Reddit от первого лица. "
                    "Начни с шокирующего признания или неожиданной ситуации. "
                    "Развивай интригу через конкретные детали и диалоги. "
                    "В кульминации раскрой неожиданный поворот, который всё меняет. "
                    "Финал должен оставить читателя в размышлениях. "
                    "Используй короткие предложения для динамики. "
                    "Без морали и нравоучений. Длина: 150-220 слов."
                )
            else:
                prompt = (
                    "Write a captivating Reddit-style first-person story. "
                    "Start with a shocking confession or unexpected situation. "
                    "Build intrigue through specific details and dialogue. "
                    "At the climax, reveal a twist that changes everything. "
                    "The ending should leave readers thinking. "
                    "Use short sentences for pacing. "
                    "No moral lessons. Length: 150-220 words."
                )
        
        # Генерим текст
        text = await _llm_generate(prompt, f"reddit [{lang}]", lang, target_sec=target_sec)
        parts = (text or "Untitled\n\n").split("\n", 1)
        title = parts[0].strip() or "Untitled"
        body = (parts[1] if len(parts) > 1 else "").strip()
        
        # Создаем простые текстовые кадры (заглушка вместо PNG)
        frames_dir = os.path.join(out_dir, "frames")
        os.makedirs(frames_dir, exist_ok=True)
        
        return {
            "title": title,
            "body": body,
            "tts_text": f"{title}. {body}",
            "frames_dir": frames_dir,
            "duration_sec": float(target_sec),
        }
    
    async def reddit_compose(frames_dir: str, bg_video_path: str,
                             duration: float, fps: int, out_dir: str) -> str:
        """Упрощенная композиция - просто копируем фон"""
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, "reddit_visual.mp4")
        
        # Простая обрезка фона до нужной длительности
        d = f"{duration:.3f}"
        await _ffrun(
            FFMPEG_BIN, "-y",
            "-i", bg_video_path,
            "-t", d,
            "-vf", "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2",
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
            out_path
        )
        return out_path


__all__ = ["generate_short", "generate_for_channel"]


def _norm_str(x: Any, default: str = "") -> str:
    return default if x is None else str(x).strip()


async def _resolve_channel(channel: Union[Dict[str, Any], str, int]) -> Dict[str, Any]:
    """Допускаем dict/имя/_id/tg_channel_id; при ошибках — отдаём вменяемый дефолт"""
    if isinstance(channel, dict):
        return channel

    try:
        from db.database import db
        query: Dict[str, Any] = {}
        if isinstance(channel, int):
            query = {"tg_channel_id": channel}
        elif isinstance(channel, str):
            from bson import ObjectId
            if len(channel) in (12, 24):
                try:
                    query = {"_id": ObjectId(channel)}
                except Exception:
                    query = {}
            if not query:
                query = {"name": channel}
        if query:
            doc = await db().channels.find_one(query)
            if doc:
                return dict(doc)
    except Exception:
        pass

    # sane defaults
    return {
        "theme": "reddit",
        "tts_engine": "gtts",
        "tts_lang": "en",
        "fps": 30,
        "reddit_target_sec": 75,
        "prompt_preset": "default",
    }


async def _generate_reddit(ch: Dict[str, Any], out_dir: str) -> Dict[str, str]:
    """Генерация Reddit истории с синхронизацией текста и аудио"""
    # 1) Генерируем только текст (БЕЗ рендеринга кадров)
    from utils.story_gen import generate_story as _llm_generate

    lang = _norm_str(ch.get("tts_lang") or "en").lower()
    target_sec = int(ch.get("reddit_target_sec") or 75)
    preset = _norm_str(ch.get("prompt_preset") or "default")

    # Получаем промпт из БД
    prompt = None
    try:
        from db.database import db
        doc = await db().prompts.find_one({"scope": "reddit", "preset": preset, "lang": lang})
        if doc and doc.get("text"):
            prompt = doc["text"]
    except Exception:
        pass

    # Генерируем текст истории
    text = await _llm_generate(prompt, preset, lang, target_sec=target_sec)
    parts = (text or "Untitled\n\n").split("\n", 1)
    title = parts[0].strip() or "Untitled"
    body = (parts[1] if len(parts) > 1 else "").strip()
    tts_text = f"{title}. {body}"

    # 2) Генерируем TTS СРАЗУ, чтобы получить реальную длительность
    tts_voice = ch.get("tts_voice")
    tts_speed = float(ch.get("tts_speed") or 1.3)

    audio_path = os.path.join(out_dir, "voice.mp3")
    await synthesize_tts(
        text=tts_text,
        out_path=audio_path,
        voice=tts_voice,
        lang=lang,
        speed=tts_speed,
    )

    # Получаем РЕАЛЬНУЮ длительность аудио
    real_dur = await probe_duration(audio_path)
    dur = max(1.0, real_dur)

    # 3) ТЕПЕРЬ рендерим кадры с РЕАЛЬНОЙ длительностью аудио для синхронизации
    from utils.engines.RedditStory import render_reddit_frames

    frames_dir = os.path.join(out_dir, "frames")
    fps = int(ch.get("fps") or 30)
    theme_cfg = {
        "subreddit": ch.get("reddit_subreddit") or "r/AskReddit",
        "meta": ch.get("reddit_meta") or "↑ 12.3k • 6 hours ago",
        "pad": 24,
    }

    render_reddit_frames(
        out_dir=frames_dir,
        raw_title=title,
        raw_body=body,
        fps=fps,
        duration=dur,  # Используем РЕАЛЬНУЮ длительность аудио!
        theme_cfg=theme_cfg,
        canvas=(1080, 960),  # Нижняя половина экрана - карточка не на весь экран!
    )

    # 4) Получаем параметры фона
    background_type = _norm_str(ch.get("background_type") or "video").lower()
    card_position = _norm_str(ch.get("reddit_card_position") or "center").lower()

    # 5) Генерируем или выбираем фон
    if background_type == "animation":
        # Генерируем анимацию
        from utils.animations import AnimationGenerator
        import random

        anim_gen = AnimationGenerator(output_dir=out_dir)
        available_anims = anim_gen.get_available_animations()

        # Выбираем случайную анимацию или используем заданную в конфиге
        animation_type = ch.get("animation_type")
        if not animation_type or animation_type not in [a["type"] for a in available_anims]:
            # Случайный выбор если не задано или не найдено
            animation_type = random.choice(available_anims)["type"]

        bg_clip = await anim_gen.generate_animation(
            animation_type=animation_type,
            duration=int(dur) + 1,  # +1 секунда для запаса
            output_path=os.path.join(out_dir, "animation_bg.mp4"),
            resolution="1080p"
        )
    else:
        # Используем видео фон
        bg_clip = await choose_random_bg_segment(
            duration=dur,
            out_dir=out_dir,
            pool_dir=os.path.join("assets", "bg", "reddit"),  # fallback директория
            fallback=os.path.join("assets", "bg", "default.mp4"),
            scope="reddit"  # берет из БД в первую очередь
        )

    # 6) Композиция видеоряда (без аудио)
    composed_video = await reddit_compose(
        frames_dir=frames_dir,
        bg_video_path=bg_clip,
        duration=dur,
        fps=fps,
        out_dir=out_dir,
        background_type=background_type,
        card_position=card_position,
    )

    # 7) Субтитры (опционально) + финальный mux
    subs_lang = _norm_str(ch.get("subs_lang") or "") or None

    srt_path = None
    if subs_lang:
        srt_path = os.path.join(out_dir, "subs.srt")
        build_srt_by_text_length(text=tts_text, total_duration=dur, out_path=srt_path)

    final_path = os.path.join(out_dir, "final.mp4")
    await mux_av_with_optional_subs(
        video_path=composed_video,
        audio_path=audio_path,
        srt_path=srt_path,
        out_path=final_path,
        metadata={"title": title},
    )

    # Обновляем счетчик генераций
    try:
        from db.database import db
        await db().channels.update_one(
            {"_id": ch.get("_id")},
            {"$inc": {"generated_total": 1}}
        )
    except Exception:
        pass

    return {
        "video_path": final_path,
        "text": f'{title}\n\n{body}',
        "is_reddit": "1",
    }


async def _generate_cuts(ch: Dict[str, Any], out_dir: str) -> Dict[str, str]:
    """Режим ✂️ Нарезки с поддержкой баннеров"""
    cuts = ch.get("cuts") or {}
    kind = (cuts.get("kind") or "cartoons").lower()
    collection = cuts.get("collection")
    mn = int(cuts.get("min_sec", 180))
    mx = int(cuts.get("max_sec", 240))

    if not collection:
        raise RuntimeError("Не выбрана коллекция для «Нарезок». Задай её в настройках канала.")

    # Получаем конфигурацию баннера из канала
    banner_config = ch.get("banner")  # {"file": "banner.png", "position": "top|center|bottom"}
    
    # Генерируем видео с баннером (если он есть)
    final, picked, seg_dur = await make_cut_from_collection(
        kind=kind,
        collection=collection,
        out_dir=out_dir,
        min_sec=mn,
        max_sec=mx,
        banner_config=banner_config  # Передаем конфиг баннера
    )

    # Обновляем счетчик
    try:
        from db.database import db
        await db().channels.update_one(
            {"_id": ch.get("_id")},
            {"$inc": {"generated_total": 1}}
        )
    except Exception:
        pass

    # Добавляем информацию о баннере в результат
    banner_info = ""
    if banner_config:
        banner_info = f" • Banner: {banner_config.get('file', 'none')} [{banner_config.get('position', 'center')}]"

    return {
        "video_path": final,
        "text": f"Cut from {collection} • {picked} • {int(seg_dur)}s{banner_info}",
        "is_cuts": "1",
    }


async def generate_for_channel(channel: Union[Dict[str, Any], str, int], out_dir: str) -> Dict[str, str]:
    ch = await _resolve_channel(channel)

    # Если у канала задан cuts-конфиг — считаем, что это тематика «Нарезки»
    if ch.get("cuts"):
        return await _generate_cuts(ch, out_dir)

    # Проверяем режим animation_only
    if ch.get("mode") == "animation_only":
        return await _generate_animation_only(ch, out_dir)

    # Иначе пытаемся распознать строковую тематику
    theme_name = _norm_str(ch.get("theme") or ch.get("theme_name") or "")
    if "reddit" in theme_name.lower() or not theme_name:
        return await _generate_reddit(ch, out_dir)

    # Поддержка явных строк вида "✂️ Нарезки"
    low = theme_name.lower()
    if "нарезк" in low or "cuts" in low:
        if not ch.get("cuts"):
            raise RuntimeError("Тематика «Нарезки» выбрана, но конфиг cuts не задан для канала.")
        return await _generate_cuts(ch, out_dir)

    # Если ничего не подошло - генерим Reddit по умолчанию
    return await _generate_reddit(ch, out_dir)


# Обратная совместимость
async def _generate_animation_only(ch: Dict[str, Any], out_dir: str) -> Dict[str, str]:
    """Генерация видео: только анимация + озвучка истории (без карточки)"""
    from utils.story_gen import generate_story as _llm_generate
    from utils.animations import AnimationGenerator
    import random

    os.makedirs(out_dir, exist_ok=True)

    # 1) Параметры
    lang = _norm_str(ch.get("tts_lang") or "en").lower()
    target_sec = int(ch.get("reddit_target_sec") or 75)
    preset = str(ch.get("prompt_preset") or "default")

    # 2) Генерируем текст истории
    prompt = None
    try:
        from db.database import db
        doc = await db().prompts.find_one({"scope": "reddit", "preset": preset, "lang": lang})
        if doc and doc.get("text"):
            prompt = doc["text"]
    except Exception:
        pass

    if not prompt:
        if lang.startswith("ru"):
            prompt = (
                "Расскажи ТРИГГЕРНУЮ и провокационную историю из жизни от первого лица. "
                "ОБЯЗАТЕЛЬНО используй одну из этих тем или похожих:\n"
                "- Девушка моего друга напилась и что-то произошло между нами\n"
                "- Когда мне исполнилось 20, друзья затащили меня в стриптиз-клуб и заказали приват-танец\n"
                "- Застукал супруга с любовником/любовницей в неожиданном месте\n"
                "- Коллега по работе сделала мне неожиданное предложение на корпоративе\n"
                "- Соседка постучалась ко мне ночью в одном белье\n"
                "- Бывшая вернулась через 5 лет и призналась в шокирующем\n\n"
                "КОНТЕНТ:\n"
                "- История должна быть ТРЕШОВОЙ и скандальной\n"
                "- Используй ЦЕНЗУРУ чтобы обойти бан ТикТока (замени откровенные слова на '*', 'н-слово', 'п-слово' и т.д.)\n"
                "- Мат МОЖНО использовать, но с цензурой (например: 'бл*', 'х*й', 'п*здец')\n"
                "- Начни с МАКСИМАЛЬНО цепляющего момента\n"
                "- Создай интригу и драму\n\n"
                "СТИЛЬ И ЯЗЫК:\n"
                "- Пиши МАКСИМАЛЬНО естественно, как говорит обычный человек 18-25 лет\n"
                "- Используй МОЛОДЕЖНЫЙ СЛЕНГ: 'зашквар', 'красава', 'жиза', 'кринж', 'вайб', 'рофл', 'чилить', 'краш', 'флексить', 'агриться', 'рил'\n"
                "- Добавляй разговорные словечки: 'типа', 'короче', 'ну', 'вообще', 'прикинь', 'реально', 'кароч', 'ваще', 'значит'\n"
                "- Используй ЖИВЫЕ эмоции и восклицания: 'Вау!', 'Офигеть!', 'Капец!', 'Жесть!', 'Ого!', 'Ничё себе!'\n"
                "- Пиши так, как будто рассказываешь другу историю вживую, без формальностей\n\n"
                "АДАПТАЦИЯ ДЛЯ ОЗВУЧКИ НЕЙРОСЕТЬЮ:\n"
                "- Используй КОРОТКИЕ предложения (5-10 слов) для естественных пауз и дыхания\n"
                "- Ставь многоточия '...' для драматических пауз и напряжения\n"
                "- Используй тире '—' для резких смен мысли или неожиданных моментов\n"
                "- Добавляй восклицательные знаки '!' для эмоциональных акцентов и правильной интонации\n"
                "- Используй вопросы '?' чтобы создать интригу и естественную вопросительную интонацию\n"
                "- Выделяй ВАЖНЫЕ слова заглавными буквами для ударения: 'Она РЕАЛЬНО это сделала', 'Я был в ШОКЕ'\n"
                "- Разбивай длинные мысли запятыми для правильного дыхания и ритма\n"
                "- Пиши числительные словами: 'двадцать лет' вместо '20 лет', 'три часа ночи' вместо '3 часа'\n"
                "- Используй фразовые паузы: начинай новые мысли с новой строки или после точки\n\n"
                "СТРУКТУРА:\n"
                "- Начни с ВЗРЫВНОГО момента, сразу в действие (без предисловий!)\n"
                "- Используй короткие абзацы (2-3 предложения)\n"
                "- Чередуй короткие и чуть более длинные фразы для естественного ритма\n"
                "- Заканчивай на пике эмоций или неожиданным поворотом\n"
                "- Длина: 150-220 слов\n\n"
                "ПРИМЕР ПРАВИЛЬНОГО СТИЛЯ:\n"
                "'Значит, прихожу я домой... А там ОНА. С моим лучшим другом! На МОЁм диване, ваще. Типа, я офигел конкретно. Стою, смотрю на эту жизу... И вообще не врубаюсь, что происходит. Она как подскочила — глаза размером с тарелки! Короче, началась такая жесть...'\n\n"
                "ВАЖНО: НЕ используй литературный язык! Только живая разговорная речь!"
            )
        else:
            prompt = (
                "Tell a TRIGGERING and provocative life story in first person. "
                "MUST use one of these themes or similar:\n"
                "- My friend's girlfriend got drunk and something happened between us\n"
                "- When I turned 20, friends took me to a strip club and got me a private dance\n"
                "- Caught my spouse with their lover in an unexpected place\n"
                "- Coworker made me an unexpected proposition at the office party\n"
                "- Neighbor knocked on my door at night wearing only underwear\n"
                "- Ex came back after 5 years and confessed something shocking\n\n"
                "CONTENT:\n"
                "- Story must be TRASHY and scandalous\n"
                "- Use CENSORSHIP to avoid TikTok bans (replace explicit words with '*', 's-word', 'p-word', etc.)\n"
                "- Profanity is ALLOWED but censored (e.g., 'f*ck', 'sh*t', 'd*mn')\n"
                "- Start with the MOST captivating moment\n"
                "- Create intrigue and drama\n\n"
                "STYLE & LANGUAGE:\n"
                "- Write SUPER naturally, like a real 18-25 year old talking\n"
                "- Use YOUTH SLANG: 'ngl', 'fr fr', 'lowkey', 'highkey', 'sus', 'cap/no cap', 'vibe', 'slay', 'rizz', 'simp', 'based'\n"
                "- Add conversational fillers: 'like', 'literally', 'honestly', 'basically', 'I mean', 'you know', 'right?'\n"
                "- Use LIVE emotions and reactions: 'Yo!', 'Bruh!', 'OMG!', 'No way!', 'Damn!', 'Holy sh*t!'\n"
                "- Write like you're telling a friend IRL, super casual and real\n\n"
                "TTS NEURAL VOICE OPTIMIZATION:\n"
                "- Use SHORT sentences (5-10 words) for natural pauses and breathing\n"
                "- Add ellipsis '...' for dramatic pauses and tension\n"
                "- Use em-dashes '—' for sudden thought changes or shocking moments\n"
                "- Add exclamation marks '!' for emotional emphasis and proper intonation\n"
                "- Use questions '?' to create intrigue and natural questioning tone\n"
                "- CAPITALIZE important words for stress: 'She ACTUALLY did that', 'I was SHOCKED'\n"
                "- Break long thoughts with commas for proper breathing rhythm\n"
                "- Write numbers as words: 'twenty years old' not '20', 'three AM' not '3 AM'\n"
                "- Use phrase breaks: start new thoughts on new lines or after periods\n\n"
                "STRUCTURE:\n"
                "- Start with EXPLOSIVE moment, jump right into action (NO intro!)\n"
                "- Use short paragraphs (2-3 sentences)\n"
                "- Alternate between short and slightly longer phrases for rhythm\n"
                "- End on emotional peak or plot twist\n"
                "- Length: 150-220 words\n\n"
                "EXAMPLE OF CORRECT STYLE:\n"
                "'So I walk into my apartment... And there SHE is. With my best friend! On MY couch, literally. Like, I completely froze. Just standing there, staring at this mess... Can't even process what's happening. She JUMPED up — eyes wide as plates! Bro, absolute chaos started...'\n\n"
                "CRITICAL: NO formal/literary language! Only natural conversational speech!"
            )

    text = await _llm_generate(prompt, f"animation_story [{lang}]", lang, target_sec=target_sec)

    # 3) Генерируем анимацию
    anim_gen = AnimationGenerator(output_dir=out_dir)
    available_anims = anim_gen.get_available_animations()

    # Выбираем анимацию
    animation_type = ch.get("animation_type")
    if not animation_type or animation_type not in [a["type"] for a in available_anims]:
        animation_type = random.choice(available_anims)["type"]

    animation_path = await anim_gen.generate_animation(
        animation_type=animation_type,
        duration=target_sec + 1,
        output_path=os.path.join(out_dir, "animation.mp4"),
        resolution="1080p"
    )

    # 4) Генерируем TTS
    tts_voice = ch.get("tts_voice")
    tts_speed = float(ch.get("tts_speed") or 1.3)  # Ускорено на ~20%

    audio_path = os.path.join(out_dir, "voice.mp3")
    await synthesize_tts(
        text=text,
        out_path=audio_path,
        voice=tts_voice,
        lang=lang,
        speed=tts_speed,
    )

    # 5) Получаем реальную длительность аудио
    real_dur = await probe_duration(audio_path)

    # 6) Обрезаем/зацикливаем анимацию под длительность аудио и добавляем аудио
    final_path = os.path.join(out_dir, "final.mp4")
    await _mux_animation_audio(animation_path, audio_path, real_dur, final_path)

    # Обновляем счетчик
    try:
        from db.database import db
        await db().channels.update_one(
            {"_id": ch.get("_id")},
            {"$inc": {"generated_total": 1}}
        )
    except Exception:
        pass

    return {
        "video_path": final_path,
        "text": text,
        "is_animation_only": "1",
    }


async def _mux_animation_audio(animation_path: str, audio_path: str,
                                duration: float, out_path: str) -> None:
    """Совмещает анимацию с аудио, зацикливая анимацию если нужно"""
    from utils.config import FFMPEG_BIN
    from utils.ffmpeg import _run as _ffrun

    d = f"{duration:.3f}"

    # Зацикливаем анимацию и добавляем аудио
    await _ffrun(
        FFMPEG_BIN, "-y",
        "-stream_loop", "-1", "-i", animation_path,  # Зацикливаем анимацию
        "-i", audio_path,
        "-t", d,
        "-map", "0:v",  # Видео из первого входа (анимация)
        "-map", "1:a",  # Аудио из второго входа (озвучка)
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-crf", "23",
        "-c:a", "aac",
        "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        out_path
    )


async def generate_short(channel: Union[Dict[str, Any], str, int], out_dir: str) -> Dict[str, str]:
    return await generate_for_channel(channel, out_dir)