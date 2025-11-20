# utils/story_gen.py
import os
import re
import random
from typing import Optional

from utils.config import OPENAI_API_KEY

OPENAI_CHAT_URL = "https://api.openai.com/v1/chat/completions"
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

def _trim(text: str) -> str:
    return re.sub(r"\n{3,}", "\n\n", (text or "").strip())

def _sys_prompt(lang: str) -> str:
    if (lang or "").lower().startswith("ru"):
        return (
            "Ты рассказчик реальных историй из жизни обычных людей. Пиши как будто это случилось с тобой или твоим знакомым. "
            "Язык — живой, разговорный русский. Без пафоса и драматизации. "
            "ФОРМАТ: первая строка — короткий заголовок-суть (без кавычек). Затем 3-5 абзацев. "
            "СТИЛЬ: Пиши просто и честно. Конкретные детали быта. Реальные диалоги как люди говорят. "
            "Обычные эмоции обычных людей. История должна быть узнаваемой — такое могло случиться с каждым. "
            "БЕЗ: надуманных поворотов, шокирующих признаний, мистики, драмы ради драмы. "
            "Просто интересная жизненная ситуация."
        )
    # EN by default
    return (
        "You tell real-life stories of ordinary people. Write as if this happened to you or someone you know. "
        "Use natural, conversational English. No drama or exaggeration. "
        "FORMAT: first line is a short title that captures the essence (no quotes). Then 3-5 paragraphs. "
        "STYLE: Write simply and honestly. Specific everyday details. Real dialogue as people actually talk. "
        "Ordinary emotions of ordinary people. The story should be relatable — could happen to anyone. "
        "NO: contrived twists, shocking confessions, mystery, drama for drama's sake. "
        "Just an interesting slice of life."
    )

def _user_prompt(theme_prompt: str, lang: str, target_sec: int) -> str:
    # целим ~150–220 слов ≈ 60–90 сек (зависит от TTS)
    if (lang or "").lower().startswith("ru"):
        return (
            f"{theme_prompt}\n\n"
            f"Ограничения: длина 150–220 слов (≈ {target_sec} сек при озвучке). "
            "Первая строка — это заголовок. Далее — тело истории. Не добавляй форматирование Markdown."
        )
    return (
        f"{theme_prompt}\n\n"
        f"Constraints: 150–220 words (≈ {target_sec}s read). "
        "First line is the title. Then the body. Do NOT add Markdown formatting."
    )

async def generate_story(theme_prompt: Optional[str], theme_name: Optional[str], lang: str, target_sec: int = 75) -> str:
    """
    Возвращает строку: первая строка — title, далее — body. Язык управляется lang ('ru'|'en').
    theme_prompt имеет приоритет; если его нет — делаем пресет по имени темы.
    """
    prompt = (theme_prompt or "").strip()
    if not prompt:
        # пресеты по имени темы
        name = (theme_name or "").lower()
        if "reddit" in name or "реддит" in name:
            prompt = (
                "Расскажи РЕАЛЬНУЮ историю от первого лица. Выбери ОДНУ тему:\n"
                "• Как я устроился на работу и что там увидел в первый день\n"
                "• Разговор с таксистом который запомнился\n"
                "• Случай в магазине/кафе/транспорте\n"
                "• Как помог незнакомцу или незнакомец помог мне\n"
                "• Неловкая ситуация на работе/учёбе\n"
                "• Что я понял после ссоры с другом/родственником\n"
                "• Случайная встреча со старым знакомым\n\n"
                "ВАЖНО: Пиши как обычный человек рассказывает историю другу. "
                "Конкретные детали: что сказал, что ответил, что подумал. "
                "Реальные эмоции: раздражение, удивление, смущение, радость. "
                "Простой язык без красивостей. Диалоги как люди реально говорят. "
                "История должна быть УЗНАВАЕМОЙ — читатель думает 'о, у меня тоже такое было'. "
                "Без драматизации, без морали, без Reddit."
                if lang.startswith("ru")
                else
                "Tell a REAL first-person story. Pick ONE topic:\n"
                "• My first day at a new job and what I saw\n"
                "• A taxi/uber driver conversation I remember\n"
                "• Something that happened at a store/cafe/on the bus\n"
                "• How I helped a stranger or they helped me\n"
                "• An awkward moment at work/school\n"
                "• What I realized after an argument with friend/family\n"
                "• Running into someone from my past\n\n"
                "IMPORTANT: Write like a regular person telling a story to a friend. "
                "Specific details: what was said, what you replied, what you thought. "
                "Real emotions: annoyance, surprise, embarrassment, happiness. "
                "Simple language, no fancy words. Dialogue as people actually talk. "
                "Story must be RELATABLE — reader thinks 'yeah that happened to me too'. "
                "No drama, no moral lessons, don't mention Reddit."
            )
        else:
            prompt = "Write a short, engaging story for a vertical short video." if not lang.startswith("ru") \
                     else "Напиши короткую, увлекательную историю для вертикального шорт-видео."

    if not OPENAI_API_KEY:
        # Фолбэк, чтобы ничего не падало — но лучше поставить ключ
        return "Untitled Story\n\nI missed the bus to my exam, but a stranger offered me a ride. I made it just in time."

    import aiohttp
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": _sys_prompt(lang)},
            {"role": "user", "content": _user_prompt(prompt, lang, target_sec)}
        ],
        "temperature": 1.0,  # Повышена для большего разнообразия и креативности
        "max_tokens": 700,   # Увеличено для более развёрнутых историй
        "presence_penalty": 0.3,  # Поощряем новые темы
        "frequency_penalty": 0.3  # Избегаем повторений
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(OPENAI_CHAT_URL, json=payload, headers=headers, timeout=120) as resp:
            data = await resp.json()
            if resp.status != 200:
                raise RuntimeError(f"OpenAI error {resp.status}: {data}")
            text = data["choices"][0]["message"]["content"]
            text = _trim(text)

    # Страхуемся: если модель вернула без явного заголовка — подставим
    parts = text.splitlines()
    if len(parts) <= 1:
        title = "Story"
        body = text
        return f"{title}\n\n{body}"
    return text
