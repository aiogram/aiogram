from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Awaitable, Callable

from aiogram.methods import Response, TelegramMethod
from aiogram.types import TelegramObject

if TYPE_CHECKING:
    from ...bot import Bot


NextRequestMiddlewareType = Callable[
    ["Bot", TelegramMethod[TelegramObject]], Awaitable[Response[TelegramObject]]
]


class BaseRequestMiddleware(ABC):
    """
    Generic middleware class
    """

    @abstractmethod
    async def __call__(
        self,
        bot: "Bot",
        method: TelegramMethod[TelegramObject],
        make_request: NextRequestMiddlewareType,
    ) -> Response[TelegramObject]:
        """
        Execute middleware

        :param bot: bot for request making
        :param method: Request method (Subclass of :class:`aiogram.methods.base.TelegramMethod`)
        :param make_request: Wrapped make_request in middlewares chain

        :return: :class:`aiogram.methods.Response`
        """
        pass
