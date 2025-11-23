from aiogram import Router, types, F
from aiogram.filters import CommandStart, StateFilter
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

router = Router()


def get_main_menu() -> InlineKeyboardMarkup:
    """Главное меню - inline клавиатура"""
    buttons = [
        [InlineKeyboardButton(text="🎬 Создать видео", callback_data="menu:create")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data="menu:stats")],
        [InlineKeyboardButton(text="⚙️ Настройки", callback_data="menu:settings")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.message(CommandStart())
async def on_start(message: types.Message):
    """Старт бота - показываем главное меню"""
    await message.answer(
        "👋 <b>YouTube Farm</b>\n\n"
        "Бот для автоматического создания вирусных видео для TikTok и YouTube Shorts\n\n"
        "Выберите действие:",
        reply_markup=get_main_menu()
    )


@router.callback_query(F.data == "menu:main")
async def back_to_main(callback: types.CallbackQuery, state: FSMContext):
    """Возврат в главное меню"""
    await state.clear()  # Очищаем состояние при возврате в главное меню
    await callback.message.edit_text(
        "👋 <b>YouTube Farm</b>\n\n"
        "Бот для автоматического создания вирусных видео для TikTok и YouTube Shorts\n\n"
        "Выберите действие:",
        reply_markup=get_main_menu()
    )
    await callback.answer()


@router.callback_query(F.data == "menu:create")
async def menu_create(callback: types.CallbackQuery):
    """Меню создания видео"""
    buttons = [
        [InlineKeyboardButton(text="✂️ Нарезки", callback_data="create:cuts")],
        [InlineKeyboardButton(text="📱 Жизненные истории", callback_data="create:reddit")],
        [InlineKeyboardButton(text="😱 Страшные истории", callback_data="create:horror")],
        [InlineKeyboardButton(text="💡 Познавательные факты", callback_data="create:facts")],
        [InlineKeyboardButton(text="📜 Исторические факты", callback_data="create:history")],
        [InlineKeyboardButton(text="📰 Последние новости", callback_data="create:news")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="menu:main")],
    ]
    await callback.message.edit_text(
        "🎬 <b>Создание видео</b>\n\n"
        "Выберите тип видео:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )
    await callback.answer()


@router.callback_query(F.data == "menu:stats")
async def menu_stats(callback: types.CallbackQuery):
    """Статистика"""
    from db.database import db

    try:
        # Подсчитываем общее количество созданных видео
        total_count = 0

        stats_text = (
            "📊 <b>Статистика</b>\n\n"
            f"Всего создано видео: <b>{total_count}</b>\n\n"
            "Статистика будет добавлена позже"
        )
    except Exception as e:
        stats_text = f"⚠️ Ошибка загрузки статистики: {e}"

    buttons = [
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="menu:main")],
    ]

    await callback.message.edit_text(
        stats_text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )
    await callback.answer()


@router.callback_query(F.data == "menu:settings")
async def menu_settings(callback: types.CallbackQuery):
    """Настройки"""
    buttons = [
        [InlineKeyboardButton(text="🎙 Голоса для историй", callback_data="settings:voices")],
        [InlineKeyboardButton(text="📝 Промпты Reddit", callback_data="settings:prompts")],
        [InlineKeyboardButton(text="🎞 Библиотека фонов", callback_data="settings:backgrounds")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="menu:main")],
    ]
    await callback.message.edit_text(
        "⚙️ <b>Настройки</b>\n\n"
        "Выберите раздел:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )
    await callback.answer()


@router.callback_query(F.data == "settings:voices")
async def settings_voices(callback: types.CallbackQuery):
    """Настройки голосов"""
    from db.database import preset_voices_list

    voices = await preset_voices_list()

    buttons = []
    for v in voices:
        name = v.get("name", "Unknown")
        lang = v.get("lang", "en").upper()
        buttons.append([InlineKeyboardButton(
            text=f"🎤 {name} ({lang})",
            callback_data=f"voice:info:{v.get('voice_id')}"
        )])

    buttons.append([InlineKeyboardButton(text="➕ Добавить голос", callback_data="voice:add")])
    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="menu:settings")])

    text = f"🎙 <b>Голоса для историй</b>\n\nВсего голосов: {len(voices)}" if voices else "🎙 <b>Голоса для историй</b>\n\nСписок пуст"

    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )
    await callback.answer()


@router.callback_query(F.data == "voice:add")
async def voice_add(callback: types.CallbackQuery, state: FSMContext):
    """Добавление нового голоса по ID из GenAIPro"""
    await callback.message.edit_text(
        "🎙 <b>Добавление голоса</b>\n\n"
        "Введите Voice ID из GenAIPro (ElevenLabs):\n"
        "Например: <code>h9NSQvWZaC4NFusYsxT9</code>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отмена", callback_data="settings:voices")]
        ])
    )
    await state.set_state("waiting_voice_id")
    await callback.answer()


@router.message(F.text, StateFilter("waiting_voice_id"))
async def voice_id_received(message: types.Message, state: FSMContext):
    """Получен Voice ID - запрашиваем название"""
    voice_id = message.text.strip()

    if len(voice_id) < 5 or len(voice_id) > 50:
        await message.answer("❌ Неверный формат Voice ID. Попробуйте еще раз:")
        return

    await state.update_data(voice_id=voice_id)
    await message.answer(
        f"✅ Voice ID принят: <code>{voice_id}</code>\n\n"
        "Теперь введите название для этого голоса:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отмена", callback_data="settings:voices")]
        ])
    )
    await state.set_state("waiting_voice_name")


@router.message(F.text, StateFilter("waiting_voice_name"))
async def voice_name_received(message: types.Message, state: FSMContext):
    """Получено имя голоса - сохраняем"""
    from db.database import db

    data = await state.get_data()
    voice_id = data.get("voice_id")
    name = message.text.strip()

    if len(name) > 50:
        await message.answer("❌ Название слишком длинное (максимум 50 символов)")
        return

    await state.clear()
    msg = await message.answer("💾 Сохраняю голос...")

    try:
        # Сохраняем в БД
        await db().preset_voices.insert_one({
            "name": name,
            "voice_id": voice_id,
            "lang": "ru",
            "created_at": message.date
        })

        await msg.edit_text(
            f"✅ Голос <b>{name}</b> (ID: <code>{voice_id}</code>) успешно добавлен!",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Назад к голосам", callback_data="settings:voices")]
            ])
        )
    except Exception as e:
        await msg.edit_text(
            f"❌ Ошибка при сохранении: {str(e)}",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Назад к голосам", callback_data="settings:voices")]
            ])
        )


@router.callback_query(F.data == "settings:prompts")
async def settings_prompts(callback: types.CallbackQuery):
    """Настройки промптов"""
    buttons = [
        [InlineKeyboardButton(text="📱 Жизненные истории", callback_data="prompts:reddit")],
        [InlineKeyboardButton(text="🧠 Познавательные истории", callback_data="prompts:educational")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="menu:settings")],
    ]
    await callback.message.edit_text(
        "📝 <b>Промпты</b>\n\nВыберите тип историй:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )
    await callback.answer()


@router.callback_query(F.data == "settings:backgrounds")
async def settings_backgrounds(callback: types.CallbackQuery):
    """Настройки фонов"""
    from db.database import backgrounds_list

    docs = await backgrounds_list(scope="reddit")

    buttons = [
        [InlineKeyboardButton(text="➕ Загрузить фон", callback_data="bg:upload")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="menu:settings")],
    ]

    text = f"🎞 <b>Библиотека фонов</b>\n\nЗагружено видео: {len(docs)}" if docs else "🎞 <b>Библиотека фонов</b>\n\nСписок пуст"

    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )
    await callback.answer()


@router.callback_query(F.data == "menu:tasks")
async def menu_tasks(callback: types.CallbackQuery):
    """Просмотр задач пользователя"""
    from utils.task_queue import get_task_queue, TaskStatus

    task_queue = get_task_queue()
    user_tasks = task_queue.get_user_tasks(callback.from_user.id)

    if not user_tasks:
        buttons = [
            [InlineKeyboardButton(text="🎬 Создать видео", callback_data="menu:create")],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="menu:main")],
        ]
        await callback.message.edit_text(
            "📋 <b>Мои задачи</b>\n\n"
            "У вас пока нет задач",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
        )
        await callback.answer()
        return

    # Группируем задачи по статусу
    pending = [t for t in user_tasks if t.status == TaskStatus.PENDING]
    running = [t for t in user_tasks if t.status == TaskStatus.RUNNING]
    completed = [t for t in user_tasks if t.status == TaskStatus.COMPLETED]
    failed = [t for t in user_tasks if t.status == TaskStatus.FAILED]

    # Формируем текст
    text = "📋 <b>Мои задачи</b>\n\n"

    if running:
        text += "⚙️ <b>Выполняется:</b>\n"
        for task in running[:3]:
            icon = {
                "reddit": "📱",
                "educational": "🧠",
                "cuts": "✂️",
                "horror": "😱",
                "facts": "💡",
                "history": "📜",
                "news": "📰"
            }.get(task.task_type, "🎬")
            text += f"{icon} <code>{task.task_id}</code>\n"
        text += "\n"

    if pending:
        text += f"⏳ <b>В очереди:</b> {len(pending)}\n"
        for i, task in enumerate(pending[:3], 1):
            icon = {
                "reddit": "📱",
                "educational": "🧠",
                "cuts": "✂️",
                "horror": "😱",
                "facts": "💡",
                "history": "📜",
                "news": "📰"
            }.get(task.task_type, "🎬")
            text += f"{i}. {icon} <code>{task.task_id}</code>\n"
        if len(pending) > 3:
            text += f"   ... и ещё {len(pending) - 3}\n"
        text += "\n"

    if completed:
        text += f"✅ <b>Завершено:</b> {len(completed)}\n\n"

    if failed:
        text += f"❌ <b>Ошибок:</b> {len(failed)}\n\n"

    text += f"📊 Всего задач: {len(user_tasks)}"

    buttons = [
        [InlineKeyboardButton(text="🔄 Обновить", callback_data="menu:tasks")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="menu:main")],
    ]

    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )
    await callback.answer()
