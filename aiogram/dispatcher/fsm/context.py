from typing import Any, Dict, Optional

from aiogram import Bot
from aiogram.dispatcher.fsm.storage.base import BaseStorage, StateType


class FSMContext:
    def __init__(self, bot: Bot, storage: BaseStorage, chat_id: int, user_id: int) -> None:
        self.bot = bot
        self.storage = storage
        self.chat_id = chat_id
        self.user_id = user_id

    async def set_state(self, state: StateType = None) -> None:
        await self.storage.set_state(
            bot=self.bot, chat_id=self.chat_id, user_id=self.user_id, state=state
        )

    async def get_state(self) -> Optional[str]:
        return await self.storage.get_state(
            bot=self.bot, chat_id=self.chat_id, user_id=self.user_id
        )

    async def set_data(self, data: Dict[str, Any]) -> None:
        await self.storage.set_data(
            bot=self.bot, chat_id=self.chat_id, user_id=self.user_id, data=data
        )

    async def get_data(self) -> Dict[str, Any]:
        return await self.storage.get_data(
            bot=self.bot, chat_id=self.chat_id, user_id=self.user_id
        )

    async def update_data(
        self, data: Optional[Dict[str, Any]] = None, **kwargs: Any
    ) -> Dict[str, Any]:
        if data:
            kwargs.update(data)
        return await self.storage.update_data(
            bot=self.bot, chat_id=self.chat_id, user_id=self.user_id, data=kwargs
        )

    async def clear(self) -> None:
        await self.set_state(state=None)
        await self.set_data({})
