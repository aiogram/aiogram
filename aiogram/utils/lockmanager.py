from __future__ import annotations

import logging
from asyncio import Lock
from types import TracebackType
from typing import Dict, Optional, Type

logger = logging.getLogger(__name__)


class CantDeleteWithWaiters(Exception):
    """Sync primitive with waiters cant be deleted"""

    pass


class LockManager:
    def __init__(self, storage_data: Dict[str, Lock], key: str = "global"):
        self.storage_data = storage_data
        self.key = key
        self._current_lock: Optional[Lock] = None

    async def __aenter__(self) -> None:
        await self.acquire()

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        self.release()

    async def acquire(self) -> None:
        self._current_lock = self.get_lock(self.key)
        await self._current_lock.acquire()

    def release(self) -> None:
        if not self._current_lock:
            self._current_lock = self.get_lock(self.key)
        try:
            self._current_lock.release()
        finally:
            if not self._current_lock.locked() and not self._current_lock._waiters:  # type: ignore
                self.del_lock(self.key)

    def get_lock(self, key: str) -> Lock:
        """
        Return Lock from storage,
        if key not exist in storage then create lock
        :param key: key
        :return: Lock
        """
        return self.storage_data.setdefault(key, Lock())

    def del_lock(self, key: str) -> None:
        """
        Delete lock from storage,
        raise CantDeleteWithWaiters exception
        if key for deleting not found logging this
        :param key: key
        :return:
        """
        lock = self.storage_data.get(key)
        if not lock:
            logger.warning("Can`t find Lock by key to delete %s" % key)
        elif lock._waiters:  # type: ignore
            raise CantDeleteWithWaiters("Can`t delete Lock with waiters %s" % lock)
        else:
            del self.storage_data[key]
