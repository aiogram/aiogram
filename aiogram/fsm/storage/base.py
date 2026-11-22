from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator, Mapping
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Final, Literal, overload

from aiogram.fsm.state import State

StateType = str | State | None

DEFAULT_DESTINY = "default"


@dataclass(frozen=True, slots=True)
class StorageKey:
    bot_id: int
    chat_id: int
    user_id: int
    thread_id: int | None = None
    business_connection_id: str | None = None
    destiny: str = DEFAULT_DESTINY
    is_guest: bool = False


class _Unchanged(Enum):
    UNCHANGED = "UNCHANGED"

    def __repr__(self) -> str:
        return "UNCHANGED"


UNCHANGED: Final = _Unchanged.UNCHANGED
"""Marks a part of a :class:`StorageWrite` that the write leaves as it is."""


@dataclass(frozen=True, slots=True, kw_only=True)
class StorageRecord:
    """
    State and data of one storage key, as returned by :meth:`BaseStorage.get_records`.

    The record is frozen, but :attr:`data` is a plain :class:`dict` owned by the caller:
    changing it does not change the storage.
    """

    state: str | None = None
    data: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class StorageWrite:
    """
    One write for :meth:`BaseStorage.apply_writes`.

    A part left as :data:`UNCHANGED` is not touched. :code:`state=None` clears the state
    and :code:`data={}` clears the data, as :meth:`BaseStorage.set_state` and
    :meth:`BaseStorage.set_data` do.
    """

    key: StorageKey
    state: StateType | Literal[_Unchanged.UNCHANGED] = UNCHANGED
    data: Mapping[str, Any] | Literal[_Unchanged.UNCHANGED] = UNCHANGED


class KeyBuilder(ABC):
    """Base class for key builder."""

    @abstractmethod
    def build(
        self,
        key: StorageKey,
        part: Literal["data", "state", "lock"] | None = None,
    ) -> str:
        """
        Build key to be used in storage's db queries

        :param key: contextual key
        :param part: part of the record
        :return: key to be used in storage's db queries
        """


class DefaultKeyBuilder(KeyBuilder):
    """
    Simple key builder with default prefix.

    Generates a colon-joined string with prefix, chat_id, user_id,
    optional bot_id, business_connection_id, guest marker, thread_id, destiny and field.

    Format:
     :code:`<prefix>:<bot_id?>:<business_connection_id?>:<guest?>:<chat_id>:<thread_id?>:<user_id>:<destiny?>:<field?>`

    The :code:`guest` part is added only for keys of guest chats
    (:code:`StorageKey.is_guest`), so keys of regular chats are not affected by it.
    """

    def __init__(
        self,
        *,
        prefix: str = "fsm",
        separator: str = ":",
        with_bot_id: bool = False,
        with_business_connection_id: bool = False,
        with_destiny: bool = False,
        with_guest: bool = True,
    ) -> None:
        """
        :param prefix: prefix for all records
        :param separator: separator
        :param with_bot_id: include Bot id in the key
        :param with_business_connection_id: include business connection id
        :param with_destiny: include destiny key
        :param with_guest: add the :code:`guest` part to keys of guest chats,
            so they don't share records with the bot's own chats that have the same id
        """
        self.prefix = prefix
        self.separator = separator
        self.with_bot_id = with_bot_id
        self.with_business_connection_id = with_business_connection_id
        self.with_destiny = with_destiny
        self.with_guest = with_guest

    def build(
        self,
        key: StorageKey,
        part: Literal["data", "state", "lock"] | None = None,
    ) -> str:
        parts = [self.prefix]
        if self.with_bot_id:
            parts.append(str(key.bot_id))
        if self.with_business_connection_id and key.business_connection_id:
            parts.append(str(key.business_connection_id))
        if self.with_guest and key.is_guest:
            parts.append("guest")
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

    No storage promises atomicity across keys or across the state and data parts of one
    key, including :meth:`get_records` and :meth:`apply_writes`: updates of one FSM key
    are serialised by event isolation. :meth:`update_data` is atomic in the built-in
    storages; the fallback here is not. An atomic merge still does not make an
    application read-modify-write atomic: two callers can both read :code:`n=0` and
    both write :code:`n=1`.
    """

    @abstractmethod
    async def set_state(self, key: StorageKey, state: StateType = None) -> None:
        """
        Set state for specified key

        :param key: storage key
        :param state: new state
        """

    @abstractmethod
    async def get_state(self, key: StorageKey) -> str | None:
        """
        Get key state

        :param key: storage key
        :return: current state
        """

    @abstractmethod
    async def set_data(self, key: StorageKey, data: Mapping[str, Any]) -> None:
        """
        Write data (replace)

        :param key: storage key
        :param data: new data
        """

    @abstractmethod
    async def get_data(self, key: StorageKey) -> dict[str, Any]:
        """
        Get current data for key

        :param key: storage key
        :return: current data
        """

    @overload
    async def get_value(self, storage_key: StorageKey, dict_key: str) -> Any | None:
        """
        Get single value from data by key

        :param storage_key: storage key
        :param dict_key: value key
        :return: value stored in key of dict or ``None``
        """

    @overload
    async def get_value(self, storage_key: StorageKey, dict_key: str, default: Any) -> Any:
        """
        Get single value from data by key

        :param storage_key: storage key
        :param dict_key: value key
        :param default: default value to return
        :return: value stored in key of dict or default
        """

    async def get_value(
        self,
        storage_key: StorageKey,
        dict_key: str,
        default: Any | None = None,
    ) -> Any | None:
        data = await self.get_data(storage_key)
        return data.get(dict_key, default)

    async def update_data(self, key: StorageKey, data: Mapping[str, Any]) -> dict[str, Any]:
        """
        Update date in the storage for key (like dict.update)

        This fallback reads and then writes the data, so it is not atomic;
        storages that can merge in one step override it.

        :param key: storage key
        :param data: partial data
        :return: new data
        """
        current_data = await self.get_data(key=key)
        current_data.update(data)
        await self.set_data(key=key, data=current_data)
        return current_data.copy()

    async def get_records(self, *keys: StorageKey) -> list[StorageRecord]:
        """
        Read state and data of several keys.

        Storages that can read them in one round trip override this; the fallback calls
        :meth:`get_state` and :meth:`get_data` for each key in order. The read is not a
        snapshot: no atomicity across keys or parts is promised.

        :param keys: storage keys, duplicates allowed
        :return: one record per key, in the order of the keys
        """
        return [
            StorageRecord(state=await self.get_state(key=key), data=await self.get_data(key=key))
            for key in keys
        ]

    async def apply_writes(self, *writes: StorageWrite) -> None:
        """
        Apply several writes in order; a later write to the same part of a key wins.

        Storages that can write in one round trip override this; the fallback calls
        :meth:`set_state` and then :meth:`set_data` for each write, skipping
        :data:`UNCHANGED` parts. No atomicity across keys or parts is promised: when a
        write fails, the writes before it stay applied.

        :param writes: writes to apply
        """
        for write in writes:
            if write.state is not UNCHANGED:
                await self.set_state(key=write.key, state=write.state)
            if write.data is not UNCHANGED:
                await self.set_data(key=write.key, data=write.data)

    @abstractmethod
    async def close(self) -> None:  # pragma: no cover
        """
        Close storage (database connection, file or etc.)
        """


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
