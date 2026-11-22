from typing import Any

from aiogram import loggers
from aiogram.methods import TelegramMethod
from aiogram.methods.base import TelegramType

from .base import BaseRequestMiddleware, RequestContext


class RequestLogging(BaseRequestMiddleware):
    def __init__(self, ignore_methods: list[type[TelegramMethod[Any]]] | None = None):
        """
        Middleware for logging outgoing requests

        :param ignore_methods: methods to ignore in logging middleware
        """
        self.ignore_methods = ignore_methods or []

    async def __call__(self, ctx: RequestContext[TelegramType]) -> TelegramType:
        if type(ctx.method) not in self.ignore_methods:
            loggers.middlewares.info(
                "Make request with method=%r by bot id=%d",
                type(ctx.method).__name__,
                ctx.bot.id,
            )
        return await ctx.next()
