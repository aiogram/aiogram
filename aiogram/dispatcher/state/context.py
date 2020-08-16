from typing import Any, Callable, Dict, Generic, Mapping, Optional

from aiogram.dispatcher.storage.base import BaseStorage

from .._typedef import StorageDataT


def _default_key_maker(chat_id: Optional[int] = None, user_id: Optional[int] = None) -> str:
    if chat_id is None and user_id is None:
        raise ValueError("`user` or `chat` parameter is required but no one is provided!")

    if user_id is None and chat_id is not None:
        user_id = chat_id
    elif user_id is not None and chat_id is None:
        chat_id = user_id
    return f"{chat_id}:{user_id}"


class CurrentUserContext(Generic[StorageDataT]):
    __slots__ = "key", "storage"

    def __init__(
        self,
        storage: BaseStorage[StorageDataT],
        chat_id: Optional[int],
        user_id: Optional[int],
        key_maker: Callable[[Optional[int], Optional[int]], str] = _default_key_maker,
    ):
        assert (
            chat_id or user_id
        ) is not None, "Either chat_id or user_id should be non-None value"

        self.storage = storage
        self.key = key_maker(chat_id, user_id)

    async def get_state(self, default: Optional[str] = None) -> Optional[str]:
        return await self.storage.get_state(self.key, default=default)

    async def get_data(self) -> StorageDataT:
        return await self.storage.get_data(self.key)

    async def update_data(self, data: Optional[StorageDataT] = None, **kwargs: Any) -> None:
        if data is not None and not isinstance(data, Mapping):
            raise ValueError("Data is expected to be a map")  # todo

        temp_data: Dict[str, Any] = {}

        if isinstance(data, Mapping):
            temp_data.update(**data)

        temp_data.update(**kwargs)

        await self.storage.update_data(self.key, data=temp_data)  # type: ignore

    async def set_state(self, state: Optional[str] = None) -> None:
        await self.storage.set_state(self.key, state=state)

    async def set_data(self, data: Optional[StorageDataT] = None) -> None:
        await self.storage.set_data(self.key, data=data)

    async def reset_state(self, with_data: bool = True) -> None:
        await self.storage.reset_state(self.key, with_data=with_data)

    async def reset_data(self) -> None:
        await self.storage.reset_data(self.key)

    async def finish(self) -> None:
        await self.storage.finish(self.key)
