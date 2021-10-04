import logging
from typing import TYPE_CHECKING, Awaitable, Callable, List, Optional, Type

from aiogram import loggers
from aiogram.methods import TelegramMethod
from aiogram.methods.base import Response
from aiogram.types import TelegramObject

from .base import BaseRequestMiddleware

if TYPE_CHECKING:
    from ...bot import Bot

NextRequestMiddlewareType = Callable[
    ["Bot", TelegramMethod[TelegramObject]], Awaitable[Response[TelegramObject]]
]

logger = logging.getLogger(__name__)


class RequestLogging(BaseRequestMiddleware):
    def __init__(
        self, ignore_methods: Optional[List[Type[TelegramMethod[TelegramObject]]]] = None
    ):
        self.ignore_methods = ignore_methods if ignore_methods else []

    async def __call__(
        self,
        bot: "Bot",
        method: TelegramMethod[TelegramObject],
        make_request: NextRequestMiddlewareType,
    ) -> Response[TelegramObject]:
        if type(method) not in self.ignore_methods:
            loggers.middlewares.info(
                "Make request with method=%s by bot id=%d",
                method.__class__.__name__,
                bot.id,
            )
        return await make_request(bot, method)
