from typing import Any, Optional
from warnings import warn

from .base import BaseStorage


def warn_storage_is_dummy() -> None:
    warn(
        "You haven’t set any storage yet so no states and no data will be saved. \n"
        "You can connect MemoryStorage for debug purposes or non-essential data.",
        UserWarning,
        5,
    )
    return None


class DummyStorage(BaseStorage[Any]):
    async def get_state(self, key: str, default: Optional[str] = None) -> None:
        return warn_storage_is_dummy()

    async def set_state(self, key: str, state: Optional[str]) -> None:
        return warn_storage_is_dummy()

    async def get_data(self, key: str, default: Any = None) -> None:
        return warn_storage_is_dummy()

    async def set_data(self, key: str, data: Any) -> None:
        return warn_storage_is_dummy()

    async def update_data(self, key: str, data: Any) -> None:
        return warn_storage_is_dummy()

    async def close(self) -> None:
        return warn_storage_is_dummy()

    async def wait_closed(self) -> None:
        return warn_storage_is_dummy()

    async def reset_data(self, key: str) -> None:
        return warn_storage_is_dummy()

    async def reset_state(self, key: str, with_data: Optional[bool] = True) -> None:
        return warn_storage_is_dummy()

    async def finish(self, key: str) -> None:
        return warn_storage_is_dummy()
