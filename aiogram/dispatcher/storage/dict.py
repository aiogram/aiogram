import copy
from typing import Any, Dict, Optional

from typing_extensions import TypedDict

from .base import BaseStorage


class _UserStorageMetaData(TypedDict):
    state: Optional[str]
    data: Dict[str, Any]


class DictStorage(BaseStorage[Dict[str, Any]]):
    """
    Python dictionary data structure based state storage.
    Not the most persistent storage, not recommended for in-production environments.
    """

    def __init__(self) -> None:
        self.data: Dict[str, _UserStorageMetaData] = {}

    def resolve_address(self, key: str) -> None:
        if key not in self.data:
            self.data[key] = {"state": None, "data": {}}

    async def get_state(self, key: str) -> Optional[str]:
        self.resolve_address(key)
        return self.data[key]["state"]

    async def get_data(self, key: str) -> Dict[str, Any]:
        self.resolve_address(key=key)
        return copy.deepcopy(self.data[key]["data"])

    async def update_data(self, key: str, data: Optional[Dict[str, Any]] = None) -> None:
        if data is None:
            data = {}
        self.resolve_address(key=key)
        self.data[key]["data"].update(data)

    async def set_state(self, key: str, state: Optional[str] = None) -> None:
        self.resolve_address(key=key)
        self.data[key]["state"] = state

    async def set_data(self, key: str, data: Optional[Dict[str, Any]] = None) -> None:
        self.resolve_address(key=key)
        self.data[key]["data"] = copy.deepcopy(data)  # type: ignore

    async def reset_state(self, key: str, with_data: bool = True) -> None:
        await self.set_state(key=key, state=None)
        if with_data:
            await self.set_data(key=key, data={})

    async def wait_closed(self) -> None:
        pass

    async def close(self) -> None:
        self.data.clear()
