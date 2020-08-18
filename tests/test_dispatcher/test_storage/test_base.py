from typing import Any, Optional

import pytest

from aiogram.dispatcher.storage.base import BaseStorage

try:
    from asynctest import CoroutineMock, patch
except ImportError:
    from unittest.mock import AsyncMock as CoroutineMock, patch  # type: ignore


STORAGE_ABSTRACT_METHODS = {
    "get_data",
    "get_state",
    "set_data",
    "set_state",
    "update_data",
    "close",
    "wait_closed",
}


class TestBaseStorage:
    def test_do_not_impl_abstract_methods(self):
        with pytest.raises(TypeError):

            class etcd(BaseStorage):  # example of bad not implemented storage
                nothing = lambda: None

            etcd()

    def test_do_impl_abstract_methods(self):
        class good(BaseStorage):
            async def get_state(self, key: str) -> Optional[str]:
                pass

            async def set_state(self, key: str, state: Optional[str]) -> None:
                pass

            async def get_data(self, key: str) -> Any:
                pass

            async def set_data(self, key: str, data: Optional[Any]) -> None:
                pass

            async def update_data(self, key: str, data: Any) -> None:
                pass

            async def close(self) -> None:
                pass

            async def wait_closed(self) -> None:
                pass

        good()
