from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from typing import List, Dict, Any

BTN_CREATE_SHORT = "🎬 Создать шорт"
BTN_CREATE_LONG  = "📽️ Длинное видео"
BTN_STATISTICS   = "📊 Статистика"
BTN_CHANNELS     = "📺 Каналы"
BTN_SETTINGS     = "⚙️ Настройки"
BTN_BACK         = "⬅️ Назад"
BTN_THEMES       = "🎭 Тематики"
# BTN_VOICE_CLONE removed - using pre-made voices only

# Кнопки для Reddit анимаций
BTN_BG_VIDEO = "🎞 Залипательное видео"
BTN_BG_ANIMATION = "⭕ Анимация (круг)"

# Кнопки для длинных видео
BTN_LONG_LANG_RU = "🇷🇺 Русский"
BTN_LONG_LANG_EN = "🇬🇧 English"
BTN_LONG_LANG_UA = "🇺🇦 Українська"

BTN_CHANNEL_ADD            = "➕ Добавить канал"
BTN_CHANNEL_SET_TTS        = "🔊 Выбрать озвучку"
BTN_CHANNEL_SET_SUBS       = "💬 Субтитры"
BTN_CHANNEL_SET_BANNER     = "🖼 Установить баннер"
BTN_CHANNEL_SET_BACKGROUND = "🎨 Тип фона"
BTN_CHANNEL_DELETE         = "🗑 Удалить канал"

BTN_CUTS_LIBRARY         = "📚 Библиотека медиа"
BTN_CHANNEL_SET_CUTS     = "🎬 Выбрать коллекцию"
BTN_CHANNEL_SET_CUTS_DUR = "⏱ Длительность нарезки"
BTN_CUTS_RESCAN          = "🔄 Пересканировать папку"

# Кнопки для настроек
BTN_REDDIT_PROMPTS = "📝 Промпты Reddit"
BTN_MEDIA_LIBRARY = "🎞 Библиотека фонов"
BTN_BANNERS_LIBRARY = "🖼 Баннеры для нарезок"
BTN_PRESET_VOICES = "🎙 Голоса для Reddit"

BTN_TTS_GTTS        = "🟢 gTTS"
BTN_TTS_ELEVENLABS  = "🟣 ElevenLabs"
BTN_TTS_EDGE        = "🔵 Edge TTS"
BTN_TTS_SILERO      = "🟠 Silero"

BTN_TTS_LANG_EN = "🇬🇧 Английский"
BTN_TTS_LANG_RU = "🇷🇺 Русский"

BTN_SUBS_OFF = "🚫 Без субтитров"
BTN_SUBS_EN  = "🇬🇧 Субтитры EN"
BTN_SUBS_RU  = "🇷🇺 Субтитры RU"

BTN_YES = "✅ Да"
BTN_NO  = "❌ Нет"

BTN_EDGE_LIST_RU = "🇷🇺 Русские голоса"
BTN_EDGE_LIST_EN = "🇬🇧 Английские голоса"
BTN_EDGE_GENDER_MALE   = "👨 Мужской"
BTN_EDGE_GENDER_FEMALE = "👩 Женский"

BTN_VOICE_PREV   = "⏮ Предыдущая страница"
BTN_VOICE_NEXT   = "⏭ Следующая страница"
BTN_VOICE_CHOOSE = "✅ Выбрать этот голос"

BTN_GTTS_LANGS_QUICK = ["en", "ru"]

BTN_ELEVEN_LANG_EN  = "🇬🇧 English"
BTN_ELEVEN_LANG_RU  = "🇷🇺 Русский"

BTN_SILERO_GENDER_MALE   = "👨 Мужской (Silero)"
BTN_SILERO_GENDER_FEMALE = "👩 Женский (Silero)"

BTN_THEME_CUTS   = "✂️ Нарезки"
BTN_THEME_REDDIT = "🧵 Reddit"

# Кнопки для упрощенного флоу создания видео
BTN_SIMPLE_CUTS = "✂️ Нарезки"
BTN_SIMPLE_REDDIT = "📱 Жизненные истории"
BTN_SIMPLE_EDUCATIONAL = "🧠 Познавательные истории"
BTN_SIMPLE_ANIMATION = "🎨 Только анимация"

# Кнопки для языков реддит стори
BTN_LANG_RU = "🇷🇺 Русский"
BTN_LANG_EN = "🇬🇧 English"

# Кнопки для форматов реддит стори
BTN_FORMAT_TOP_VIDEO = "📺 Карточка сверху + видео"
BTN_FORMAT_CENTER = "⏺ Карточка по центру"
BTN_FORMAT_ANIMATION = "⭕ Карточка + анимация"

# Кнопки навигации для тестирования голосов
BTN_VOICE_TEST_PREV = "⬅️ Назад"
BTN_VOICE_TEST_NEXT = "➡️ Вперед"
BTN_VOICE_TEST_SELECT = "✅ Выбрать"
BTN_VOICE_TEST_CANCEL = "❌ Отменить"

# Кнопки для позиции баннера
BTN_BANNER_POS_TOP = "⬆️ Сверху"
BTN_BANNER_POS_CENTER = "⏺ По центру"
BTN_BANNER_POS_BOTTOM = "⬇️ Снизу"
BTN_BANNER_REMOVE = "❌ Убрать баннер"


def main_kb() -> ReplyKeyboardMarkup:
    """
    Главное меню:
    - Создать шорт / Длинное видео
    - Каналы | Статистика
    - Настройки
    """
    kb = [
        [KeyboardButton(text=BTN_CREATE_SHORT), KeyboardButton(text=BTN_CREATE_LONG)],
        [KeyboardButton(text=BTN_CHANNELS), KeyboardButton(text=BTN_STATISTICS)],
        [KeyboardButton(text=BTN_SETTINGS)],
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)


def reddit_background_type_kb() -> ReplyKeyboardMarkup:
    """Выбор типа фона для Reddit видео"""
    kb = [
        [KeyboardButton(text=BTN_BG_VIDEO)],
        [KeyboardButton(text=BTN_BG_ANIMATION)],
        [KeyboardButton(text=BTN_BACK)],
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)


def long_video_language_kb() -> ReplyKeyboardMarkup:
    """Выбор языка для длинного видео"""
    kb = [
        [KeyboardButton(text=BTN_LONG_LANG_RU)],
        [KeyboardButton(text=BTN_LONG_LANG_UA)],
        [KeyboardButton(text=BTN_LONG_LANG_EN)],
        [KeyboardButton(text=BTN_BACK)],
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)


def long_video_duration_kb() -> ReplyKeyboardMarkup:
    """Выбор длительности для длинного видео"""
    kb = [
        [KeyboardButton(text="⏱ 10 минут")],
        [KeyboardButton(text="⏱ 15 минут")],
        [KeyboardButton(text="⏱ 20 минут")],
        [KeyboardButton(text=BTN_BACK)],
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)


def long_video_topics_kb(topics: List[str]) -> ReplyKeyboardMarkup:
    """Клавиатура с предложенными темами"""
    rows = []
    for i, topic in enumerate(topics[:4], 1):
        short_topic = topic[:40] + "..." if len(topic) > 40 else topic
        rows.append([KeyboardButton(text=f"{i}. {short_topic}")])
    rows.append([KeyboardButton(text="✍️ Своя тема")])
    rows.append([KeyboardButton(text=BTN_BACK)])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def long_video_confirm_kb() -> ReplyKeyboardMarkup:
    """Подтверждение генерации длинного видео"""
    kb = [
        [KeyboardButton(text="✅ Начать генерацию")],
        [KeyboardButton(text=BTN_BACK)],
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)


def settings_kb() -> ReplyKeyboardMarkup:
    """Клавиатура настроек - теперь с библиотекой медиа и баннерами"""
    kb = [
        [KeyboardButton(text=BTN_REDDIT_PROMPTS)],
        [KeyboardButton(text=BTN_PRESET_VOICES)],  # Предустановленные голоса для Reddit
        [KeyboardButton(text=BTN_MEDIA_LIBRARY)],
        [KeyboardButton(text=BTN_CUTS_LIBRARY)],  # Библиотека медиа для нарезок
        [KeyboardButton(text=BTN_BANNERS_LIBRARY)],  # Баннеры для нарезок
        [KeyboardButton(text=BTN_BACK)],
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)


def channels_list_kb(names: List[str]) -> ReplyKeyboardMarkup:
    rows = [[KeyboardButton(text=name)] for name in names] if names else []
    rows += [[KeyboardButton(text=BTN_CHANNEL_ADD)], [KeyboardButton(text=BTN_BACK)]]
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def channel_actions_kb_reddit() -> ReplyKeyboardMarkup:
    kb = [
        [KeyboardButton(text=BTN_CHANNEL_SET_TTS)],
        [KeyboardButton(text=BTN_CHANNEL_SET_SUBS)],
        [KeyboardButton(text=BTN_CHANNEL_SET_BACKGROUND)],
        [KeyboardButton(text=BTN_CHANNEL_DELETE)],
        [KeyboardButton(text=BTN_BACK)],
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)


def channel_actions_kb_cuts() -> ReplyKeyboardMarkup:
    kb = [
        [KeyboardButton(text=BTN_CHANNEL_SET_CUTS)],
        [KeyboardButton(text=BTN_CHANNEL_SET_CUTS_DUR)],
        [KeyboardButton(text=BTN_CHANNEL_SET_BANNER)],  # Добавлена кнопка баннера
        [KeyboardButton(text=BTN_CHANNEL_DELETE)],
        [KeyboardButton(text=BTN_BACK)],
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)


def tts_select_kb() -> ReplyKeyboardMarkup:
    kb = [
        [KeyboardButton(text=BTN_TTS_EDGE), KeyboardButton(text=BTN_TTS_ELEVENLABS)],
        [KeyboardButton(text=BTN_TTS_GTTS), KeyboardButton(text=BTN_TTS_SILERO)],
        [KeyboardButton(text=BTN_BACK)],
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)


def tts_lang_select_kb() -> ReplyKeyboardMarkup:
    kb = [
        [KeyboardButton(text=BTN_TTS_LANG_EN), KeyboardButton(text=BTN_TTS_LANG_RU)],
        [KeyboardButton(text=BTN_BACK)],
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)


def subs_select_kb() -> ReplyKeyboardMarkup:
    kb = [
        [KeyboardButton(text=BTN_SUBS_EN), KeyboardButton(text=BTN_SUBS_RU)],
        [KeyboardButton(text=BTN_BACK)],
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)


def themes_list_with_cuts_kb(names: List[str]) -> ReplyKeyboardMarkup:
    rows: List[List[KeyboardButton]] = []
    rows.append([KeyboardButton(text=BTN_THEME_CUTS)])
    rows.append([KeyboardButton(text=BTN_THEME_REDDIT)])
    if names:
        for n in names:
            if n.strip() in (BTN_THEME_CUTS, BTN_THEME_REDDIT):
                continue
            rows.append([KeyboardButton(text=n)])
    rows.append([KeyboardButton(text=BTN_BACK)])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def edge_voice_lang_kb() -> ReplyKeyboardMarkup:
    kb = [
        [KeyboardButton(text=BTN_EDGE_LIST_RU)],
        [KeyboardButton(text=BTN_EDGE_LIST_EN)],
        [KeyboardButton(text=BTN_BACK)],
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)


def edge_voice_gender_kb() -> ReplyKeyboardMarkup:
    kb = [
        [KeyboardButton(text=BTN_EDGE_GENDER_MALE), KeyboardButton(text=BTN_EDGE_GENDER_FEMALE)],
        [KeyboardButton(text=BTN_BACK)],
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)


def voices_list_kb(voices: List[str], page: int, per_page: int = 8) -> ReplyKeyboardMarkup:
    total = len(voices)
    pages = max(1, (total + per_page - 1) // per_page)
    page = max(0, min(page, pages - 1))
    start, end = page * per_page, min(total, (page + 1) * per_page)
    rows = [[KeyboardButton(text=v)] for v in voices[start:end]]

    nav = []
    if pages > 1:
        if page > 0:
            nav.append(KeyboardButton(text=BTN_VOICE_PREV))
        if page < pages - 1:
            nav.append(KeyboardButton(text=BTN_VOICE_NEXT))
    if nav:
        rows.append(nav)

    rows.append([KeyboardButton(text=BTN_BACK)])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def voice_confirm_kb() -> ReplyKeyboardMarkup:
    kb = [
        [KeyboardButton(text=BTN_VOICE_CHOOSE)],
        [KeyboardButton(text=BTN_BACK)],
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)


def gtts_lang_quick_kb() -> ReplyKeyboardMarkup:
    row = [KeyboardButton(text=l) for l in BTN_GTTS_LANGS_QUICK]
    kb = [row, [KeyboardButton(text=BTN_BACK)]]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)


def eleven_lang_select_kb() -> ReplyKeyboardMarkup:
    """Выбор языка для ElevenLabs/GenAIPro голоса"""
    kb = [
        [KeyboardButton(text=BTN_ELEVEN_LANG_EN), KeyboardButton(text=BTN_ELEVEN_LANG_RU)],
        [KeyboardButton(text=BTN_BACK)],
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)


def silero_gender_kb() -> ReplyKeyboardMarkup:
    kb = [
        [KeyboardButton(text=BTN_SILERO_GENDER_MALE), KeyboardButton(text=BTN_SILERO_GENDER_FEMALE)],
        [KeyboardButton(text=BTN_BACK)],
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)


def confirm_delete_kb() -> ReplyKeyboardMarkup:
    kb = [
        [KeyboardButton(text=BTN_YES), KeyboardButton(text=BTN_NO)],
        [KeyboardButton(text=BTN_BACK)],
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)


def cuts_kind_kb() -> ReplyKeyboardMarkup:
    kb = [
        [KeyboardButton(text="🎨 Мультики"), KeyboardButton(text="🎞 Фильмы")],
        [KeyboardButton(text=BTN_BACK)],
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)


def cuts_collections_kb(names: List[str], show_create: bool = True) -> ReplyKeyboardMarkup:
    rows = [[KeyboardButton(text=n)] for n in names] if names else []
    if show_create:
        rows.insert(0, [KeyboardButton(text="➕ Создать коллекцию")])
    rows.append([KeyboardButton(text=BTN_BACK)])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def cuts_add_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BTN_CUTS_RESCAN)],
            [KeyboardButton(text=BTN_BACK)]
        ],
        resize_keyboard=True
    )


# Inline клавиатуры для промптов
def prompts_inline_kb(presets: List[str], lang: str) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(text=f"✏️ {p} ({lang})", callback_data=f"prompt:edit:{p}:{lang}")]
            for p in presets]
    rows.append([InlineKeyboardButton(text="➕ Новый пресет", callback_data=f"prompt:new:{lang}")])
    rows.append([InlineKeyboardButton(text="🔄 Переключить язык", callback_data=f"prompt:lang:{lang}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def media_inline_kb(files: List[str]) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(text=f"🗑 {f}", callback_data=f"media:del:{f}")] for f in files[:10]]
    if len(files) > 10:
        rows.append([InlineKeyboardButton(text=f"📄 Показано 10 из {len(files)}", callback_data="noop")])
    rows.append([InlineKeyboardButton(text="➕ Загрузить .mp4", callback_data="media:upload")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def banners_inline_kb(files: List[str]) -> InlineKeyboardMarkup:
    """Inline клавиатура для баннеров"""
    rows = [[InlineKeyboardButton(text=f"🗑 {f}", callback_data=f"banner:del:{f}")] for f in files[:10]]
    if len(files) > 10:
        rows.append([InlineKeyboardButton(text=f"📄 Показано 10 из {len(files)}", callback_data="noop")])
    rows.append([InlineKeyboardButton(text="➕ Загрузить .png", callback_data="banner:upload")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def banner_select_kb(banners: List[str]) -> ReplyKeyboardMarkup:
    """Клавиатура выбора баннера для канала"""
    rows = [[KeyboardButton(text=name)] for name in banners]
    if not banners:
        rows.append([KeyboardButton(text="❌ Нет доступных баннеров")])
    rows.append([KeyboardButton(text=BTN_BANNER_REMOVE)])
    rows.append([KeyboardButton(text=BTN_BACK)])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def banner_position_kb() -> ReplyKeyboardMarkup:
    """Клавиатура выбора позиции баннера"""
    kb = [
        [KeyboardButton(text=BTN_BANNER_POS_TOP)],
        [KeyboardButton(text=BTN_BANNER_POS_CENTER)],
        [KeyboardButton(text=BTN_BANNER_POS_BOTTOM)],
        [KeyboardButton(text=BTN_BACK)],
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)


# Клавиатуры для упрощенного флоу создания видео
def simple_theme_select_kb() -> ReplyKeyboardMarkup:
    """Выбор тематики видео (упрощенный флоу)"""
    kb = [
        [KeyboardButton(text=BTN_SIMPLE_CUTS)],
        [KeyboardButton(text=BTN_SIMPLE_REDDIT)],
        [KeyboardButton(text=BTN_SIMPLE_EDUCATIONAL)],
        [KeyboardButton(text=BTN_BACK)],
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)


def simple_language_kb() -> ReplyKeyboardMarkup:
    """Выбор языка для реддит стори (deprecated - используйте simple_language_inline_kb)"""
    kb = [
        [KeyboardButton(text=BTN_LANG_RU), KeyboardButton(text=BTN_LANG_EN)],
        [KeyboardButton(text=BTN_BACK)],
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)


def simple_language_inline_kb() -> InlineKeyboardMarkup:
    """Inline выбор языка для историй"""
    buttons = [
        [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang:ru")],
        [InlineKeyboardButton(text="🇬🇧 English", callback_data="lang:en")],
        [InlineKeyboardButton(text="🇫🇷 Français", callback_data="lang:fr")],
        [InlineKeyboardButton(text="❌ Отменить", callback_data="lang:cancel")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def simple_reddit_format_kb() -> ReplyKeyboardMarkup:
    """Выбор формата реддит стори (deprecated - используйте simple_reddit_format_inline_kb)"""
    kb = [
        [KeyboardButton(text=BTN_FORMAT_TOP_VIDEO)],
        [KeyboardButton(text=BTN_FORMAT_CENTER)],
        [KeyboardButton(text=BTN_FORMAT_ANIMATION)],
        [KeyboardButton(text=BTN_BACK)],
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)


def simple_reddit_format_inline_kb() -> InlineKeyboardMarkup:
    """Inline выбор формата - только анимация с орбитами"""
    buttons = [
        [InlineKeyboardButton(text="⭕ Анимация (шарик с орбитами)", callback_data="format:animation")],
        [InlineKeyboardButton(text="❌ Отменить", callback_data="format:cancel")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def voice_test_navigation_kb() -> ReplyKeyboardMarkup:
    """Навигация при тестировании голосов"""
    kb = [
        [KeyboardButton(text=BTN_VOICE_TEST_PREV), KeyboardButton(text=BTN_VOICE_TEST_NEXT)],
        [KeyboardButton(text=BTN_VOICE_TEST_SELECT), KeyboardButton(text=BTN_VOICE_TEST_CANCEL)],
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)


def preset_voices_list_kb(voices: List[str]) -> ReplyKeyboardMarkup:
    """Список предустановленных голосов в админке"""
    rows = [[KeyboardButton(text=f"🎤 {v}")] for v in voices]
    rows.insert(0, [KeyboardButton(text="➕ Добавить голос")])
    rows.append([KeyboardButton(text=BTN_BACK)])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def preset_voices_actions_kb() -> ReplyKeyboardMarkup:
    """Действия с предустановленным голосом"""
    kb = [
        [KeyboardButton(text="🎧 Прослушать")],
        [KeyboardButton(text="🗑 Удалить")],
        [KeyboardButton(text=BTN_BACK)],
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)


def simple_animation_select_kb(animations: List[str]) -> ReplyKeyboardMarkup:
    """Выбор типа анимации"""
    rows = [[KeyboardButton(text=anim)] for anim in animations]
    rows.append([KeyboardButton(text="🎲 Случайная анимация")])
    rows.append([KeyboardButton(text=BTN_BACK)])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


# Voice cloning removed - using pre-made voices only