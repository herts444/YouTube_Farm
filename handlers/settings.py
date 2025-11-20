from __future__ import annotations

import os
import time
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.filters import StateFilter
from PIL import Image

from utils.keyboards import (
    BTN_SETTINGS, BTN_BACK,
    BTN_MEDIA_LIBRARY, BTN_REDDIT_PROMPTS, BTN_BANNERS_LIBRARY, BTN_CUTS_LIBRARY, BTN_PRESET_VOICES,
    main_kb, settings_kb, prompts_inline_kb, media_inline_kb, banners_inline_kb,
    preset_voices_list_kb, preset_voices_actions_kb
)
from db.database import (
    prompts_list, prompts_get, prompts_upsert, prompts_delete_by_id,
    backgrounds_list, backgrounds_add, backgrounds_delete,
    banners_list, banners_add, banners_delete,
    preset_voices_list, preset_voices_add, preset_voices_delete, preset_voices_get_by_voice_id
)

router = Router(name="settings")

# ================= FSM =================
class PromptEdit(StatesGroup):
    editing = State()
    creating = State()
    entering_preset_name = State()

class MediaUpload(StatesGroup):
    waiting_file = State()
    waiting_banner = State()

class SettingsMenu(StatesGroup):
    main = State()

class CutsLibrary(StatesGroup):
    viewing = State()

class PresetVoices(StatesGroup):
    viewing = State()
    adding_name = State()
    adding_voice_id = State()
    adding_lang = State()
    adding_description = State()
    voice_actions = State()

# ================= Entry =================
@router.message(F.text == BTN_SETTINGS)
async def open_settings(msg: Message, state: FSMContext):
    await state.set_state(SettingsMenu.main)
    await msg.answer("⚙️ Настройки", reply_markup=settings_kb())

# Обработчик кнопки Назад в контексте настроек
@router.message(StateFilter(SettingsMenu.main, PromptEdit.editing, PromptEdit.creating,
                           PromptEdit.entering_preset_name, MediaUpload.waiting_file,
                           MediaUpload.waiting_banner, CutsLibrary.viewing,
                           PresetVoices.viewing, PresetVoices.adding_name, PresetVoices.adding_voice_id,
                           PresetVoices.adding_lang, PresetVoices.adding_description, PresetVoices.voice_actions),
                F.text == BTN_BACK)
async def back_from_settings(msg: Message, state: FSMContext):
    await state.clear()
    await msg.answer("Главное меню", reply_markup=main_kb())

# ================= ПРОМПТЫ =================
@router.message(StateFilter(SettingsMenu.main), F.text == BTN_REDDIT_PROMPTS)
async def show_prompts_menu(msg: Message, state: FSMContext):
    lang = "ru"  # По умолчанию русский
    await state.update_data(prompt_lang=lang)
    docs = await prompts_list(scope="reddit", lang=lang)
    presets = sorted(list({d["preset"] for d in docs}))
    
    if not presets:
        # Если нет пресетов, создаем default
        await prompts_upsert(
            scope="reddit", 
            preset="default", 
            lang=lang,
            text="Напиши захватывающую историю в стиле Reddit. Начни с интригующего хука, развивай напряжение и заверши неожиданным поворотом.",
            updated_by=msg.from_user.id
        )
        presets = ["default"]
    
    kb = prompts_inline_kb(presets, lang)
    await msg.answer(f"📝 Промпты Reddit ({lang.upper()})\nВыберите пресет для редактирования:", reply_markup=kb)

@router.callback_query(F.data.startswith("prompt:lang:"))
async def switch_lang(cb: CallbackQuery, state: FSMContext):
    current_lang = cb.data.split(":")[2]
    new_lang = "en" if current_lang == "ru" else "ru"
    await state.update_data(prompt_lang=new_lang)
    
    docs = await prompts_list(scope="reddit", lang=new_lang)
    presets = sorted(list({d["preset"] for d in docs}))
    
    if not presets:
        presets = ["default"]
    
    kb = prompts_inline_kb(presets, new_lang)
    await cb.message.edit_text(f"📝 Промпты Reddit ({new_lang.upper()})\nВыберите пресет для редактирования:", reply_markup=kb)
    await cb.answer(f"Переключено на {new_lang.upper()}")

@router.callback_query(F.data.startswith("prompt:edit:"))
async def prompt_edit(cb: CallbackQuery, state: FSMContext):
    _, _, preset, lang = cb.data.split(":")
    doc = await prompts_get("reddit", preset, lang)
    
    if doc:
        text = doc.get("text", "— пусто —")
    else:
        # Создаем базовый промпт
        if lang == "ru":
            text = ("Напиши захватывающую историю в стиле Reddit от первого лица. "
                   "Начни с цепляющего хука, развивай интригу, заверши неожиданным поворотом. "
                   "Без морали, естественный язык, конкретика. Длина: 150-220 слов.")
        else:
            text = ("Write a captivating Reddit-style first-person story. "
                   "Start with a hook, build tension, end with a twist. "
                   "No moral, natural language, specifics. Length: 150-220 words.")
    
    await state.update_data(preset=preset, lang=lang)
    
    buttons = [[InlineKeyboardButton(text="🗑 Удалить пресет", callback_data=f"prompt:del:{preset}:{lang}")]] if preset != "default" else []
    kb = InlineKeyboardMarkup(inline_keyboard=buttons) if buttons else None
    
    await cb.message.answer(
        f"📝 Редактирование промпта\n"
        f"Пресет: <b>{preset}</b>\n"
        f"Язык: <b>{lang}</b>\n\n"
        f"Текущий промпт:\n<i>{text}</i>\n\n"
        f"Отправьте новый текст промпта одним сообщением:",
        reply_markup=kb
    )
    await state.set_state(PromptEdit.editing)
    await cb.answer()

@router.callback_query(F.data.startswith("prompt:del:"))
async def prompt_delete(cb: CallbackQuery, state: FSMContext):
    _, _, preset, lang = cb.data.split(":")
    
    if preset == "default":
        await cb.answer("Нельзя удалить пресет default", show_alert=True)
        return
    
    doc = await prompts_get("reddit", preset, lang)
    if doc:
        await prompts_delete_by_id(doc["_id"])
        await cb.answer(f"Пресет {preset} удален")
    else:
        await cb.answer("Нечего удалять")
    
    # Обновляем список
    docs = await prompts_list(scope="reddit", lang=lang)
    presets = sorted(list({d["preset"] for d in docs})) or ["default"]
    await cb.message.edit_text(f"📝 Промпты Reddit ({lang.upper()})\nВыберите пресет:", reply_markup=prompts_inline_kb(presets, lang))

@router.message(PromptEdit.editing)
async def prompt_save_edit(msg: Message, state: FSMContext):
    data = await state.get_data()
    preset = data.get("preset", "default")
    lang = data.get("lang", "ru")
    
    await prompts_upsert(
        scope="reddit",
        preset=preset,
        lang=lang,
        text=msg.text,
        updated_by=msg.from_user.id
    )
    
    await msg.answer(f"✅ Промпт <b>{preset}/{lang}</b> сохранён!", reply_markup=settings_kb())
    await state.set_state(SettingsMenu.main)

@router.callback_query(F.data.startswith("prompt:new:"))
async def prompt_new(cb: CallbackQuery, state: FSMContext):
    _, _, lang = cb.data.split(":")
    await state.update_data(lang=lang)
    await state.set_state(PromptEdit.entering_preset_name)
    await cb.message.answer(f"Введите название нового пресета (например: mystory, horror, funny):")
    await cb.answer()

@router.message(PromptEdit.entering_preset_name)
async def prompt_new_name(msg: Message, state: FSMContext):
    preset_name = msg.text.strip().lower().replace(" ", "_")
    data = await state.get_data()
    lang = data.get("lang", "ru")
    
    # Проверяем, не существует ли уже
    existing = await prompts_get("reddit", preset_name, lang)
    if existing:
        await msg.answer(f"⚠️ Пресет <b>{preset_name}</b> уже существует. Введите другое название:")
        return
    
    await state.update_data(preset=preset_name)
    await state.set_state(PromptEdit.creating)
    
    if lang == "ru":
        example = ("Напиши историю о [тема]. Начни с неожиданного факта, "
                  "развивай сюжет через конфликт, заверши ироничным выводом.")
    else:
        example = ("Write a story about [topic]. Start with surprising fact, "
                  "develop through conflict, end with ironic conclusion.")
    
    await msg.answer(
        f"📝 Создание пресета <b>{preset_name}</b> ({lang})\n\n"
        f"Пример промпта:\n<i>{example}</i>\n\n"
        f"Отправьте текст промпта:"
    )

@router.message(PromptEdit.creating)
async def prompt_new_save(msg: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "ru")
    preset = data.get("preset", "custom")
    
    await prompts_upsert("reddit", preset, lang, msg.text, updated_by=msg.from_user.id)
    await msg.answer(f"✅ Новый пресет <b>{preset}/{lang}</b> создан!", reply_markup=settings_kb())
    await state.set_state(SettingsMenu.main)

# ================= БИБЛИОТЕКА ФОНОВ =================
@router.message(StateFilter(SettingsMenu.main), F.text == BTN_MEDIA_LIBRARY)
async def media_list_screen(msg: Message):
    docs = await backgrounds_list(scope="reddit")
    files = [d["file"] for d in docs]
    
    if not files:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="➕ Загрузить первое видео", callback_data="media:upload")]
        ])
        await msg.answer(
            "🎞 Библиотека фонов (Reddit)\n\n"
            "Пока пусто. Загрузите видео для использования в качестве фона.\n"
            "Рекомендуется 10-20 разных видео длительностью 5+ минут.",
            reply_markup=kb
        )
    else:
        kb = media_inline_kb(files)
        await msg.answer(
            f"🎞 Библиотека фонов (Reddit)\n"
            f"Загружено видео: {len(files)}\n\n"
            f"При генерации будет выбрано случайное видео и случайный отрезок из него.",
            reply_markup=kb
        )

@router.callback_query(F.data == "media:upload")
async def media_ask_upload(cb: CallbackQuery, state: FSMContext):
    await state.set_state(MediaUpload.waiting_file)
    await cb.message.answer(
        "📤 Отправьте MP4 видео для фона.\n"
        "Рекомендации:\n"
        "• Длительность 5+ минут\n"
        "• Вертикальное или квадратное\n"
        "• Спокойный контент (природа, геймплей, абстракция)"
    )
    await cb.answer()

@router.message(MediaUpload.waiting_file, F.video | F.document)
async def media_handle_upload(msg: Message, state: FSMContext):
    file = msg.video or msg.document
    if not file:
        await msg.answer("⚠️ Отправьте видеофайл")
        return
    
    filename = file.file_name or "video.mp4"
    if not filename.lower().endswith((".mp4", ".mov", ".mkv", ".webm")):
        await msg.answer("⚠️ Поддерживаются только видео форматы: .mp4, .mov, .mkv, .webm")
        return
    
    # Проверяем размер
    size = getattr(file, "file_size", 0) or 0
    if size > 50 * 1024 * 1024:  # 50 MB
        await msg.answer("⚠️ Файл слишком большой (макс 50 МБ). Используйте ссылку на файл или загрузите напрямую на сервер.")
        return
    
    # Сохраняем
    dest_dir = os.path.join("assets", "bg", "reddit")
    os.makedirs(dest_dir, exist_ok=True)
    
    # Уникальное имя
    unique_name = f"{int(time.time())}_{filename}"
    dst = os.path.join(dest_dir, unique_name)
    
    await msg.bot.download(file, destination=dst)
    await backgrounds_add("reddit", unique_name, dst, uploaded_by=msg.from_user.id)
    
    # Показываем обновленный список
    docs = await backgrounds_list(scope="reddit")
    await msg.answer(
        f"✅ Видео загружено!\n"
        f"Всего фонов: {len(docs)}\n\n"
        f"Добавьте еще видео или вернитесь в настройки.",
        reply_markup=settings_kb()
    )
    await state.set_state(SettingsMenu.main)

@router.callback_query(F.data.startswith("media:del:"))
async def media_delete_one(cb: CallbackQuery):
    fname = cb.data.replace("media:del:", "")
    
    # Удаляем из БД
    await backgrounds_delete("reddit", fname)
    
    # Удаляем файл
    try:
        path = os.path.join("assets", "bg", "reddit", fname)
        if os.path.exists(path):
            os.remove(path)
    except Exception:
        pass
    
    await cb.answer("Удалено")
    
    # Обновляем список
    docs = await backgrounds_list(scope="reddit")
    files = [d["file"] for d in docs]
    
    if files:
        await cb.message.edit_reply_markup(reply_markup=media_inline_kb(files))
    else:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="➕ Загрузить видео", callback_data="media:upload")]
        ])
        await cb.message.edit_text("🎞 Библиотека пуста", reply_markup=kb)

# ================= БИБЛИОТЕКА БАННЕРОВ =================
@router.message(StateFilter(SettingsMenu.main), F.text == BTN_BANNERS_LIBRARY)
async def banners_list_screen(msg: Message):
    docs = await banners_list(scope="cuts")
    files = [d["file"] for d in docs]
    
    if not files:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="➕ Загрузить первый баннер", callback_data="banner:upload")]
        ])
        await msg.answer(
            "🖼 Библиотека баннеров для нарезок\n\n"
            "Пока пусто. Загрузите PNG баннеры (логотипы, водяные знаки).\n"
            "Рекомендуемый размер: 200-400px по ширине, прозрачный фон.",
            reply_markup=kb
        )
    else:
        kb = banners_inline_kb(files)
        await msg.answer(
            f"🖼 Библиотека баннеров для нарезок\n"
            f"Загружено баннеров: {len(files)}\n\n"
            f"Баннеры можно привязать к каналу в настройках канала.",
            reply_markup=kb
        )

@router.callback_query(F.data == "banner:upload")
async def banner_ask_upload(cb: CallbackQuery, state: FSMContext):
    await state.set_state(MediaUpload.waiting_banner)
    await cb.message.answer(
        "📤 Отправьте PNG файл баннера.\n"
        "Рекомендации:\n"
        "• Формат: PNG с прозрачностью\n"
        "• Размер: 200-400px по ширине\n"
        "• Содержание: логотип, водяной знак, название канала"
    )
    await cb.answer()

@router.message(MediaUpload.waiting_banner, F.photo | F.document)
async def banner_handle_upload(msg: Message, state: FSMContext):
    file = None
    filename = None
    
    # Обработка фото (Telegram конвертирует в JPEG, но мы сохраним как PNG)
    if msg.photo:
        file = msg.photo[-1]  # Берем самое большое разрешение
        filename = f"banner_{int(time.time())}.png"
    # Обработка документа
    elif msg.document:
        file = msg.document
        filename = file.file_name or f"banner_{int(time.time())}.png"
        
        if not filename.lower().endswith(".png"):
            await msg.answer("⚠️ Поддерживается только формат PNG")
            return
    
    if not file:
        await msg.answer("⚠️ Отправьте PNG файл")
        return
    
    # Проверяем размер
    size = getattr(file, "file_size", 0) or 0
    if size > 10 * 1024 * 1024:  # 10 MB
        await msg.answer("⚠️ Файл слишком большой (макс 10 МБ)")
        return
    
    # Сохраняем
    dest_dir = os.path.join("assets", "banners", "cuts")
    os.makedirs(dest_dir, exist_ok=True)
    
    # Уникальное имя
    if not filename:
        filename = f"banner_{int(time.time())}.png"
    
    # Убеждаемся что имя уникальное
    base_name = os.path.splitext(filename)[0]
    ext = ".png"
    counter = 0
    unique_name = filename
    while os.path.exists(os.path.join(dest_dir, unique_name)):
        counter += 1
        unique_name = f"{base_name}_{counter}{ext}"
    
    dst = os.path.join(dest_dir, unique_name)
    
    # Скачиваем файл
    await msg.bot.download(file, destination=dst)
    
    # Если это было фото (JPEG), конвертируем в PNG
    if msg.photo:
        try:
            img = Image.open(dst)
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            img.save(dst, 'PNG')
        except Exception as e:
            await msg.answer(f"⚠️ Ошибка обработки изображения: {e}")
            os.remove(dst)
            return
    
    # Добавляем в БД
    await banners_add("cuts", unique_name, dst, uploaded_by=msg.from_user.id)
    
    # Показываем обновленный список
    docs = await banners_list(scope="cuts")
    await msg.answer(
        f"✅ Баннер загружен: {unique_name}\n"
        f"Всего баннеров: {len(docs)}\n\n"
        f"Теперь вы можете привязать его к каналу.",
        reply_markup=settings_kb()
    )
    await state.set_state(SettingsMenu.main)

@router.callback_query(F.data.startswith("banner:del:"))
async def banner_delete_one(cb: CallbackQuery):
    fname = cb.data.replace("banner:del:", "")
    
    # Удаляем из БД
    await banners_delete("cuts", fname)
    
    # Удаляем файл
    try:
        path = os.path.join("assets", "banners", "cuts", fname)
        if os.path.exists(path):
            os.remove(path)
    except Exception:
        pass
    
    await cb.answer("Удалено")
    
    # Обновляем список
    docs = await banners_list(scope="cuts")
    files = [d["file"] for d in docs]
    
    if files:
        await cb.message.edit_reply_markup(reply_markup=banners_inline_kb(files))
    else:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="➕ Загрузить баннер", callback_data="banner:upload")]
        ])
        await cb.message.edit_text("🖼 Библиотека баннеров пуста", reply_markup=kb)

# ================= БИБЛИОТЕКА МЕДИА (перенос из cuts.py) =================
@router.message(StateFilter(SettingsMenu.main), F.text == BTN_CUTS_LIBRARY)
async def cuts_library_entry(msg: Message, state: FSMContext):
    await state.set_state(CutsLibrary.viewing)
    await msg.answer(
        "📚 Библиотека медиа для нарезок\n\n"
        "Управление коллекциями видео осуществляется через раздел:\n"
        "Каналы → Выбрать канал → Выбрать коллекцию\n\n"
        "Там вы можете:\n"
        "• Создать новую коллекцию\n"
        "• Загрузить видео в коллекцию\n"
        "• Выбрать коллекцию для канала",
        reply_markup=settings_kb()
    )

# ================= PRESET VOICES (Предустановленные голоса для Reddit) =================
@router.message(StateFilter(SettingsMenu.main), F.text == BTN_PRESET_VOICES)
async def preset_voices_entry(msg: Message, state: FSMContext):
    """Показывает список предустановленных голосов"""
    voices = await preset_voices_list()

    if not voices:
        await msg.answer(
            "🎙 Предустановленные голоса для Reddit\n\n"
            "Список пуст. Добавьте голоса из GenAIPro API.\n\n"
            "Для добавления нажмите ➕ Добавить голос",
            reply_markup=preset_voices_list_kb([])
        )
    else:
        voice_names = [f"{v['name']} ({v['lang'].upper()})" for v in voices]
        await msg.answer(
            f"🎙 Предустановленные голоса для Reddit\n\n"
            f"Всего голосов: {len(voices)}\n\n"
            f"Выберите голос для действий:",
            reply_markup=preset_voices_list_kb(voice_names)
        )

    await state.set_state(PresetVoices.viewing)


@router.message(PresetVoices.viewing, F.text == "➕ Добавить голос")
async def preset_voice_add_start(msg: Message, state: FSMContext):
    """Начало добавления нового голоса"""
    await state.set_state(PresetVoices.adding_name)
    await msg.answer(
        "🎙 Добавление нового голоса\n\n"
        "Шаг 1/4: Введите название голоса\n"
        "Например: Sarah, Antoni, Rachel\n\n"
        "Или нажмите Назад для отмены."
    )


@router.message(PresetVoices.adding_name, F.text)
async def preset_voice_add_name(msg: Message, state: FSMContext):
    """Получение названия голоса"""
    name = msg.text.strip()
    await state.update_data(voice_name=name)
    await state.set_state(PresetVoices.adding_voice_id)

    await msg.answer(
        f"✅ Название: {name}\n\n"
        f"Шаг 2/4: Введите Voice ID из GenAIPro\n"
        f"Например: uju3wxzG5OhpWcoi3SMy\n\n"
        f"Voice ID можно найти в админке GenAIPro."
    )


@router.message(PresetVoices.adding_voice_id, F.text)
async def preset_voice_add_id(msg: Message, state: FSMContext):
    """Получение voice_id"""
    voice_id = msg.text.strip()
    await state.update_data(voice_id=voice_id)
    await state.set_state(PresetVoices.adding_lang)

    from utils.keyboards import ReplyKeyboardMarkup, KeyboardButton
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="ru"), KeyboardButton(text="en")],
            [KeyboardButton(text=BTN_BACK)]
        ],
        resize_keyboard=True
    )

    await msg.answer(
        f"✅ Voice ID: {voice_id}\n\n"
        f"Шаг 3/4: Выберите язык голоса",
        reply_markup=kb
    )


@router.message(PresetVoices.adding_lang, F.text.in_(["ru", "en"]))
async def preset_voice_add_lang(msg: Message, state: FSMContext):
    """Получение языка"""
    lang = msg.text.strip().lower()
    await state.update_data(lang=lang)
    await state.set_state(PresetVoices.adding_description)

    await msg.answer(
        f"✅ Язык: {lang.upper()}\n\n"
        f"Шаг 4/4: Введите описание голоса (необязательно)\n"
        f"Например: Женский, мягкий, американский акцент\n\n"
        f"Или отправьте '-' чтобы пропустить."
    )


@router.message(PresetVoices.adding_description, F.text)
async def preset_voice_add_description(msg: Message, state: FSMContext):
    """Сохранение голоса"""
    description = msg.text.strip() if msg.text.strip() != "-" else None

    data = await state.get_data()
    name = data.get("voice_name")
    voice_id = data.get("voice_id")
    lang = data.get("lang")

    # Сохраняем в БД
    try:
        await preset_voices_add(
            name=name,
            voice_id=voice_id,
            lang=lang,
            description=description,
            created_by=msg.from_user.id
        )

        await msg.answer(
            f"✅ Голос добавлен!\n\n"
            f"📝 Название: {name}\n"
            f"🆔 Voice ID: {voice_id}\n"
            f"🌐 Язык: {lang.upper()}\n"
            f"📄 Описание: {description or 'не указано'}",
            reply_markup=settings_kb()
        )

        await state.set_state(SettingsMenu.main)

    except Exception as e:
        await msg.answer(
            f"⚠️ Ошибка при добавлении голоса:\n{e}",
            reply_markup=settings_kb()
        )
        await state.set_state(SettingsMenu.main)


@router.message(PresetVoices.viewing, F.text.startswith("🎤 "))
async def preset_voice_select(msg: Message, state: FSMContext):
    """Выбор голоса для действий"""
    # Парсим имя голоса из кнопки "🎤 Name (LANG)"
    text = msg.text.replace("🎤 ", "")

    # Разделяем на имя и язык
    if "(" in text and ")" in text:
        name_part = text.split("(")[0].strip()
        lang_part = text.split("(")[1].replace(")", "").strip().lower()
    else:
        await msg.answer("⚠️ Не удалось распознать голос")
        return

    # Ищем голос в БД
    voices = await preset_voices_list(lang=lang_part)
    voice = None
    for v in voices:
        if v["name"] == name_part:
            voice = v
            break

    if not voice:
        await msg.answer("⚠️ Голос не найден в базе данных")
        return

    await state.update_data(selected_voice=voice)
    await state.set_state(PresetVoices.voice_actions)

    desc = voice.get("description", "не указано")
    await msg.answer(
        f"🎤 {voice['name']}\n\n"
        f"🆔 Voice ID: {voice['voice_id']}\n"
        f"🌐 Язык: {voice['lang'].upper()}\n"
        f"📄 Описание: {desc}\n\n"
        f"Выберите действие:",
        reply_markup=preset_voices_actions_kb()
    )


@router.message(PresetVoices.voice_actions, F.text == "🎧 Прослушать")
async def preset_voice_listen(msg: Message, state: FSMContext):
    """Тестовое прослушивание голоса"""
    import tempfile
    import shutil
    from utils.genaipro import synthesize_preview

    data = await state.get_data()
    voice = data.get("selected_voice")

    if not voice:
        await msg.answer("⚠️ Голос не выбран")
        return

    lang = voice["lang"]
    voice_id = voice["voice_id"]

    # Тестовый текст
    if lang == "ru":
        test_text = f"Привет! Меня зовут {voice['name']}. Это тестовое сообщение для проверки голоса."
    else:
        test_text = f"Hello! My name is {voice['name']}. This is a test message to preview the voice."

    await msg.answer("⏳ Генерирую превью...")

    try:
        preview_dir = tempfile.mkdtemp(prefix="voice_preview_")
        preview_path = os.path.join(preview_dir, "preview.mp3")

        await synthesize_preview(
            voice_id=voice_id,
            text=test_text,
            output_path=preview_path
        )

        from aiogram.types import FSInputFile
        await msg.answer_voice(
            FSInputFile(preview_path),
            caption=f"🎤 {voice['name']} ({lang.upper()})"
        )

        # Очистка
        try:
            shutil.rmtree(preview_dir, ignore_errors=True)
        except:
            pass

    except Exception as e:
        await msg.answer(f"⚠️ Ошибка при генерации превью:\n{e}")


@router.message(PresetVoices.voice_actions, F.text == "🗑 Удалить")
async def preset_voice_delete(msg: Message, state: FSMContext):
    """Удаление голоса"""
    data = await state.get_data()
    voice = data.get("selected_voice")

    if not voice:
        await msg.answer("⚠️ Голос не выбран")
        return

    try:
        await preset_voices_delete(voice["voice_id"])

        await msg.answer(
            f"✅ Голос '{voice['name']}' удален",
            reply_markup=settings_kb()
        )

        await state.set_state(SettingsMenu.main)

    except Exception as e:
        await msg.answer(
            f"⚠️ Ошибка при удалении:\n{e}",
            reply_markup=settings_kb()
        )
        await state.set_state(SettingsMenu.main)