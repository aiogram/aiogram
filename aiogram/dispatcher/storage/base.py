import abc
from typing import Generic, Optional, TypeVar

_DataT = TypeVar("_DataT")


class BaseStorage(Generic[_DataT], abc.ABC):
    @abc.abstractmethod
    async def get_state(self, key: str) -> Optional[str]:
        raise NotImplementedError

    @abc.abstractmethod
    async def set_state(self, key: str, state: Optional[str]) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    async def get_data(self, key: str) -> _DataT:
        raise NotImplementedError

    @abc.abstractmethod
    async def set_data(self, key: str, data: Optional[_DataT]) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    async def update_data(self, key: str, data: _DataT) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    async def close(self) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    async def wait_closed(self) -> None:
        raise NotImplementedError

    # naively implemented basic, base member methods
    async def reset_state(self, key: str, with_data: bool = True) -> None:
        await self.set_state(key=key, state=None)

        if with_data:
            await self.set_data(key=key, data=None)

    async def reset_data(self, key: str) -> None:
        await self.set_data(key=key, data=None)

    async def finish(self, key: str) -> None:
        await self.reset_state(key=key, with_data=True)
