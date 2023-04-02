import functools
from typing import Any, Callable, Dict, List, Optional, Sequence, Union, overload

from aiogram.dispatcher.event.bases import (
    MiddlewareEventType,
    MiddlewareType,
    NextMiddlewareType,
)
from aiogram.dispatcher.event.handler import CallbackType
from aiogram.types import TelegramObject


class MiddlewareManager(Sequence[MiddlewareType[TelegramObject]]):
    def __init__(self) -> None:
        self._middlewares: List[MiddlewareType[TelegramObject]] = []

    def register(
        self,
        middleware: MiddlewareType[TelegramObject],
    ) -> MiddlewareType[TelegramObject]:
        self._middlewares.append(middleware)
        return middleware

    def unregister(self, middleware: MiddlewareType[TelegramObject]) -> None:
        self._middlewares.remove(middleware)

    def __call__(
        self,
        middleware: Optional[MiddlewareType[TelegramObject]] = None,
    ) -> Union[
        Callable[[MiddlewareType[TelegramObject]], MiddlewareType[TelegramObject]],
        MiddlewareType[TelegramObject],
    ]:
        if middleware is None:
            return self.register
        return self.register(middleware)

    @overload
    def __getitem__(self, item: int) -> MiddlewareType[TelegramObject]:
        pass

    @overload
    def __getitem__(self, item: slice) -> Sequence[MiddlewareType[TelegramObject]]:
        pass

    def __getitem__(
        self, item: Union[int, slice]
    ) -> Union[MiddlewareType[TelegramObject], Sequence[MiddlewareType[TelegramObject]]]:
        return self._middlewares[item]

    def __len__(self) -> int:
        return len(self._middlewares)

    @staticmethod
    def wrap_middlewares(
        middlewares: Sequence[MiddlewareType[MiddlewareEventType]], handler: CallbackType
    ) -> NextMiddlewareType[MiddlewareEventType]:
        @functools.wraps(handler)
        def handler_wrapper(event: TelegramObject, kwargs: Dict[str, Any]) -> Any:
            return handler(event, **kwargs)

        middleware = handler_wrapper
        for m in reversed(middlewares):
            middleware = functools.partial(m, middleware)
        return middleware
