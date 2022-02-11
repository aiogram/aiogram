import asyncio
import logging
import time
from asyncio import Event, Lock
from contextlib import suppress
from types import TracebackType
from typing import Any, Awaitable, Callable, Dict, Optional, Type, Union

from aiogram import BaseMiddleware, Bot
from aiogram.dispatcher.flags.getter import get_flag
from aiogram.types import Message, TelegramObject

logger = logging.getLogger(__name__)
DEFAULT_INTERVAL = 5.0
DEFAULT_INITIAL_SLEEP = 0.1


class ChatActionSender:
    def __init__(
        self,
        *,
        chat_id: Union[str, int],
        action: str = "typing",
        interval: float = DEFAULT_INTERVAL,
        initial_sleep: float = DEFAULT_INTERVAL,
        bot: Optional[Bot] = None,
    ) -> None:
        if bot is None:
            bot = Bot.get_current(False)
        self.chat_id = chat_id
        self.action = action
        self.interval = interval
        self.initial_sleep = initial_sleep
        self.bot = bot

        self._close_event = Event()
        self._running = False
        self._lock = Lock()

    async def _worker(self) -> None:
        logger.debug(
            "Started chat action %r sender in chat_id=%s via bot id=%d",
            self.action,
            self.chat_id,
            self.bot.id,
        )
        try:
            counter = 0
            await asyncio.sleep(self.initial_sleep)
            while not self._close_event.is_set():
                start = time.monotonic()
                logger.debug(
                    "Sent chat action %r to chat_id=%s via bot %d (already sent actions %d)",
                    self.action,
                    self.chat_id,
                    self.bot.id,
                    counter,
                )
                await self.bot.send_chat_action(chat_id=self.chat_id, action=self.action)
                counter += 1

                interval = self.interval - (time.monotonic() - start)
                with suppress(asyncio.TimeoutError):
                    await asyncio.wait_for(self._close_event.wait(), interval)
        finally:
            logger.debug(
                "Finished chat action %r sender in chat_id=%s via bot id=%d",
                self.action,
                self.chat_id,
                self.bot.id,
            )
            self._running = False

    async def _run(self) -> None:
        async with self._lock:
            if self._running:
                raise RuntimeError("Already running")
            asyncio.create_task(self._worker())

    def _stop(self) -> None:
        if not self._close_event.is_set():
            self._close_event.set()

    async def __aenter__(self) -> "ChatActionSender":
        await self._run()
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> Any:
        self._stop()

    @classmethod
    def typing(
        cls,
        bot: Bot,
        chat_id: Union[int, str],
        interval: float = DEFAULT_INTERVAL,
        initial_sleep: float = DEFAULT_INITIAL_SLEEP,
    ) -> "ChatActionSender":
        return cls(
            bot=bot,
            chat_id=chat_id,
            action="typing",
            interval=interval,
            initial_sleep=initial_sleep,
        )

    @classmethod
    def upload_photo(
        cls,
        bot: Bot,
        chat_id: Union[int, str],
        interval: float = DEFAULT_INTERVAL,
        initial_sleep: float = DEFAULT_INITIAL_SLEEP,
    ) -> "ChatActionSender":
        return cls(
            bot=bot,
            chat_id=chat_id,
            action="upload_photo",
            interval=interval,
            initial_sleep=initial_sleep,
        )

    @classmethod
    def record_video(
        cls,
        bot: Bot,
        chat_id: Union[int, str],
        interval: float = DEFAULT_INTERVAL,
        initial_sleep: float = DEFAULT_INITIAL_SLEEP,
    ) -> "ChatActionSender":
        return cls(
            bot=bot,
            chat_id=chat_id,
            action="record_video",
            interval=interval,
            initial_sleep=initial_sleep,
        )

    @classmethod
    def upload_video(
        cls,
        bot: Bot,
        chat_id: Union[int, str],
        interval: float = DEFAULT_INTERVAL,
        initial_sleep: float = DEFAULT_INITIAL_SLEEP,
    ) -> "ChatActionSender":
        return cls(
            bot=bot,
            chat_id=chat_id,
            action="upload_video",
            interval=interval,
            initial_sleep=initial_sleep,
        )

    @classmethod
    def record_voice(
        cls,
        bot: Bot,
        chat_id: Union[int, str],
        interval: float = DEFAULT_INTERVAL,
        initial_sleep: float = DEFAULT_INITIAL_SLEEP,
    ) -> "ChatActionSender":
        return cls(
            bot=bot,
            chat_id=chat_id,
            action="record_voice",
            interval=interval,
            initial_sleep=initial_sleep,
        )

    @classmethod
    def upload_voice(
        cls,
        bot: Bot,
        chat_id: Union[int, str],
        interval: float = DEFAULT_INTERVAL,
        initial_sleep: float = DEFAULT_INITIAL_SLEEP,
    ) -> "ChatActionSender":
        return cls(
            bot=bot,
            chat_id=chat_id,
            action="upload_voice",
            interval=interval,
            initial_sleep=initial_sleep,
        )

    @classmethod
    def upload_document(
        cls,
        bot: Bot,
        chat_id: Union[int, str],
        interval: float = DEFAULT_INTERVAL,
        initial_sleep: float = DEFAULT_INITIAL_SLEEP,
    ) -> "ChatActionSender":
        return cls(
            bot=bot,
            chat_id=chat_id,
            action="upload_document",
            interval=interval,
            initial_sleep=initial_sleep,
        )

    @classmethod
    def choose_sticker(
        cls,
        bot: Bot,
        chat_id: Union[int, str],
        interval: float = DEFAULT_INTERVAL,
        initial_sleep: float = DEFAULT_INITIAL_SLEEP,
    ) -> "ChatActionSender":
        return cls(
            bot=bot,
            chat_id=chat_id,
            action="choose_sticker",
            interval=interval,
            initial_sleep=initial_sleep,
        )

    @classmethod
    def find_location(
        cls,
        bot: Bot,
        chat_id: Union[int, str],
        interval: float = DEFAULT_INTERVAL,
        initial_sleep: float = DEFAULT_INITIAL_SLEEP,
    ) -> "ChatActionSender":
        return cls(
            bot=bot,
            chat_id=chat_id,
            action="find_location",
            interval=interval,
            initial_sleep=initial_sleep,
        )

    @classmethod
    def record_video_note(
        cls,
        bot: Bot,
        chat_id: Union[int, str],
        interval: float = DEFAULT_INTERVAL,
        initial_sleep: float = DEFAULT_INITIAL_SLEEP,
    ) -> "ChatActionSender":
        return cls(
            bot=bot,
            chat_id=chat_id,
            action="record_video_note",
            interval=interval,
            initial_sleep=initial_sleep,
        )

    @classmethod
    def upload_video_note(
        cls,
        bot: Bot,
        chat_id: Union[int, str],
        interval: float = DEFAULT_INTERVAL,
        initial_sleep: float = DEFAULT_INITIAL_SLEEP,
    ) -> "ChatActionSender":
        return cls(
            bot=bot,
            chat_id=chat_id,
            action="upload_video_note",
            interval=interval,
            initial_sleep=initial_sleep,
        )


class ChatActionMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        if not isinstance(event, Message):
            return await handler(event, data)
        bot = data["bot"]

        chat_action = get_flag(data, "chat_action") or "typing"
        kwargs = {}
        if isinstance(chat_action, dict):
            if initial_sleep := chat_action.get("initial_sleep"):
                kwargs["initial_sleep"] = initial_sleep
            if interval := chat_action.get("interval"):
                kwargs["interval"] = interval
            if action := chat_action.get("action"):
                kwargs["action"] = action
        elif isinstance(chat_action, bool):
            kwargs["action"] = "typing"
        else:
            kwargs["action"] = chat_action
        async with ChatActionSender(bot=bot, chat_id=event.chat.id, **kwargs):
            return await handler(event, data)
