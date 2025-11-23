# utils/story_gen.py
import os
import re
from typing import Optional

from utils.config import OPENAI_API_KEY, GROK_API_KEY

# Используем Grok API если есть ключ, иначе OpenAI
USE_GROK = bool(GROK_API_KEY)
GROK_CHAT_URL = "https://api.x.ai/v1/chat/completions"
OPENAI_CHAT_URL = "https://api.openai.com/v1/chat/completions"

# Модели
GROK_MODEL = "grok-3"
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# Выбираем API
API_URL = GROK_CHAT_URL if USE_GROK else OPENAI_CHAT_URL
API_KEY = GROK_API_KEY if USE_GROK else OPENAI_API_KEY
MODEL = GROK_MODEL if USE_GROK else OPENAI_MODEL

def _trim(text: str) -> str:
    return re.sub(r"\n{3,}", "\n\n", (text or "").strip())

def _sys_prompt(lang: str) -> str:
    if (lang or "").lower().startswith("ru"):
        return (
            "Ты настоящий рассказчик с миллионами слушателей. Пишешь от первого лица, как будто это случилось с тобой недавно.\n\n"

            "Твоя задача — рассказать историю которая заставит людей остановиться и слушать. Не выдумывай формулы, не следуй шаблонам. "
            "Каждая история уникальна. Иногда она начинается с мелочи, иногда — с взрыва эмоций. Иногда финал неожиданный, иногда — он и так понятен, но путь к нему цепляет. "
            "Главное — чтобы читатель почувствовал, что это РЕАЛЬНАЯ жизнь, а не выдуманный сценарий.\n\n"

            "СТРОГО на русском языке! Никаких английских слов типа okay, well, seriously, like, whatever, actually, basically. "
            "Только русские выражения: ладно, короче, серьезно, типа, вообще, реально.\n\n"

            "Структура проста: короткий цепляющий заголовок, потом 4-6 абзацев истории. Каждый абзац — 2-4 предложения. "
            "НО не делай это очевидным! Пусть история течет естественно.\n\n"

            "Пиши живым языком:\n"
            "- Как говоришь с другом за столом. С паузами, недоговорками, междометиями\n"
            "- Конкретные детали: что человек сказал, как посмотрел, что ты подумал в тот момент\n"
            "- Реальные эмоции без пафоса: злость, стыд, страх, облегчение, удивление\n"
            "- Внутренний монолог: 'я подумал', 'сердце ёкнуло', 'мне стало не по себе'\n"
            "- Диалоги настоящие — люди не говорят законченными фразами, они запинаются, бросают слова\n\n"

            "Что цепляет:\n"
            "- Когда что-то идет не по плану\n"
            "- Когда узнаешь то, что не должен был\n"
            "- Когда обычная ситуация разворачивается неожиданно\n"
            "- Когда чьи-то слова или действия меняют все\n"
            "- Когда понимаешь правду которая била по глазам а ты не замечал\n\n"

            "ИЗБЕГАЙ:\n"
            "- Одинаковых зачинов ('Никогда не думал что', 'Это случилось когда')\n"
            "- Морали и выводов в конце ('Теперь я понял что', 'С тех пор я')\n"
            "- Надуманной драмы и преувеличений\n"
            "- Предсказуемых финалов\n"
            "- Слов-триггеров: оружие, наркотики, политика, явное насилие\n"
            "- Повторяющихся структур и клише\n\n"

            "Темы которые реально цепляют (выбери что зайдет, но не ограничивайся этим):\n\n"
            "ОТНОШЕНИЯ И ИЗМЕНЫ:\n"
            "Застукал парня/девушку с кем-то. Увидел переписку которую не должен был. "
            "Друг признался что спит с моей бывшей. Понял что меня использовали ради денег/квартиры. "
            "На свадьбе/вечеринке случилось ЧТО-ТО.\n\n"
            "ДЕНЬГИ И ПРЕДАТЕЛЬСТВО:\n"
            "Узнал что друг/партнер крал у меня. Коллега подставил и я потерял работу. "
            "Родственник оказался в долгах. Выиграл крупную сумму и люди изменились.\n\n"
            "СКАНДАЛЫ И РАЗОБЛАЧЕНИЯ:\n"
            "Узнал грязный секрет о человеке которого все уважают. Случайно увидел что делает сосед/коллега. "
            "Нашел улики которые разрушили чью-то жизнь. На вечеринке кто-то признался в ТАКОМ.\n\n"
            "КОНФЛИКТЫ И ДРАКИ:\n"
            "Драка из-за девушки/денег. Словесная перепалка переросла в ТАКОЕ. "
            "Кто-то наехал не на того. Месть за предательство.\n\n"
            "РЕЗКАЯ СМЕНА СУДЬБЫ:\n"
            "Одна встреча изменила всю жизнь. Один звонок/сообщение и жизнь рухнула. "
            "Случайное решение привело к ТАКИМ последствиям. Был на дне, через день на коне.\n\n"
            "ИНТИМНЫЕ СИТУАЦИИ (БЕЗ ПОРНО):\n"
            "Случайно узнал о тайной связи. Пьяная вечеринка закончилась ТАКИМИ последствиями. "
            "Утро после которое изменило отношения. Застукал людей в неожиданном месте.\n\n"

            "Пиши ОСТРО но без мата и явного контента. Намекай, дай читателю домыслить самому. "
            "Фокус на эмоциях и последствиях, а не на деталях действия.\n\n"

            "Главное: читатель должен подумать 'блин, вот это поворот' или 'я бы на его месте...' или 'как он после этого живет?'. "
            "Не стремись к шаблонным реакциям — стремись к тому чтобы история задержалась в голове."
        )
    # EN by default
    return (
        "You're a genuine storyteller with millions of listeners. You write in first person, as if this happened to you recently.\n\n"

        "Your task is to tell a story that makes people stop and listen. Don't create formulas, don't follow templates. "
        "Each story is unique. Sometimes it starts with something small, sometimes with an emotional explosion. Sometimes the ending is unexpected, "
        "sometimes it's obvious but the journey is what hooks you. The key is making the reader feel this is REAL life, not a scripted scenario.\n\n"

        "Structure is simple: short catchy title, then 4-6 paragraphs of story. Each paragraph is 2-4 sentences. "
        "BUT don't make it obvious! Let the story flow naturally.\n\n"

        "Write in living language:\n"
        "- Like talking to a friend over drinks. With pauses, half-thoughts, interjections\n"
        "- Concrete details: what they said, how they looked, what you thought in that moment\n"
        "- Real emotions without drama: anger, shame, fear, relief, surprise\n"
        "- Internal monologue: 'I thought', 'my heart sank', 'I got this sick feeling'\n"
        "- Real dialogue — people don't speak in complete sentences, they stutter, drop words\n\n"

        "What hooks people:\n"
        "- When something doesn't go as planned\n"
        "- When you learn something you weren't supposed to\n"
        "- When a normal situation turns unexpected\n"
        "- When someone's words or actions change everything\n"
        "- When you realize a truth that was staring you in the face\n\n"

        "AVOID:\n"
        "- Same openings ('Never thought that', 'This happened when')\n"
        "- Morals and lessons at the end ('Now I understand that', 'Since then I')\n"
        "- Fake drama and exaggeration\n"
        "- Predictable endings\n"
        "- Trigger words: weapons, drugs, politics, explicit violence\n"
        "- Repetitive structures and clichés\n\n"

        "Themes that actually hook people (pick what hits, but don't limit yourself):\n\n"
        "RELATIONSHIPS & CHEATING:\n"
        "Caught partner with someone. Saw messages you weren't supposed to. "
        "Friend confessed they're sleeping with your ex. Realized someone was using you for money/place. "
        "Something went DOWN at a wedding/party.\n\n"
        "MONEY & BETRAYAL:\n"
        "Found out friend/partner was stealing from you. Coworker backstabbed and you lost job. "
        "Relative in huge debt. Won big money and people changed.\n\n"
        "SCANDALS & EXPOSURES:\n"
        "Learned dirty secret about someone everyone respects. Accidentally saw what neighbor/coworker does. "
        "Found evidence that destroyed someone's life. Someone confessed THAT at a party.\n\n"
        "CONFLICTS & FIGHTS:\n"
        "Fight over girl/money. Verbal argument escalated into THAT. "
        "Someone messed with wrong person. Revenge for betrayal.\n\n"
        "LIFE CHANGED IN ONE DAY:\n"
        "One meeting changed entire life. One call/message and life collapsed. "
        "Random decision led to SUCH consequences. Was at rock bottom, next day on top.\n\n"
        "INTIMATE SITUATIONS (NO PORN):\n"
        "Accidentally learned about secret affair. Drunk party ended with SUCH consequences. "
        "Morning after that changed relationships. Caught people in unexpected place.\n\n"

        "Write EDGY but without profanity and explicit content. Hint, let the reader fill in the blanks. "
        "Focus on emotions and consequences, not action details.\n\n"

        "The key: reader should think 'damn, what a twist' or 'I'd do the same' or 'how does he live with that?'. "
        "Don't aim for template reactions — aim for the story to stick in their head."
    )

def _user_prompt(theme_prompt: str, lang: str, target_sec: int) -> str:
    # целим ~250–380 слов для 1-2 минут при TTS 1.3x
    if (lang or "").lower().startswith("ru"):
        return (
            f"{theme_prompt}\n\n"
            f"КРИТИЧНО - ФОРМАТ ВЫВОДА:\n"
            f"- Длина: 250–380 слов (≈ {target_sec} сек при озвучке, идеально 1-2 минуты)\n"
            f"- Первая строка — это заголовок (обычный текст)\n"
            f"- Далее — тело истории\n"
            f"- НИКАКОГО форматирования: без **, __, *, _, #, `, [], (), <>, и других спецсимволов!\n"
            f"- Только обычный текст с буквами, цифрами, знаками препинания (точка, запятая, восклицательный, вопросительный)\n"
            f"- Запрещены символы Markdown: ** __ * _ # ` [ ] ( ) < >\n"
            f"- Пиши ЧИСТЫМ ТЕКСТОМ без какого-либо форматирования!"
        )
    return (
        f"{theme_prompt}\n\n"
        f"CRITICAL - OUTPUT FORMAT:\n"
        f"- Length: 250–380 words (≈ {target_sec}s read, ideally 1-2 minutes)\n"
        f"- First line is the title (plain text)\n"
        f"- Then the body\n"
        f"- NO formatting: no **, __, *, _, #, `, [], (), <>, or any special symbols!\n"
        f"- Only plain text with letters, numbers, punctuation (period, comma, exclamation, question mark)\n"
        f"- Forbidden Markdown symbols: ** __ * _ # ` [ ] ( ) < >\n"
        f"- Write in PLAIN TEXT without any formatting!"
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
        if "educational" in name or "познавательн" in name:
            prompt = (
                "Расскажи про один факт, феномен или историю которая заставит задуматься. "
                "Выбери что-то из психологии, науки, истории, природы, экономики или культуры. "
                "То что реально интересно, не избито и заставляет по-другому посмотреть на вещи.\n\n"
                "Рассказывай так, будто объясняешь другу за чашкой кофе. Не сухо, а с эмоциями и живыми примерами. "
                "Начни с чего-то что цепляет внимание — вопрос, удивительный факт, что-то что ломает стереотипы. "
                "Потом объясни суть простыми словами, добавь примеры из жизни.\n\n"
                "Избегай:\n"
                "- Заученных фраз типа 'Интересный факт', 'Знаете ли вы', 'Оказывается'\n"
                "- Длинных научных терминов без объяснений\n"
                "- Скучных списков и перечислений\n"
                "- Морали в конце\n\n"
                "Используй:\n"
                "- Вопросы которые заставляют задуматься: 'А ты замечал что...?', 'Почему...?'\n"
                "- Живые сравнения и аналогии\n"
                "- Конкретные примеры и истории\n"
                "- Связь с реальной жизнью\n\n"
                "СТРОГО на русском! Никаких английских слов (okay, actually, basically и т.д.)."
                if lang.startswith("ru")
                else
                "Tell about one fact, phenomenon or story that makes you think. "
                "Pick something from psychology, science, history, nature, economics or culture. "
                "Something genuinely interesting, not cliché, that makes you see things differently.\n\n"
                "Tell it like explaining to a friend over coffee. Not dry, but with emotion and real examples. "
                "Start with something that grabs attention — a question, surprising fact, something that breaks stereotypes. "
                "Then explain simply, add real-life examples.\n\n"
                "Avoid:\n"
                "- Rehearsed phrases like 'Interesting fact', 'Did you know', 'It turns out'\n"
                "- Long scientific terms without explanation\n"
                "- Boring lists and enumerations\n"
                "- Moral at the end\n\n"
                "Use:\n"
                "- Questions that make you think: 'Ever notice that...?', 'Why...?'\n"
                "- Living comparisons and analogies\n"
                "- Concrete examples and stories\n"
                "- Connection to real life"
            )
        elif "reddit" in name or "реддит" in name:
            prompt = (
                "Расскажи взрывную историю от первого лица. Выбери одну острую тему:\n\n"
                "ИЗМЕНЫ И ПРЕДАТЕЛЬСТВО:\n"
                "Застукал девушку/парня с моим лучшим другом. Нашел переписку и охренел. "
                "На вечеринке узнал что меня рогоносят уже полгода. Друг признался что трахался с моей бывшей всё время.\n\n"
                "ДЕНЬГИ И ЖАДНОСТЬ:\n"
                "Партнер слил общий бизнес и свалил с деньгами. Узнал что родственник воровал годами. "
                "Выиграл в лотерею и увидел настоящие лица людей. Коллега подставил чтобы забрать мою должность.\n\n"
                "ДРАКИ И КОНФЛИКТЫ:\n"
                "Наехал не на того чувака и огреб по полной (или наоборот). Драка из-за девушки закончилась ТАК. "
                "Месть за предательство (спланировал и осуществил). Словесная перепалка переросла в мордобой.\n\n"
                "ИНТИМНЫЕ СКАНДАЛЫ:\n"
                "После пьянки проснулся в ТАКОЙ ситуации. Застукал соседа/коллегу в пикантной ситуации. "
                "Узнал о тайной связи которая всех шокировала. Утро после вечеринки разрушило отношения.\n\n"
                "РЕЗКАЯ СМЕНА СУДЬБЫ:\n"
                "Один звонок и жизнь перевернулась. Спонтанное решение привело к ТАКИМ последствиям. "
                "Вчера был никем, сегодня всё изменилось (или наоборот). Случайная встреча изменила ВСЁ.\n\n"
                "ШОКИРУЮЩИЕ РАЗОБЛАЧЕНИЯ:\n"
                "Узнал что уважаемый человек на самом деле... Нашел улики которые разрушили чужую жизнь. "
                "Случайно увидел что творится за закрытыми дверями. Секрет который изменил всё моё отношение.\n\n"
                "Пиши ЖЁСТКО и без цензуры эмоций! 'охренел', 'офигел', 'в шоке' - это нормально. "
                "НО избегай прямого мата и явного порно. Намекай, интригуй, давай читателю додумать. "
                "Фокус на том КАК ты себя чувствовал, ЧТО подумал, КАКИЕ были последствия. "
                "Добавь детали: что он сказал ДОСЛОВНО, как выглядел, что ты ответил, что сделал потом.\n\n"
                "КРИТИЧНО: Только РУССКИЙ язык! Запрещены английские слова: seriously, like, okay, whatever, wow, nice, well. "
                "Используй русские аналоги!"
                if lang.startswith("ru")
                else
                "Tell an explosive first-person story. Pick one spicy topic:\n\n"
                "CHEATING & BETRAYAL:\n"
                "Caught girlfriend/boyfriend with my best friend. Found messages and couldn't believe it. "
                "At party learned I've been cheated on for half a year. Friend confessed he was fucking my ex the whole time.\n\n"
                "MONEY & GREED:\n"
                "Partner drained our business and ran with money. Found out relative was stealing for years. "
                "Won lottery and saw people's true faces. Coworker backstabbed me to take my position.\n\n"
                "FIGHTS & CONFLICTS:\n"
                "Messed with wrong guy and got beaten (or vice versa). Fight over a girl ended LIKE THAT. "
                "Revenge for betrayal (planned and executed). Verbal argument turned into fistfight.\n\n"
                "INTIMATE SCANDALS:\n"
                "Woke up after drunk night in SUCH situation. Caught neighbor/coworker in spicy situation. "
                "Learned about secret affair that shocked everyone. Morning after party destroyed relationships.\n\n"
                "SUDDEN FATE CHANGE:\n"
                "One call and life flipped. Spontaneous decision led to SUCH consequences. "
                "Yesterday was nobody, today everything changed (or opposite). Random meeting changed EVERYTHING.\n\n"
                "SHOCKING EXPOSURES:\n"
                "Learned that respected person is actually... Found evidence that destroyed someone's life. "
                "Accidentally saw what happens behind closed doors. Secret I learned changed my whole attitude.\n\n"
                "Write HARD without censoring emotions! 'freaked out', 'in shock' - that's normal. "
                "BUT avoid direct profanity and explicit porn. Hint, intrigue, let reader fill in. "
                "Focus on HOW you felt, WHAT you thought, WHAT were consequences. "
                "Add details: what they said VERBATIM, how they looked, what you replied, what you did after."
            )
        elif "horror" in name or "страш" in name:
            prompt = (
                "Расскажи СТРАШНУЮ историю от первого лица которая заставит мурашки по коже. "
                "Это должна быть реалистичная история которая могла произойти в реальной жизни — не фантастика!\n\n"
                "ТЕМЫ:\n"
                "ПАРАНОРМАЛЬНОЕ:\n"
                "Слышал странные звуки ночью которые не объяснить. Видел ТАКОЕ что не верю сам. "
                "В новой квартире/доме происходит ЧТО-ТО. Старый дом родственников хранит тайну. "
                "Почувствовал чье-то присутствие хотя был один.\n\n"
                "ЛЮДИ-ПСИХОПАТЫ:\n"
                "Сосед оказался НЕ ТЕМ за кого себя выдавал. Попутчик в дороге повел себя ЖУТКО. "
                "Незнакомец преследовал меня. Понял что коллега/знакомый опасен. "
                "Увидел ЧТО-ТО в доме соседа что леденит кровь.\n\n"
                "ОПАСНЫЕ СИТУАЦИИ:\n"
                "Заблудился в лесу/заброшке и услышал ТАКОЕ. Пошел туда куда не стоило. "
                "Один в темноте что-то/кто-то приближалось. Понял что за мной следят. "
                "Чуть не погиб из-за ЭТОГО.\n\n"
                "МИСТИЧЕСКИЕ СОВПАДЕНИЯ:\n"
                "Приснился сон который СБЫЛСЯ страшным образом. Почувствовал что должно случиться плохое — и случилось. "
                "Странные совпадения которые пугают. Нашел что-то что лучше бы не находил.\n\n"
                "УЖАСНЫЕ ОТКРЫТИЯ:\n"
                "Узнал страшную тайну семьи. Нашел в доме/чердаке/подвале ЧТО-ТО жуткое. "
                "Случайно увидел что делает человек и теперь боюсь. Прошлое дома/места оказалось ТАКИМ.\n\n"
                "Пиши напряженно, с деталями:\n"
                "- Описывай атмосферу: темнота, тишина, странные звуки, ощущения\n"
                "- Нарастающее напряжение — от легкого беспокойства к настоящему страху\n"
                "- Конкретные детали: что слышал, видел, чувствовал в тот момент\n"
                "- Внутренний монолог: 'сердце колотилось', 'кровь застыла', 'не мог пошевелиться'\n"
                "- Избегай банальностей типа 'было темно и страшно'\n\n"
                "КРИТИЧНО: Только РУССКИЙ язык! Без английских слов!\n\n"
                "История должна быть РЕАЛЬНОЙ и правдоподобной. Читатель должен подумать 'бл*ть, а вдруг со мной такое...' "
                "Не стремись к хеппи-энду — пусть останется тревожное чувство."
                if lang.startswith("ru")
                else
                "Tell a SCARY first-person story that gives goosebumps. "
                "Must be realistic — could happen in real life, not fantasy!\n\n"
                "THEMES:\n"
                "PARANORMAL:\n"
                "Heard strange sounds at night can't explain. Saw SOMETHING don't believe myself. "
                "In new apartment/house SOMETHING happens. Old relative's house keeps secret. "
                "Felt someone's presence though alone.\n\n"
                "PSYCHO PEOPLE:\n"
                "Neighbor turned out NOT who claimed to be. Hitchhiker acted CREEPY. "
                "Stranger followed me. Realized coworker/acquaintance is dangerous. "
                "Saw SOMETHING in neighbor's house that chills blood.\n\n"
                "DANGEROUS SITUATIONS:\n"
                "Got lost in forest/abandoned place heard THAT. Went where shouldn't have. "
                "Alone in darkness something/someone approaching. Realized being watched. "
                "Almost died because of THIS.\n\n"
                "MYSTIC COINCIDENCES:\n"
                "Dreamed dream that CAME TRUE terribly. Felt something bad will happen — and it did. "
                "Strange coincidences that scare. Found something wish hadn't.\n\n"
                "HORRIBLE DISCOVERIES:\n"
                "Learned family's dark secret. Found in house/attic/basement SOMETHING creepy. "
                "Accidentally saw what person does and now scared. Past of house/place turned out SUCH.\n\n"
                "Write tensely with details:\n"
                "- Describe atmosphere: darkness, silence, strange sounds, feelings\n"
                "- Rising tension — from light worry to real fear\n"
                "- Concrete details: what heard, saw, felt in that moment\n"
                "- Internal monologue: 'heart pounded', 'blood froze', 'couldn't move'\n"
                "- Avoid clichés like 'it was dark and scary'\n\n"
                "Story must be REAL and believable. Reader should think 'fuck, what if this happens to me...' "
                "Don't aim for happy ending — let anxious feeling remain."
            )
        elif "facts" in name or "факт" in name:
            prompt = (
                "Расскажи УДИВИТЕЛЬНЫЙ факт который заставит остановиться и подумать. "
                "Выбери что-то из науки, психологии, природы, технологий, космоса, биологии или физики.\n\n"
                "ЧТО ЗАЦЕПИТ:\n"
                "- Факт который ломает привычное понимание мира\n"
                "- То что звучит невероятно но это правда\n"
                "- Неожиданная связь между вещами\n"
                "- Что-то что объясняет странные явления\n"
                "- Факт который меняет взгляд на обычные вещи\n\n"
                "ПРИМЕРЫ ТЕМ (не ограничивайся этим):\n"
                "КОСМОС: Масштабы вселенной, странные планеты, черные дыры, время в космосе\n"
                "БИОЛОГИЯ: Необычные способности животных/растений, эволюция, генетика\n"
                "ПСИХОЛОГИЯ: Как работает мозг, когнитивные искажения, память, восприятие\n"
                "ФИЗИКА: Квантовая механика, время, гравитация, свет, звук\n"
                "ХИМИЯ: Необычные реакции, элементы, молекулы в жизни\n"
                "ТЕХНОЛОГИИ: Как работает привычное, будущие технологии, AI\n"
                "ПРИРОДА: Погода, океаны, горы, явления природы\n\n"
                "КАК РАССКАЗЫВАТЬ:\n"
                "- Начни с вопроса или утверждения которое цепляет\n"
                "- Объясни простыми словами без сложных терминов\n"
                "- Добавь сравнение которое помогает представить масштаб/суть\n"
                "- Покажи как это связано с реальной жизнью\n"
                "- Закончи так чтобы захотелось узнать больше\n\n"
                "ИЗБЕГАЙ:\n"
                "- Заученных фраз: 'Знаете ли вы', 'Оказывается', 'Интересный факт'\n"
                "- Списков и перечислений\n"
                "- Скучного научного языка\n"
                "- Банальных фактов которые все знают\n\n"
                "КРИТИЧНО: Только РУССКИЙ язык! Без английских слов!\n\n"
                "Рассказывай так будто делишься с другом чем-то офигенным что недавно узнал. "
                "С эмоциями, удивлением, желанием поделиться."
                if lang.startswith("ru")
                else
                "Tell AMAZING fact that makes you stop and think. "
                "Pick from science, psychology, nature, tech, space, biology or physics.\n\n"
                "WHAT HOOKS:\n"
                "- Fact that breaks usual understanding of world\n"
                "- Sounds incredible but true\n"
                "- Unexpected connection between things\n"
                "- Explains strange phenomena\n"
                "- Changes view on ordinary things\n\n"
                "EXAMPLE THEMES (not limited):\n"
                "SPACE: Universe scales, weird planets, black holes, time in space\n"
                "BIOLOGY: Unusual animal/plant abilities, evolution, genetics\n"
                "PSYCHOLOGY: How brain works, cognitive biases, memory, perception\n"
                "PHYSICS: Quantum mechanics, time, gravity, light, sound\n"
                "CHEMISTRY: Unusual reactions, elements, molecules in life\n"
                "TECH: How familiar works, future tech, AI\n"
                "NATURE: Weather, oceans, mountains, natural phenomena\n\n"
                "HOW TO TELL:\n"
                "- Start with question or statement that hooks\n"
                "- Explain simply without complex terms\n"
                "- Add comparison helping imagine scale/essence\n"
                "- Show connection to real life\n"
                "- End making want to know more\n\n"
                "AVOID:\n"
                "- Rehearsed phrases: 'Did you know', 'Turns out', 'Interesting fact'\n"
                "- Lists and enumerations\n"
                "- Boring scientific language\n"
                "- Banal facts everyone knows\n\n"
                "Tell like sharing with friend something awesome just learned. "
                "With emotions, surprise, desire to share."
            )
        elif "history" in name or "истор" in name:
            prompt = (
                "Расскажи ЗАХВАТЫВАЮЩИЙ исторический факт или событие о котором мало кто знает. "
                "Не школьная история а реальные события которые удивляют и заставляют по-другому взглянуть на прошлое.\n\n"
                "ЧТО ИНТЕРЕСНО:\n"
                "- Неизвестные детали известных событий\n"
                "- Удивительные личности которых забыли\n"
                "- События которые изменили мир но о них не говорят\n"
                "- Странные совпадения в истории\n"
                "- Факты которые кажутся выдумкой но это правда\n\n"
                "ТЕМЫ (выбери одну):\n"
                "ДРЕВНИЙ МИР: Египет, Рим, Греция, древние цивилизации, загадки прошлого\n"
                "СРЕДНЕВЕКОВЬЕ: Рыцари, крестовые походы, замки, короли, интриги\n"
                "ВЕЛИКИЕ ОТКРЫТИЯ: Путешественники, ученые, изобретатели, экспедиции\n"
                "ВОЙНЫ И БИТВЫ: Неизвестные герои, странные тактики, секретные операции\n"
                "20 ВЕК: Мировые войны, холодная война, СССР, технологии, космос\n"
                "ПРАВИТЕЛИ И ДИКТАТОРЫ: Их странности, тайны, решения изменившие мир\n"
                "ЗАГАДКИ ИСТОРИИ: Неразгаданные тайны, пропавшие цивилизации, артефакты\n\n"
                "КАК РАССКАЗЫВАТЬ:\n"
                "- Начни с интригующего момента: 'В 1943 году произошло ТО о чем молчали 50 лет...'\n"
                "- Расскажи историю как детектив — с деталями и напряжением\n"
                "- Добавь живые детали: что люди чувствовали, говорили, делали\n"
                "- Покажи как это повлияло на будущее\n"
                "- Объясни почему об этом мало знают\n\n"
                "ИЗБЕГАЙ:\n"
                "- Сухого перечисления дат и фактов\n"
                "- Банальных историй из учебников\n"
                "- Скучного академического языка\n"
                "- Моралей и выводов\n\n"
                "КРИТИЧНО: Только РУССКИЙ язык! Без английских слов!\n\n"
                "Рассказывай как рассказываешь другу невероятную историю которую сам недавно узнал. "
                "С азартом, удивлением, желанием поделиться."
                if lang.startswith("ru")
                else
                "Tell GRIPPING historical fact or event few know about. "
                "Not school history but real events that amaze and change view on past.\n\n"
                "WHAT'S INTERESTING:\n"
                "- Unknown details of known events\n"
                "- Amazing personalities forgotten\n"
                "- Events that changed world but not talked about\n"
                "- Strange coincidences in history\n"
                "- Facts that seem fiction but true\n\n"
                "THEMES (pick one):\n"
                "ANCIENT WORLD: Egypt, Rome, Greece, ancient civilizations, mysteries\n"
                "MEDIEVAL: Knights, crusades, castles, kings, intrigues\n"
                "GREAT DISCOVERIES: Travelers, scientists, inventors, expeditions\n"
                "WARS & BATTLES: Unknown heroes, strange tactics, secret operations\n"
                "20TH CENTURY: World wars, cold war, USSR, tech, space\n"
                "RULERS & DICTATORS: Their oddities, secrets, world-changing decisions\n"
                "HISTORY MYSTERIES: Unsolved mysteries, lost civilizations, artifacts\n\n"
                "HOW TO TELL:\n"
                "- Start with intriguing moment: 'In 1943 happened THAT kept secret 50 years...'\n"
                "- Tell story like detective — with details and tension\n"
                "- Add vivid details: what people felt, said, did\n"
                "- Show how it affected future\n"
                "- Explain why few know about it\n\n"
                "AVOID:\n"
                "- Dry listing of dates and facts\n"
                "- Banal stories from textbooks\n"
                "- Boring academic language\n"
                "- Morals and conclusions\n\n"
                "Tell like telling friend incredible story just learned. "
                "With excitement, surprise, desire to share."
            )
        elif "news" in name or "новост" in name:
            prompt = (
                "Расскажи о РЕЗОНАНСНОМ недавнем событии или тренде который сейчас обсуждают. "
                "Это должно быть актуально, интересно широкой аудитории и подано живо.\n\n"
                "ТЕМЫ (выбери самое актуальное):\n"
                "ТЕХНОЛОГИИ: Новые AI модели, прорывы в технологиях, вирусные приложения, гаджеты\n"
                "НАУКА: Открытия, исследования, космос, медицина, экология\n"
                "ОБЩЕСТВО: Вирусные истории, тренды, социальные движения, культурные явления\n"
                "ЗНАМЕНИТОСТИ: Громкие скандалы, неожиданные повороты, разоблачения\n"
                "ЭКОНОМИКА: Криптовалюты, стартапы, компании, финансовые потрясения\n"
                "СПОРТ: Рекорды, скандалы, неожиданные победы, истории спортсменов\n"
                "ИНТЕРНЕТ: Вирусные видео, мемы, скандалы в соцсетях, новые платформы\n\n"
                "КАК РАССКАЗЫВАТЬ:\n"
                "- Начни с цепляющего факта: 'Вчера весь интернет взорвался из-за...'\n"
                "- Объясни ПОЧЕМУ это важно и почему все обсуждают\n"
                "- Добавь контекст: что было до, что происходит сейчас\n"
                "- Покажи разные точки зрения если есть спор\n"
                "- Объясни как это может повлиять на людей\n\n"
                "СТИЛЬ:\n"
                "- Динамично и живо — как рассказываешь другу последние новости\n"
                "- Без официоза и канцелярита\n"
                "- С эмоциями и личным отношением\n"
                "- Простым языком без заумных терминов\n\n"
                "ИЗБЕГАЙ:\n"
                "- Сухого новостного стиля\n"
                "- Сложных политических тем\n"
                "- Негатива и депрессивных новостей\n"
                "- Фейков и непроверенной информации\n\n"
                "КРИТИЧНО: Только РУССКИЙ язык! Без английских слов!\n\n"
                "Рассказывай как делишься с другом крутой новостью которую только что узнал. "
                "С энтузиазмом, удивлением, желанием обсудить."
                if lang.startswith("ru")
                else
                "Tell about RESONANT recent event or trend being discussed now. "
                "Must be current, interesting to wide audience and presented lively.\n\n"
                "THEMES (pick most current):\n"
                "TECH: New AI models, tech breakthroughs, viral apps, gadgets\n"
                "SCIENCE: Discoveries, research, space, medicine, ecology\n"
                "SOCIETY: Viral stories, trends, social movements, cultural phenomena\n"
                "CELEBRITIES: Loud scandals, unexpected turns, exposures\n"
                "ECONOMY: Crypto, startups, companies, financial shocks\n"
                "SPORTS: Records, scandals, unexpected wins, athlete stories\n"
                "INTERNET: Viral videos, memes, social media scandals, new platforms\n\n"
                "HOW TO TELL:\n"
                "- Start with hooking fact: 'Yesterday internet exploded because...'\n"
                "- Explain WHY important and why everyone discussing\n"
                "- Add context: what was before, what happening now\n"
                "- Show different viewpoints if disputed\n"
                "- Explain how might affect people\n\n"
                "STYLE:\n"
                "- Dynamic and lively — like telling friend latest news\n"
                "- Without formal bureaucratic language\n"
                "- With emotions and personal attitude\n"
                "- Simple language without complex terms\n\n"
                "AVOID:\n"
                "- Dry news style\n"
                "- Complex political topics\n"
                "- Negativity and depressing news\n"
                "- Fakes and unverified info\n\n"
                "Tell like sharing with friend cool news just learned. "
                "With enthusiasm, surprise, desire to discuss."
            )
        else:
            prompt = (
                "Расскажи ОСТРУЮ историю с неожиданным поворотом. "
                "Темы: измены, предательство, драки, резкая смена судьбы, интимные скандалы, шокирующие разоблачения. "
                "История должна ВЗРЫВАТЬ мозг с первой секунды! Пиши жёстко, эмоционально, с конкретными деталями. "
                "Читатель должен думать 'ВООБЩЕ ОХ*ЕТЬ!'"
                if lang.startswith("ru")
                else
                "Tell a SPICY story with unexpected twist. "
                "Topics: cheating, betrayal, fights, sudden fate change, intimate scandals, shocking exposures. "
                "Story must BLOW minds from the first second! Write hard, emotionally, with specific details. "
                "Reader should think 'HOLY FUCKING SHIT!'"
            )

    if not API_KEY:
        # Фолбэк, чтобы ничего не падало — но лучше поставить ключ
        return "Untitled Story\n\nI missed the bus to my exam, but a stranger offered me a ride. I made it just in time."

    import aiohttp
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

    # Настройки для МАКСИМАЛЬНО свободной и острой генерации (особенно для Grok)
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": _sys_prompt(lang)},
            {"role": "user", "content": _user_prompt(prompt, lang, target_sec)}
        ],
        "temperature": 1.3,  # МАКСИМАЛЬНАЯ креативность и остроту
        "max_tokens": 900,   # Больше места для деталей
        "presence_penalty": 0.6,  # Сильно поощряем новые острые темы
        "frequency_penalty": 0.5,  # Избегаем повторяющихся фраз и клише
        "top_p": 0.95  # Широкий выбор токенов для более дерзкого контента
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(API_URL, json=payload, headers=headers, timeout=120) as resp:
            data = await resp.json()
            if resp.status != 200:
                api_name = "Grok" if USE_GROK else "OpenAI"
                raise RuntimeError(f"{api_name} error {resp.status}: {data}")
            text = data["choices"][0]["message"]["content"]
            text = _trim(text)

    # Очищаем текст от Markdown символов
    text = _clean_markdown(text)

    # Страхуемся: если модель вернула без явного заголовка — подставим
    parts = text.splitlines()
    if len(parts) <= 1:
        title = "Story"
        body = text
        return f"{title}\n\n{body}"
    return text


def _clean_markdown(text: str) -> str:
    """Удаляет Markdown форматирование из текста"""
    # Удаляем жирный текст (**текст** или __текст__)
    text = re.sub(r'\*\*([^\*]+)\*\*', r'\1', text)
    text = re.sub(r'__([^_]+)__', r'\1', text)

    # Удаляем курсив (*текст* или _текст_)
    text = re.sub(r'\*([^\*]+)\*', r'\1', text)
    text = re.sub(r'_([^_]+)_', r'\1', text)

    # Удаляем заголовки (# текст, ## текст и т.д.)
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)

    # Удаляем inline код (`текст`)
    text = re.sub(r'`([^`]+)`', r'\1', text)

    # Удаляем ссылки [текст](url)
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)

    # Удаляем оставшиеся специальные символы
    text = text.replace('**', '').replace('__', '').replace('~~', '')
    text = text.replace('<', '').replace('>', '')

    return text
