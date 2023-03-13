from asyncio import Lock
from collections import defaultdict
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from typing import Any, AsyncGenerator, DefaultDict, Dict, Hashable, Optional

from aiogram.fsm.state import State
from aiogram.fsm.storage.base import (
    BaseEventIsolation,
    BaseStorage,
    StateType,
    StorageKey,
)


@dataclass
class MemoryStorageRecord:
    data: Dict[str, Any] = field(default_factory=dict)
    state: Optional[str] = None


class MemoryStorage(BaseStorage):
    """
    Default FSM storage, stores all data in :class:`dict` and loss everything on shutdown

    .. warning::

        Is not recommended using in production in due to you will lose all data
        when your bot restarts
    """

    def __init__(self) -> None:
        self.storage: DefaultDict[StorageKey, MemoryStorageRecord] = defaultdict(
            MemoryStorageRecord
        )

    async def close(self) -> None:
        pass

    async def set_state(self, key: StorageKey, state: StateType = None) -> None:
        self.storage[key].state = state.state if isinstance(state, State) else state

    async def get_state(self, key: StorageKey) -> Optional[str]:
        return self.storage[key].state

    async def set_data(self, key: StorageKey, data: Dict[str, Any]) -> None:
        self.storage[key].data = data.copy()

    async def get_data(self, key: StorageKey) -> Dict[str, Any]:
        return self.storage[key].data.copy()


class DisabledEventIsolation(BaseEventIsolation):
    @asynccontextmanager
    async def lock(self, key: StorageKey) -> AsyncGenerator[None, None]:
        yield

    async def close(self) -> None:
        pass


class SimpleEventIsolation(BaseEventIsolation):
    def __init__(self) -> None:
        # TODO: Unused locks cleaner is needed
        self._locks: DefaultDict[Hashable, Lock] = defaultdict(Lock)

    @asynccontextmanager
    async def lock(self, key: StorageKey) -> AsyncGenerator[None, None]:
        lock = self._locks[key]
        async with lock:
            yield

    async def close(self) -> None:
        self._locks.clear()
