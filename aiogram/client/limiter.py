from typing import Optional
import asyncio
import time
import random
from collections import deque

class PrioritySlidingWindowLimiter:
    """
    Ограничитель частоты запросов с поддержкой приоритетов.
    Активируется только при наличии задач в очереди.
    """

    def __init__(self, max_calls: int, period: float):
        self.max_calls = max_calls
        self.period = period
        
        # Очереди для запросов
        self.high_priority_queue = asyncio.Queue()
        self.low_priority_queue = asyncio.Queue()
        
        # История вызовов для скользящего окна
        self.calls_history: deque[float] = deque()
        
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
                    future = await self.high_priority_queue.get()
                    await self._wait_and_release(future)
                    self.high_priority_queue.task_done()
                
                # Если высокоприоритетных нет - обрабатываем низкоприоритетные
                elif not self.low_priority_queue.empty():
                    future = await self.low_priority_queue.get()
                    await self._wait_and_release(future)
                    self.low_priority_queue.task_done()

        finally:
            self._processing = False
            self._processing_task = None

    async def _wait_and_release(self, future: asyncio.Future):
        """Ждем возможности выполнить запрос и разрешаем его"""
        try:
            await self._wait_sliding_window()
            if not future.done():
                future.set_result(None)
        except Exception as e:
            if not future.done():
                future.set_exception(e)

    async def _wait_sliding_window(self):
        """Ожидание в соответствии со скользящим окном"""
        async with self.lock:
            now = time.monotonic()
            
            # Очищаем устаревшие записи
            while self.calls_history and now - self.calls_history[0] > self.period:
                self.calls_history.popleft()

            # Если достигнут лимит - ждем
            if len(self.calls_history) >= self.max_calls:
                # Добавляем jitter для избежания коллизий
                jitter_sleep = random.uniform(0.1, 0.5)
                await asyncio.sleep(jitter_sleep)
                
                # Ждем освобождения слота
                if self.calls_history:  # Проверяем, что очередь не пуста
                    sleep_for = self.period - (now - self.calls_history[0]) + 0.01
                    await asyncio.sleep(max(0, sleep_for))
            
            # Записываем время вызова
            self.calls_history.append(time.monotonic())

    async def wait(self, low_priority: bool = False) -> None:
        """
        Ожидание разрешения на выполнение запроса.
        
        Args:
            priority: Приоритет запроса (HIGH или LOW)
        """
        future = asyncio.Future()
        
        # Добавляем в соответствующую очередь
        if not low_priority:
            await self.high_priority_queue.put(future)
        else:
            await self.low_priority_queue.put(future)
        
        # Запускаем обработчик, если он не активен
        if not self._processing:
            self._processing = True
            self._processing_task = asyncio.create_task(self._process_queue())
        
        # Ждем разрешения
        await future

    def can_execute_immediately(self) -> bool:
        """Проверяет, можно ли выполнить запрос немедленно"""
        now = time.monotonic()
        with self.lock:
            # Очищаем устаревшие записи
            while self.calls_history and now - self.calls_history[0] > self.period:
                self.calls_history.popleft()
            
            return len(self.calls_history) < self.max_calls

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
