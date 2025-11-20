# handlers/statistics.py
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from db.database import list_channels
from utils.keyboards import BTN_STATISTICS, main_kb

router = Router()

@router.message(F.text == BTN_STATISTICS)
async def stats_entry(message: types.Message, state: FSMContext):
    """
    Показываем по каждому каналу: сколько шортов уже сгенерировано.
    Поле 'generated_total' инкрементится в utils/generation.py после успешной сборки.
    """
    # Сбрасываем любое состояние FSM при входе в статистику
    await state.clear()
    
    channels = await list_channels()
    
    if not channels:
        await message.answer(
            "📊 <b>Статистика</b>\n\n"
            "Пока нет созданных каналов.\n"
            "Создайте канал в разделе 📺 Каналы",
            reply_markup=main_kb()
        )
        return

    lines = []
    total = 0
    
    for ch in channels:
        name = ch.get("name", "—")
        cnt = int(ch.get("generated_total", 0) or 0)
        total += cnt
        
        # Добавляем эмодзи в зависимости от количества
        if cnt == 0:
            emoji = "⚪"
        elif cnt < 5:
            emoji = "🟡"
        elif cnt < 10:
            emoji = "🟢"
        else:
            emoji = "🔥"
            
        lines.append(f"{emoji} <b>{name}</b> — {cnt} видео")

    # Формируем красивый вывод
    if lines:
        channels_text = "\n".join(lines)
    else:
        channels_text = "Каналы пока не создавали видео"
    
    # Добавляем общую статистику
    txt = (
        f"📊 <b>Статистика генераций</b>\n\n"
        f"<b>По каналам:</b>\n{channels_text}\n\n"
        f"━━━━━━━━━━━━━━━\n"
        f"📹 <b>Всего создано видео:</b> {total}\n"
        f"📺 <b>Активных каналов:</b> {len(channels)}"
    )
    
    # Добавляем подсказку если нет генераций
    if total == 0:
        txt += (
            "\n\n💡 <i>Подсказка: создайте канал и нажмите"
            " «🎬 Создать шорт» для генерации первого видео</i>"
        )
    
    await message.answer(txt, reply_markup=main_kb())