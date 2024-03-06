from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any, AsyncGenerator, Dict, Optional, Union

from aiogram.fsm.state import State

StateType = Optional[Union[str, State]]

DEFAULT_DESTINY = "default"


@dataclass(frozen=True)
class StorageKey:
    bot_id: int
    chat_id: int
    user_id: int
    thread_id: Optional[int] = None
    destiny: str = DEFAULT_DESTINY


class BaseStorage(ABC):
    """
    Base class for all FSM storages
    """

    @abstractmethod
    async def set_state(self, key: StorageKey, state: StateType = None) -> None:
        """
        Set state for specified key

        :param key: storage key
        :param state: new state
        """
        pass

    @abstractmethod
    async def get_state(self, key: StorageKey) -> Optional[str]:
        """
        Get key state

        :param key: storage key
        :return: current state
        """
        pass

    @abstractmethod
    async def set_data(self, key: StorageKey, data: Dict[str, Any]) -> None:
        """
        Write data (replace)

        :param key: storage key
        :param data: new data
        """
        pass

    @abstractmethod
    async def get_data(self, key: StorageKey) -> Dict[str, Any]:
        """
        Get current data for key

        :param key: storage key
        :return: current data
        """
        pass

    async def get_value(self, key: StorageKey, data_key: str, default: Any = None) -> Any:
        """
        Get selected value by key in current data

        :param key: storage key
        :param data_key: key of selected data
        :return: value of current data by key
        """
        current_data = await self.get_data(key=key)
        return current_data.get(data_key, default)

    async def update_data(self, key: StorageKey, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update date in the storage for key (like dict.update)

        :param key: storage key
        :param data: partial data
        :return: new data
        """
        current_data = await self.get_data(key=key)
        current_data.update(data)
        await self.set_data(key=key, data=current_data)
        return current_data.copy()

    @abstractmethod
    async def close(self) -> None:  # pragma: no cover
        """
        Close storage (database connection, file or etc.)
        """
        pass


class BaseEventIsolation(ABC):
    @abstractmethod
    @asynccontextmanager
    async def lock(self, key: StorageKey) -> AsyncGenerator[None, None]:
        """
        Isolate events with lock.
        Will be used as context manager

        :param key: storage key
        :return: An async generator
        """
        yield None

    @abstractmethod
    async def close(self) -> None:
        pass
