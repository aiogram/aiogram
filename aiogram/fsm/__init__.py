from contextlib import suppress

from .context import FSMContext
from .middleware import FSMContextMiddleware
from .state import State, StatesGroup, StatesGroupMeta
from .storage import (
    BaseEventIsolation,
    BaseStorage,
    DisabledEventIsolation,
    MemoryStorage,
    MemoryStorageRecord,
    SimpleEventIsolation,
    StorageKey,
)

with suppress(ImportError):
    from .storage import (
        DefaultKeyBuilder,
        KeyBuilder,
        RedisEventIsolation,
        RedisStorage,
    )

from .strategy import FSMStrategy, apply_strategy

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
    "FSMContext",
    "State",
    "StatesGroup",
    "StatesGroupMeta",
    "FSMContextMiddleware",
    "FSMStrategy",
    "apply_strategy",
)
