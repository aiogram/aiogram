import logging
from typing import TYPE_CHECKING, Any, List, Optional, Type

from aiogram import loggers
from aiogram.methods import TelegramMethod
from aiogram.methods.base import Response, TelegramType

from .base import BaseRequestMiddleware, NextRequestMiddlewareType

if TYPE_CHECKING:
    from ...bot import Bot

logger = logging.getLogger(__name__)


class RequestLogging(BaseRequestMiddleware):
    def __init__(self, ignore_methods: Optional[List[Type[TelegramMethod[Any]]]] = None):
        """
        Middleware for logging outgoing requests

        :param ignore_methods: methods to ignore in logging middleware
        """
        self.ignore_methods = ignore_methods if ignore_methods else []

    async def __call__(
        self,
        make_request: NextRequestMiddlewareType[TelegramType],
        bot: "Bot",
        method: TelegramMethod[TelegramType],
    ) -> Response[TelegramType]:
        if type(method) not in self.ignore_methods:
            loggers.middlewares.info(
                "Make request with method=%r by bot id=%d",
                type(method).__name__,
                bot.id,
            )
        return await make_request(bot, method)
