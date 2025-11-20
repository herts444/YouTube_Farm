from aiogram import Router, types
from aiogram.filters import CommandStart
from utils.keyboards import main_kb

router = Router()

@router.message(CommandStart())
async def on_start(message: types.Message):
    await message.answer(
        "👋 Привет! Это бот для авто-создания и подготовки Shorts.\nВыбери раздел:",
        reply_markup=main_kb()
    )
