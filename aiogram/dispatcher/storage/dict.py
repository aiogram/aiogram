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
        self._data: Dict[str, _UserStorageMetaData] = {}

    def _make_spot_for_key(self, key: str) -> None:
        if key not in self._data:
            self._data[key] = {"state": None, "data": {}}

    async def get_state(self, key: str) -> Optional[str]:
        self._make_spot_for_key(key)
        return self._data[key]["state"]

    async def get_data(self, key: str) -> Dict[str, Any]:
        self._make_spot_for_key(key=key)
        return copy.deepcopy(self._data[key]["data"])

    async def update_data(self, key: str, data: Optional[Dict[str, Any]] = None) -> None:
        if data is None:
            data = {}
        self._make_spot_for_key(key=key)
        self._data[key]["data"].update(data)

    async def set_state(self, key: str, state: Optional[str] = None) -> None:
        self._make_spot_for_key(key=key)
        self._data[key]["state"] = state

    async def set_data(self, key: str, data: Optional[Dict[str, Any]] = None) -> None:
        self._make_spot_for_key(key=key)
        self._data[key]["data"] = copy.deepcopy(data)  # type: ignore

    async def wait_closed(self) -> None:
        pass

    async def close(self) -> None:
        self._data.clear()
