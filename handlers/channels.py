# handlers/channels.py
from __future__ import annotations

import os
from aiogram import Router, F, types
from aiogram.types import FSInputFile
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from db.database import (
    list_channels,
    create_channel,
    get_channel,
    set_channel_theme,
    list_themes,
    delete_channel,
    set_channel_tts_lang,
    set_channel_tts_voice,
    set_channel_tts_speed,
    set_channel_cuts,
    set_channel_cuts_duration,
    set_channel_banner,
    set_channel_background_type,
    banners_list,
)

from utils.cuts import list_collections, count_videos
# TTS теперь только GenAIPro
from utils.keyboards import (
    # главные / общие
    BTN_CHANNELS,
    BTN_CHANNEL_ADD,
    BTN_BACK,
    BTN_CHANNEL_SET_TTS,
    BTN_CHANNEL_DELETE,
    BTN_YES,
    BTN_NO,
    BTN_CHANNEL_SET_SUBS,
    BTN_SUBS_OFF,
    BTN_SUBS_EN,
    BTN_SUBS_RU,
    BTN_CHANNEL_SET_BANNER,
    BTN_BANNER_POS_TOP,
    BTN_BANNER_POS_CENTER,
    BTN_BANNER_POS_BOTTOM,
    BTN_BANNER_REMOVE,
    main_kb,
    channels_list_kb,
    channel_actions_kb_reddit,
    channel_actions_kb_cuts,
    subs_select_kb,
    themes_list_with_cuts_kb,
    confirm_delete_kb,
    banner_select_kb,
    banner_position_kb,
    # GenAIPro TTS
    BTN_ELEVEN_LANG_EN,
    BTN_ELEVEN_LANG_RU,
    # CUTS
    BTN_CHANNEL_SET_CUTS,
    BTN_CHANNEL_SET_CUTS_DUR,
    cuts_kind_kb,
    cuts_collections_kb,
    # Тематика «Нарезки»
    BTN_THEME_CUTS,
    # Reddit фон
    BTN_CHANNEL_SET_BACKGROUND,
    BTN_BG_VIDEO,
    BTN_BG_ANIMATION,
    reddit_background_type_kb,
)

router = Router()

def _is_cuts_theme(name: str | None) -> bool:
    if not name:
        return False
    t = str(name or "").strip().lower()
    return "нарезк" in t or "cuts" in t

# ======================== FSM ========================
class ChannelFSM(StatesGroup):
    listing = State()
    create_name = State()
    selected = State()

    # Тематика (только при создании канала)
    choose_theme = State()

    # Reddit: TTS/сабы
    choose_subs = State()

    # Reddit: Тип фона (видео или анимация)
    choose_background_type = State()

    # GenAIPro TTS настройки
    tts_choose_lang = State()
    tts_enter_voice_id = State()
    tts_enter_speed = State()

    # CUTS
    cuts_choose_kind = State()
    cuts_choose_collection = State()
    cuts_set_duration = State()
    
    # BANNERS (новые состояния)
    banner_select = State()
    banner_position = State()

    # Удаление
    confirm_delete = State()


# ======================== ВХОД В «КАНАЛЫ» ========================
@router.message(F.text == BTN_CHANNELS)
async def channels_entry(message: types.Message, state: FSMContext):
    await state.set_state(ChannelFSM.listing)
    names = [c["name"] for c in await list_channels()]
    await message.answer("📺 Каналы:", reply_markup=channels_list_kb(names))


# ======================== ДОБАВИТЬ КАНАЛ ========================
@router.message(ChannelFSM.listing, F.text == BTN_CHANNEL_ADD)
async def channel_add_start(message: types.Message, state: FSMContext):
    await state.set_state(ChannelFSM.create_name)
    await message.answer("Введи название канала (уникальное):", reply_markup=types.ReplyKeyboardRemove())


@router.message(ChannelFSM.create_name, F.text == BTN_BACK)
async def channel_add_cancel(message: types.Message, state: FSMContext):
    await state.set_state(ChannelFSM.listing)
    names = [c["name"] for c in await list_channels()]
    await message.answer("Отменено. 📺 Каналы:", reply_markup=channels_list_kb(names))


@router.message(ChannelFSM.create_name)
async def channel_add_save(message: types.Message, state: FSMContext):
    name = message.text.strip()
    doc = await create_channel(name)
    await state.update_data(channel_id=doc["_id"], channel_name=doc["name"])

    # ШАГ 2: сразу просим выбрать тематику (только при создании)
    await state.set_state(ChannelFSM.choose_theme)
    themes = [t["name"] for t in await list_themes()]
    await message.answer("Выбери тематику канала:", reply_markup=themes_list_with_cuts_kb(themes))


# ======================== ВЫБОР СУЩЕСТВУЮЩЕГО КАНАЛА ========================
@router.message(ChannelFSM.listing)
async def channel_pick(message: types.Message, state: FSMContext):
    # ВАЖНО: сначала проверяем специальные кнопки
    if message.text == BTN_BACK:
        await state.clear()
        await message.answer("Главное меню:", reply_markup=main_kb())
        return
    
    if message.text == BTN_CHANNEL_ADD:
        # Это уже обрабатывается другим хендлером выше
        return
    
    # Теперь ищем канал
    found = await get_channel(message.text.strip())
    if not found:
        names = [c["name"] for c in await list_channels()]
        await message.answer("Не нашёл такой канал.", reply_markup=channels_list_kb(names))
        return

    await state.update_data(channel_id=found["_id"], channel_name=found["name"])
    await state.set_state(ChannelFSM.selected)

    # Информационная плашка
    theme_name = str(found.get("theme") or "").strip()
    if _is_cuts_theme(theme_name) or found.get("cuts"):
        cuts = found.get("cuts") or {}
        kind = (cuts.get("kind") or "cartoons").lower()
        collection = cuts.get("collection") or "—"
        mn = int(cuts.get("min_sec", 180))
        mx = int(cuts.get("max_sec", 240))
        cnt = count_videos(kind, collection) if collection and collection != "—" else 0
        kind_ru = "Мультики" if kind == "cartoons" else "Фильмы"
        
        # Информация о баннере
        banner_info = ""
        banner_config = found.get("banner")
        if banner_config:
            banner_file = banner_config.get("file", "не установлен")
            banner_pos = banner_config.get("position", "center")
            pos_ru = {"top": "сверху", "center": "по центру", "bottom": "снизу"}.get(banner_pos, banner_pos)
            banner_info = f"\n🖼 Баннер: <b>{banner_file}</b> ({pos_ru})"
        else:
            banner_info = "\n🖼 Баннер: <b>не установлен</b>"
        
        info = (
            f"✅ Выбран канал: <b>{found['name']}</b>\n"
            f"Тематика: <b>✂️ Нарезки</b>\n"
            f"Коллекция: <b>{kind_ru} / {collection}</b>\n"
            f"Серий в коллекции: <b>{cnt}</b>\n"
            f"Длительность: <b>{mn}-{mx} сек.</b>"
            f"{banner_info}"
        )
        await message.answer(info, reply_markup=channel_actions_kb_cuts())
    else:
        info = (
            f"✅ Выбран канал: <b>{found['name']}</b>\n"
            f"Тематика: <b>{theme_name or 'Reddit'}</b>"
        )
        await message.answer(info, reply_markup=channel_actions_kb_reddit())

@router.message(ChannelFSM.selected, F.text == BTN_BACK)
async def selected_back(message: types.Message, state: FSMContext):
    await state.set_state(ChannelFSM.listing)
    names = [c["name"] for c in await list_channels()]
    await message.answer("📺 Каналы:", reply_markup=channels_list_kb(names))


# ======================== ВЫБОР ТЕМАТИКИ (только при создании) ========================
@router.message(ChannelFSM.choose_theme, F.text == BTN_BACK)
async def choose_theme_back(message: types.Message, state: FSMContext):
    # Отмена -> к списку каналов
    await state.set_state(ChannelFSM.listing)
    names = [c["name"] for c in await list_channels()]
    await message.answer("Отменено. 📺 Каналы:", reply_markup=channels_list_kb(names))


@router.message(ChannelFSM.choose_theme)
async def apply_theme(message: types.Message, state: FSMContext):
    data = await state.get_data()
    pick = message.text.strip()
    await set_channel_theme(data["channel_id"], pick)

    await state.set_state(ChannelFSM.selected)
    if pick == BTN_THEME_CUTS or _is_cuts_theme(pick):
        await message.answer(f"✅ Тематика установлена: <b>{pick}</b>", reply_markup=channel_actions_kb_cuts())
    else:
        await message.answer(f"✅ Тематика установлена: <b>{pick}</b>", reply_markup=channel_actions_kb_reddit())


# ======================== БАННЕРЫ ДЛЯ НАРЕЗОК ========================
@router.message(ChannelFSM.selected, F.text == BTN_CHANNEL_SET_BANNER)
async def banner_select_start(message: types.Message, state: FSMContext):
    """Начало выбора баннера для канала"""
    # Получаем список доступных баннеров из БД
    docs = await banners_list(scope="cuts")
    banners = [d["file"] for d in docs]
    
    if not banners:
        await message.answer(
            "❌ Нет доступных баннеров.\n\n"
            "Сначала загрузите баннеры через:\n"
            "Настройки → Баннеры для нарезок",
            reply_markup=channel_actions_kb_cuts()
        )
        return
    
    await state.set_state(ChannelFSM.banner_select)
    await state.update_data(available_banners=banners)
    await message.answer(
        "🖼 Выберите баннер для канала:\n\n"
        "Баннер будет отображаться на всех видео этого канала.",
        reply_markup=banner_select_kb(banners)
    )


@router.message(ChannelFSM.banner_select, F.text == BTN_BACK)
async def banner_select_back(message: types.Message, state: FSMContext):
    """Возврат из выбора баннера"""
    await state.set_state(ChannelFSM.selected)
    await message.answer("Вернулся к действиям канала.", reply_markup=channel_actions_kb_cuts())


@router.message(ChannelFSM.banner_select, F.text == BTN_BANNER_REMOVE)
async def banner_remove(message: types.Message, state: FSMContext):
    """Удаление баннера с канала"""
    data = await state.get_data()
    channel_id = data.get("channel_id")
    
    # Убираем баннер
    await set_channel_banner(channel_id, None)
    
    await state.set_state(ChannelFSM.selected)
    await message.answer(
        "✅ Баннер удален с канала.\n"
        "Видео будут генерироваться без баннера.",
        reply_markup=channel_actions_kb_cuts()
    )


@router.message(ChannelFSM.banner_select)
async def banner_pick(message: types.Message, state: FSMContext):
    """Выбор конкретного баннера"""
    data = await state.get_data()
    banners = data.get("available_banners", [])
    
    selected_file = message.text.strip()
    if selected_file not in banners:
        await message.answer(
            "❌ Выберите баннер из списка ниже:",
            reply_markup=banner_select_kb(banners)
        )
        return
    
    await state.update_data(selected_banner=selected_file)
    await state.set_state(ChannelFSM.banner_position)
    await message.answer(
        f"🖼 Выбран баннер: <b>{selected_file}</b>\n\n"
        "Теперь выберите позицию баннера на видео:",
        reply_markup=banner_position_kb()
    )


@router.message(ChannelFSM.banner_position, F.text == BTN_BACK)
async def banner_position_back(message: types.Message, state: FSMContext):
    """Возврат из выбора позиции"""
    data = await state.get_data()
    banners = data.get("available_banners", [])
    await state.set_state(ChannelFSM.banner_select)
    await message.answer(
        "Вернулся к выбору баннера:",
        reply_markup=banner_select_kb(banners)
    )


@router.message(ChannelFSM.banner_position, F.text.in_({BTN_BANNER_POS_TOP, BTN_BANNER_POS_CENTER, BTN_BANNER_POS_BOTTOM}))
async def banner_position_apply(message: types.Message, state: FSMContext):
    """Применение баннера с выбранной позицией"""
    data = await state.get_data()
    channel_id = data.get("channel_id")
    banner_file = data.get("selected_banner")
    
    # Определяем позицию
    position_map = {
        BTN_BANNER_POS_TOP: "top",
        BTN_BANNER_POS_CENTER: "center", 
        BTN_BANNER_POS_BOTTOM: "bottom"
    }
    position = position_map.get(message.text, "center")
    position_ru = {
        "top": "сверху",
        "center": "по центру",
        "bottom": "снизу"
    }.get(position, position)
    
    # Сохраняем баннер
    await set_channel_banner(channel_id, banner_file, position)
    
    await state.set_state(ChannelFSM.selected)
    await message.answer(
        f"✅ Баннер установлен!\n\n"
        f"📄 Файл: <b>{banner_file}</b>\n"
        f"📍 Позиция: <b>{position_ru}</b>\n\n"
        f"Теперь все видео этого канала будут генерироваться с этим баннером.",
        reply_markup=channel_actions_kb_cuts()
    )


# ======================== REDDIT: ОЗВУЧКА / САБЫ ========================
@router.message(ChannelFSM.selected, F.text == BTN_CHANNEL_SET_TTS)
async def tts_setup_start(message: types.Message, state: FSMContext):
    """Начало настройки TTS - выбор языка"""
    await state.set_state(ChannelFSM.tts_choose_lang)
    await message.answer(
        "🎙 <b>Настройка озвучки (GenAIPro)</b>\n\n"
        "Выберите язык голоса:",
        reply_markup=types.ReplyKeyboardMarkup(
            keyboard=[
                [types.KeyboardButton(text=BTN_ELEVEN_LANG_EN), types.KeyboardButton(text=BTN_ELEVEN_LANG_RU)],
                [types.KeyboardButton(text=BTN_BACK)]
            ],
            resize_keyboard=True
        )
    )


@router.message(ChannelFSM.tts_choose_lang, F.text == BTN_BACK)
async def tts_lang_back(message: types.Message, state: FSMContext):
    await state.set_state(ChannelFSM.selected)
    await message.answer("Вернулся к действиям канала.", reply_markup=channel_actions_kb_reddit())


@router.message(ChannelFSM.tts_choose_lang, F.text.in_({BTN_ELEVEN_LANG_EN, BTN_ELEVEN_LANG_RU}))
async def tts_lang_pick(message: types.Message, state: FSMContext):
    """Выбор языка и переход к вводу voice_id"""
    lang = "en" if message.text == BTN_ELEVEN_LANG_EN else "ru"
    await state.update_data(tts_lang=lang)
    await state.set_state(ChannelFSM.tts_enter_voice_id)

    await message.answer(
        f"✅ Язык: <b>{lang}</b>\n\n"
        "Теперь введите <b>voice_id</b> голоса ElevenLabs.\n\n"
        "Примеры voice_id:\n"
        "• <code>uju3wxzG5OhpWcoi3SMy</code> (Sarah - EN)\n"
        "• <code>21m00Tcm4TlvDq8ikWAM</code> (Rachel - EN)\n"
        "• <code>Xb7hH8MSUJpSbSDYk0k2</code> (Antoni - multilang)\n\n"
        "📌 Найти voice_id можно на:\n"
        "https://elevenlabs.io/voice-library",
        reply_markup=types.ReplyKeyboardMarkup(
            keyboard=[[types.KeyboardButton(text=BTN_BACK)]],
            resize_keyboard=True
        )
    )


@router.message(ChannelFSM.tts_enter_voice_id, F.text == BTN_BACK)
async def tts_voice_id_back(message: types.Message, state: FSMContext):
    await state.set_state(ChannelFSM.tts_choose_lang)
    await message.answer(
        "Выберите язык голоса:",
        reply_markup=types.ReplyKeyboardMarkup(
            keyboard=[
                [types.KeyboardButton(text=BTN_ELEVEN_LANG_EN), types.KeyboardButton(text=BTN_ELEVEN_LANG_RU)],
                [types.KeyboardButton(text=BTN_BACK)]
            ],
            resize_keyboard=True
        )
    )


@router.message(ChannelFSM.tts_enter_voice_id, F.text)
async def tts_save_voice_id(message: types.Message, state: FSMContext):
    """Сохранение voice_id и переход к выбору скорости"""
    voice_id = message.text.strip()

    # Валидация voice_id
    if len(voice_id) < 10 or len(voice_id) > 30:
        await message.answer(
            "❌ Неверный формат voice_id.\n"
            "Voice ID должен быть 10-30 символов.\n\n"
            "Пример: <code>uju3wxzG5OhpWcoi3SMy</code>"
        )
        return

    if not voice_id.isalnum():
        await message.answer(
            "❌ Voice ID должен содержать только буквы и цифры.\n\n"
            "Пример: <code>uju3wxzG5OhpWcoi3SMy</code>"
        )
        return

    await state.update_data(tts_voice_id=voice_id)
    await state.set_state(ChannelFSM.tts_enter_speed)

    await message.answer(
        f"✅ Voice ID: <code>{voice_id}</code>\n\n"
        "Теперь выберите <b>скорость речи</b>:\n\n"
        "• <code>0.9</code> - медленнее\n"
        "• <code>1.0</code> - нормальная\n"
        "• <code>1.1</code> - чуть быстрее (рекомендуется)\n"
        "• <code>1.2</code> - быстрая\n\n"
        "Введите число от 0.7 до 1.2:",
        reply_markup=types.ReplyKeyboardMarkup(
            keyboard=[
                [types.KeyboardButton(text="1.0"), types.KeyboardButton(text="1.1"), types.KeyboardButton(text="1.2")],
                [types.KeyboardButton(text=BTN_BACK)]
            ],
            resize_keyboard=True
        )
    )


@router.message(ChannelFSM.tts_enter_speed, F.text == BTN_BACK)
async def tts_speed_back(message: types.Message, state: FSMContext):
    await state.set_state(ChannelFSM.tts_enter_voice_id)
    await message.answer(
        "Введите voice_id голоса:",
        reply_markup=types.ReplyKeyboardMarkup(
            keyboard=[[types.KeyboardButton(text=BTN_BACK)]],
            resize_keyboard=True
        )
    )


@router.message(ChannelFSM.tts_enter_speed, F.text)
async def tts_save_all(message: types.Message, state: FSMContext):
    """Сохранение всех настроек TTS"""
    try:
        speed = float(message.text.strip())
        if speed < 0.7 or speed > 1.2:
            raise ValueError("Out of range")
    except ValueError:
        await message.answer(
            "❌ Неверное значение скорости.\n"
            "Введите число от 0.7 до 1.2\n\n"
            "Примеры: 1.0, 1.1, 1.2"
        )
        return

    data = await state.get_data()
    channel_id = data["channel_id"]
    lang = data.get("tts_lang", "en")
    voice_id = data.get("tts_voice_id")

    # Сохраняем все настройки
    await set_channel_tts_lang(channel_id, lang)
    await set_channel_tts_voice(channel_id, voice_id)
    await set_channel_tts_speed(channel_id, speed)

    await state.set_state(ChannelFSM.selected)
    await message.answer(
        f"✅ <b>Озвучка настроена!</b>\n\n"
        f"🌍 Язык: <b>{lang}</b>\n"
        f"🔑 Voice ID: <code>{voice_id}</code>\n"
        f"⚡ Скорость: <b>{speed}x</b>\n\n"
        f"Теперь все видео этого канала будут озвучиваться этим голосом.",
        reply_markup=channel_actions_kb_reddit()
    )


@router.message(ChannelFSM.selected, F.text == BTN_CHANNEL_SET_SUBS)
async def subs_start(message: types.Message, state: FSMContext):
    await state.set_state(ChannelFSM.choose_subs)
    await message.answer("Выбери режим субтитров:", reply_markup=subs_select_kb())


@router.message(ChannelFSM.choose_subs, F.text == BTN_BACK)
async def subs_back(message: types.Message, state: FSMContext):
    await state.set_state(ChannelFSM.selected)
    await message.answer("Вернулся к действиям канала.", reply_markup=channel_actions_kb_reddit())


@router.message(ChannelFSM.choose_subs, F.text.in_({BTN_SUBS_OFF, BTN_SUBS_EN, BTN_SUBS_RU}))
async def subs_apply(message: types.Message, state: FSMContext):
    # TODO: при необходимости — сохранить настройку субтитров в БД
    await state.set_state(ChannelFSM.selected)
    await message.answer(f"✅ Субтитры: {message.text}", reply_markup=channel_actions_kb_reddit())


# ======================== CUTS (НАРЕЗКИ) ========================
@router.message(ChannelFSM.selected, F.text == BTN_CHANNEL_SET_CUTS)
async def cuts_assign_start(message: types.Message, state: FSMContext):
    await state.set_state(ChannelFSM.cuts_choose_kind)
    await message.answer("Режим «Нарезки»: выбери тип:", reply_markup=cuts_kind_kb())


@router.message(ChannelFSM.cuts_choose_kind, F.text == BTN_BACK)
async def cuts_assign_back1(message: types.Message, state: FSMContext):
    await state.set_state(ChannelFSM.selected)
    await message.answer("Вернулся к действиям канала.", reply_markup=channel_actions_kb_cuts())


@router.message(ChannelFSM.cuts_choose_kind)
async def cuts_assign_pick_kind(message: types.Message, state: FSMContext):
    txt = message.text.strip().lower()
    if txt not in {"🎨 мультики", "🎞 фильмы"}:
        await message.answer("Выбери тип:", reply_markup=cuts_kind_kb())
        return
    kind = "cartoons" if txt == "🎨 мультики" else "films"
    await state.update_data(cuts_kind=kind)

    cols = list_collections(kind)
    await state.set_state(ChannelFSM.cuts_choose_collection)
    await message.answer("Выбери коллекцию:", reply_markup=cuts_collections_kb(cols, show_create=False))


@router.message(ChannelFSM.cuts_choose_collection, F.text == BTN_BACK)
async def cuts_assign_back2(message: types.Message, state: FSMContext):
    await state.set_state(ChannelFSM.cuts_choose_kind)
    await message.answer("Выбери тип:", reply_markup=cuts_kind_kb())


@router.message(ChannelFSM.cuts_choose_collection)
async def cuts_assign_apply(message: types.Message, state: FSMContext):
    data = await state.get_data()
    kind = data.get("cuts_kind", "cartoons")
    collection = message.text.strip()

    await set_channel_cuts(data["channel_id"], kind, collection)
    await state.set_state(ChannelFSM.selected)
    cnt = count_videos(kind, collection)
    kind_ru = "Мультики" if kind == "cartoons" else "Фильмы"
    await message.answer(
        f"✅ Канал привязан к коллекции: <b>{kind_ru} / {collection}</b>\n"
        f"Серий в коллекции: <b>{cnt}</b>",
        reply_markup=channel_actions_kb_cuts()
    )


@router.message(ChannelFSM.selected, F.text == BTN_CHANNEL_SET_CUTS_DUR)
async def cuts_dur_start(message: types.Message, state: FSMContext):
    await state.set_state(ChannelFSM.cuts_set_duration)
    await message.answer("Введи длительность через дефис в секундах, например: 180-240", reply_markup=types.ReplyKeyboardRemove())


@router.message(ChannelFSM.cuts_set_duration, F.text == BTN_BACK)
async def cuts_dur_back(message: types.Message, state: FSMContext):
    await state.set_state(ChannelFSM.selected)
    await message.answer("Вернулся к действиям канала.", reply_markup=channel_actions_kb_cuts())


@router.message(ChannelFSM.cuts_set_duration)
async def cuts_dur_apply(message: types.Message, state: FSMContext):
    txt = message.text.strip()
    try:
        a, b = txt.split("-", 1)
        mn, mx = int(a), int(b)
        if mn < 30 or mx < mn:
            raise ValueError
    except Exception:
        await message.answer("Неверный формат. Пример: 180-240")
        return

    data = await state.get_data()
    await set_channel_cuts_duration(data["channel_id"], mn, mx)

    await state.set_state(ChannelFSM.selected)
    await message.answer(f"✅ Длительность нарезки установлена: {mn}-{mx} сек.", reply_markup=channel_actions_kb_cuts())


# ======================== УДАЛЕНИЕ КАНАЛА ========================
@router.message(ChannelFSM.selected, F.text == BTN_CHANNEL_DELETE)
async def delete_start(message: types.Message, state: FSMContext):
    await state.set_state(ChannelFSM.confirm_delete)
    await message.answer("Точно удалить канал?", reply_markup=confirm_delete_kb())


@router.message(ChannelFSM.confirm_delete, F.text == BTN_BACK)
async def delete_cancel(message: types.Message, state: FSMContext):
    await state.set_state(ChannelFSM.selected)
    await message.answer("Удаление отменено.", reply_markup=channel_actions_kb_cuts())


@router.message(ChannelFSM.confirm_delete, F.text == BTN_YES)
async def delete_confirm(message: types.Message, state: FSMContext):
    data = await state.get_data()
    channel_id = data.get("channel_id")
    name = data.get("channel_name", "")
    if channel_id:
        await delete_channel(channel_id)
    await state.set_state(ChannelFSM.listing)
    names = [c["name"] for c in await list_channels()]
    await message.answer(f"🗑 Канал <b>{name}</b> удалён.", reply_markup=channels_list_kb(names))


@router.message(ChannelFSM.confirm_delete, F.text == BTN_NO)
async def delete_no(message: types.Message, state: FSMContext):
    await state.set_state(ChannelFSM.selected)
    await message.answer("Удаление отменено.", reply_markup=channel_actions_kb_cuts())


# ======================== ТИП ФОНА (REDDIT) ========================
@router.message(ChannelFSM.selected, F.text == BTN_CHANNEL_SET_BACKGROUND)
async def background_type_start(message: types.Message, state: FSMContext):
    """Начало выбора типа фона для Reddit"""
    await state.set_state(ChannelFSM.choose_background_type)
    await message.answer(
        "🎨 Выберите тип фона для Reddit видео:\n\n"
        "🎞 <b>Залипательное видео</b> - использовать MP4 видео из библиотеки\n"
        "⭕ <b>Анимация (круг)</b> - создавать анимацию с прыгающим шариком",
        reply_markup=reddit_background_type_kb(),
        parse_mode="HTML"
    )


@router.message(ChannelFSM.choose_background_type, F.text == BTN_BACK)
async def background_type_back(message: types.Message, state: FSMContext):
    await state.set_state(ChannelFSM.selected)
    await message.answer("Вернулся к действиям канала.", reply_markup=channel_actions_kb_reddit())


@router.message(ChannelFSM.choose_background_type, F.text.in_({BTN_BG_VIDEO, BTN_BG_ANIMATION}))
async def background_type_apply(message: types.Message, state: FSMContext):
    """Применение выбора типа фона"""
    bg_type = "video" if message.text == BTN_BG_VIDEO else "animation"
    bg_name = "Залипательное видео" if bg_type == "video" else "Анимация (круг)"

    data = await state.get_data()
    await set_channel_background_type(data["channel_id"], bg_type)

    await state.set_state(ChannelFSM.selected)
    await message.answer(
        f"✅ Тип фона установлен: <b>{bg_name}</b>\n\n"
        f"Теперь все Reddit видео этого канала будут использовать этот тип фона.",
        reply_markup=channel_actions_kb_reddit(),
        parse_mode="HTML"
    )