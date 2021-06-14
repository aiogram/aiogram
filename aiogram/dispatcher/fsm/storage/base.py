from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Dict, Optional, Union

from aiogram import Bot
from aiogram.dispatcher.fsm.state import State

StateType = Optional[Union[str, State]]


class BaseStorage(ABC):
    @abstractmethod
    @asynccontextmanager
    async def lock(
        self, bot: Bot, chat_id: int, user_id: int
    ) -> AsyncGenerator[None, None]:  # pragma: no cover
        yield None

    @abstractmethod
    async def set_state(
        self, bot: Bot, chat_id: int, user_id: int, state: StateType = None
    ) -> None:  # pragma: no cover
        pass

    @abstractmethod
    async def get_state(
        self, bot: Bot, chat_id: int, user_id: int
    ) -> Optional[str]:  # pragma: no cover
        pass

    @abstractmethod
    async def set_data(
        self, bot: Bot, chat_id: int, user_id: int, data: Dict[str, Any]
    ) -> None:  # pragma: no cover
        pass

    @abstractmethod
    async def get_data(
        self, bot: Bot, chat_id: int, user_id: int
    ) -> Dict[str, Any]:  # pragma: no cover
        pass

    async def update_data(
        self, bot: Bot, chat_id: int, user_id: int, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        current_data = await self.get_data(bot=bot, chat_id=chat_id, user_id=user_id)
        current_data.update(data)
        await self.set_data(bot=bot, chat_id=chat_id, user_id=user_id, data=current_data)
        return current_data.copy()

    @abstractmethod
    async def close(self) -> None:  # pragma: no cover
        pass
