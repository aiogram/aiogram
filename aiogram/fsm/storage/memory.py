import asyncio
from collections import defaultdict
from collections.abc import AsyncGenerator, Hashable, Mapping
from contextlib import asynccontextmanager
from copy import copy
from dataclasses import dataclass, field
from threading import Lock
from typing import Any, overload

from aiogram.exceptions import DataNotDictLikeError
from aiogram.fsm.state import State
from aiogram.fsm.storage.base import (
    UNCHANGED,
    BaseEventIsolation,
    BaseStorage,
    StateType,
    StorageKey,
    StorageRecord,
    StorageWrite,
)


@dataclass
class MemoryStorageRecord:
    data: dict[str, Any] = field(default_factory=dict)
    state: str | None = None


class MemoryStorage(BaseStorage):
    """
    Default FSM storage; uses a regular :class:`dict` to store data and
    does not persist it across restarts.

    It is thread-safe at the map level: one :class:`threading.Lock` guards every read and
    write of :attr:`storage`, and :meth:`update_data`, :meth:`get_records` and
    :meth:`apply_writes` each run in a single critical section. :meth:`apply_writes` checks
    every write before it applies any, so a write with invalid data raises with nothing applied.
    Reads never create records, and a record whose state is :code:`None` and whose data is
    empty is removed.

    Copies are shallow, as in 3.x: nested mutable values returned by :meth:`get_data` and
    :meth:`get_value` are shared with the stored record, so change them only through
    :meth:`set_data` or :meth:`update_data`. Direct access to :attr:`storage` (a plain
    :code:`dict[StorageKey, MemoryStorageRecord]`) bypasses the lock and is not thread-safe.

    .. warning::

        This storage is not recommended for production use, as all data is lost
        when the bot restarts
    """

    def __init__(self) -> None:
        self.storage: dict[StorageKey, MemoryStorageRecord] = {}
        # ponytail: one global lock (PD-21); shard it if contention is ever measured
        self._lock = Lock()

    def __copy__(self) -> "MemoryStorage":
        # a shallow copy shares the records, so it must share the lock that guards them too
        clone = object.__new__(type(self))
        clone.__dict__.update(self.__dict__)
        return clone

    def __getstate__(self) -> dict[str, Any]:
        # copy.deepcopy() and pickle copy the records, so the copy gets a lock of its own
        state = self.__dict__.copy()
        del state["_lock"]
        return state

    def __setstate__(self, state: dict[str, Any]) -> None:
        self.__dict__.update(state)
        self._lock = Lock()

    async def close(self) -> None:
        pass

    def _put(self, key: StorageKey, record: MemoryStorageRecord) -> None:
        """Store the record, or drop it when it holds nothing. Call with the lock held."""
        if record.state is None and not record.data:
            self.storage.pop(key, None)
        else:
            self.storage[key] = record

    async def set_state(self, key: StorageKey, state: StateType = None) -> None:
        state = state.state if isinstance(state, State) else state
        with self._lock:
            record = self.storage.get(key) or MemoryStorageRecord()
            record.state = state
            self._put(key, record)

    async def get_state(self, key: StorageKey) -> str | None:
        with self._lock:
            record = self.storage.get(key)
            return None if record is None else record.state

    @staticmethod
    def _plain_data(data: Mapping[str, Any]) -> dict[str, Any]:
        if not isinstance(data, dict):
            msg = f"Data must be a dict or dict-like object, got {type(data).__name__}"
            raise DataNotDictLikeError(msg)
        return dict(data)  # a plain dict: no user override runs under the lock later

    async def set_data(self, key: StorageKey, data: Mapping[str, Any]) -> None:
        data = self._plain_data(data)
        with self._lock:
            record = self.storage.get(key) or MemoryStorageRecord()
            record.data = data
            self._put(key, record)

    async def get_data(self, key: StorageKey) -> dict[str, Any]:
        with self._lock:
            record = self.storage.get(key)
            return {} if record is None else record.data.copy()

    async def update_data(self, key: StorageKey, data: Mapping[str, Any]) -> dict[str, Any]:
        """
        Merge data into the stored data (like :meth:`dict.update`) atomically:
        the read, the merge and the copy happen in one critical section.

        :param key: storage key
        :param data: partial data
        :return: a copy of the merged data
        """
        if type(data) is not dict:  # a user Mapping runs its own code: iterate it outside the lock
            data = dict(data)
        with self._lock:
            record = self.storage.get(key) or MemoryStorageRecord()
            record.data = merged = {**record.data, **data}  # a new dict, as the 3.x get+set did
            self._put(key, record)
            return merged.copy()

    async def get_records(self, *keys: StorageKey) -> list[StorageRecord]:
        with self._lock:
            records = [self.storage.get(key) for key in keys]
            return [
                StorageRecord()
                if record is None
                else StorageRecord(state=record.state, data=record.data.copy())
                for record in records
            ]

    async def apply_writes(self, *writes: StorageWrite) -> None:
        # check and normalise every write before the lock: a bad one raises with nothing applied
        prepared = [
            (
                write.key,
                write.state.state if isinstance(write.state, State) else write.state,
                write.data if write.data is UNCHANGED else self._plain_data(write.data),
            )
            for write in writes
        ]
        if not prepared:
            return
        with self._lock:
            for key, state, data in prepared:
                record = self.storage.get(key) or MemoryStorageRecord()
                if state is not UNCHANGED:
                    record.state = state
                if data is not UNCHANGED:
                    record.data = data
                self._put(key, record)

    @overload
    async def get_value(self, storage_key: StorageKey, dict_key: str) -> Any | None: ...

    @overload
    async def get_value(self, storage_key: StorageKey, dict_key: str, default: Any) -> Any: ...

    async def get_value(
        self,
        storage_key: StorageKey,
        dict_key: str,
        default: Any | None = None,
    ) -> Any | None:
        with self._lock:
            record = self.storage.get(storage_key)
            value = default if record is None else record.data.get(dict_key, default)
        # copy() may run a user __copy__, so it stays outside the lock
        return copy(value)


class DisabledEventIsolation(BaseEventIsolation):
    @asynccontextmanager
    async def lock(self, key: StorageKey) -> AsyncGenerator[None, None]:
        yield

    async def close(self) -> None:
        pass


class SimpleEventIsolation(BaseEventIsolation):
    def __init__(self) -> None:
        # TODO: Unused locks cleaner is needed
        self._locks: defaultdict[Hashable, asyncio.Lock] = defaultdict(asyncio.Lock)

    @asynccontextmanager
    async def lock(self, key: StorageKey) -> AsyncGenerator[None, None]:
        lock = self._locks[key]
        async with lock:
            yield

    async def close(self) -> None:
        self._locks.clear()
