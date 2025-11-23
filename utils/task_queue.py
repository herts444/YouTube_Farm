"""
Система очереди задач для фоновой генерации видео
"""
import asyncio
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum


class TaskStatus(Enum):
    """Статусы задачи"""
    PENDING = "pending"      # Ожидает выполнения
    RUNNING = "running"      # Выполняется
    COMPLETED = "completed"  # Завершена
    FAILED = "failed"        # Ошибка


@dataclass
class VideoTask:
    """Задача на генерацию видео"""
    task_id: str
    user_id: int
    task_type: str  # "reddit", "educational", "cuts"
    config: Dict[str, Any]
    status: TaskStatus = TaskStatus.PENDING
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class TaskQueue:
    """Очередь задач на генерацию видео"""

    def __init__(self):
        self.queue: asyncio.Queue[VideoTask] = asyncio.Queue()
        self.tasks: Dict[str, VideoTask] = {}  # task_id -> VideoTask
        self.user_tasks: Dict[int, List[str]] = {}  # user_id -> [task_ids]
        self._task_counter = 0
        self._worker_running = False

    def generate_task_id(self) -> str:
        """Генерирует уникальный ID задачи"""
        self._task_counter += 1
        return f"task_{int(time.time())}_{self._task_counter}"

    async def add_task(self, user_id: int, task_type: str, config: Dict[str, Any]) -> VideoTask:
        """Добавляет задачу в очередь"""
        task_id = self.generate_task_id()
        task = VideoTask(
            task_id=task_id,
            user_id=user_id,
            task_type=task_type,
            config=config
        )

        # Сохраняем задачу
        self.tasks[task_id] = task

        # Добавляем в список задач пользователя
        if user_id not in self.user_tasks:
            self.user_tasks[user_id] = []
        self.user_tasks[user_id].append(task_id)

        # Добавляем в очередь
        await self.queue.put(task)

        return task

    def get_task(self, task_id: str) -> Optional[VideoTask]:
        """Получает задачу по ID"""
        return self.tasks.get(task_id)

    def get_user_tasks(self, user_id: int, status: Optional[TaskStatus] = None) -> List[VideoTask]:
        """Получает все задачи пользователя"""
        task_ids = self.user_tasks.get(user_id, [])
        tasks = [self.tasks[tid] for tid in task_ids if tid in self.tasks]

        if status:
            tasks = [t for t in tasks if t.status == status]

        return sorted(tasks, key=lambda t: t.created_at, reverse=True)

    def get_queue_position(self, task_id: str) -> Optional[int]:
        """Возвращает позицию задачи в очереди (1-based)"""
        task = self.tasks.get(task_id)
        if not task or task.status != TaskStatus.PENDING:
            return None

        # Считаем позицию в очереди
        position = 1
        for tid, t in self.tasks.items():
            if t.status == TaskStatus.PENDING and t.created_at < task.created_at:
                position += 1

        return position

    def get_stats(self) -> Dict[str, int]:
        """Статистика очереди"""
        stats = {
            "pending": 0,
            "running": 0,
            "completed": 0,
            "failed": 0,
            "total": len(self.tasks)
        }

        for task in self.tasks.values():
            stats[task.status.value] += 1

        return stats

    async def start_worker(self, bot, generator_func):
        """Запускает фоновый worker для обработки задач"""
        if self._worker_running:
            return

        self._worker_running = True
        print("[TaskQueue] Worker started")

        while self._worker_running:
            try:
                # Получаем задачу из очереди
                task = await self.queue.get()

                # Обновляем статус
                task.status = TaskStatus.RUNNING
                task.started_at = time.time()

                # Уведомляем пользователя о начале
                try:
                    type_emoji = {
                        "reddit": "📱",
                        "educational": "🧠",
                        "cuts": "✂️",
                        "horror": "😱",
                        "facts": "💡",
                        "history": "📜",
                        "news": "📰"
                    }.get(task.task_type, "🎬")
                    await bot.send_message(
                        task.user_id,
                        f"{type_emoji} <b>Начата генерация видео</b>\n\n"
                        f"ID задачи: <code>{task.task_id}</code>\n"
                        f"⏳ Это займёт 1-2 минуты..."
                    )
                except Exception as e:
                    print(f"[TaskQueue] Failed to send start notification: {e}")

                # Выполняем генерацию
                try:
                    result = await generator_func(task)
                    task.status = TaskStatus.COMPLETED
                    task.result = result
                    task.completed_at = time.time()

                    # Уведомляем пользователя об успехе
                    try:
                        from aiogram.types import FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton

                        buttons = [
                            [InlineKeyboardButton(text="🎬 Создать ещё", callback_data="menu:create")],
                            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="menu:main")],
                        ]

                        # Отправляем видео
                        video_path = result.get("video_path")
                        caption = result.get("caption", f"✅ Видео готово!\nID: {task.task_id}")

                        if video_path:
                            await bot.send_video(
                                task.user_id,
                                FSInputFile(video_path),
                                caption=caption,
                                reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
                            )
                        else:
                            await bot.send_message(
                                task.user_id,
                                caption,
                                reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
                            )
                    except Exception as e:
                        print(f"[TaskQueue] Failed to send result: {e}")
                        # Отправляем текстовое уведомление
                        await bot.send_message(
                            task.user_id,
                            f"✅ Видео готово!\nID: {task.task_id}"
                        )

                except Exception as e:
                    task.status = TaskStatus.FAILED
                    task.error = str(e)
                    task.completed_at = time.time()

                    # Уведомляем пользователя об ошибке
                    try:
                        buttons = [
                            [InlineKeyboardButton(text="🔄 Попробовать снова", callback_data="menu:create")],
                            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="menu:main")],
                        ]
                        await bot.send_message(
                            task.user_id,
                            f"⚠️ <b>Ошибка при генерации видео</b>\n\n"
                            f"ID задачи: <code>{task.task_id}</code>\n"
                            f"Ошибка: <code>{str(e)[:200]}</code>",
                            reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
                        )
                    except Exception as notify_err:
                        print(f"[TaskQueue] Failed to send error notification: {notify_err}")

                # Помечаем задачу как обработанную
                self.queue.task_done()

            except Exception as e:
                print(f"[TaskQueue] Worker error: {e}")
                await asyncio.sleep(1)

    def stop_worker(self):
        """Останавливает worker"""
        self._worker_running = False
        print("[TaskQueue] Worker stopped")


# Глобальный экземпляр очереди
_task_queue: Optional[TaskQueue] = None


def get_task_queue() -> TaskQueue:
    """Получает глобальный экземпляр очереди"""
    global _task_queue
    if _task_queue is None:
        _task_queue = TaskQueue()
    return _task_queue
