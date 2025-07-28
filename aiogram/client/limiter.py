from typing import Optional, Dict
from pydantic import BaseModel
from enum import Enum
import asyncio
import time
import random
from collections import deque

class ChatType(Enum):
    PRIVATE = "private"
    GROUP = "group"
    CHANNEL = "channel"

class DefaultLimiter(BaseModel):
    PER_CHAT_LIMIT: int = 1
    PER_CHAT_PERIOD: float = 1.0

    GROUP_LIMIT: int = 20
    GROUP_PERIOD: float = 60.0

    BROADCAST_LIMIT: int = 30
    BROADCAST_PERIOD: float = 1.0

class TelegramRateLimiter:
    """
    Ограничитель частоты запросов для Telegram ботов с поддержкой разных типов чатов.
    Поддерживает три типа лимитов:
    1. В одном чате - не более 1 сообщения в секунду
    2. В группе - не более 20 сообщений в минуту
    3. Для массовых уведомлений - не более 30 сообщений в секунду
    """

    def __init__(self, settings: DefaultLimiter = None):
        if settings is None:
            settings = DefaultLimiter()

        # Лимиты для Telegram
        self.PER_CHAT_LIMIT = settings.PER_CHAT_LIMIT
        self.PER_CHAT_PERIOD = settings.PER_CHAT_PERIOD
        
        self.GROUP_LIMIT = settings.GROUP_LIMIT
        self.GROUP_PERIOD = settings.GROUP_PERIOD
        
        self.BROADCAST_LIMIT = settings.BROADCAST_LIMIT
        self.BROADCAST_PERIOD = settings.BROADCAST_PERIOD
        
        # Очереди для запросов по приоритетам
        self.high_priority_queue = asyncio.Queue()
        self.low_priority_queue = asyncio.Queue()
        
        # История вызовов для разных лимитов
        self.per_chat_history: Dict[str, deque] = {}  # chat_id -> deque[timestamp]
        self.group_history: deque = deque()  # для групповых чатов
        self.broadcast_history: deque = deque()  # для всех сообщений
        
        # Блокировка для потокобезопасной работы
        self.lock = asyncio.Lock()
        
        # Флаг активности обработчика
        self._processing = False
        self._processing_task: Optional[asyncio.Task] = None

    async def _process_queue(self):
        """Обработка очереди до полного опустошения"""
        try:
            while not self.high_priority_queue.empty() or not self.low_priority_queue.empty():
                # Сначала обрабатываем высокоприоритетные запросы
                if not self.high_priority_queue.empty():
                    item = await self.high_priority_queue.get()
                    await self._wait_and_release(item)
                    self.high_priority_queue.task_done()
                
                # Если высокоприоритетных нет - обрабатываем низкоприоритетные
                elif not self.low_priority_queue.empty():
                    item = await self.low_priority_queue.get()
                    await self._wait_and_release(item)
                    self.low_priority_queue.task_done()

        finally:
            self._processing = False
            self._processing_task = None

    async def _wait_and_release(self, item: dict):
        """Ждем возможности выполнить запрос и разрешаем его"""
        future = item['future']
        chat_id = item['chat_id']
        chat_type = item['chat_type']
        is_broadcast = item['is_broadcast']
        
        try:
            await self._wait_telegram_limits(chat_id, chat_type, is_broadcast)
            if not future.done():
                future.set_result(None)
        except Exception as e:
            if not future.done():
                future.set_exception(e)

    async def _wait_telegram_limits(self, chat_id: str, chat_type: ChatType, is_broadcast: bool):
        """Ожидание в соответствии с лимитами Telegram"""
        async with self.lock:
            now = time.monotonic()
            # Очищаем устаревшие записи для всех лимитов
            self._cleanup_history(now)
            # Проверяем все лимиты и ждем, если нужно
            while True:
                can_proceed = True
                sleep_time = 0
                # 1. Лимит для конкретного чата (1 сообщение/сек)
                if len(self.per_chat_history.get(chat_id, deque())) >= self.PER_CHAT_LIMIT:
                    oldest = self.per_chat_history[chat_id][0]
                    sleep_time = max(sleep_time, self.PER_CHAT_PERIOD - (now - oldest) + 0.01)
                    can_proceed = False
                # 2. Лимит для групп (20 сообщений/минуту)
                if chat_type in [ChatType.GROUP, ChatType.CHANNEL]:
                    if len(self.group_history) >= self.GROUP_LIMIT:
                        oldest = self.group_history[0]
                        sleep_time = max(sleep_time, self.GROUP_PERIOD - (now - oldest) + 0.01)
                        can_proceed = False
                # 3. Лимит для массовых рассылок (30 сообщений/сек)
                if is_broadcast:
                    if len(self.broadcast_history) >= self.BROADCAST_LIMIT:
                        oldest = self.broadcast_history[0]
                        sleep_time = max(sleep_time, self.BROADCAST_PERIOD - (now - oldest) + 0.01)
                        can_proceed = False
                if can_proceed:
                    break
                # Добавляем небольшой jitter для избежания коллизий
                await asyncio.sleep(max(0, sleep_time))
                # Обновляем время после ожидания
                now = time.monotonic()
                self._cleanup_history(now)
            # Записываем время вызова во все соответствующие истории
            self._record_call(now, chat_id, chat_type, is_broadcast)

    def _cleanup_history(self, now: float):
        """Очищает устаревшие записи из всех очередей"""
        # Очищаем историю для конкретных чатов
        chats_to_remove = []
        for chat_id, history in self.per_chat_history.items():
            while history and now - history[0] > self.PER_CHAT_PERIOD:
                history.popleft()
            if len(history) == 0:
                chats_to_remove.append(chat_id)
        # Удаляем пустые очереди чатов
        for chat_id in chats_to_remove:
            del self.per_chat_history[chat_id]
        # Очищаем историю групп
        while self.group_history and now - self.group_history[0] > self.GROUP_PERIOD:
            self.group_history.popleft()
        # Очищаем историю массовых рассылок
        while self.broadcast_history and now - self.broadcast_history[0] > self.BROADCAST_PERIOD:
            self.broadcast_history.popleft()

    def _record_call(self, timestamp: float, chat_id: str, chat_type: ChatType, is_broadcast: bool):
        """Записывает вызов во все соответствующие очереди"""
        # Запись для лимита по чату
        if chat_id not in self.per_chat_history:
            self.per_chat_history[chat_id] = deque()
        self.per_chat_history[chat_id].append(timestamp)
        # Запись для лимита групп, если это группа или канал
        if chat_type in [ChatType.GROUP, ChatType.CHANNEL]:
            self.group_history.append(timestamp)
        # Запись для лимита массовых рассылок
        if is_broadcast:
            self.broadcast_history.append(timestamp)

    async def wait(self, chat_id: str, chat_type: ChatType = ChatType.PRIVATE, 
                   is_broadcast: bool = False) -> None:
        """
        Ожидание разрешения на выполнение запроса в соответствии с лимитами Telegram.
        Рассылки автоматически считаются низкоприоритетными.
        
        Args:
            chat_id: ID чата (строка, чтобы поддерживать и числовые и строковые ID)
            chat_type: Тип чата (PRIVATE, GROUP, CHANNEL)
            is_broadcast: Является ли сообщение частью массовой рассылки
        """
        future = asyncio.Future()
        item = {
            'future': future,
            'chat_id': str(chat_id),
            'chat_type': chat_type,
            'is_broadcast': is_broadcast
        }
        
        # Рассылки идут в низкоприоритетную очередь, остальное - в высокоприоритетную
        if is_broadcast:
            await self.low_priority_queue.put(item)
        else:
            await self.high_priority_queue.put(item)
        
        # Запускаем обработчик, если он не активен
        if not self._processing:
            self._processing = True
            self._processing_task = asyncio.create_task(self._process_queue())
        
        # Ждем разрешения
        await future

    def can_execute_immediately(self, chat_id: str, chat_type: ChatType = ChatType.PRIVATE, 
                               is_broadcast: bool = False) -> bool:
        """Проверяет, можно ли выполнить запрос немедленно"""
        now = time.monotonic()
        chat_id = str(chat_id)
        
        with self.lock:
            # Очищаем устаревшие записи
            self._cleanup_history(now)
            
            # Проверяем все лимиты
            # 1. Лимит для конкретного чата
            if len(self.per_chat_history.get(chat_id, deque())) >= self.PER_CHAT_LIMIT:
                return False
            
            # 2. Лимит для групп
            if chat_type in [ChatType.GROUP, ChatType.CHANNEL]:
                if len(self.group_history) >= self.GROUP_LIMIT:
                    return False
            
            # 3. Лимит для массовых рассылок
            if is_broadcast:
                if len(self.broadcast_history) >= self.BROADCAST_LIMIT:
                    return False
            
            return True

    async def wait_until_idle(self):
        """Ожидание завершения всех задач в очереди"""
        if self._processing_task:
            await self._processing_task

    async def close(self):
        """Завершение работы лимитера"""
        if self._processing_task:
            self._processing_task.cancel()
            try:
                await self._processing_task
            except asyncio.CancelledError:
                pass
