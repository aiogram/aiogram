from __future__ import annotations

from functools import partial
from typing import (
    TYPE_CHECKING,
    Any,
    Awaitable,
    Callable,
    List,
    Optional,
    Sequence,
    Union,
    overload,
)

from aiogram.client.session.middlewares.base import (
    NextRequestMiddlewareType,
    RequestMiddlewareType,
)
from aiogram.methods import Response
from aiogram.methods.base import TelegramMethod, TelegramType
from aiogram.types import TelegramObject

if TYPE_CHECKING:
    from aiogram import Bot


class RequestMiddlewareManager(Sequence[RequestMiddlewareType]):
    def __init__(self) -> None:
        self._middlewares: List[RequestMiddlewareType] = []

    def register(
        self,
        middleware: RequestMiddlewareType,
    ) -> RequestMiddlewareType:
        self._middlewares.append(middleware)
        return middleware

    def unregister(self, middleware: RequestMiddlewareType) -> None:
        self._middlewares.remove(middleware)

    def __call__(
        self,
        middleware: Optional[RequestMiddlewareType] = None,
    ) -> Union[Callable[[RequestMiddlewareType], RequestMiddlewareType], RequestMiddlewareType,]:
        if middleware is None:
            return self.register
        return self.register(middleware)

    @overload
    def __getitem__(self, item: int) -> RequestMiddlewareType:
        pass

    @overload
    def __getitem__(self, item: slice) -> Sequence[RequestMiddlewareType]:
        pass

    def __getitem__(
        self, item: Union[int, slice]
    ) -> Union[RequestMiddlewareType, Sequence[RequestMiddlewareType]]:
        return self._middlewares[item]

    def __len__(self) -> int:
        return len(self._middlewares)

    def wrap_middlewares(
        self,
        callback: Callable[[Bot, TelegramMethod], Awaitable[Response]],
        **kwargs: Any,
    ) -> NextRequestMiddlewareType:
        middleware = partial(callback, **kwargs)
        for m in reversed(self._middlewares):
            middleware = partial(m, middleware)  # type: ignore
        return middleware
