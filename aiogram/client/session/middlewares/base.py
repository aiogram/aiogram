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
        make_request: NextRequestMiddlewareType,
        bot: "Bot",
        method: TelegramMethod[TelegramObject],
    ) -> Response[TelegramObject]:
        """
        Execute middleware

        :param make_request: Wrapped make_request in middlewares chain
        :param bot: bot for request making
        :param method: Request method (Subclass of :class:`aiogram.methods.base.TelegramMethod`)

        :return: :class:`aiogram.methods.Response`
        """
        pass
