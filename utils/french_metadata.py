# utils/french_metadata.py
"""
Генерация французских тегов и описаний для видео
"""
import asyncio
from typing import Dict, List
from utils.config import OPENAI_API_KEY, GROK_API_KEY

# Используем Grok API если есть ключ, иначе OpenAI
USE_GROK = bool(GROK_API_KEY)
GROK_CHAT_URL = "https://api.x.ai/v1/chat/completions"
OPENAI_CHAT_URL = "https://api.openai.com/v1/chat/completions"

# Модели
GROK_MODEL = "grok-3"
OPENAI_MODEL = "gpt-4o-mini"

# Выбираем API
API_URL = GROK_CHAT_URL if USE_GROK else OPENAI_CHAT_URL
API_KEY = GROK_API_KEY if USE_GROK else OPENAI_API_KEY
MODEL = GROK_MODEL if USE_GROK else OPENAI_MODEL


async def generate_french_metadata(story_text: str, story_type: str = "default") -> Dict[str, any]:
    """
    Генерирует французское описание и хештеги для истории

    Args:
        story_text: Текст истории на любом языке
        story_type: Тип истории (default, educational, reddit)

    Returns:
        {
            "description": "Описание до 100 символов на французском",
            "hashtags": ["#hashtag1", "#hashtag2", "#hashtag3", "#hashtag4"]
        }
    """
    if not API_KEY:
        # Fallback если нет API ключа
        return {
            "description": "Histoire intéressante et captivante",
            "hashtags": ["#histoire", "#viral", "#trending", "#shortsvideo"]
        }

    # Определяем промпт в зависимости от типа истории
    if story_type == "educational":
        context = "une histoire éducative et informative"
        suggested_tags = "#éducation #savoir #culture #apprendre"
    elif story_type in ("reddit", "default"):
        context = "une histoire de vie captivante et dramatique"
        suggested_tags = "#histoire #vrai #choquant #viral"
    else:
        context = "une histoire intéressante"
        suggested_tags = "#histoire #viral #trending #shortsvideo"

    system_prompt = (
        "Tu es un expert en création de contenu viral pour TikTok et YouTube Shorts en français. "
        "Tu dois créer des descriptions courtes et percutantes avec des hashtags qui maximisent l'engagement."
    )

    user_prompt = f"""Voici le texte d'une histoire (peut être en russe, anglais ou français):

{story_text[:500]}

C'est {context}.

Génère pour cette vidéo:
1. Une description accrocheuse de MAXIMUM 100 caractères en français (très important: pas plus de 100 caractères!)
2. Exactement 4 hashtags pertinents en français qui vont générer des vues

La description doit:
- Être en français
- Faire maximum 100 caractères (CRITIQUE!)
- Être percutante et donner envie de regarder
- Pas de guillemets, juste le texte

Les hashtags doivent:
- Être au format #hashtag
- Être en français
- Être en rapport avec le thème de l'histoire
- Attirer l'audience TikTok/YouTube Shorts
- Exemples de thèmes: {suggested_tags}

FORMAT DE RÉPONSE (respecte exactement ce format):
DESCRIPTION: [ta description de max 100 caractères]
HASHTAGS: #tag1 #tag2 #tag3 #tag4
"""

    try:
        import aiohttp
        headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

        payload = {
            "model": MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 200,
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(API_URL, json=payload, headers=headers, timeout=60) as resp:
                data = await resp.json()
                if resp.status != 200:
                    api_name = "Grok" if USE_GROK else "OpenAI"
                    print(f"{api_name} error {resp.status}: {data}")
                    raise RuntimeError(f"{api_name} error")

                text = data["choices"][0]["message"]["content"].strip()

                # Парсим ответ
                description = ""
                hashtags = []

                for line in text.split("\n"):
                    line = line.strip()
                    if line.startswith("DESCRIPTION:"):
                        description = line.replace("DESCRIPTION:", "").strip()
                        # Обрезаем до 100 символов если длиннее
                        if len(description) > 100:
                            description = description[:97] + "..."
                    elif line.startswith("HASHTAGS:"):
                        tags_str = line.replace("HASHTAGS:", "").strip()
                        hashtags = [tag.strip() for tag in tags_str.split() if tag.startswith("#")]

                # Проверяем что получили результат
                if not description:
                    description = "Histoire captivante à découvrir"

                if len(hashtags) < 4:
                    # Добавляем дефолтные хештеги если не хватает
                    default_tags = ["#histoire", "#viral", "#trending", "#shortsvideo", "#pourtoi", "#fyp"]
                    for tag in default_tags:
                        if tag not in hashtags and len(hashtags) < 4:
                            hashtags.append(tag)

                # Берем только первые 4 хештега
                hashtags = hashtags[:4]

                return {
                    "description": description,
                    "hashtags": hashtags
                }

    except Exception as e:
        print(f"Error generating French metadata: {e}")
        # Fallback
        return {
            "description": "Histoire intéressante et captivante",
            "hashtags": ["#histoire", "#viral", "#trending", "#shortsvideo"]
        }


def format_french_caption(title: str, description: str, hashtags: List[str]) -> str:
    """
    Форматирует финальную подпись для видео

    Args:
        title: Заголовок истории
        description: Французское описание
        hashtags: Список хештегов

    Returns:
        Отформатированная подпись
    """
    hashtags_str = " ".join(hashtags)
    return f"{description}\n\n{hashtags_str}"
