from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any, AsyncGenerator, Dict, Literal, Optional, Union

from aiogram.fsm.state import State

StateType = Optional[Union[str, State]]

DEFAULT_DESTINY = "default"


@dataclass(frozen=True)
class StorageKey:
    bot_id: int
    chat_id: int
    user_id: int
    thread_id: Optional[int] = None
    business_connection_id: Optional[str] = None
    destiny: str = DEFAULT_DESTINY


class KeyBuilder(ABC):
    """Base class for key builder."""

    @abstractmethod
    def build(
        self,
        key: StorageKey,
        part: Optional[Literal["data", "state", "lock"]] = None,
    ) -> str:
        """
        Build key to be used in storage's db queries

        :param key: contextual key
        :param part: part of the record
        :return: key to be used in storage's db queries
        """
        pass


class DefaultKeyBuilder(KeyBuilder):
    """
    Simple key builder with default prefix.

    Generates a colon-joined string with prefix, chat_id, user_id,
    optional bot_id, business_connection_id, destiny and field.

    Format:
     :code:`<prefix>:<bot_id?>:<business_connection_id?>:<chat_id>:<user_id>:<destiny?>:<field?>`
    """

    def __init__(
        self,
        *,
        prefix: str = "fsm",
        separator: str = ":",
        with_bot_id: bool = False,
        with_business_connection_id: bool = False,
        with_destiny: bool = False,
    ) -> None:
        """
        :param prefix: prefix for all records
        :param separator: separator
        :param with_bot_id: include Bot id in the key
        :param with_business_connection_id: include business connection id
        :param with_destiny: include destiny key
        """
        self.prefix = prefix
        self.separator = separator
        self.with_bot_id = with_bot_id
        self.with_business_connection_id = with_business_connection_id
        self.with_destiny = with_destiny

    def build(
        self,
        key: StorageKey,
        part: Optional[Literal["data", "state", "lock"]] = None,
    ) -> str:
        parts = [self.prefix]
        if self.with_bot_id:
            parts.append(str(key.bot_id))
        if self.with_business_connection_id and key.business_connection_id:
            parts.append(str(key.business_connection_id))
        parts.append(str(key.chat_id))
        if key.thread_id:
            parts.append(str(key.thread_id))
        parts.append(str(key.user_id))
        if self.with_destiny:
            parts.append(key.destiny)
        elif key.destiny != DEFAULT_DESTINY:
            error_message = (
                "Default key builder is not configured to use key destiny other than the default."
                "\n\nProbably, you should set `with_destiny=True` in for DefaultKeyBuilder."
            )
            raise ValueError(error_message)
        if part:
            parts.append(part)
        return self.separator.join(parts)


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
