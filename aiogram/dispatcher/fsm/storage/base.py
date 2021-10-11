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
    """
    Base class for all FSM storages
    """

    @abstractmethod
    @asynccontextmanager
    async def lock(self, bot: Bot, key: StorageKey) -> AsyncGenerator[None, None]:
        """
        Isolate events with lock.
        Will be used as context manager

        :param bot: instance of the current bot
        :param key: storage key
        :return: An async generator
        """
        yield None

    @abstractmethod
    async def set_state(self, bot: Bot, key: StorageKey, state: StateType = None) -> None:
        """
        Set state for specified key

        :param bot: instance of the current bot
        :param key: storage key
        :param state: new state
        """
        pass

    @abstractmethod
    async def get_state(self, bot: Bot, key: StorageKey) -> Optional[str]:
        """
        Get key state

        :param bot: instance of the current bot
        :param key: storage key
        :return: current state
        """
        pass

    @abstractmethod
    async def set_data(self, bot: Bot, key: StorageKey, data: Dict[str, Any]) -> None:
        """
        Write data (replace)

        :param bot: instance of the current bot
        :param key: storage key
        :param data: new data
        """
        pass

    @abstractmethod
    async def get_data(self, bot: Bot, key: StorageKey) -> Dict[str, Any]:
        """
        Get current data for key

        :param bot: instance of the current bot
        :param key: storage key
        :return: current data
        """
        pass

    async def update_data(self, bot: Bot, key: StorageKey, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update date in the storage for key (like dict.update)

        :param bot: instance of the current bot
        :param key: storage key
        :param data: partial data
        :return: new data
        """
        current_data = await self.get_data(bot=bot, key=key)
        current_data.update(data)
        await self.set_data(bot=bot, key=key, data=current_data)
        return current_data.copy()

    @abstractmethod
    async def close(self) -> None:  # pragma: no cover
        """
        Close storage (database connection, file or etc.)
        """
        pass
