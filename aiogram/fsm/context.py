from typing import Any, Dict, Optional

from aiogram import Bot
from aiogram.fsm.storage.base import BaseStorage, StateType, StorageKey


class FSMContext:
    def __init__(self, bot: Bot, storage: BaseStorage, key: StorageKey) -> None:
        self.bot = bot
        self.storage = storage
        self.key = key

    async def set_state(self, state: StateType = None) -> None:
        await self.storage.set_state(bot=self.bot, key=self.key, state=state)

    async def get_state(self) -> Optional[str]:
        return await self.storage.get_state(bot=self.bot, key=self.key)

    async def set_data(self, data: Dict[str, Any]) -> None:
        await self.storage.set_data(bot=self.bot, key=self.key, data=data)

    async def get_data(self) -> Dict[str, Any]:
        return await self.storage.get_data(bot=self.bot, key=self.key)

    async def update_data(
        self, data: Optional[Dict[str, Any]] = None, **kwargs: Any
    ) -> Dict[str, Any]:
        if data:
            kwargs.update(data)
        return await self.storage.update_data(bot=self.bot, key=self.key, data=kwargs)

    async def clear(self) -> None:
        await self.set_state(state=None)
        await self.set_data({})
