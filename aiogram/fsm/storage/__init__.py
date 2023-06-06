from .base import BaseEventIsolation, BaseStorage, StorageKey
from .memory import (
    DisabledEventIsolation,
    MemoryStorage,
    MemoryStorageRecord,
    SimpleEventIsolation,
)

try:
    from .redis import DefaultKeyBuilder, KeyBuilder, RedisEventIsolation, RedisStorage
except ModuleNotFoundError:
    from aiogram import loggers

    loggers.dispatcher.warning(
        msg="NOTE that Redis package should be installed to use RedisStorage"
    )


__all__ = (
    "StorageKey",
    "BaseStorage",
    "BaseEventIsolation",
    "MemoryStorageRecord",
    "MemoryStorage",
    "DisabledEventIsolation",
    "SimpleEventIsolation",
    "KeyBuilder",
    "DefaultKeyBuilder",
    "RedisStorage",
    "RedisEventIsolation",
)
