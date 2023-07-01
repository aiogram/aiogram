from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Awaitable, Callable, Union

from aiogram.methods import Response, TelegramMethod
from aiogram.methods.base import TelegramType

if TYPE_CHECKING:
    from ...bot import Bot

NextRequestMiddlewareType = Callable[["Bot", TelegramMethod], Awaitable[Response]]
RequestMiddlewareType = Union[
    "BaseRequestMiddleware",
    Callable[
        [NextRequestMiddlewareType, "Bot", TelegramMethod],
        Awaitable[Response],
    ],
]


class BaseRequestMiddleware(ABC):
    """
    Generic middleware class
    """

    @abstractmethod
    async def __call__(
        self,
        make_request: NextRequestMiddlewareType[TelegramType],
        bot: "Bot",
        method: TelegramMethod[TelegramType],
    ) -> Response[TelegramType]:
        """
        Execute middleware

        :param make_request: Wrapped make_request in middlewares chain
        :param bot: bot for request making
        :param method: Request method (Subclass of :class:`aiogram.methods.base.TelegramMethod`)

        :return: :class:`aiogram.methods.Response`
        """
        pass
