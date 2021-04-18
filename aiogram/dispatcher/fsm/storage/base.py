from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Dict, Optional, Union

from aiogram.dispatcher.fsm.state import State

StateType = Optional[Union[str, State]]


class BaseStorage(ABC):
    @abstractmethod
    @asynccontextmanager
    async def lock(self) -> AsyncGenerator[None, None]:
        yield None

    @abstractmethod
    async def set_state(self, chat_id: int, user_id: int, state: StateType = None) -> None:
        pass

    @abstractmethod
    async def get_state(self, chat_id: int, user_id: int) -> Optional[str]:
        pass

    @abstractmethod
    async def set_data(self, chat_id: int, user_id: int, data: Dict[str, Any]) -> None:
        pass

    @abstractmethod
    async def get_data(self, chat_id: int, user_id: int) -> Dict[str, Any]:
        pass

    async def update_data(
        self, chat_id: int, user_id: int, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        current_data = await self.get_data(chat_id=chat_id, user_id=user_id)
        current_data.update(data)
        await self.set_data(chat_id=chat_id, user_id=user_id, data=current_data)
        return current_data.copy()
