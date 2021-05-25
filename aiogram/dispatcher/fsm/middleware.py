from typing import Any, Awaitable, Callable, Dict, Optional

from aiogram.dispatcher.fsm.context import FSMContext
from aiogram.dispatcher.fsm.storage.base import BaseStorage
from aiogram.dispatcher.fsm.strategy import FSMStrategy, apply_strategy
from aiogram.dispatcher.middlewares.base import BaseMiddleware
from aiogram.types import Update


class FSMContextMiddleware(BaseMiddleware[Update]):
    def __init__(
        self,
        storage: BaseStorage,
        strategy: FSMStrategy = FSMStrategy.USER_IN_CHAT,
        isolate_events: bool = True,
    ) -> None:
        self.storage = storage
        self.strategy = strategy
        self.isolate_events = isolate_events

    async def __call__(
        self,
        handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: Dict[str, Any],
    ) -> Any:
        context = self.resolve_event_context(data)
        data["fsm_storage"] = self.storage
        if context:
            data.update({"state": context, "raw_state": await context.get_state()})
            if self.isolate_events:
                async with self.storage.lock(chat_id=context.chat_id, user_id=context.user_id):
                    return await handler(event, data)
        return await handler(event, data)

    def resolve_event_context(self, data: Dict[str, Any]) -> Optional[FSMContext]:
        user = data.get("event_from_user")
        chat = data.get("event_chat")
        chat_id = chat.id if chat else None
        user_id = user.id if user else None
        return self.resolve_context(chat_id=chat_id, user_id=user_id)

    def resolve_context(
        self, chat_id: Optional[int], user_id: Optional[int]
    ) -> Optional[FSMContext]:
        if chat_id is None:
            chat_id = user_id

        if chat_id is not None and user_id is not None:
            chat_id, user_id = apply_strategy(
                chat_id=chat_id, user_id=user_id, strategy=self.strategy
            )
            return self.get_context(chat_id=chat_id, user_id=user_id)
        return None

    def get_context(self, chat_id: int, user_id: int) -> FSMContext:
        return FSMContext(storage=self.storage, chat_id=chat_id, user_id=user_id)
