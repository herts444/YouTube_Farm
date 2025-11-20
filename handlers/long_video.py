"""
Handler for long video generation (historical videos)
"""
from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from utils import keyboards as kb
from utils.historical import HistoricalVideoGenerator
import logging

logger = logging.getLogger(__name__)

router = Router()


class LongVideoFSM(StatesGroup):
    """FSM states for long video generation"""
    selecting_language = State()
    selecting_duration = State()
    viewing_topics = State()
    entering_custom_topic = State()
    confirming = State()
    generating = State()


@router.message(F.text == kb.BTN_CREATE_LONG)
async def start_long_video(message: Message, state: FSMContext):
    """Start long video creation"""
    await message.answer(
        "📽️ <b>Создание длинного видео</b>\n\n"
        "Выберите язык озвучки и текста:",
        reply_markup=kb.long_video_language_kb(),
        parse_mode="HTML"
    )
    await state.set_state(LongVideoFSM.selecting_language)


@router.message(LongVideoFSM.selecting_language, F.text.in_([
    kb.BTN_LONG_LANG_RU,
    kb.BTN_LONG_LANG_EN,
    kb.BTN_LONG_LANG_UA
]))
async def language_selected(message: Message, state: FSMContext):
    """Language selection handler"""
    lang_map = {
        kb.BTN_LONG_LANG_RU: ('russian', '🇷🇺 Русский'),
        kb.BTN_LONG_LANG_EN: ('english', '🇬🇧 English'),
        kb.BTN_LONG_LANG_UA: ('ukrainian', '🇺🇦 Українська')
    }

    lang_code, lang_name = lang_map[message.text]
    await state.update_data(language=lang_code, language_name=lang_name)

    await message.answer(
        f"✅ Выбран язык: {lang_name}\n\n"
        "⏱ Теперь выберите длительность видео:",
        reply_markup=kb.long_video_duration_kb()
    )
    await state.set_state(LongVideoFSM.selecting_duration)


@router.message(LongVideoFSM.selecting_duration, F.text.startswith("⏱"))
async def duration_selected(message: Message, state: FSMContext):
    """Duration selection handler"""
    # Parse duration from text: "⏱ 10 минут" -> 10
    duration_text = message.text.split()[1]
    duration_minutes = int(duration_text)
    duration_seconds = duration_minutes * 60

    # Calculate number of scenes (20 seconds per scene average)
    num_scenes = duration_seconds // 20

    await state.update_data(
        duration_minutes=duration_minutes,
        duration_seconds=duration_seconds,
        num_scenes=num_scenes
    )

    data = await state.get_data()
    language = data['language']

    # Generate topic suggestions
    await message.answer(
        "💡 Генерирую идеи для видео...\n\n"
        "⏳ Пожалуйста, подождите...",
        reply_markup=ReplyKeyboardRemove()
    )

    try:
        generator = HistoricalVideoGenerator()
        topics = generator.generate_topic_suggestions(
            num_suggestions=4,
            language=language
        )

        await state.update_data(suggested_topics=topics)

        await message.answer(
            f"✅ Длительность: {duration_minutes} минут\n\n"
            "💡 <b>Выберите тему или введите свою:</b>",
            reply_markup=kb.long_video_topics_kb(topics),
            parse_mode="HTML"
        )
        await state.set_state(LongVideoFSM.viewing_topics)

    except Exception as e:
        logger.error(f"Error generating topics: {e}")
        await message.answer(
            f"❌ Ошибка при генерации идей:\n{str(e)[:200]}\n\n"
            "Введите тему вручную:",
            reply_markup=kb.main_kb()
        )
        await state.clear()


@router.message(LongVideoFSM.viewing_topics, F.text == "✍️ Своя тема")
async def enter_custom_topic(message: Message, state: FSMContext):
    """User wants to enter custom topic"""
    data = await state.get_data()
    lang_name = data['language_name']

    await message.answer(
        f"✍️ <b>Введите тему для видео</b>\n\n"
        f"Язык: {lang_name}\n\n"
        "Примеры тем:\n"
        "• Как Наполеон сжег Москву\n"
        "• Полет Гагарина в космос\n"
        "• Падение Берлинской стены\n\n"
        "Напишите тему следующим сообщением:",
        reply_markup=kb.main_kb(),
        parse_mode="HTML"
    )
    await state.set_state(LongVideoFSM.entering_custom_topic)


@router.message(LongVideoFSM.entering_custom_topic)
async def custom_topic_entered(message: Message, state: FSMContext):
    """Handle custom topic input"""
    if message.text == kb.BTN_BACK:
        await start_long_video(message, state)
        return

    topic = message.text.strip()

    if len(topic) < 10:
        await message.answer(
            "❌ Тема слишком короткая. Введите более подробную тему (минимум 10 символов):"
        )
        return

    await state.update_data(topic=topic)
    await show_confirmation(message, state)


@router.message(LongVideoFSM.viewing_topics, F.text.startswith(("1.", "2.", "3.", "4.")))
async def topic_number_selected(message: Message, state: FSMContext):
    """Topic selected by number"""
    data = await state.get_data()
    suggested_topics = data.get('suggested_topics', [])

    # Parse topic number: "1. Topic text" -> 0
    topic_num = int(message.text[0]) - 1

    if topic_num < len(suggested_topics):
        topic = suggested_topics[topic_num]
        await state.update_data(topic=topic)
        await show_confirmation(message, state)
    else:
        await message.answer("❌ Неверный номер темы. Попробуйте еще раз.")


async def show_confirmation(message: Message, state: FSMContext):
    """Show confirmation screen"""
    data = await state.get_data()

    topic = data['topic']
    lang_name = data['language_name']
    duration_minutes = data['duration_minutes']
    num_scenes = data['num_scenes']

    await message.answer(
        "📝 <b>Подтверждение генерации</b>\n\n"
        f"🎬 Тема: {topic}\n"
        f"🗣 Язык: {lang_name}\n"
        f"⏱ Длительность: {duration_minutes} минут\n"
        f"🎞 Сцен: {num_scenes}\n\n"
        "⚠️ <b>Внимание:</b> Генерация займет 5-15 минут\n\n"
        "Начать генерацию?",
        reply_markup=kb.long_video_confirm_kb(),
        parse_mode="HTML"
    )
    await state.set_state(LongVideoFSM.confirming)


@router.message(LongVideoFSM.confirming, F.text == "✅ Начать генерацию")
async def start_generation(message: Message, state: FSMContext):
    """Start video generation"""
    data = await state.get_data()

    topic = data['topic']
    language = data['language']
    duration_seconds = data['duration_seconds']
    num_scenes = data['num_scenes']

    progress_msg = await message.answer(
        "🎬 <b>Генерация видео началась</b>\n\n"
        "⏳ Этап 1/4: Генерация сценария...\n\n"
        "Это может занять несколько минут. Пожалуйста, подождите...",
        reply_markup=ReplyKeyboardRemove(),
        parse_mode="HTML"
    )

    await state.set_state(LongVideoFSM.generating)

    try:
        generator = HistoricalVideoGenerator()

        # Update progress - Story generation
        await progress_msg.edit_text(
            "🎬 <b>Генерация видео</b>\n\n"
            "✅ Этап 1/4: Сценарий создан\n"
            "⏳ Этап 2/4: Генерация аудио...",
            parse_mode="HTML"
        )

        result = await generator.generate_video(
            topic=topic,
            language=language,
            duration_seconds=duration_seconds,
            num_scenes=num_scenes,
            voice_gender='male',
            image_width=1024,
            image_height=576,
            num_inference_steps=4
        )

        # Send video
        with open(result['video_path'], 'rb') as video_file:
            await message.answer_document(
                document=video_file,
                caption=(
                    f"✅ <b>Ваше видео готово!</b>\n\n"
                    f"📝 Тема: {topic}\n"
                    f"⏱ Длительность: {data['duration_minutes']} минут\n"
                    f"🎞 Сцен: {num_scenes}"
                ),
                parse_mode="HTML"
            )

        await progress_msg.delete()

        await message.answer(
            "🎉 Генерация завершена!\n\n"
            "Выберите действие:",
            reply_markup=kb.main_kb()
        )

        await state.clear()

    except Exception as e:
        logger.error(f"Error generating video: {e}")
        import traceback
        traceback.print_exc()

        error_text = str(e)[:300]

        await progress_msg.edit_text(
            f"❌ <b>Ошибка при генерации:</b>\n\n"
            f"<code>{error_text}</code>\n\n"
            "Попробуйте еще раз или выберите другую тему.",
            parse_mode="HTML"
        )

        await message.answer(
            "Вернуться в главное меню:",
            reply_markup=kb.main_kb()
        )

        await state.clear()


@router.message(F.text == kb.BTN_BACK)
async def back_handler(message: Message, state: FSMContext):
    """Back button handler for all states"""
    current_state = await state.get_state()

    if current_state == LongVideoFSM.selecting_language.state:
        await message.answer(
            "Вернулись в главное меню",
            reply_markup=kb.main_kb()
        )
        await state.clear()

    elif current_state == LongVideoFSM.selecting_duration.state:
        await start_long_video(message, state)

    elif current_state in [
        LongVideoFSM.viewing_topics.state,
        LongVideoFSM.entering_custom_topic.state
    ]:
        # Go back to duration selection
        await message.answer(
            "⏱ Выберите длительность видео:",
            reply_markup=kb.long_video_duration_kb()
        )
        await state.set_state(LongVideoFSM.selecting_duration)

    elif current_state == LongVideoFSM.confirming.state:
        # Go back to topic selection
        data = await state.get_data()
        topics = data.get('suggested_topics', [])

        await message.answer(
            "💡 Выберите тему или введите свою:",
            reply_markup=kb.long_video_topics_kb(topics)
        )
        await state.set_state(LongVideoFSM.viewing_topics)
