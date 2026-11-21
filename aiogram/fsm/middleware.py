from collections.abc import Awaitable, Callable
from typing import Any, cast

from aiogram import Bot
from aiogram.dispatcher.middlewares.base import BaseMiddleware
from aiogram.dispatcher.middlewares.user_context import EVENT_CONTEXT_KEY, EventContext
from aiogram.enums import ChatType
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import (
    DEFAULT_DESTINY,
    BaseEventIsolation,
    BaseStorage,
    StorageKey,
)
from aiogram.fsm.strategy import FSMStrategy, apply_strategy
from aiogram.types import TelegramObject


class FSMContextMiddleware(BaseMiddleware):
    def __init__(
        self,
        storage: BaseStorage,
        events_isolation: BaseEventIsolation,
        strategy: FSMStrategy = FSMStrategy.USER_IN_CHAT,
        key_on_sender_chat: bool = False,
    ) -> None:
        """
        :param storage: FSM storage
        :param events_isolation: events isolation
        :param strategy: FSM strategy
        :param key_on_sender_chat: for messages sent on behalf of a chat
            (anonymous group administrators, users posting as a channel)
            use :code:`sender_chat.id` instead of the placeholder sender user id
            as the user id of the FSM key
        """
        self.storage = storage
        self.strategy = strategy
        self.events_isolation = events_isolation
        self.key_on_sender_chat = key_on_sender_chat

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        bot: Bot = cast(Bot, data["bot"])
        context = self.resolve_event_context(bot, data)
        data["fsm_storage"] = self.storage
        if context:
            # Bugfix: https://github.com/aiogram/aiogram/issues/1317
            # State should be loaded after lock is acquired
            async with self.events_isolation.lock(key=context.key):
                data.update({"state": context, "raw_state": await context.get_state()})
                return await handler(event, data)
        return await handler(event, data)

    def resolve_event_context(
        self,
        bot: Bot,
        data: dict[str, Any],
        destiny: str = DEFAULT_DESTINY,
    ) -> FSMContext | None:
        event_context: EventContext = cast(EventContext, data.get(EVENT_CONTEXT_KEY))
        user_id = event_context.user_id
        if (
            self.key_on_sender_chat
            and event_context.sender_chat is not None
            and event_context.chat is not None
            and event_context.chat.type != ChatType.CHANNEL
        ):
            user_id = event_context.sender_chat.id
        return self.resolve_context(
            bot=bot,
            chat_id=event_context.chat_id,
            user_id=user_id,
            thread_id=event_context.thread_id,
            business_connection_id=event_context.business_connection_id,
            destiny=destiny,
            is_guest=event_context.is_guest,
        )

    def resolve_context(
        self,
        bot: Bot,
        chat_id: int | None,
        user_id: int | None,
        thread_id: int | None = None,
        business_connection_id: str | None = None,
        destiny: str = DEFAULT_DESTINY,
        is_guest: bool = False,
    ) -> FSMContext | None:
        if chat_id is None:
            chat_id = user_id
        elif user_id is None and self.strategy in {FSMStrategy.CHAT, FSMStrategy.CHAT_TOPIC}:
            # CHAT/CHAT_TOPIC are chat-scoped, so missing user_id can fallback to chat_id.
            user_id = chat_id

        if chat_id is not None and user_id is not None:
            chat_id, user_id, thread_id = apply_strategy(
                chat_id=chat_id,
                user_id=user_id,
                thread_id=thread_id,
                strategy=self.strategy,
            )
            return self.get_context(
                bot=bot,
                chat_id=chat_id,
                user_id=user_id,
                thread_id=thread_id,
                business_connection_id=business_connection_id,
                destiny=destiny,
                is_guest=is_guest,
            )
        return None

    def get_context(
        self,
        bot: Bot,
        chat_id: int,
        user_id: int,
        thread_id: int | None = None,
        business_connection_id: str | None = None,
        destiny: str = DEFAULT_DESTINY,
        is_guest: bool = False,
    ) -> FSMContext:
        return FSMContext(
            storage=self.storage,
            key=StorageKey(
                user_id=user_id,
                chat_id=chat_id,
                bot_id=bot.id,
                thread_id=thread_id,
                business_connection_id=business_connection_id,
                destiny=destiny,
                is_guest=is_guest,
            ),
        )

    async def close(self) -> None:
        await self.storage.close()
        await self.events_isolation.close()
