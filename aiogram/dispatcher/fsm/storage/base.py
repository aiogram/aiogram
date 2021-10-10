from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any, AsyncGenerator, Dict, Optional, Union

from aiogram import Bot
from aiogram.dispatcher.fsm.state import State

StateType = Optional[Union[str, State]]

DEFAULT_DESTINY = "default"


@dataclass(frozen=True)
class StorageKey:
    bot_id: int
    chat_id: int
    user_id: int
    destiny: str = DEFAULT_DESTINY


class BaseStorage(ABC):
    @abstractmethod
    @asynccontextmanager
    async def lock(self, bot: Bot, key: StorageKey) -> AsyncGenerator[None, None]:
        yield None

    @abstractmethod
    async def set_state(self, bot: Bot, key: StorageKey, state: StateType = None) -> None:
        pass

    @abstractmethod
    async def get_state(self, bot: Bot, key: StorageKey) -> Optional[str]:
        pass

    @abstractmethod
    async def set_data(self, bot: Bot, key: StorageKey, data: Dict[str, Any]) -> None:
        pass

    @abstractmethod
    async def get_data(self, bot: Bot, key: StorageKey) -> Dict[str, Any]:
        pass

    async def update_data(self, bot: Bot, key: StorageKey, data: Dict[str, Any]) -> Dict[str, Any]:
        current_data = await self.get_data(bot=bot, key=key)
        current_data.update(data)
        await self.set_data(bot=bot, key=key, data=current_data)
        return current_data.copy()

    @abstractmethod
    async def close(self) -> None:  # pragma: no cover
        pass
