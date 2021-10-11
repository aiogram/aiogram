from asyncio import Lock
from collections import defaultdict
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from typing import Any, AsyncGenerator, DefaultDict, Dict, Optional

from aiogram import Bot
from aiogram.dispatcher.fsm.state import State
from aiogram.dispatcher.fsm.storage.base import BaseStorage, StateType, StorageKey


@dataclass
class MemoryStorageRecord:
    data: Dict[str, Any] = field(default_factory=dict)
    state: Optional[str] = None
    lock: Lock = field(default_factory=Lock)


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

    @asynccontextmanager
    async def lock(self, bot: Bot, key: StorageKey) -> AsyncGenerator[None, None]:
        async with self.storage[key].lock:
            yield None

    async def set_state(self, bot: Bot, key: StorageKey, state: StateType = None) -> None:
        self.storage[key].state = state.state if isinstance(state, State) else state

    async def get_state(self, bot: Bot, key: StorageKey) -> Optional[str]:
        return self.storage[key].state

    async def set_data(self, bot: Bot, key: StorageKey, data: Dict[str, Any]) -> None:
        self.storage[key].data = data.copy()

    async def get_data(self, bot: Bot, key: StorageKey) -> Dict[str, Any]:
        return self.storage[key].data.copy()
