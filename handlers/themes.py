# handlers/themes.py
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext

from db.database import list_themes
from utils.keyboards import BTN_THEMES, BTN_BACK, main_kb

router = Router()

@router.message(F.text == BTN_THEMES)
async def themes_entry(message: types.Message, state: FSMContext):
    """
    Раздел «Тематики». Теперь он только информирует:
    - список доступных тематик из БД
    - напоминание, что выбор тематики делается в настройках канала
    """
    themes = await list_themes()
    names = [t.get("name", "—") for t in themes] if themes else []

    if names:
        listing = "\n".join(f"• {n}" for n in names)
    else:
        listing = "— пока нет пользовательских тематик —"

    text = (
        "🎭 <b>Тематики</b>\n\n"
        "Теперь тематика выбирается <b>в настройках конкретного канала</b> "
        "(после создания канала сразу появляется выбор тематики).\n\n"
        "Доступные тематики из БД:\n"
        f"{listing}\n\n"
        "Также доступна виртуальная тематика: <b>✂️ Нарезки</b>."
    )

    await message.answer(text, reply_markup=main_kb())

@router.message(F.text == BTN_BACK)
async def themes_back(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Главное меню:", reply_markup=main_kb())
