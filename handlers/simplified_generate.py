# handlers/simplified_generate.py
"""
Упрощенный обработчик создания видео без каналов.
Прямой выбор параметров при создании.
"""
import os
import shutil
import tempfile
from aiogram import Router, F, types
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from utils.keyboards import (
    BTN_CREATE_SHORT, BTN_BACK, BTN_SIMPLE_CUTS, BTN_SIMPLE_REDDIT, BTN_SIMPLE_ANIMATION,
    BTN_LANG_RU, BTN_LANG_EN,
    BTN_FORMAT_TOP_VIDEO, BTN_FORMAT_CENTER, BTN_FORMAT_ANIMATION,
    main_kb, simple_theme_select_kb, simple_language_kb, simple_reddit_format_kb,
    cuts_collections_kb, simple_animation_select_kb
)
from utils.cuts import make_cut_from_collection
from utils.generation import _generate_reddit
from utils.ffmpeg import ensure_telegram_size
from db.database import preset_voices_list
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

router = Router()


class SimpleGenFSM(StatesGroup):
    """FSM состояния для упрощенного создания видео"""
    choose_theme = State()          # Выбор тематики (Нарезки / Reddit / Анимация)

    # Для нарезок
    choose_cuts_collection = State()  # Выбор коллекции

    # Для Reddit
    choose_language = State()        # Выбор языка
    choose_voice = State()           # Выбор голоса с тестированием
    choose_format = State()          # Выбор формата

    # Для режима только анимация
    choose_animation_language = State()  # Выбор языка для озвучки
    choose_animation_voice = State()     # Выбор голоса для озвучки
    choose_animation_type = State()      # Выбор типа анимации


# ========================= ГЛАВНОЕ МЕНЮ =========================

@router.message(F.text == BTN_CREATE_SHORT)
async def simple_gen_entry(message: types.Message, state: FSMContext):
    """Точка входа - выбор тематики"""
    await state.set_state(SimpleGenFSM.choose_theme)
    await message.answer(
        "Выберите тематику видео:",
        reply_markup=simple_theme_select_kb()
    )


@router.message(SimpleGenFSM.choose_theme, F.text == BTN_BACK)
async def back_to_main(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Главное меню:", reply_markup=main_kb())


# ========================= НАРЕЗКИ =========================

@router.message(SimpleGenFSM.choose_theme, F.text == BTN_SIMPLE_CUTS)
async def cuts_select_collection(message: types.Message, state: FSMContext):
    """Выбор коллекции для нарезок"""
    # Получаем список всех коллекций (и мультики, и фильмы)
    from utils.cuts import list_collections

    cartoons = list_collections("cartoons")
    films = list_collections("films")

    all_collections = []
    for c in cartoons:
        all_collections.append(("cartoons", c))
    for f in films:
        all_collections.append(("films", f))

    if not all_collections:
        await message.answer(
            "❌ Нет загруженных коллекций.\n\n"
            "Добавьте видео в папки:\n"
            "• assets/cartoons/название_коллекции/\n"
            "• assets/films/название_коллекции/",
            reply_markup=main_kb()
        )
        await state.clear()
        return

    # Формируем список для выбора
    collection_names = [f"{kind}: {name}" for kind, name in all_collections]

    await state.update_data(all_collections=all_collections)
    await state.set_state(SimpleGenFSM.choose_cuts_collection)
    await message.answer(
        "Выберите коллекцию для нарезки:",
        reply_markup=cuts_collections_kb(collection_names, show_create=False)
    )


@router.message(SimpleGenFSM.choose_cuts_collection, F.text == BTN_BACK)
async def cuts_back_to_theme(message: types.Message, state: FSMContext):
    await state.set_state(SimpleGenFSM.choose_theme)
    await message.answer("Выберите тематику видео:", reply_markup=simple_theme_select_kb())


@router.message(SimpleGenFSM.choose_cuts_collection, F.text)
async def cuts_generate(message: types.Message, state: FSMContext):
    """Генерация нарезки"""
    text = message.text.strip()

    data = await state.get_data()
    all_collections = data.get("all_collections", [])

    # Находим выбранную коллекцию
    selected = None
    for kind, name in all_collections:
        if text == f"{kind}: {name}":
            selected = (kind, name)
            break

    if not selected:
        await message.answer("❌ Коллекция не найдена. Попробуйте еще раз.")
        return

    kind, collection = selected

    await message.answer("🚀 Создаю нарезку... Это может занять немного времени.")

    # Создаем временную директорию
    workdir = tempfile.mkdtemp(prefix="cuts_")

    try:
        # Генерируем нарезку (180-240 секунд по умолчанию)
        final_path, picked_file, duration = await make_cut_from_collection(
            kind=kind,
            collection=collection,
            out_dir=workdir,
            min_sec=180,
            max_sec=240,
            banner_config=None
        )

        # Оптимизируем для Telegram
        target_path = os.path.join(workdir, "final_tg.mp4")
        safe_path = await ensure_telegram_size(final_path, target_path, target_mb=48)

        # Отправляем
        caption = f"✂️ Нарезка из {collection}\n📁 {picked_file}\n⏱ {int(duration)} сек"
        await message.answer_video(
            types.FSInputFile(safe_path),
            caption=caption,
            reply_markup=main_kb()
        )

    except Exception as e:
        await message.answer(f"⚠️ Ошибка при создании нарезки: {e}", reply_markup=main_kb())
    finally:
        # Очистка
        try:
            shutil.rmtree(workdir, ignore_errors=True)
        except:
            pass
        await state.clear()


# ========================= REDDIT STORY =========================

@router.message(SimpleGenFSM.choose_theme, F.text == BTN_SIMPLE_REDDIT)
async def reddit_select_language(message: types.Message, state: FSMContext):
    """Выбор языка для Reddit Story"""
    await state.set_state(SimpleGenFSM.choose_language)
    await message.answer(
        "Выберите язык для истории:",
        reply_markup=simple_language_kb()
    )


@router.message(SimpleGenFSM.choose_language, F.text == BTN_BACK)
async def reddit_back_to_theme(message: types.Message, state: FSMContext):
    await state.set_state(SimpleGenFSM.choose_theme)
    await message.answer("Выберите тематику видео:", reply_markup=simple_theme_select_kb())


@router.message(SimpleGenFSM.choose_language, F.text.in_([BTN_LANG_RU, BTN_LANG_EN]))
async def reddit_select_voice(message: types.Message, state: FSMContext):
    """Выбор голоса из предустановленных"""
    lang = "ru" if message.text == BTN_LANG_RU else "en"

    await state.update_data(language=lang)

    try:
        # Получаем ВСЕ предустановленные голоса (без фильтра по языку)
        voices = await preset_voices_list()

        if not voices:
            await message.answer(
                f"❌ Нет предустановленных голосов\n\n"
                f"Добавьте голоса через:\n"
                f"⚙️ Настройки → 🎙 Голоса для Reddit",
                reply_markup=main_kb()
            )
            await state.clear()
            return

        # Формируем список для отображения
        voice_list = [(v["name"], v["voice_id"], v.get("description")) for v in voices]

        # Сохраняем список голосов
        await state.update_data(voices=voice_list)
        await state.set_state(SimpleGenFSM.choose_voice)

        # Показываем список голосов inline кнопками
        await show_voice_list(message, state)

    except Exception as e:
        await message.answer(
            f"⚠️ Ошибка при загрузке голосов: {e}",
            reply_markup=main_kb()
        )
        await state.clear()


async def show_voice_list(message: types.Message, state: FSMContext):
    """Показывает список голосов с inline кнопками"""
    data = await state.get_data()
    voices = data.get("voices", [])

    if not voices:
        await message.answer("❌ Ошибка: нет доступных голосов")
        return

    # Создаем inline клавиатуру с голосами
    buttons = []
    for idx, (name, voice_id, description) in enumerate(voices):
        display_name = f"{name}"
        if description:
            display_name += f" - {description[:30]}"  # Ограничиваем длину

        buttons.append([
            InlineKeyboardButton(
                text=f"🎤 {display_name}",
                callback_data=f"voice:choose:{idx}"
            )
        ])

    # Добавляем кнопку отмены
    buttons.append([
        InlineKeyboardButton(text="❌ Отменить", callback_data="voice:cancel")
    ])

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    await message.answer(
        f"🎙 Выберите голос для озвучки:\n\n"
        f"Доступно голосов: {len(voices)}",
        reply_markup=keyboard
    )


# Обработчик выбора голоса из списка
@router.callback_query(F.data.startswith("voice:choose:"))
async def voice_choose_callback(callback: types.CallbackQuery, state: FSMContext):
    """Выбор конкретного голоса из списка"""
    current_state = await state.get_state()
    if current_state != SimpleGenFSM.choose_voice:
        await callback.answer("⚠️ Сессия устарела", show_alert=True)
        return

    # Получаем индекс выбранного голоса
    voice_index = int(callback.data.split(":")[2])

    data = await state.get_data()
    voices = data.get("voices", [])

    if not voices or voice_index >= len(voices):
        await callback.answer("❌ Ошибка: голос не найден", show_alert=True)
        return

    # Голос в формате (name, voice_id, description)
    name, voice_id, description = voices[voice_index]

    display_name = name
    if description:
        display_name += f" - {description}"

    await state.update_data(voice_id=voice_id, voice_name=name)
    await state.set_state(SimpleGenFSM.choose_format)

    await callback.message.answer(
        f"✅ Голос выбран: {display_name}\n\n"
        "Теперь выберите формат видео:",
        reply_markup=simple_reddit_format_kb()
    )

    try:
        await callback.message.delete()
    except:
        pass

    await callback.answer()


@router.callback_query(F.data == "voice:cancel")
async def voice_cancel_callback(callback: types.CallbackQuery, state: FSMContext):
    """Отмена выбора голоса (inline)"""
    await state.set_state(SimpleGenFSM.choose_language)
    await callback.message.answer("Выберите язык для истории:", reply_markup=simple_language_kb())

    try:
        await callback.message.delete()
    except:
        pass

    await callback.answer()




@router.message(SimpleGenFSM.choose_voice, F.text == BTN_BACK)
async def voice_back_to_language(message: types.Message, state: FSMContext):
    await state.set_state(SimpleGenFSM.choose_language)
    await message.answer("Выберите язык для истории:", reply_markup=simple_language_kb())


# ========================= ФОРМАТ И ГЕНЕРАЦИЯ =========================

@router.message(SimpleGenFSM.choose_format, F.text == BTN_BACK)
async def format_back_to_voice(message: types.Message, state: FSMContext):
    """Возврат к выбору голоса"""
    await state.set_state(SimpleGenFSM.choose_voice)
    # Показываем список голосов снова
    await show_voice_list(message, state)


@router.message(SimpleGenFSM.choose_format, F.text.in_([
    BTN_FORMAT_TOP_VIDEO, BTN_FORMAT_CENTER, BTN_FORMAT_ANIMATION
]))
async def reddit_generate(message: types.Message, state: FSMContext):
    """Генерация Reddit Story"""
    data = await state.get_data()
    lang = data.get("language", "en")
    voice_id = data.get("voice_id")
    voice_name = data.get("voice_name", "Unknown")

    # Определяем формат
    if message.text == BTN_FORMAT_TOP_VIDEO:
        bg_type = "video"
        card_position = "top"
    elif message.text == BTN_FORMAT_CENTER:
        bg_type = "video"
        card_position = "center"
    else:  # BTN_FORMAT_ANIMATION
        bg_type = "animation"
        card_position = "center"

    await message.answer(
        f"🚀 Создаю Reddit Story...\n\n"
        f"🌐 Язык: {lang.upper()}\n"
        f"🎤 Голос: {voice_name}\n"
        f"📺 Формат: {message.text}\n\n"
        f"⏳ Это может занять 1-2 минуты..."
    )

    # Создаем временную директорию
    workdir = tempfile.mkdtemp(prefix="reddit_")

    try:
        # Формируем конфиг канала для генерации
        channel_config = {
            "tts_lang": lang,
            "tts_voice": voice_id,
            "tts_speed": 1.1,
            "tts_engine": "genaipro",
            "reddit_target_sec": 75,
            "prompt_preset": "default",
            "background_type": bg_type,
            "reddit_card_position": card_position,
            "fps": 30,
            "subs_lang": None  # Без субтитров по умолчанию
        }

        # Генерируем Reddit Story
        result = await _generate_reddit(channel_config, workdir)

        final_path = result["video_path"]

        # Оптимизируем для Telegram
        target_path = os.path.join(workdir, "final_tg.mp4")
        safe_path = await ensure_telegram_size(final_path, target_path, target_mb=48)

        # Отправляем
        caption = f"📱 Reddit Story\n🌐 {lang.upper()}\n🎤 {voice_name}"
        await message.answer_video(
            types.FSInputFile(safe_path),
            caption=caption,
            reply_markup=main_kb()
        )

    except Exception as e:
        await message.answer(
            f"⚠️ Ошибка при создании Reddit Story:\n{e}",
            reply_markup=main_kb()
        )
    finally:
        # Очистка
        try:
            shutil.rmtree(workdir, ignore_errors=True)
        except:
            pass
        await state.clear()


# ========================= РЕЖИМ ТОЛЬКО АНИМАЦИЯ =========================

@router.message(SimpleGenFSM.choose_theme, F.text == BTN_SIMPLE_ANIMATION)
async def animation_select_language(message: types.Message, state: FSMContext):
    """Выбор языка для режима только анимация"""
    await state.set_state(SimpleGenFSM.choose_animation_language)
    await message.answer(
        "Выберите язык для озвучки:",
        reply_markup=simple_language_kb()
    )


@router.message(SimpleGenFSM.choose_animation_language, F.text == BTN_BACK)
async def animation_back_to_theme(message: types.Message, state: FSMContext):
    await state.set_state(SimpleGenFSM.choose_theme)
    await message.answer("Выберите тематику видео:", reply_markup=simple_theme_select_kb())


@router.message(SimpleGenFSM.choose_animation_language, F.text.in_([BTN_LANG_RU, BTN_LANG_EN]))
async def animation_select_voice(message: types.Message, state: FSMContext):
    """Выбор голоса для озвучки"""
    lang = "ru" if message.text == BTN_LANG_RU else "en"
    await state.update_data(language=lang)

    try:
        voices = await preset_voices_list()

        if not voices:
            await message.answer(
                f"❌ Нет предустановленных голосов\n\n"
                f"Добавьте голоса через:\n"
                f"⚙️ Настройки → 🎙 Голоса для Reddit",
                reply_markup=main_kb()
            )
            await state.clear()
            return

        voice_list = [(v["name"], v["voice_id"], v.get("description")) for v in voices]
        await state.update_data(voices=voice_list)
        await state.set_state(SimpleGenFSM.choose_animation_voice)
        await show_animation_voice_list(message, state)

    except Exception as e:
        await message.answer(
            f"⚠️ Ошибка при загрузке голосов: {e}",
            reply_markup=main_kb()
        )
        await state.clear()


async def show_animation_voice_list(message: types.Message, state: FSMContext):
    """Показывает список голосов для анимации"""
    data = await state.get_data()
    voices = data.get("voices", [])

    if not voices:
        await message.answer("❌ Ошибка: нет доступных голосов")
        return

    buttons = []
    for idx, (name, _voice_id, description) in enumerate(voices):
        display_name = f"{name}"
        if description:
            display_name += f" - {description[:30]}"

        buttons.append([
            InlineKeyboardButton(
                text=f"🎤 {display_name}",
                callback_data=f"anim_voice:choose:{idx}"
            )
        ])

    buttons.append([
        InlineKeyboardButton(text="❌ Отменить", callback_data="anim_voice:cancel")
    ])

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    await message.answer(
        f"🎙 Выберите голос для озвучки:\n\n"
        f"Доступно голосов: {len(voices)}",
        reply_markup=keyboard
    )


@router.callback_query(F.data.startswith("anim_voice:choose:"))
async def animation_voice_choose_callback(callback: types.CallbackQuery, state: FSMContext):
    """Выбор голоса для анимации"""
    current_state = await state.get_state()
    if current_state != SimpleGenFSM.choose_animation_voice:
        await callback.answer("⚠️ Сессия устарела", show_alert=True)
        return

    voice_index = int(callback.data.split(":")[2])
    data = await state.get_data()
    voices = data.get("voices", [])

    if not voices or voice_index >= len(voices):
        await callback.answer("❌ Ошибка: голос не найден", show_alert=True)
        return

    name, voice_id, description = voices[voice_index]
    display_name = name
    if description:
        display_name += f" - {description}"

    await state.update_data(voice_id=voice_id, voice_name=name)
    await state.set_state(SimpleGenFSM.choose_animation_type)

    # Показываем список анимаций
    from utils.animations import AnimationGenerator
    anim_gen = AnimationGenerator()
    available_anims = anim_gen.get_available_animations()
    anim_names = [f"{a['name']}" for a in available_anims]

    await callback.message.answer(
        f"✅ Голос выбран: {display_name}\n\n"
        "Теперь выберите тип анимации:",
        reply_markup=simple_animation_select_kb(anim_names)
    )

    try:
        await callback.message.delete()
    except:
        pass

    await callback.answer()


@router.callback_query(F.data == "anim_voice:cancel")
async def animation_voice_cancel_callback(callback: types.CallbackQuery, state: FSMContext):
    """Отмена выбора голоса для анимации"""
    await state.set_state(SimpleGenFSM.choose_animation_language)
    await callback.message.answer("Выберите язык для озвучки:", reply_markup=simple_language_kb())

    try:
        await callback.message.delete()
    except:
        pass

    await callback.answer()


@router.message(SimpleGenFSM.choose_animation_voice, F.text == BTN_BACK)
async def animation_voice_back(message: types.Message, state: FSMContext):
    await state.set_state(SimpleGenFSM.choose_animation_language)
    await message.answer("Выберите язык для озвучки:", reply_markup=simple_language_kb())


@router.message(SimpleGenFSM.choose_animation_type, F.text == BTN_BACK)
async def animation_type_back(message: types.Message, state: FSMContext):
    """Возврат к выбору голоса"""
    await state.set_state(SimpleGenFSM.choose_animation_voice)
    await show_animation_voice_list(message, state)


@router.message(SimpleGenFSM.choose_animation_type, F.text)
async def animation_generate(message: types.Message, state: FSMContext):
    """Генерация видео: только анимация + озвучка"""
    data = await state.get_data()
    lang = data.get("language", "en")
    voice_id = data.get("voice_id")
    voice_name = data.get("voice_name", "Unknown")

    # Определяем тип анимации
    from utils.animations import AnimationGenerator
    anim_gen = AnimationGenerator()
    available_anims = anim_gen.get_available_animations()

    animation_type = None
    if message.text == "🎲 Случайная анимация":
        animation_type = None  # Случайный выбор
    else:
        # Ищем по названию
        for anim in available_anims:
            if message.text == anim["name"]:
                animation_type = anim["type"]
                break

    await message.answer(
        f"🚀 Создаю видео с анимацией...\n\n"
        f"🌐 Язык: {lang.upper()}\n"
        f"🎤 Голос: {voice_name}\n"
        f"🎨 Анимация: {message.text}\n\n"
        f"⏳ Это может занять 2-3 минуты..."
    )

    # Создаем временную директорию
    workdir = tempfile.mkdtemp(prefix="animation_")

    try:
        # Формируем конфиг канала для генерации
        channel_config = {
            "mode": "animation_only",
            "tts_lang": lang,
            "tts_voice": voice_id,
            "tts_speed": 1.1,
            "tts_engine": "genaipro",
            "reddit_target_sec": 75,
            "prompt_preset": "default",
            "animation_type": animation_type,
            "fps": 30,
        }

        # Генерируем видео
        from utils.generation import generate_for_channel
        result = await generate_for_channel(channel_config, workdir)

        final_path = result["video_path"]

        # Оптимизируем для Telegram
        target_path = os.path.join(workdir, "final_tg.mp4")
        safe_path = await ensure_telegram_size(final_path, target_path, target_mb=48)

        # Отправляем
        caption = f"🎨 Анимация + озвучка\n🌐 {lang.upper()}\n🎤 {voice_name}"
        await message.answer_video(
            types.FSInputFile(safe_path),
            caption=caption,
            reply_markup=main_kb()
        )

    except Exception as e:
        await message.answer(
            f"⚠️ Ошибка при создании видео:\n{e}",
            reply_markup=main_kb()
        )
    finally:
        # Очистка
        try:
            shutil.rmtree(workdir, ignore_errors=True)
        except:
            pass
        await state.clear()
