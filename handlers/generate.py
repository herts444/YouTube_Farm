# bot/handlers/generate.py
import os
import shutil
from aiogram import Router, F, types
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from utils.keyboards import (
    BTN_CREATE_SHORT, BTN_BACK, main_kb, channels_list_kb
)
from db.database import list_channels, db
from utils.generation import generate_short
from utils.ffmpeg import ensure_telegram_size

router = Router()

class GenFSM(StatesGroup):
    choose_channel = State()

@router.message(F.text == BTN_CREATE_SHORT)
async def gen_entry(message: types.Message, state: FSMContext):
    channels = await list_channels()
    if not channels:
        await message.answer("Сначала создай канал в разделе 📺 Каналы.", reply_markup=main_kb())
        return
    names = [c["name"] for c in channels]
    await state.set_state(GenFSM.choose_channel)
    await message.answer("Выбери канал для генерации:", reply_markup=channels_list_kb(names))

@router.message(GenFSM.choose_channel, F.text == BTN_BACK)
async def gen_back_to_main(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Главное меню:", reply_markup=main_kb())

@router.message(GenFSM.choose_channel, F.text)
async def gen_pick_channel_and_generate(message: types.Message, state: FSMContext):
    name = message.text.strip()
    ch = await db().channels.find_one({"name": name})
    if not ch:
        names = [c["name"] for c in await list_channels()]
        await message.answer("Не найден канал с таким именем.", reply_markup=channels_list_kb(names))
        return

    channel_id = str(ch["_id"])
    workdir = os.path.join("./out", channel_id)
    os.makedirs(workdir, exist_ok=True)

    # Сообщение о старте генерации
    await message.answer("🚀 Генерация запущена! Это может занять немного времени…")

    try:
        result = await generate_short(channel_id, out_dir=workdir)
    except Exception as e:
        await message.answer(f"⚠️ Ошибка генерации: {e}", reply_markup=main_kb())
        try:
            shutil.rmtree(workdir, ignore_errors=True)
        except Exception:
            pass
        return

    final_path = result["video_path"]
    target_path = os.path.join(workdir, os.path.basename(final_path).replace(".mp4", "_tg.mp4"))
    safe_path = await ensure_telegram_size(final_path, target_path, target_mb=48)

    # Отправляем видео БЕЗ подписи, но сразу с клавиатурой главного меню
    await message.answer_video(types.FSInputFile(safe_path), reply_markup=main_kb())

    # Полная очистка out/<channel_id>
    try:
        shutil.rmtree(workdir, ignore_errors=True)
    except Exception:
        pass

    await state.clear()
