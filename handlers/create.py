# handlers/create.py
"""
Упрощенный обработчик создания видео через inline меню с фоновой очередью
"""
from aiogram import Router, F, types
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from utils.cuts import list_collections
from db.database import preset_voices_list

router = Router()


class CreateFSM(StatesGroup):
    """FSM для создания видео"""
    # Нарезки
    choose_cuts_collection = State()

    # Истории
    choose_language = State()
    choose_voice = State()


# ========================= НАРЕЗКИ =========================

@router.callback_query(F.data == "create:cuts")
async def cuts_start(callback: types.CallbackQuery, state: FSMContext):
    """Начало создания нарезок"""
    cartoons = list_collections("cartoons")
    films = list_collections("films")

    all_collections = []
    for c in cartoons:
        all_collections.append(("cartoons", c))
    for f in films:
        all_collections.append(("films", f))

    if not all_collections:
        buttons = [[InlineKeyboardButton(text="⬅️ Назад", callback_data="menu:create")]]
        await callback.message.edit_text(
            "❌ <b>Нет загруженных коллекций</b>\n\n"
            "Добавьте видео в папки:\n"
            "• <code>assets/cartoons/название/</code>\n"
            "• <code>assets/films/название/</code>",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
        )
        await callback.answer()
        return

    # Inline кнопки для коллекций
    buttons = []
    for kind, name in all_collections:
        icon = '🎬' if kind == 'films' else '📺'
        buttons.append([InlineKeyboardButton(
            text=f"{icon} {name}",
            callback_data=f"cuts:gen:{kind}:{name}"
        )])

    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="menu:create")])

    await callback.message.edit_text(
        "✂️ <b>Нарезки</b>\n\n"
        "Выберите коллекцию:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("cuts:gen:"))
async def cuts_generate(callback: types.CallbackQuery, state: FSMContext):
    """Генерация нарезки - добавляем в очередь"""
    from utils.task_queue import get_task_queue

    parts = callback.data.split(":")
    kind = parts[2]
    collection = parts[3]

    # Конфиг для генерации
    cuts_config = {
        "kind": kind,
        "collection": collection,
        "min_sec": 30,
        "max_sec": 60,
        "banner_config": None
    }

    # Добавляем задачу в очередь
    task_queue = get_task_queue()
    task = await task_queue.add_task(
        user_id=callback.from_user.id,
        task_type="cuts",
        config=cuts_config
    )

    # Получаем позицию в очереди
    queue_position = task_queue.get_queue_position(task.task_id)

    # Возвращаем пользователя в главное меню с информацией о задаче
    buttons = [
        [InlineKeyboardButton(text="📋 Мои задачи", callback_data="menu:tasks")],
        [InlineKeyboardButton(text="🎬 Создать ещё", callback_data="menu:create")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="menu:main")],
    ]

    queue_info = f"\n📊 Позиция в очереди: {queue_position}" if queue_position and queue_position > 1 else ""

    await callback.message.edit_text(
        f"✅ <b>Задача добавлена в очередь!</b>\n\n"
        f"✂️ Тип: нарезка\n"
        f"🎬 Коллекция: {collection}\n"
        f"🆔 ID: <code>{task.task_id}</code>{queue_info}\n\n"
        f"⏳ Генерация начнётся автоматически\n"
        f"📬 Вы получите уведомление когда видео будет готово\n\n"
        f"💡 Вы можете продолжать пользоваться ботом!",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )
    await callback.answer()


# ========================= ЖИЗНЕННЫЕ ИСТОРИИ =========================

@router.callback_query(F.data == "create:reddit")
async def reddit_start(callback: types.CallbackQuery, state: FSMContext):
    """Начало создания жизненной истории - выбор языка"""
    await state.update_data(story_type="reddit")
    await state.set_state(CreateFSM.choose_language)

    buttons = [
        [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang:ru")],
        [InlineKeyboardButton(text="🇬🇧 English", callback_data="lang:en")],
        [InlineKeyboardButton(text="🇫🇷 Français", callback_data="lang:fr")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="menu:create")],
    ]

    await callback.message.edit_text(
        "📱 <b>Жизненная история</b>\n\n"
        "Выберите язык:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )
    await callback.answer()


# ========================= ПОЗНАВАТЕЛЬНЫЕ ИСТОРИИ =========================

@router.callback_query(F.data == "create:educational")
async def educational_start(callback: types.CallbackQuery, state: FSMContext):
    """Начало создания познавательной истории - выбор языка"""
    await state.update_data(story_type="educational")
    await state.set_state(CreateFSM.choose_language)

    buttons = [
        [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang:ru")],
        [InlineKeyboardButton(text="🇬🇧 English", callback_data="lang:en")],
        [InlineKeyboardButton(text="🇫🇷 Français", callback_data="lang:fr")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="menu:create")],
    ]

    await callback.message.edit_text(
        "🧠 <b>Познавательная история</b>\n\n"
        "Выберите язык:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )
    await callback.answer()


# ========================= СТРАШНЫЕ ИСТОРИИ =========================

@router.callback_query(F.data == "create:horror")
async def horror_start(callback: types.CallbackQuery, state: FSMContext):
    """Начало создания страшной истории - выбор языка"""
    await state.update_data(story_type="horror")
    await state.set_state(CreateFSM.choose_language)

    buttons = [
        [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang:ru")],
        [InlineKeyboardButton(text="🇬🇧 English", callback_data="lang:en")],
        [InlineKeyboardButton(text="🇫🇷 Français", callback_data="lang:fr")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="menu:create")],
    ]

    await callback.message.edit_text(
        "😱 <b>Страшная история</b>\n\n"
        "Выберите язык:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )
    await callback.answer()


# ========================= ПОЗНАВАТЕЛЬНЫЕ ФАКТЫ =========================

@router.callback_query(F.data == "create:facts")
async def facts_start(callback: types.CallbackQuery, state: FSMContext):
    """Начало создания познавательных фактов - выбор языка"""
    await state.update_data(story_type="facts")
    await state.set_state(CreateFSM.choose_language)

    buttons = [
        [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang:ru")],
        [InlineKeyboardButton(text="🇬🇧 English", callback_data="lang:en")],
        [InlineKeyboardButton(text="🇫🇷 Français", callback_data="lang:fr")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="menu:create")],
    ]

    await callback.message.edit_text(
        "💡 <b>Познавательные факты</b>\n\n"
        "Выберите язык:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )
    await callback.answer()


# ========================= ИСТОРИЧЕСКИЕ ФАКТЫ =========================

@router.callback_query(F.data == "create:history")
async def history_start(callback: types.CallbackQuery, state: FSMContext):
    """Начало создания исторических фактов - выбор языка"""
    await state.update_data(story_type="history")
    await state.set_state(CreateFSM.choose_language)

    buttons = [
        [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang:ru")],
        [InlineKeyboardButton(text="🇬🇧 English", callback_data="lang:en")],
        [InlineKeyboardButton(text="🇫🇷 Français", callback_data="lang:fr")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="menu:create")],
    ]

    await callback.message.edit_text(
        "📜 <b>Исторические факты</b>\n\n"
        "Выберите язык:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )
    await callback.answer()


# ========================= ПОСЛЕДНИЕ НОВОСТИ =========================

@router.callback_query(F.data == "create:news")
async def news_start(callback: types.CallbackQuery, state: FSMContext):
    """Начало создания новостей - выбор языка"""
    await state.update_data(story_type="news")
    await state.set_state(CreateFSM.choose_language)

    buttons = [
        [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang:ru")],
        [InlineKeyboardButton(text="🇬🇧 English", callback_data="lang:en")],
        [InlineKeyboardButton(text="🇫🇷 Français", callback_data="lang:fr")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="menu:create")],
    ]

    await callback.message.edit_text(
        "📰 <b>Последние новости</b>\n\n"
        "Выберите язык:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )
    await callback.answer()


# ========================= ВЫБОР ЯЗЫКА И ГОЛОСА =========================

@router.callback_query(F.data.startswith("lang:"), CreateFSM.choose_language)
async def language_selected(callback: types.CallbackQuery, state: FSMContext):
    """Выбран язык - показываем голоса"""
    lang_code = callback.data.split(":")[1]

    if lang_code == "cancel":
        await state.clear()
        from handlers.start import get_main_menu
        await callback.message.edit_text(
            "Отменено",
            reply_markup=get_main_menu()
        )
        await callback.answer()
        return

    await state.update_data(language=lang_code)

    # Получаем список голосов
    try:
        voices = await preset_voices_list()

        if not voices:
            buttons = [[InlineKeyboardButton(text="⬅️ Назад", callback_data="menu:create")]]
            await callback.message.edit_text(
                "❌ <b>Нет голосов</b>\n\n"
                "Добавьте голоса через:\n"
                "⚙️ Настройки → 🎙 Голоса для историй",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
            )
            await callback.answer()
            return

        # Формируем кнопки с голосами
        buttons = []
        lang_names = {"ru": "🇷🇺", "en": "🇬🇧", "fr": "🇫🇷"}

        for idx, v in enumerate(voices):
            name = v.get("name", "Unknown")
            desc = v.get("description", "")
            display = f"{name}"
            if desc:
                display += f" • {desc[:20]}"

            buttons.append([InlineKeyboardButton(
                text=display,
                callback_data=f"voice:{idx}"
            )])

        data = await state.get_data()
        story_type = data.get("story_type", "reddit")
        back_data = f"create:{story_type}"

        buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data=back_data)])

        await state.update_data(voices=voices)
        await state.set_state(CreateFSM.choose_voice)

        lang_flag = lang_names.get(lang_code, lang_code.upper())

        await callback.message.edit_text(
            f"Язык: {lang_flag}\n\n"
            f"🎙 <b>Выберите голос</b>",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
        )
        await callback.answer()

    except Exception as e:
        buttons = [[InlineKeyboardButton(text="⬅️ Назад", callback_data="menu:create")]]
        await callback.message.edit_text(
            f"⚠️ Ошибка загрузки голосов:\n<code>{e}</code>",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
        )
        await callback.answer()


@router.callback_query(F.data.startswith("voice:"), CreateFSM.choose_voice)
async def voice_selected(callback: types.CallbackQuery, state: FSMContext):
    """Выбран голос - добавляем задачу в очередь"""
    from utils.task_queue import get_task_queue

    voice_idx = int(callback.data.split(":")[1])

    data = await state.get_data()
    voices = data.get("voices", [])
    lang = data.get("language", "en")
    story_type = data.get("story_type", "reddit")

    if voice_idx >= len(voices):
        await callback.answer("⚠️ Ошибка выбора голоса", show_alert=True)
        return

    voice = voices[voice_idx]
    voice_id = voice.get("voice_id")
    voice_name = voice.get("name", "Unknown")

    # Конфиг для генерации
    channel_config = {
        "tts_lang": lang,
        "tts_voice": voice_id,
        "voice_name": voice_name,  # Сохраняем для уведомлений
        "tts_speed": 1.3,
        "tts_engine": "genaipro",
        "reddit_target_sec": 100,  # 100 сек = 1.5-2 мин видео для широкой аудитории
        "prompt_preset": story_type,  # Используем story_type для всех тематик
        "background_type": "animation",
        "reddit_card_position": "center",
        "animation_type": "bouncing_ball_rings",  # Отскакивающий шарик в кольцах
        "fps": 60,
        "subs_lang": None
    }

    # Добавляем задачу в очередь
    task_queue = get_task_queue()
    task = await task_queue.add_task(
        user_id=callback.from_user.id,
        task_type=story_type,
        config=channel_config
    )

    # Получаем позицию в очереди
    queue_position = task_queue.get_queue_position(task.task_id)
    stats = task_queue.get_stats()

    icon = "📱" if story_type == "reddit" else "🧠"
    type_text = "жизненная история" if story_type == "reddit" else "познавательная история"

    # Возвращаем пользователя в главное меню с информацией о задаче
    buttons = [
        [InlineKeyboardButton(text="📋 Мои задачи", callback_data="menu:tasks")],
        [InlineKeyboardButton(text="🎬 Создать ещё", callback_data="menu:create")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="menu:main")],
    ]

    queue_info = f"\n📊 Позиция в очереди: {queue_position}" if queue_position and queue_position > 1 else ""

    await callback.message.edit_text(
        f"✅ <b>Задача добавлена в очередь!</b>\n\n"
        f"{icon} Тип: {type_text}\n"
        f"🌐 Язык: {lang.upper()}\n"
        f"🎤 Голос: {voice_name}\n"
        f"🆔 ID: <code>{task.task_id}</code>{queue_info}\n\n"
        f"⏳ Генерация начнётся автоматически\n"
        f"📬 Вы получите уведомление когда видео будет готово\n\n"
        f"💡 Вы можете продолжать пользоваться ботом!",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )
    await callback.answer()
    await state.clear()
