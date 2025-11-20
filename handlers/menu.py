from aiogram import Router, F, types
from aiogram.filters import StateFilter
from utils.keyboards import (
    BTN_BACK, main_kb
)
from db.database import list_themes, list_channels

router = Router()

# Глобальный "Назад" теперь срабатывает только когда НЕТ активного состояния FSM.
@router.message(StateFilter(None), F.text == BTN_BACK)
async def go_back(message: types.Message):
    await message.answer("Главное меню:", reply_markup=main_kb())

